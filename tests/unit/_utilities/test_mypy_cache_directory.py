"""Behavior tests for the shared Mypy cache directory and its lock.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

from flext_infra import config
from tests import c, tm, u


class TestsFlextInfraMypyCacheDirectory:
    """The Mypy cache is shared by every checkout of one repository."""

    @staticmethod
    def test_mypy_cache_is_shared_by_every_checkout_of_one_repository(
        tmp_path: Path,
    ) -> None:
        """Linked worktrees and clones with one origin share one warm cache."""
        spec = config.Infra.codegen.make.mypy_cache
        origin = "https://example.test/fixture/shared.git"
        primary = tmp_path / "primary"
        primary.mkdir()
        u.Tests.initialize_git_repo(primary, origin)
        clone = tmp_path / "clone"
        clone.mkdir()
        u.Tests.initialize_git_repo(clone, origin)
        lane = u.Tests.git_linked_lane(tmp_path, primary, "lane")
        cached = u.Infra.mypy_cache_directory(primary)
        tm.that(
            cached.is_relative_to(u.Infra.external_cache_directory(spec)),
            eq=True,
        )
        tm.fail(cached.is_relative_to(tmp_path))
        tm.that(u.Infra.mypy_cache_directory(lane), eq=cached)
        tm.that(u.Infra.mypy_cache_directory(clone), eq=cached)
        # The identity names the interpreter implementation, never a path.
        tm.that(cached.name, eq=u.Infra.environment_cache_identity())
        tm.that(cached.name, has=str(sys.version_info.major))
        tm.fail(str(tmp_path) in str(cached))

    @staticmethod
    def test_mypy_cache_without_origin_follows_the_git_common_directory(
        tmp_path: Path,
    ) -> None:
        """A repository without origin is shared by its linked worktrees only."""
        primary = u.Tests.git_repository(tmp_path, "primary")
        u.Tests.git_run(primary, "remote", "remove", c.Infra.GIT_ORIGIN)
        other = u.Tests.git_repository(tmp_path, "other")
        u.Tests.git_run(other, "remote", "remove", c.Infra.GIT_ORIGIN)
        lane = u.Tests.git_linked_lane(tmp_path, primary, "lane")
        cached = u.Infra.mypy_cache_directory(primary)
        tm.that(u.Infra.mypy_cache_directory(lane), eq=cached)
        tm.ok(u.Infra.mypy_cache_directory(other) != cached)

    @staticmethod
    def test_mypy_cache_separates_projects_and_repositories(
        tmp_path: Path,
    ) -> None:
        """Distinct relative project paths and distinct repositories never collide."""
        primary = tmp_path / "primary"
        primary.mkdir()
        u.Tests.initialize_git_repo(primary, "https://example.test/fixture/alpha.git")
        member = primary / "member"
        member.mkdir()
        foreign = tmp_path / "foreign"
        foreign.mkdir()
        u.Tests.initialize_git_repo(foreign, "https://example.test/fixture/beta.git")
        lane = u.Tests.git_linked_lane(tmp_path, primary, "lane")
        (lane / "member").mkdir()
        root_cache = u.Infra.mypy_cache_directory(primary)
        member_cache = u.Infra.mypy_cache_directory(member)
        tm.ok(member_cache != root_cache)
        tm.that(u.Infra.mypy_cache_directory(lane / "member"), eq=member_cache)
        tm.ok(u.Infra.mypy_cache_directory(foreign) != root_cache)

    @staticmethod
    def test_mypy_cache_survives_lock_metadata_and_environment_changes(
        tmp_path: Path,
    ) -> None:
        """Rotating the lock, breaking metadata or recreating .venv keeps the key."""
        project = tmp_path / "project"
        project.mkdir()
        u.Tests.initialize_git_repo(project, "https://example.test/fixture/gamma.git")
        cached = u.Infra.mypy_cache_directory(project)
        (project / c.Infra.UV_LOCK_FILENAME).write_text("rotated\n", encoding="utf-8")
        tm.that(u.Infra.mypy_cache_directory(project), eq=cached)
        metadata = project / c.PYPROJECT_FILENAME
        metadata.write_text("[project", encoding="utf-8")
        before = metadata.read_bytes()
        tm.that(u.Infra.mypy_cache_directory(project), eq=cached)
        tm.that(metadata.read_bytes(), eq=before)
        for generation in ("first", "second"):
            environment = project / ".venv" / "bin"
            environment.mkdir(parents=True, exist_ok=True)
            (environment / "python").write_text(generation, encoding="utf-8")
            tm.that(u.Infra.mypy_cache_directory(project), eq=cached)
            shutil.rmtree(project / ".venv")

    @staticmethod
    def test_mypy_cache_lock_excludes_other_processes(tmp_path: Path) -> None:
        """Only one process at a time may run Mypy against a shared cache."""
        project = tmp_path / "project"
        project.mkdir()
        u.Tests.initialize_git_repo(project, "https://example.test/fixture/lock.git")
        cache = u.Infra.mypy_cache_directory(project)
        probe = (
            "import sys\nfrom filelock import FileLock, Timeout\n"
            "try:\n    FileLock(sys.argv[1], timeout=0.2).acquire()\n"
            "except Timeout:\n    raise SystemExit(3)\n"
        )
        lock_file = cache.with_name(f"{cache.name}.lock")
        tm.fail(lock_file.is_relative_to(cache))
        with u.Infra.mypy_cache_lock(project):
            held = u.Cli.run_raw(
                [sys.executable, "-c", probe, str(lock_file)],
                cwd=tmp_path,
            )
            tm.that(tm.ok(held).outcome.raw_return_code, eq=3)
        free = u.Cli.run_raw(
            [sys.executable, "-c", probe, str(lock_file)],
            cwd=tmp_path,
        )
        tm.that(tm.ok(free).outcome.raw_return_code, eq=0)

    @staticmethod
    def test_mypy_cache_of_a_directory_outside_git_is_its_own(
        tmp_path: Path,
    ) -> None:
        """A directory with no repository is its own identity, never a failure."""
        plain = tmp_path / "plain"
        plain.mkdir()
        sibling = tmp_path / "sibling"
        sibling.mkdir()
        tm.that(
            u.Infra.mypy_cache_directory(plain),
            eq=u.Infra.mypy_cache_directory(plain),
        )
        tm.ok(
            u.Infra.mypy_cache_directory(plain) != u.Infra.mypy_cache_directory(sibling)
        )
