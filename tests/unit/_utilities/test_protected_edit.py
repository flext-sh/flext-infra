"""Tests for protected source edits through the public infrastructure facade.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

from flext_tests import tm

from tests import c, m, u


class TestsFlextInfraUtilitiesProtectedEdit:
    def test_preview_source_writes_restores_original_sources_after_preview(
        self, tmp_path: Path
    ) -> None:
        py_file = tmp_path / "sample.py"
        original_source = "def value() -> int:\n    return 1\n"
        updated_source = "def value() -> int:\n    return 2\n"
        py_file.write_text(original_source, encoding=c.Cli.ENCODING_DEFAULT)

        result = u.Infra.preview_source_writes(
            {py_file: updated_source}, workspace=tmp_path, gates=("lint",)
        )

        tm.that(result, eq=(True, []))
        tm.that(py_file.read_text(encoding=c.Cli.ENCODING_DEFAULT), eq=original_source)

    def test_protected_source_write_skips_pytest_for_non_test_file(
        self, tmp_path: Path
    ) -> None:
        py_file = tmp_path / "sample.py"
        original_source = "def value() -> int:\n    return 1\n"
        updated_source = "def value() -> int:\n    return 2\n"
        py_file.write_text(original_source, encoding=c.Cli.ENCODING_DEFAULT)

        result = u.Infra.protected_source_write(
            py_file,
            request=m.Infra.ProtectedSourceWriteRequest(
                workspace=tmp_path, updated_source=updated_source, gates=("lint",)
            ),
        )

        tm.that(result, eq=(True, []))
        tm.that(
            py_file.read_text(encoding=c.Cli.ENCODING_DEFAULT).rstrip("\n"),
            eq=updated_source.rstrip("\n"),
        )

    def test_protected_source_write_treats_no_tests_collected_as_success(
        self, tmp_path: Path
    ) -> None:
        tests_dir = tmp_path / "tests"
        tests_dir.mkdir()
        py_file = tests_dir / "test_placeholder.py"
        original_source = "def helper() -> int:\n    return 1\n"
        updated_source = "def helper() -> int:\n    return 2\n"
        py_file.write_text(original_source, encoding=c.Cli.ENCODING_DEFAULT)

        result = u.Infra.protected_source_write(
            py_file,
            request=m.Infra.ProtectedSourceWriteRequest(
                workspace=tmp_path, updated_source=updated_source, gates=("lint",)
            ),
        )

        tm.that(result, eq=(True, []))
        tm.that(
            py_file.read_text(encoding=c.Cli.ENCODING_DEFAULT).rstrip("\n"),
            eq=updated_source.rstrip("\n"),
        )

    def test_protected_source_writes_applies_request_options(
        self, tmp_path: Path
    ) -> None:
        left_file = tmp_path / "left.py"
        right_file = tmp_path / "right.py"
        left_file.write_text("VALUE = 1\n", encoding=c.Cli.ENCODING_DEFAULT)
        right_file.write_text("VALUE = 10\n", encoding=c.Cli.ENCODING_DEFAULT)

        result = u.Infra.protected_source_writes(
            {left_file: "VALUE = 2\n", right_file: "VALUE = 20\n"},
            request=m.Infra.ProtectedSourceWritesRequest(
                workspace=tmp_path, gates=("lint",), skip_pytest=True
            ),
        )

        tm.that(result, eq=(True, []))
        tm.that(
            left_file.read_text(encoding=c.Cli.ENCODING_DEFAULT).rstrip("\n"),
            eq="VALUE = 2",
        )
        tm.that(
            right_file.read_text(encoding=c.Cli.ENCODING_DEFAULT).rstrip("\n"),
            eq="VALUE = 20",
        )
