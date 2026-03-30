"""CLI contract tests for flext_infra.github.__main__."""

from __future__ import annotations

from pathlib import Path

import pytest
from flext_core import r
from flext_tests import tm

from flext_infra.github import __main__ as github_main
from tests import m


def test_main_returns_zero_on_help() -> None:
    """--help should exit with code 0."""
    with pytest.raises(SystemExit) as exc_info:
        github_main.main(["--help"])
    tm.that(exc_info.value.code, eq=0)


def test_main_returns_nonzero_on_unknown() -> None:
    """Unknown subcommand returns exit code != 0."""
    result = github_main.main(["unknown-command"])
    tm.that(result, ne=0)


def test_pr_workspace_accepts_repeated_project_options(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: list[m.Infra.GithubPrWorkspaceInput] = []

    def _capture(params: m.Infra.GithubPrWorkspaceInput) -> r[bool]:
        captured.append(params)
        return r[bool].ok(True)

    monkeypatch.setattr(
        github_main.FlextInfraGithubCli,
        "_handle_pr_workspace",
        staticmethod(_capture),
    )

    result = github_main.main([
        "pr-workspace",
        "--workspace",
        str(tmp_path),
        "--project",
        "flext-core",
        "--project",
        "flext-api",
    ])

    tm.that(result, eq=0)
    tm.that(captured[0].project, eq=["flext-core", "flext-api"])
