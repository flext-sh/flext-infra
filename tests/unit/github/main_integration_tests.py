"""CLI integration tests for github commands against real workspaces."""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_infra import main
from flext_tests import tm
from tests import u

if TYPE_CHECKING:
    from pathlib import Path


def test_workflows_subcommand_applies_templates(tmp_path: Path) -> None:
    workspace = u.Tests.create_github_workspace(
        tmp_path, project_names=("flext-a", "flext-b")
    )
    report_path = tmp_path / "workflows.json"

    result = main([
        "github",
        "workflows",
        "--workspace",
        str(workspace),
        "--apply",
        "--report",
        str(report_path),
    ])

    tm.that(result, eq=0)
    tm.that(report_path.is_file(), eq=True)
    tm.that((workspace / "flext-a/.github/workflows/ci.yml").is_file(), eq=True)
    tm.that((workspace / "flext-b/.github/workflows/ci.yml").is_file(), eq=True)


def test_lint_subcommand_writes_report(tmp_path: Path) -> None:
    workspace = u.Tests.create_github_workspace(tmp_path, project_names=("flext-a",))
    report_path = tmp_path / "lint.json"

    result = main([
        "github",
        "lint",
        "--workspace",
        str(workspace),
        "--report",
        str(report_path),
    ])

    tm.that(report_path.is_file(), eq=True)
    tm.that(result, eq=0)


def test_pr_status_succeeds_for_minimal_repo_without_open_pull_request(
    tmp_path: Path,
) -> None:
    workspace = u.Tests.create_github_workspace(tmp_path, project_names=("flext-a",))

    result = main([
        "github",
        "pr",
        "--repo-root",
        str(workspace / "flext-a"),
        "--action",
        "status",
    ])

    tm.that(result, eq=0)
    log_path = workspace / "flext-a/.reports/workspace/pr/flext-a.log"
    tm.that(log_path.is_file(), eq=True)
    tm.that(log_path.read_text(encoding="utf-8"), lacks="No module named")


def test_pr_subcommand_rejects_removed_lifecycle_action(tmp_path: Path) -> None:
    workspace = u.Tests.create_github_workspace(tmp_path, project_names=("flext-a",))

    result = main([
        "github",
        "pr",
        "--repo-root",
        str(workspace / "flext-a"),
        "--action",
        "merge",
    ])

    tm.that(result, ne=0)
