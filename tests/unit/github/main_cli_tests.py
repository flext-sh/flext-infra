"""CLI contract tests for the centralized github CLI group."""

from __future__ import annotations

from pathlib import Path

import pytest
from flext_tests import tm

from flext_core import r
from flext_infra import FlextInfra, infra, main as infra_main
from tests import m


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
    captured: list[m.Infra.GithubPullRequestWorkspaceRequest] = []

    def _capture(
        _self: FlextInfra,
        params: m.Infra.GithubPullRequestWorkspaceRequest,
    ) -> r[m.Infra.GithubPullRequestWorkspaceReport]:
        captured.append(params)
        return r[m.Infra.GithubPullRequestWorkspaceReport].ok(
            m.Infra.GithubPullRequestWorkspaceReport(
                total=0,
                success=0,
                fail=0,
                outcomes=(),
            ),
        )

    monkeypatch.setattr(
        type(infra),
        "run_github_workspace_pull_requests",
        _capture,
    )

    result = infra_main([
        "github",
        "pr-workspace",
        "--workspace",
        str(tmp_path),
        "--projects",
        "flext-core",
        "--projects",
        "flext-api",
    ])

    tm.that(result, eq=0)
    tm.that(captured[0].projects, eq=["flext-core", "flext-api"])
