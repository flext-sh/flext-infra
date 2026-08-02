"""Public github service tests using real workspaces."""

from __future__ import annotations

import re
from pathlib import Path

from flext_infra import c, config, r
from flext_infra.gates.actionlint import FlextInfraActionlintGate
from flext_tests import tm
from tests import m, u


class TestsInfraGithub:
    """Verify GitHub automation through the public infrastructure facade."""

    def test_actionlint_gate_checks_every_workflow_in_one_execution(
        self, tmp_path: Path
    ) -> None:
        """Execute Actionlint once with every workflow discovered for a project."""
        project = tmp_path / "project"
        workflows_dir = project / c.Infra.GITHUB_WORKFLOWS_DIR
        workflows_dir.mkdir(parents=True)
        expected = tuple(
            c.Infra.GITHUB_WORKFLOWS_DIR + "/" + name
            for name in ("ci.yml", "release.yaml")
        )
        for workflow in expected:
            (project / workflow).write_text("name: CI\n", encoding="utf-8")
        runner = u.Tests.SequenceRunner([r.ok(u.Tests.stub_run())])

        result = FlextInfraActionlintGate(tmp_path, runner=runner).check(
            project,
            m.Infra.GateContext(workspace=tmp_path, reports_dir=tmp_path / "reports"),
        )

        tm.that(result.result.passed, eq=True)
        tm.that(len(runner.commands), eq=1)
        tm.that(tuple(runner.commands[0][-len(expected) :]), eq=expected)

    def test_pull_request_fails_for_minimal_repo(self, tmp_path: Path) -> None:
        """Run native gh and return a typed failure for a non-repository."""
        workspace = u.Tests.create_github_workspace(
            tmp_path, project_names=("flext-a",)
        )

        result = u.Infra.run_github_pull_request(
            m.Infra.GithubPullRequestRequest(
                repo_root=str(workspace / "flext-a"),
                action=c.Infra.PullRequestAction.STATUS,
            )
        )

        tm.fail(result)
        tm.that((result.error or ""), has="PR operation exited with code")
        log_path = workspace / "flext-a/.reports/workspace/pr/flext-a.log"
        tm.that(log_path.is_file(), eq=True)
        tm.that(log_path.read_text(encoding="utf-8"), lacks="No module named")

    def test_pull_request_create_requires_noninteractive_content(
        self, tmp_path: Path
    ) -> None:
        """Reject create before transport when title or body is absent."""
        workspace = u.Tests.create_github_workspace(
            tmp_path, project_names=("flext-a",)
        )

        result = u.Infra.run_github_pull_request(
            m.Infra.GithubPullRequestRequest(
                repo_root=str(workspace / "flext-a"),
                action=c.Infra.PullRequestAction.CREATE,
                head="feature/arbitrary",
            )
        )

        tm.fail(result)
        tm.that((result.error or ""), has="title is required")

    def test_every_workflow_make_verb_exists_in_the_codegen_ssot(self) -> None:
        """Reject any CI workflow verb absent from the canonical verb SSOT.

        ``config/codegen.yaml`` declares the only public Make verbs a generated
        Makefile exposes. A workflow that invokes anything else can never run:
        the workspace CI historically called ``make boot`` and ``make val``,
        neither of which the SSOT declares, so the first blocking step failed
        with "No rule to make target". Comparing against the SSOT (instead of
        hardcoding verb names) keeps this test correct when the SSOT changes.
        """
        declared = {verb.name for verb in config.Infra.codegen.make.verbs}
        repository_root = Path(__file__).resolve().parents[3]
        workflows_dir = repository_root / c.Infra.GITHUB_WORKFLOWS_DIR
        workflows = sorted({
            path
            for pattern in c.Infra.GITHUB_WORKFLOW_GLOBS
            for path in workflows_dir.glob(pattern)
            if path.is_file()
        })
        invoked: dict[str, set[str]] = {}
        for workflow in workflows:
            if not workflow.is_file():
                continue
            verbs = {
                match.group(1)
                for match in re.finditer(
                    r"run:\s*make\s+([a-z][a-z0-9-]*)", workflow.read_text("utf-8")
                )
            }
            undeclared = verbs - declared
            if undeclared:
                invoked[str(workflow.relative_to(repository_root))] = undeclared

        tm.that(invoked, eq={})
