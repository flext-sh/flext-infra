"""CLI integration tests for GitHub pull-request commands."""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_infra import main
from flext_tests import tm
from tests import u

if TYPE_CHECKING:
    from pathlib import Path


def test_pr_subcommand_returns_nonzero_for_minimal_repo(tmp_path: Path) -> None:
    workspace = u.Tests.create_github_workspace(tmp_path, project_names=("flext-a",))

    result = main([
        "github",
        "pr",
        "--repo-root",
        str(workspace / "flext-a"),
        "--action",
        "status",
    ])

    tm.that(result, ne=0)
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
