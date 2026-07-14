"""Public github CLI tests using real workspaces."""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_infra import main as infra_main
from tests import u
from flext_tests import tm

if TYPE_CHECKING:
    from pathlib import Path


def test_main_returns_zero_on_help() -> None:
    tm.that(infra_main(["github", "--help"]), eq=0)


def test_main_returns_one_without_subcommand() -> None:
    tm.that(infra_main(["github"]), eq=1)


def test_main_returns_nonzero_on_unknown() -> None:
    tm.that(infra_main(["github", "unknown-command"]), ne=0)


def test_pr_workspace_accepts_repeated_project_options(tmp_path: Path) -> None:
    workspace = u.Tests.create_github_workspace(
        tmp_path,
        project_names=("flext-a", "flext-b", "flext-c"),
        pr_exit_codes={"flext-a": "0", "flext-b": "0", "flext-c": "1"},
    )

    result = infra_main([
        "github",
        "pr-workspace",
        "--workspace",
        str(workspace),
        "--projects",
        "flext-a",
        "--projects",
        "flext-b",
    ])

    report_dir = workspace / ".reports/workspace/pr"
    tm.that(result, eq=0)
    assert (report_dir / "flext-a.log").is_file()
    assert (report_dir / "flext-b.log").is_file()
    assert not (report_dir / "flext-c.log").exists()
