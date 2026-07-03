"""Tests for scanner helper methods.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

from flext_tests import tm

from tests.constants import c
from tests.typings import t
from tests.utilities import u
from flext_infra.validate.scanner import FlextInfraTextPatternScanner


class TestScannerHelpers:
    """Tests for scanner helper methods."""

    def test_iter_matching_files_glob_patterns(self, tmp_path: Path) -> None:
        """Canonical file selection respects include/exclude glob patterns."""
        (tmp_path / "file1.py").write_text("")
        (tmp_path / "file2.txt").write_text("")
        (tmp_path / "file3.py").write_text("")
        (tmp_path / "test.py").write_text("")
        included = u.Infra.iter_matching_files(tmp_path, includes=["*.py"])
        tm.that(len(included), eq=3)
        excluded = u.Infra.iter_matching_files(
            tmp_path,
            includes=["*.py"],
            excludes=["test*"],
        )
        tm.that(len(excluded), eq=2)

    def test_iter_matching_files_skips_directories(self, tmp_path: Path) -> None:
        """Canonical file selection skips directories."""
        (tmp_path / "file.txt").write_text("")
        (tmp_path / "subdir").mkdir()
        files = u.Infra.iter_matching_files(tmp_path, includes=["*"])
        tm.that(len(files), eq=1)

    def test_iter_matching_files_prefers_git_tracked_files(
        self, tmp_path: Path
    ) -> None:
        """Canonical file selection prefers tracked files when Git is active."""
        init_result = u.Cli.run_raw(["git", "init"], cwd=tmp_path)
        assert init_result.success
        assert init_result.value.exit_code == 0
        email_result = u.Cli.run_raw(
            ["git", "config", "user.email", "test@example.com"],
            cwd=tmp_path,
        )
        assert email_result.success
        assert email_result.value.exit_code == 0
        name_result = u.Cli.run_raw(
            ["git", "config", "user.name", "Test User"],
            cwd=tmp_path,
        )
        assert name_result.success
        assert name_result.value.exit_code == 0
        tracked_file = tmp_path / "tracked.py"
        tracked_file.write_text("")
        untracked_file = tmp_path / "untracked.py"
        untracked_file.write_text("")
        add_result = u.Cli.run_raw(["git", "add", "tracked.py"], cwd=tmp_path)
        assert add_result.success
        assert add_result.value.exit_code == 0

        files = u.Infra.iter_matching_files(tmp_path, includes=["*.py"])

        tm.that(files, eq=[tracked_file, untracked_file])

    def test_count_matches(self, tmp_path: Path) -> None:
        """_count_matches counts regex matches and handles edge cases."""
        f = tmp_path / "test.txt"
        f.write_text("hello hello hello")
        regex = c.Tests.SCANNER_HELLO_RE
        tm.that(FlextInfraTextPatternScanner._count_matches([f], regex).value, eq=3)
        empty = tmp_path / "empty.txt"
        empty.write_text("")
        tm.that(FlextInfraTextPatternScanner._count_matches([empty], regex).value, eq=0)

    def test_count_matches_unreadable_file(self, tmp_path: Path) -> None:
        """_count_matches surfaces an unreadable file as a failure - never skipped."""
        f = tmp_path / "test.txt"
        f.write_text("hello")
        f.chmod(0o000)
        try:
            tm.that(
                FlextInfraTextPatternScanner._count_matches(
                    [f],
                    c.Tests.SCANNER_HELLO_RE,
                ).failure,
                eq=True,
            )
        finally:
            f.chmod(0o644)


__all__: t.StrSequence = []
