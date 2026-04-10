from __future__ import annotations

import os
import subprocess
from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path

from flext_infra import FlextInfraInternalDependencySyncService
from tests import u

_REPO_URL = "https://github.com/flext-sh/flext.git"


@contextmanager
def temporary_env(**updates: str | None) -> Generator[None]:
    previous = {key: os.environ.get(key) for key in updates}
    try:
        for key, value in updates.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value
        yield
    finally:
        for key, value in previous.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value


def create_git_repo(tmp_path: Path, name: str) -> Path:
    repo = tmp_path / name
    repo.mkdir(parents=True, exist_ok=True)
    (repo / "README.md").write_text(f"# {name}\n", encoding="utf-8")
    u.Infra.Tests.initialize_git_repo(repo)
    return repo


def create_bare_remote(source_repo: Path, remote_root: Path, name: str) -> Path:
    remote_root.mkdir(parents=True, exist_ok=True)
    remote_repo = remote_root / name
    subprocess.run(
        ["git", "clone", "--bare", str(source_repo), str(remote_repo)],
        check=True,
        capture_output=True,
        text=True,
    )
    return remote_repo


def add_origin(repo_root: Path, remote_repo: Path) -> None:
    subprocess.run(
        ["git", "remote", "add", "origin", str(remote_repo)],
        cwd=repo_root,
        check=True,
        capture_output=True,
        text=True,
    )


def configure_github_rewrite(home_root: Path, remote_parent: Path) -> None:
    home_root.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [
            "git",
            "config",
            "--global",
            f"url.file://{remote_parent}/.insteadOf",
            "https://github.com/flext-sh/",
        ],
        check=True,
        capture_output=True,
        text=True,
        env={**os.environ, "HOME": str(home_root)},
    )


def test_ensure_symlink_creates_and_replaces_targets(tmp_path: Path) -> None:
    source = tmp_path / "source"
    source.mkdir()

    new_target = tmp_path / "new-target"
    assert FlextInfraInternalDependencySyncService.ensure_symlink(
        new_target,
        source,
    ).is_success
    assert new_target.is_symlink()

    existing_dir = tmp_path / "existing-dir"
    existing_dir.mkdir()
    (existing_dir / "file.txt").write_text("old", encoding="utf-8")
    assert FlextInfraInternalDependencySyncService.ensure_symlink(
        existing_dir,
        source,
    ).is_success
    assert existing_dir.is_symlink()

    other = tmp_path / "other"
    other.mkdir()
    wrong_link = tmp_path / "wrong-link"
    wrong_link.symlink_to(other.resolve(), target_is_directory=True)
    assert FlextInfraInternalDependencySyncService.ensure_symlink(
        wrong_link,
        source,
    ).is_success
    assert wrong_link.resolve() == source.resolve()


def test_ensure_symlink_fails_when_parent_path_is_a_file(tmp_path: Path) -> None:
    source = tmp_path / "source"
    source.mkdir()
    parent_file = tmp_path / "parent"
    parent_file.write_text("not a directory", encoding="utf-8")

    result = FlextInfraInternalDependencySyncService.ensure_symlink(
        parent_file / "target",
        source,
    )

    assert result.is_failure


def test_ensure_checkout_clones_with_local_github_rewrite(tmp_path: Path) -> None:
    source = create_git_repo(tmp_path, "source")
    remotes = tmp_path / "remotes"
    create_bare_remote(source, remotes, "flext.git")
    home = tmp_path / "home"
    configure_github_rewrite(home, remotes)

    dep_path = tmp_path / "dep"
    with temporary_env(HOME=str(home)):
        result = FlextInfraInternalDependencySyncService().ensure_checkout(
            dep_path,
            _REPO_URL,
            "main",
        )

    assert result.is_success
    assert (dep_path / ".git").exists()


def test_ensure_checkout_existing_repo_fetches_and_checks_out(tmp_path: Path) -> None:
    source = create_git_repo(tmp_path, "source")
    remote_repo = create_bare_remote(source, tmp_path / "remotes", "origin.git")
    dep_path = create_git_repo(tmp_path, "dep")
    add_origin(dep_path, remote_repo)

    result = FlextInfraInternalDependencySyncService().ensure_checkout(
        dep_path,
        _REPO_URL,
        "main",
    )

    assert result.is_success


def test_ensure_checkout_rejects_invalid_repo_url_and_ref(tmp_path: Path) -> None:
    service = FlextInfraInternalDependencySyncService()

    invalid_repo = service.ensure_checkout(tmp_path / "dep-a", "not-a-url", "main")
    invalid_ref = service.ensure_checkout(tmp_path / "dep-b", _REPO_URL, "invalid@ref!")

    assert invalid_repo.is_failure
    assert invalid_ref.is_failure


def test_ensure_checkout_fails_when_fetch_cannot_reach_origin(tmp_path: Path) -> None:
    dep_path = create_git_repo(tmp_path, "dep")

    result = FlextInfraInternalDependencySyncService().ensure_checkout(
        dep_path,
        _REPO_URL,
        "main",
    )

    assert result.is_failure


def test_ensure_checkout_fails_when_requested_ref_is_missing(tmp_path: Path) -> None:
    source = create_git_repo(tmp_path, "source")
    remote_repo = create_bare_remote(source, tmp_path / "remotes", "origin.git")
    dep_path = create_git_repo(tmp_path, "dep")
    add_origin(dep_path, remote_repo)

    result = FlextInfraInternalDependencySyncService().ensure_checkout(
        dep_path,
        _REPO_URL,
        "release/does-not-exist",
    )

    assert result.is_failure


def test_ensure_checkout_replaces_existing_symlink_and_directory(
    tmp_path: Path,
) -> None:
    source = create_git_repo(tmp_path, "source")
    remotes = tmp_path / "remotes"
    create_bare_remote(source, remotes, "flext.git")
    home = tmp_path / "home"
    configure_github_rewrite(home, remotes)

    other = tmp_path / "other"
    other.mkdir()
    dep_symlink = tmp_path / "dep-symlink"
    dep_symlink.symlink_to(other.resolve(), target_is_directory=True)
    dep_dir = tmp_path / "dep-dir"
    dep_dir.mkdir()
    (dep_dir / "old.txt").write_text("old", encoding="utf-8")

    with temporary_env(HOME=str(home)):
        symlink_result = FlextInfraInternalDependencySyncService().ensure_checkout(
            dep_symlink,
            _REPO_URL,
            "main",
        )
        dir_result = FlextInfraInternalDependencySyncService().ensure_checkout(
            dep_dir,
            _REPO_URL,
            "main",
        )

    assert symlink_result.is_success
    assert dir_result.is_success
    assert (dep_symlink / ".git").exists()
    assert (dep_dir / ".git").exists()
