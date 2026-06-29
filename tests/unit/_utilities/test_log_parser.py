"""Tests for FlextInfraUtilitiesLogParser.extract_errors.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

import pytest

from flext_infra._utilities.log_parser import FlextInfraUtilitiesLogParser
from tests.constants import c
from tests.typings import t


class TestsFlextInfraUtilitiesLogParser:
    def test_missing_file_returns_zero_empty(self, tmp_path: Path) -> None:
        result = FlextInfraUtilitiesLogParser.extract_errors(
            tmp_path / "nonexistent.log"
        )

        assert result == (0, [])

    def test_empty_file_returns_zero_empty(self, tmp_path: Path) -> None:
        log_file = tmp_path / "empty.log"
        log_file.write_text("", encoding="utf-8")

        count, lines = FlextInfraUtilitiesLogParser.extract_errors(log_file)

        assert count == 0
        assert list(lines) == []

    def test_file_with_only_whitespace_returns_zero_empty(self, tmp_path: Path) -> None:
        log_file = tmp_path / "whitespace.log"
        log_file.write_text("   \n\n   \n", encoding="utf-8")

        count, lines = FlextInfraUtilitiesLogParser.extract_errors(log_file)

        assert count == 0
        assert list(lines) == []

    def test_error_line_is_detected(self, tmp_path: Path) -> None:
        log_file = tmp_path / "errors.log"
        log_file.write_text(f"{c.Tests.LOG_ERROR_LINES[0]}\n", encoding="utf-8")

        count, lines = FlextInfraUtilitiesLogParser.extract_errors(log_file)

        assert count == 1
        assert c.Tests.LOG_ERROR_LINES[0] in lines[0]

    def test_fail_line_is_detected(self, tmp_path: Path) -> None:
        log_file = tmp_path / "fail.log"
        log_file.write_text(f"{c.Tests.LOG_ERROR_LINES[1]}\n", encoding="utf-8")

        count, lines = FlextInfraUtilitiesLogParser.extract_errors(log_file)

        assert count == 1
        assert c.Tests.LOG_ERROR_LINES[1] in lines[0]

    def test_noise_patterns_are_skipped(self, tmp_path: Path) -> None:
        log_file = tmp_path / "noise.log"
        log_file.write_text(
            "\n".join(c.Tests.LOG_NOISE_LINES[:2]) + "\n",
            encoding="utf-8",
        )

        count, lines = FlextInfraUtilitiesLogParser.extract_errors(log_file)

        assert count == 0
        assert list(lines) == []

    def test_max_lines_truncates_results(self, tmp_path: Path) -> None:
        error_lines = "\n".join(f"ERROR: error line {i}" for i in range(10))
        log_file = tmp_path / "many_errors.log"
        log_file.write_text(error_lines + "\n", encoding="utf-8")

        count, lines = FlextInfraUtilitiesLogParser.extract_errors(
            log_file, max_lines=3
        )

        assert count == 10
        assert len(list(lines)) == 3

    def test_default_max_lines_is_five(self, tmp_path: Path) -> None:
        error_lines = "\n".join(f"ERROR: error line {i}" for i in range(10))
        log_file = tmp_path / "many_errors2.log"
        log_file.write_text(error_lines + "\n", encoding="utf-8")

        count, lines = FlextInfraUtilitiesLogParser.extract_errors(log_file)

        assert count == 10
        assert len(list(lines)) == 5

    def test_python_file_error_lines_detected(self, tmp_path: Path) -> None:
        log_file = tmp_path / "pyerr.log"
        log_file.write_text("  foo/bar.py:42 ImportError\n", encoding="utf-8")

        count, _lines = FlextInfraUtilitiesLogParser.extract_errors(log_file)

        assert count == 1

    def test_mixed_errors_and_noise(self, tmp_path: Path) -> None:
        content = "\n".join(c.Tests.LOG_MIXED_SCENARIO_LINES) + "\n"
        log_file = tmp_path / "mixed.log"
        log_file.write_text(content, encoding="utf-8")

        count, _lines = FlextInfraUtilitiesLogParser.extract_errors(log_file)

        assert count == 2

    @pytest.mark.parametrize(
        ("line", "expected_count"),
        c.Tests.LOG_PATTERN_CASES,
    )
    def test_pattern_matching(
        self, tmp_path: Path, line: str, expected_count: int
    ) -> None:
        log_file = tmp_path / "pattern.log"
        log_file.write_text(line + "\n", encoding="utf-8")

        count, _ = FlextInfraUtilitiesLogParser.extract_errors(log_file)

        assert count == expected_count

    @pytest.mark.parametrize("line", c.Tests.LOG_ERROR_LINES)
    def test_error_lines_follow_prefix_rule(self, line: str) -> None:
        assert c.Tests.LOG_ERROR_PREFIX_RE.match(line)


__all__: t.StrSequence = []
