"""Public github service tests using real workspaces."""

from __future__ import annotations

import shutil
from typing import TYPE_CHECKING

from tests import m
from tests import u
from flext_tests import tm

if TYPE_CHECKING:
    from pathlib import Path


def test_sync_github_workflows_reports_create_operations(tmp_path: Path) -> None:
    workspace = u.Tests.create_github_workspace(
        tmp_path, project_names=("flext-a", "flext-b")
    )

    result = u.Infra.sync_github_workflows(
        m.Infra.GithubWorkflowSyncRequest(workspace=str(workspace))
    )

    tm.ok(result)
    report = result.unwrap()
    tm.that(report.mode, eq="dry-run")
    tm.that(report.summary, eq={"create": 2})
    tm.that(
        [operation.project for operation in report.operations],
        eq=["flext-a", "flext-b"],
    )


def test_sync_github_workflows_apply_writes_ci_files_and_report(tmp_path: Path) -> None:
    workspace = u.Tests.create_github_workspace(
        tmp_path,
        project_names=("flext-a", "flext-b"),
        source_workflow=(
            "name: CI\n"
            "jobs:\n"
            "  ci:\n"
            "    steps:\n"
            "      - name: Boot (advisory)\n"
            "        run: make boot\n"
            "      - name: Val (advisory)\n"
            "        run: make val\n"
        ),
    )
    report_path = tmp_path / "sync-report.json"

    result = u.Infra.sync_github_workflows(
        m.Infra.GithubWorkflowSyncRequest(
            workspace=str(workspace), apply=True, report=str(report_path)
        )
    )

    tm.ok(result)
    assert report_path.is_file()
    for project_name in ("flext-a", "flext-b"):
        destination = workspace / project_name / ".github/workflows/ci.yml"
        content = destination.read_text(encoding="utf-8")
        assert destination.is_file()
        tm.that(content, has="name: CI")
        tm.that(content, has="- name: Setup (advisory)")
        tm.that(content, has="run: make setup")
        tm.that(content, has="run: make val")
        tm.that(content, lacks="run: make boot")


def test_sync_github_workflows_prunes_noncanonical_files(tmp_path: Path) -> None:
    workspace = u.Tests.create_github_workspace(tmp_path, project_names=("flext-a",))
    extra_workflow = workspace / "flext-a/.github/workflows/extra.yml"
    extra_workflow.parent.mkdir(parents=True, exist_ok=True)
    extra_workflow.write_text("name: Extra\n", encoding="utf-8")

    result = u.Infra.sync_github_workflows(
        m.Infra.GithubWorkflowSyncRequest(
            workspace=str(workspace), apply=True, prune=True
        )
    )

    tm.ok(result)
    report = result.unwrap()
    tm.that(report.summary, eq={"create": 1, "prune": 1})
    assert not extra_workflow.exists()


def test_lint_github_workflows_writes_report(tmp_path: Path) -> None:
    workspace = u.Tests.create_github_workspace(tmp_path, project_names=("flext-a",))
    report_path = tmp_path / "lint-report.json"

    result = u.Infra.lint_github_workflows(
        m.Infra.GithubWorkflowLintRequest(
            workspace=str(workspace), report=str(report_path), strict=True
        )
    )

    tm.ok(result)
    outcome = result.unwrap()
    assert report_path.is_file()
    if shutil.which("actionlint") is None:
        tm.that(outcome.status, eq="skipped")
    else:
        tm.that(outcome.status, eq="ok")


def test_run_github_pull_request_fails_for_minimal_repo(tmp_path: Path) -> None:
    workspace = u.Tests.create_github_workspace(tmp_path, project_names=("flext-a",))

    result = u.Infra.run_github_pull_request(
        m.Infra.GithubPullRequestRequest(
            repo_root=str(workspace / "flext-a"), action="status"
        )
    )

    tm.fail(result)
    tm.that((result.error or ""), has="PR operation exited with code")
