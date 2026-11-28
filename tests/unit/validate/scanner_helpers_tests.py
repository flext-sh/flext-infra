"""Tests for scanner helper methods.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from tests import c, tm, u

if TYPE_CHECKING:
    from pathlib import Path


class TestsFlextInfraScannerHelpers:
    """Tests for scanner helper methods."""

    @staticmethod
    def test_iter_matching_files_glob_patterns(tmp_path: Path) -> None:
        """Canonical file selection respects include/exclude glob patterns."""
        (tmp_path / "file1.py").write_text("")
        (tmp_path / "file2.txt").write_text("")
        (tmp_path / "file3.py").write_text("")
        (tmp_path / "test.py").write_text("")
        u.Tests.initialize_git_repo(tmp_path)
        included = u.Infra.iter_matching_files(tmp_path, includes=["*.py"])
        tm.that(len(included), eq=3)
        excluded = u.Infra.iter_matching_files(
            tmp_path,
            includes=["*.py"],
            excludes=["test*"],
        )
        tm.that(len(excluded), eq=2)

    @staticmethod
    def test_iter_matching_files_skips_directories(tmp_path: Path) -> None:
        """Canonical file selection skips directories."""
        (tmp_path / "file.txt").write_text("")
        (tmp_path / "subdir").mkdir()
        u.Tests.initialize_git_repo(tmp_path)
        files = u.Infra.iter_matching_files(tmp_path, includes=["*"])
        tm.that(len(files), eq=1)

    @staticmethod
    def test_iter_matching_files_prefers_git_tracked_files(
        tmp_path: Path,
    ) -> None:
        """Tracked selection excludes files retained by the source inventory."""
        u.Tests.git_bootstrap(tmp_path, ("init",))
        u.Tests.configure_git_identity(tmp_path)
        tracked_file = tmp_path / "tracked.py"
        tracked_file.write_text("")
        untracked_file = tmp_path / "untracked.py"
        untracked_file.write_text("")
        u.Tests.git_run(tmp_path, "add", "--", tracked_file.name)

        files = u.Infra.iter_matching_files(tmp_path, includes=["*.py"])

        tm.that(files, eq=[tracked_file])
        tm.ok(untracked_file.is_file())
        tm.that(
            u.Infra.git_source_scope_paths(tmp_path),
            eq=(tracked_file, untracked_file),
        )

    @staticmethod
    def test_iter_matching_files_excludes_git_ignored_explicit_scope(
        tmp_path: Path,
    ) -> None:
        """An ignored nested scope cannot bypass its ancestor repository policy."""
        u.Tests.git_bootstrap(tmp_path, ("init",))
        (tmp_path / c.Infra.GITIGNORE).write_text("scratch/\n", encoding="utf-8")
        scope = tmp_path / "scratch" / "project"
        scope.mkdir(parents=True)
        explicit_file = scope / "README.md"
        explicit_file.write_text("# explicit scope\n", encoding="utf-8")
        relative = explicit_file.relative_to(tmp_path).as_posix()
        tm.that(
            u.Tests.git_capture(tmp_path, "check-ignore", "--", relative).strip(),
            eq=relative,
        )

        files = u.Infra.iter_matching_files(scope, includes=["*.md"])

        tm.that(files, eq=[])
        tm.that(u.Infra.git_source_scope_paths(scope), eq=())
        tm.ok(explicit_file.is_file())

    @staticmethod
    def test_tracked_scope_refreshes_dirty_files_between_scans(
        tmp_path: Path,
    ) -> None:
        """A new source stays unpublished until indexing refreshes tracked scope."""
        u.Tests.git_bootstrap(tmp_path, ("init",))
        source = tmp_path / "src"
        source.mkdir()
        first = source / "first.py"
        first.write_text("", encoding="utf-8")
        u.Tests.git_run(tmp_path, "add", "--", first.relative_to(tmp_path).as_posix())
        tm.that(u.Infra.git_tracked_scope_paths(source), eq=[first])

        second = source / "second.py"
        second.write_text("", encoding="utf-8")
        tm.that(u.Infra.git_tracked_scope_paths(source), eq=[first])
        tm.that(u.Infra.git_source_scope_paths(source), eq=(first, second))
        tm.ok(second.is_file())
        u.Tests.git_run(tmp_path, "add", "--", second.relative_to(tmp_path).as_posix())

        tm.that(u.Infra.git_tracked_scope_paths(source), eq=[first, second])

    @staticmethod
    def test_tracked_scope_refreshes_repository_identity_after_git_init(
        tmp_path: Path,
    ) -> None:
        """New Git identity does not promote unpublished files to tracked scope."""
        source = tmp_path / "src"
        source.mkdir()
        unmanaged = source / "unmanaged.py"
        unmanaged.write_text("", encoding="utf-8")
        tm.that(u.Infra.git_tracked_scope_paths(source), eq=None)

        u.Tests.git_bootstrap(tmp_path, ("init",))
        tm.that(u.Infra.git_tracked_scope_paths(source), eq=[])
        tm.that(u.Infra.git_source_scope_paths(source), eq=(unmanaged,))
        tm.ok(unmanaged.is_file())
        u.Tests.git_run(
            tmp_path, "add", "--", unmanaged.relative_to(tmp_path).as_posix()
        )

        tm.that(u.Infra.git_tracked_scope_paths(source), eq=[unmanaged])

    @staticmethod
    def test_empty_git_scope_does_not_fall_back_to_filesystem_scan(
        tmp_path: Path,
    ) -> None:
        """A valid empty Git scope stays distinct from an external scope."""
        init_result = u.Cli.run_raw(["git", "init"], cwd=tmp_path)
        tm.ok(init_result)
        tm.ok(u.Cli.process_succeeded(init_result.value.outcome))
        scope = tmp_path / "empty"
        scope.mkdir()

        tm.that(u.Infra.git_tracked_scope_paths(scope), eq=[])
