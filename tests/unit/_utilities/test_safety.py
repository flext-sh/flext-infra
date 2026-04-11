from __future__ import annotations

from pathlib import Path

from tests import c, u


def _run_git(repo: Path, *args: str) -> None:
    result = u.Cli.run_raw(
        [c.Infra.GIT, *args],
        cwd=repo,
    )
    assert result.success
    assert result.value.exit_code == 0


def _init_git_repo(repo: Path) -> None:
    _run_git(repo, "init")
    _run_git(repo, "settings", "user.email", "tests@flext.local")
    _run_git(repo, "settings", "user.name", "Flext Tests")
    (repo / "README.md").write_text("# test repo\n", encoding="utf-8")
    _run_git(repo, "add", "README.md")
    _run_git(repo, "commit", "-m", "initial commit")


class TestSafetyCheckpoint:
    def test_create_checkpoint_returns_empty_for_clean_repo(
        self,
        tmp_path: Path,
    ) -> None:
        _init_git_repo(tmp_path)

        result = u.Infra.create_checkpoint(tmp_path)

        assert result.success
        assert result.value == ""

    def test_create_checkpoint_creates_stash_for_dirty_repo(
        self,
        tmp_path: Path,
    ) -> None:
        _init_git_repo(tmp_path)
        (tmp_path / "notes.txt").write_text("dirty\n", encoding="utf-8")

        result = u.Infra.create_checkpoint(tmp_path, label="test-checkpoint")

        assert result.success
        assert "stash@{0}" in result.value
        assert "test-checkpoint:" in result.value

    def test_create_checkpoint_returns_empty_for_non_git_folder(
        self,
        tmp_path: Path,
    ) -> None:
        result = u.Infra.create_checkpoint(tmp_path)

        assert result.success
        assert result.value == ""


class TestSafetyRollback:
    def test_rollback_to_checkpoint_invalid_stash_ref_fails(
        self,
        tmp_path: Path,
    ) -> None:
        _init_git_repo(tmp_path)

        result = u.Infra.rollback_to_checkpoint(tmp_path, "stash@{999}")

        assert result.failure

    def test_rollback_to_checkpoint_succeeds_for_non_repo(self, tmp_path: Path) -> None:
        result = u.Infra.rollback_to_checkpoint(tmp_path)

        assert result.success
        assert result.value is True
