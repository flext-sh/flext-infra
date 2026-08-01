from __future__ import annotations

from typing import TYPE_CHECKING

from flext_tests import tm
from tests import c, m, u

if TYPE_CHECKING:
    from pathlib import Path


class TestsFlextInfraUtilitiesProtectedEdit:
    def test_preview_source_writes_restores_original_sources_after_preview(
        self, tmp_path: Path
    ) -> None:
        py_file = tmp_path / "sample.py"
        original_source = "def value() -> int:\n    return 1\n"
        updated_source = "def value() -> int:\n    return 2\n"
        py_file.write_text(original_source, encoding=c.Cli.ENCODING_DEFAULT)

        result = u.Infra.preview_source_writes(
            {py_file: updated_source}, workspace=tmp_path
        )

        tm.that(result, eq=(True, []))
        tm.that(py_file.read_text(encoding=c.Cli.ENCODING_DEFAULT), eq=original_source)

    def test_protected_source_write_accepts_valid_source(
        self, tmp_path: Path
    ) -> None:
        py_file = tmp_path / "sample.py"
        original_source = "def value() -> int:\n    return 1\n"
        updated_source = "def value() -> int:\n    return 2\n"
        py_file.write_text(original_source, encoding=c.Cli.ENCODING_DEFAULT)

        result = u.Infra.protected_source_write(
            py_file,
            request=m.Infra.ProtectedSourceWriteRequest(
                workspace=tmp_path, updated_source=updated_source
            ),
        )

        tm.that(result, eq=(True, []))
        tm.that(
            py_file.read_text(encoding=c.Cli.ENCODING_DEFAULT).rstrip("\n"),
            eq=updated_source.rstrip("\n"),
        )

    def test_protected_test_source_is_not_executed(
        self, tmp_path: Path
    ) -> None:
        tests_dir = tmp_path / "tests"
        tests_dir.mkdir()
        py_file = tests_dir / "test_placeholder.py"
        original_source = "def helper() -> int:\n    return 1\n"
        updated_source = (
            "def test_runtime_owner() -> None:\n"
            '    raise RuntimeError("tests run only through make test")\n'
        )
        py_file.write_text(original_source, encoding=c.Cli.ENCODING_DEFAULT)

        result = u.Infra.protected_source_write(
            py_file,
            request=m.Infra.ProtectedSourceWriteRequest(
                workspace=tmp_path, updated_source=updated_source
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
            request=m.Infra.ProtectedSourceWritesRequest(workspace=tmp_path),
        )

        tm.that(result, eq=(True, []))
        tm.that(
            (
                left_file.read_text(encoding=c.Cli.ENCODING_DEFAULT).rstrip("\n")
                == "VALUE = 2"
            ),
            eq=True,
        )
        tm.that(
            (
                right_file.read_text(encoding=c.Cli.ENCODING_DEFAULT).rstrip("\n")
                == "VALUE = 20"
            ),
            eq=True,
        )

    def test_protected_source_write_rolls_back_invalid_syntax(
        self, tmp_path: Path
    ) -> None:
        py_file = tmp_path / "sample.py"
        original_source = "VALUE = 1\n"
        py_file.write_text(original_source, encoding=c.Cli.ENCODING_DEFAULT)

        result = u.Infra.protected_source_write(
            py_file,
            request=m.Infra.ProtectedSourceWriteRequest(
                workspace=tmp_path, updated_source="def broken(:\n"
            ),
        )

        tm.that(result[0], eq=False)
        tm.that("python-syntax" in "\n".join(result[1]), eq=True)
        tm.that(py_file.read_text(encoding=c.Cli.ENCODING_DEFAULT), eq=original_source)
