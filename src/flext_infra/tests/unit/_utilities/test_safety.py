from __future__ import annotations

from pathlib import Path

from flext_infra.tests.constants import c
from flext_infra.tests.utilities import u


def _run_git(repo: Path, *args: str) -> None:
    result = u.Cli.run_raw(
        [c.Infra.GIT, *args],
        cwd=repo,
    )
    assert result.success
    assert result.value.exit_code == 0


def _init_git_repo(repo: Path) -> None:
    _run_git(repo, "init")
    _run_git(repo, "config", "user.email", "tests@flext.local")
    _run_git(repo, "config", "user.name", "Flext Tests")
    (repo / "README.md").write_text("# test repo\n", encoding="utf-8")
    _run_git(repo, "add", "README.md")
    _run_git(repo, "commit", "-m", "initial commit")


class TestsFlextInfraUtilitiessafety:
    def test_create_checkpoint_returns_empty_for_clean_repo(
        self,
        tmp_path: Path,
    ) -> None:
        _init_git_repo(tmp_path)

        result = u.Infra.create_checkpoint(tmp_path)

        assert result.success
        assert result.value == ""

    def test_create_checkpoint_fails_for_dirty_repo(
        self,
        tmp_path: Path,
    ) -> None:
        _init_git_repo(tmp_path)
        (tmp_path / "notes.txt").write_text("dirty\n", encoding="utf-8")

        result = u.Infra.create_checkpoint(tmp_path, label="test-checkpoint")

        assert result.failure
        assert "dirty git worktree" in (result.error or "")

    def test_create_checkpoint_returns_empty_for_non_git_folder(
        self,
        tmp_path: Path,
    ) -> None:
        result = u.Infra.create_checkpoint(tmp_path)

        assert result.success
        assert result.value == ""

    def test_rollback_to_checkpoint_rejects_repository_checkpoint(
        self,
        tmp_path: Path,
    ) -> None:
        _init_git_repo(tmp_path)

        result = u.Infra.rollback_to_checkpoint(tmp_path, "checkpoint-ref")

        assert result.failure
        assert "repository-wide checkpoint rollback is unsupported" in (
            result.error or ""
        )

    def test_rollback_to_checkpoint_succeeds_for_non_repo(self, tmp_path: Path) -> None:
        result = u.Infra.rollback_to_checkpoint(tmp_path)

        assert result.success
        assert result.value is True
