"""CLI integration tests for github commands against real workspaces."""

from __future__ import annotations

from pathlib import Path

from flext_infra import main
from tests import u


def test_workflows_subcommand_applies_templates(
    tmp_path: Path,
) -> None:
    workspace = u.Tests.create_github_workspace(
        tmp_path,
        project_names=("flext-a", "flext-b"),
    )
    report_path = tmp_path / "workflows.json"

    result = main(
        [
            "github",
            "workflows",
            "--workspace",
            str(workspace),
            "--apply",
            "--report",
            str(report_path),
        ],
    )

    assert result == 0
    assert report_path.is_file()
    assert (workspace / "flext-a/.github/workflows/ci.yml").is_file()
    assert (workspace / "flext-b/.github/workflows/ci.yml").is_file()


def test_lint_subcommand_writes_report(
    tmp_path: Path,
) -> None:
    workspace = u.Tests.create_github_workspace(
        tmp_path,
        project_names=("flext-a",),
    )
    report_path = tmp_path / "lint.json"

    result = main(
        [
            "github",
            "lint",
            "--workspace",
            str(workspace),
            "--report",
            str(report_path),
        ],
    )

    assert report_path.is_file()
    assert result == 0


def test_pr_subcommand_returns_nonzero_for_minimal_repo(
    tmp_path: Path,
) -> None:
    workspace = u.Tests.create_github_workspace(
        tmp_path,
        project_names=("flext-a",),
    )

    result = main(
        [
            "github",
            "pr",
            "--repo-root",
            str(workspace / "flext-a"),
            "--action",
            "status",
        ],
    )

    assert result != 0
