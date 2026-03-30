"""CLI contract tests for flext_infra.github.__main__."""

from __future__ import annotations

import sys
from collections.abc import Sequence
from pathlib import Path

import pytest
from flext_tests import tm

from flext_infra.github import __main__ as github_main


def test_pr_subcommand_preserves_explicit_argv(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: list[str] = []

    def _run_pr(argv: Sequence[str]) -> int:
        captured.extend(argv)
        return 0

    monkeypatch.setattr(github_main, "run_pr", _run_pr)
    exit_code = github_main.run([
        "--workspace",
        str(tmp_path),
        "pr",
        "--repo-root",
        str(tmp_path),
        "--action",
        "status",
    ])
    tm.that(exit_code, eq=0)
    assert captured == [
        "--repo-root",
        str(tmp_path),
        "--action",
        "status",
    ]


def test_lint_rejects_apply_before_subcommand(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        sys,
        "argv",
        ["flext-infra", "--apply", "lint"],
    )
    tm.that(github_main.main(), eq=2)
