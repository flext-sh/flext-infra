"""Public github service tests using real workspaces."""

from __future__ import annotations

import shutil
from pathlib import Path

from tests import m, u


def test_sync_github_workflows_reports_create_operations(
    tmp_path: Path,
) -> None:
    workspace = u.Infra.Tests.create_github_workspace(
        tmp_path,
        project_names=("flext-a", "flext-b"),
    )

    result = u.Infra.sync_github_workflows(
        m.Infra.GithubWorkflowSyncRequest(workspace=str(workspace)),
    )

    assert result.success
    report = result.unwrap()
    assert report.mode == "dry-run"
    assert report.summary == {"create": 2}
    assert [operation.project for operation in report.operations] == [
        "flext-a",
        "flext-b",
    ]


def test_sync_github_workflows_apply_writes_ci_files_and_report(
    tmp_path: Path,
) -> None:
    workspace = u.Infra.Tests.create_github_workspace(
        tmp_path,
        project_names=("flext-a", "flext-b"),
    )
    report_path = tmp_path / "sync-report.json"

    result = u.Infra.sync_github_workflows(
        m.Infra.GithubWorkflowSyncRequest(
            workspace=str(workspace),
            apply=True,
            report=str(report_path),
        ),
    )

    assert result.success
    assert report_path.is_file()
    for project_name in ("flext-a", "flext-b"):
        destination = workspace / project_name / ".github/workflows/ci.yml"
        assert destination.is_file()
        assert "name: CI" in destination.read_text(encoding="utf-8")


def test_sync_github_workflows_prunes_noncanonical_files(
    tmp_path: Path,
) -> None:
    workspace = u.Infra.Tests.create_github_workspace(
        tmp_path,
        project_names=("flext-a",),
    )
    extra_workflow = workspace / "flext-a/.github/workflows/extra.yml"
    extra_workflow.parent.mkdir(parents=True, exist_ok=True)
    extra_workflow.write_text("name: Extra\n", encoding="utf-8")

    result = u.Infra.sync_github_workflows(
        m.Infra.GithubWorkflowSyncRequest(
            workspace=str(workspace),
            apply=True,
            prune=True,
        ),
    )

    assert result.success
    report = result.unwrap()
    assert report.summary == {"create": 1, "prune": 1}
    assert not extra_workflow.exists()


def test_lint_github_workflows_writes_report(
    tmp_path: Path,
) -> None:
    workspace = u.Infra.Tests.create_github_workspace(
        tmp_path,
        project_names=("flext-a",),
    )
    report_path = tmp_path / "lint-report.json"

    result = u.Infra.lint_github_workflows(
        m.Infra.GithubWorkflowLintRequest(
            workspace=str(workspace),
            report=str(report_path),
            strict=True,
        ),
    )

    assert result.success
    outcome = result.unwrap()
    assert report_path.is_file()
    if shutil.which("actionlint") is None:
        assert outcome.status == "skipped"
    else:
        assert outcome.status == "ok"


def test_run_github_pull_request_fails_for_minimal_repo(
    tmp_path: Path,
) -> None:
    workspace = u.Infra.Tests.create_github_workspace(
        tmp_path,
        project_names=("flext-a",),
    )

    result = u.Infra.run_github_pull_request(
        m.Infra.GithubPullRequestRequest(
            repo_root=str(workspace / "flext-a"),
            action="status",
        ),
    )

    assert result.failure
    assert "PR operation exited with code" in (result.error or "")
