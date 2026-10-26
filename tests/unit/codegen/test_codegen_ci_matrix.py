"""Public functional contract for multi-environment CI matrix codegen.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from flext_infra import config
from tests import c, tm, u
from tests.unit.codegen.ci_matrix_support import TestsFlextInfraCodegenCiMatrixSupport


@pytest.mark.slow
class TestsFlextInfraCodegenCiMatrix(TestsFlextInfraCodegenCiMatrixSupport):
    """Prove codegen emits the CI matrix workflow and distro Dockerfiles."""

    @staticmethod
    def test_ci_matrix_profiles_are_topology_complete() -> None:
        """Matrix and distro Dockerfiles cover both repository-local profiles."""
        entries = config.Infra.codegen.templates.entries
        matrix = next(
            entry
            for entry in entries
            if entry.destination == ".github/workflows/ci-matrix.yml"
        )
        tm.that(set(matrix.profiles), eq={"workspace", "standalone"})
        docker_dests = {
            f"tests/fixtures/ci/docker/{name}.Dockerfile"
            for name in ("ubuntu", "debian", "fedora", "alpine", "arch")
        }
        for entry in entries:
            if entry.destination not in docker_dests:
                continue
            tm.that(set(entry.profiles), eq={"workspace", "standalone"})

    @staticmethod
    def test_ci_matrix_workflow_emitted(rendered_project: Path) -> None:
        """Generated project carries .github/workflows/ci-matrix.yml."""
        root = rendered_project
        tm.ok((root / ".github" / "workflows" / "ci-matrix.yml").is_file())

    @staticmethod
    def test_latest_mise_is_owned_only_by_make_setup(
        rendered_project: Path,
    ) -> None:
        """Generated workflows never install Mise or uv beside make setup."""
        root = rendered_project
        workflows = root / ".github" / "workflows"

        for workflow in workflows.glob("*.yml"):
            content = workflow.read_text(encoding="utf-8")
            tm.that(content, lacks="jdx/mise-action")
            tm.that(content, lacks="astral-sh/setup-uv")
            tm.that(content, lacks="Install direnv")

    @staticmethod
    def test_external_attestation_orchestration_is_not_generated_by_flext(
        rendered_project: Path,
    ) -> None:
        """FLEXT exposes primitives without selecting AI Hub's GitHub capability."""
        root = rendered_project
        makefile = (root / "Makefile").read_text(encoding="utf-8")
        tm.that(makefile, lacks="_builtin_checkpoint_")
        tm.fail((root / ".github/scripts/gate-attestation.sh").exists())
        tm.fail((root / ".github/workflows/gate-attestation.yml").exists())
        tm.fail((root / ".github/attestations/allowed_signers").exists())

    @staticmethod
    def test_github_apps_are_not_selected_for_draft_prs(
        rendered_project: Path,
    ) -> None:
        """Versioned app policy reserves external review for non-Draft PRs."""
        root = rendered_project
        tm.fail((root / "cubic.yaml").exists())
        tm.fail((root / ".coderabbit.yaml").exists())

    @staticmethod
    def test_ci_workflow_uses_immutable_action_catalog(
        rendered_project: Path,
    ) -> None:
        """Every generated action reference resolves from the typed action SSOT."""
        root = rendered_project
        workflows = "\n".join(
            (root / ".github" / "workflows" / filename).read_text(encoding="utf-8")
            for filename in ("ci.yml", "ci-matrix.yml")
        )
        catalog = tuple(config.Infra.codegen.github_actions.values())
        used_actions = tuple(
            line.split("uses:", maxsplit=1)[1].strip().split(maxsplit=1)[0]
            for line in workflows.splitlines()
            if "uses:" in line
        )
        tm.that(len(used_actions), gt=0)
        # A reference names a catalog repository, or one of its sub-actions
        # (``actions/cache/restore``), at exactly the catalog version.
        for action in used_actions:
            reference, version = action.rsplit("@", maxsplit=1)
            tm.that(
                any(
                    version == entry.version
                    and (
                        reference == entry.repository
                        or reference.startswith(f"{entry.repository}/")
                    )
                    for entry in catalog
                ),
                eq=True,
                msg=action,
            )

        tm.that(workflows, lacks="continue-on-error")
        tm.that(workflows, lacks="set +e")
        tm.that(workflows, lacks="|| make")
        tm.that(workflows, lacks="soft-pass")

    @staticmethod
    def test_blocking_ci_bootstraps_only_through_make_setup(
        rendered_project: Path,
    ) -> None:
        """Generated CI executes its declared Make lifecycle in policy order."""
        workflow = u.Cli.yaml_load_mapping(
            rendered_project / ".github" / "workflows" / "ci.yml",
        )
        jobs = u.Cli.JSON_MAPPING_ADAPTER.validate_python(workflow["jobs"])
        ci_job = u.Cli.JSON_MAPPING_ADAPTER.validate_python(jobs["ci"])
        steps = [
            u.Cli.JSON_MAPPING_ADAPTER.validate_python(value)
            for value in u.Cli.JSON_LIST_ADAPTER.validate_python(ci_job["steps"])
        ]
        make = config.Infra.codegen.make
        prefix = f"{make.ci.variable}={make.ci.value} make "
        expected = tuple(
            f"{make.ci.variable}={make.ci.value} {step.make_command}"
            for step in make.workflow if "ci" in step.contexts
        )
        observed = tuple(
            command
            for step in steps
            if isinstance(command := step.get("run"), str)
            and command.startswith(prefix)
        )
        tm.that(observed, eq=expected)
        tm.that(workflow.get("permissions"), eq=None)
        permissions = u.Cli.JSON_MAPPING_ADAPTER.validate_python(ci_job["permissions"])
        tm.that(permissions["contents"], eq="read")
        tm.fail("merge-guard" in jobs)

    @staticmethod
    def test_every_approval_verb_blocks_on_push_and_pull_request(
        rendered_project: Path,
    ) -> None:
        """CI runs each approval verb as its own blocking step on every event.

        The former single ``make pre-commit`` step failed unattended runs
        because setup refused a stale lock; setup now provisions whatever the
        locks state (operator-ruling-2026-10-09-setup-resilient), so the gates
        run on push and pull request instead of only on manual dispatch. After
        setup, every verb reports even when an earlier one is red.
        """
        workflow = (rendered_project / ".github" / "workflows" / "ci.yml").read_text(
            encoding="utf-8",
        )
        phases = tuple(
            step for step in config.Infra.codegen.make.workflow if "ci" in step.contexts
        )
        for index, phase in enumerate(phases):
            block = workflow.split(
                f"- name: {phase.make_command} (blocking)", maxsplit=1
            )[1]
            block = block.split("\n      - name:", maxsplit=1)[0]
            tm.that(block, lacks="workflow_dispatch")
            tm.that(block, has=phase.make_command)
            if index:
                tm.that(
                    block,
                    has=f"steps.approval-{phases[0].identity}.outcome == 'success'",
                )
        tm.that(workflow, lacks="- name: Approval (blocking)")

    @staticmethod
    def test_ci_runs_make_test_through_the_persistent_testmon_database(
        rendered_project: Path,
    ) -> None:
        """Cache restore and save reference their actual database producers."""
        workflow = u.Cli.yaml_load_mapping(
            rendered_project / ".github" / "workflows" / "ci.yml",
        )
        jobs = u.Cli.JSON_MAPPING_ADAPTER.validate_python(workflow["jobs"])
        ci_job = u.Cli.JSON_MAPPING_ADAPTER.validate_python(jobs["ci"])
        steps = [
            u.Cli.JSON_MAPPING_ADAPTER.validate_python(value)
            for value in u.Cli.JSON_LIST_ADAPTER.validate_python(ci_job["steps"])
        ]
        make = config.Infra.codegen.make
        test_run = f"{make.ci.variable}={make.ci.value} make {c.Infra.VERB_TEST}"
        test_step = next(step for step in steps if step.get("run") == test_run)
        resolver = next(step for step in steps if step.get("id") == "testmon_path")
        action = config.Infra.codegen.github_actions["cache"]
        restore = next(
            step
            for step in steps
            if step.get("uses") == f"{action.repository}/restore@{action.version}"
            and step.get("name") == "Restore testmon database"
        )
        restore_inputs = u.Cli.JSON_MAPPING_ADAPTER.validate_python(restore["with"])
        tm.that(
            restore_inputs["path"],
            eq=f"${{{{ steps.{resolver['id']}.outputs.database }}}}",
        )
        saves = [
            step
            for step in steps
            if step.get("uses") == f"{action.repository}/save@{action.version}"
            and step.get("name") == "Save testmon database"
        ]
        tm.that(bool(saves), eq=make.testmon_cache_policy.save_enabled)
        if not saves:
            return
        tm.that(saves, len=1)
        save = saves[0]
        save_inputs = u.Cli.JSON_MAPPING_ADAPTER.validate_python(save["with"])
        tm.that(
            save_inputs["path"],
            eq=f"${{{{ steps.{test_step['id']}.outputs.testmon_database }}}}",
        )
        tm.that(save_inputs["key"], eq=restore_inputs["key"])
        tm.that(
            steps.index(resolver)
            < steps.index(restore)
            < steps.index(test_step)
            < steps.index(save),
            eq=True,
        )
        tm.that(
            save["if"],
            has=[
                "always()",
                "!cancelled()",
                f"steps.{test_step['id']}.outputs.testmon_saveable",
                f"steps.{test_step['id']}.outputs.testmon_digest",
            ],
        )

    @staticmethod
    def test_blocking_ci_does_not_configure_github_cli_auth(
        rendered_project: Path,
    ) -> None:
        """FLEXT codegen never selects GitHub CLI authentication."""
        root = rendered_project
        workflow = (root / ".github" / "workflows" / "ci.yml").read_text(
            encoding="utf-8",
        )

        tm.that(workflow, lacks="- name: Configure GitHub authentication")
        tm.that(workflow, lacks="GH_TOKEN: ${{ github.token }}")
        tm.that(workflow, lacks="run: gh auth setup-git")
        steps_index = workflow.index("    steps:")
        setup_index = workflow.index("run: CI=Y make setup")
        tm.ok(steps_index < setup_index)

    @staticmethod
    def test_rendered_workflow_shell_commands_parse(
        rendered_project: Path,
    ) -> None:
        """The real runner shell parses every generated command body.

        Raises:
            TypeError: If workflow job steps must be a sequence.

        """
        root = rendered_project
        workflow = root / ".github" / "workflows" / "ci.yml"
        document = u.Cli.yaml_load_mapping(workflow)
        jobs = u.Cli.JSON_MAPPING_ADAPTER.validate_python(document["jobs"])
        parsed = 0
        for raw_job in jobs.values():
            job = u.Cli.JSON_MAPPING_ADAPTER.validate_python(raw_job)
            steps = job["steps"]
            if not isinstance(steps, list):
                msg = "workflow job steps must be a sequence"
                raise TypeError(msg)
            for raw_step in steps:
                step = u.Cli.JSON_MAPPING_ADAPTER.validate_python(raw_step)
                script = step.get("run")
                if not isinstance(script, str):
                    continue
                outcome = tm.ok(u.Cli.run(["bash", "-n", "-c", script]))
                tm.that(
                    u.Cli.process_succeeded(outcome.outcome),
                    eq=True,
                    msg=outcome.stderr,
                )
                parsed += 1
        tm.that(parsed, gt=0)

    @staticmethod
    def test_rendered_pre_commit_uses_typed_hook_contexts(
        rendered_project: Path,
    ) -> None:
        """Generated hooks select the declared commands at real Git stages."""
        document = u.Cli.yaml_load_mapping(
            rendered_project / ".pre-commit-config.yaml",
        )
        hooks = [
            u.Cli.JSON_MAPPING_ADAPTER.validate_python(hook)
            for repository in u.Cli.JSON_LIST_ADAPTER.validate_python(document["repos"])
            for hook in u.Cli.JSON_LIST_ADAPTER.validate_python(
                u.Cli.JSON_MAPPING_ADAPTER.validate_python(repository)["hooks"],
            )
        ]
        make = config.Infra.codegen.make
        commits = [hook for hook in hooks if hook.get("stages") == ["pre-commit"]]
        tm.that(len(commits), eq=int(make.pre_commit))
        if commits:
            tm.that(
                commits[0]["entry"],
                has=f"{make.ci.variable}={make.ci.pre_commit_value} make check",
            )
        pushes = [hook for hook in hooks if hook.get("stages") == ["pre-push"]]
        expected = tuple(
            step.verb
            for step in make.workflow
            if make.pre_push and "pre_push" in step.contexts
        )
        tm.that(len(pushes), eq=len(expected))
        for hook, verb in zip(pushes, expected, strict=True):
            tm.that(hook["entry"], has=f"make {verb}")
            tm.that(hook["pass_filenames"], eq=False)
            tm.that(hook["always_run"], eq=True)

    @staticmethod
    def test_ci_workflow_cancels_superseded_ref_runs(
        rendered_project: Path,
    ) -> None:
        """Generated CI groups competing runs by workflow and ref."""
        root = rendered_project
        workflow = (root / ".github" / "workflows" / "ci.yml").read_text(
            encoding="utf-8",
        )

        tm.that(workflow, has="concurrency:")
        tm.that(
            workflow,
            has=(
                "group: ${{ github.workflow }}-${{ github.event_name }}-"
                "${{ github.event.pull_request.number || github.ref }}"
            ),
        )
        tm.that(workflow, has="cancel-in-progress: true")

    def test_ci_workflow_is_identical_across_fresh_checkouts(
        self,
        tmp_path: Path,
        rendered_project: Path,
    ) -> None:
        """Equivalent declarations produce the same public CI artifact bytes."""
        root = rendered_project
        workflow = (root / ".github" / "workflows" / "ci.yml").read_text(
            encoding="utf-8",
        )
        root2 = self.render_project(tmp_path / "member-again")
        workflow2 = (root2 / ".github" / "workflows" / "ci.yml").read_text(
            encoding="utf-8",
        )
        tm.that(workflow2, eq=workflow)

    @staticmethod
    def test_docs_workflow_inits_private_submodules_when_configured() -> None:
        """Docs jobs that run make setup must use the same deploy-key init as CI."""
        private = u.CodegenTestSupport.Ci.synthetic_private_submodules()
        tpl = (
            Path(__file__).resolve().parents[3]
            / "src/flext_infra/templates/project/base/.github/workflows/docs.yml.j2"
        )
        spec = u.CodegenTestSupport.Ci.workflow_spec(
            dist="example-workspace",
            make_profile=c.Infra.MakeProfile.WORKSPACE,
            repository_branch="develop",
            ci_trigger_branches=("dev", "develop", "0.12.0-dev", "develop", "main"),
        ).model_copy(update={"private_submodules": private})
        rendered = u.Cli.template_render(tpl, spec)
        tm.ok(rendered)
        rendered_text: str = rendered.value
        tm.that(rendered_text, has="Init private workspace projects")
        tm.that(rendered_text.count("Init private workspace projects"), eq=2)

    @staticmethod
    def test_ci_uses_typed_action_catalog(rendered_project: Path) -> None:
        """Every generated action reference resolves from the typed action SSOT."""
        root = rendered_project
        workflow = (root / ".github" / "workflows" / "ci.yml").read_text(
            encoding="utf-8",
        )
        actions = config.Infra.codegen.github_actions
        for action in actions.values():
            # Every reference to a catalog repository, or to one of its
            # sub-actions (``actions/cache/restore``), pins the catalog version.
            references = re.findall(
                rf"uses: ({re.escape(action.repository)}(?:/[\w.-]+)*)@(\S+)",
                workflow,
            )
            for _reference, version in references:
                tm.that(version, eq=action.version)


__all__: list[str] = ["TestsFlextInfraCodegenCiMatrix"]
