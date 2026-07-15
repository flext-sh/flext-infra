"""Tests for safe checkpoint handling.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

from flext_tests import tm

from tests import c, u


def _run_git(repo: Path, *args: str) -> None:
    result = u.Cli.run_raw([c.Infra.GIT, *args], cwd=repo)
    tm.ok(result)
    tm.that(result.value.exit_code, eq=0)


def _init_git_repo(repo: Path) -> None:
    _run_git(repo, "init")
    _run_git(repo, "config", "user.email", "tests@flext.local")
    _run_git(repo, "config", "user.name", "Flext Tests")
    (repo / "README.md").write_text("# test repo\n", encoding="utf-8")
    _run_git(repo, "add", "README.md")
    _run_git(repo, "commit", "-m", "initial commit")


class TestsFlextInfraUtilitiessafety:
    def test_create_checkpoint_returns_empty_for_clean_repo(
        self, tmp_path: Path
    ) -> None:
        _init_git_repo(tmp_path)

        result = u.Infra.create_checkpoint(tmp_path)

        tm.ok(result)
        tm.that(result.value, eq="")

    def test_create_checkpoint_fails_for_dirty_repo(self, tmp_path: Path) -> None:
        _init_git_repo(tmp_path)
        (tmp_path / "notes.txt").write_text("dirty\n", encoding="utf-8")

        result = u.Infra.create_checkpoint(tmp_path, label="test-checkpoint")

        tm.fail(result)
        tm.that((result.error or ""), has="dirty git worktree")

    def test_create_checkpoint_returns_empty_for_non_git_folder(
        self, tmp_path: Path
    ) -> None:
        result = u.Infra.create_checkpoint(tmp_path)

        tm.ok(result)
        tm.that(result.value, eq="")

    def test_rollback_to_checkpoint_rejects_repository_checkpoint(
        self, tmp_path: Path
    ) -> None:
        _init_git_repo(tmp_path)

        result = u.Infra.rollback_to_checkpoint(tmp_path, "checkpoint-ref")

        tm.fail(result)
        tm.that(
            (result.error or ""),
            has="repository-wide checkpoint rollback is unsupported",
        )

    def test_rollback_to_checkpoint_succeeds_for_non_repo(self, tmp_path: Path) -> None:
        result = u.Infra.rollback_to_checkpoint(tmp_path)

        tm.ok(result)
        tm.that(result.value, eq=True)
