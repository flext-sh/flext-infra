"""CLI contract tests for the centralized github CLI group."""

from __future__ import annotations

from pathlib import Path

import pytest
from flext_tests import tm
from tests import m

from flext_core import r
from flext_infra import main as infra_main
from flext_infra.github.service import FlextInfraGithubService


def test_main_returns_zero_on_help() -> None:
    """--help should exit with code 0."""
    result = infra_main(["github", "--help"])
    tm.that(result, eq=0)


def test_main_returns_nonzero_on_unknown() -> None:
    """Unknown subcommand returns exit code != 0."""
    result = infra_main(["github", "unknown-command"])
    tm.that(result, ne=0)


def test_pr_workspace_accepts_repeated_project_options(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: list[m.Infra.GithubPrWorkspaceInput] = []

    def _capture(
        _self: FlextInfraGithubService,
        params: m.Infra.GithubPrWorkspaceInput,
    ) -> r[bool]:
        captured.append(params)
        return r[bool].ok(True)

    monkeypatch.setattr(
        FlextInfraGithubService,
        "execute_pr_workspace",
        _capture,
    )

    result = infra_main([
        "github",
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
