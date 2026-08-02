from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
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

        result = u.Infra.preview_source_writes({py_file: updated_source})

        tm.that(result, eq=None)
        tm.that(py_file.read_text(encoding=c.Cli.ENCODING_DEFAULT), eq=original_source)

    def test_preview_source_writes_restores_after_callback_failure(
        self, tmp_path: Path
    ) -> None:
        py_file = tmp_path / "sample.py"
        original_source = "VALUE = 1\n"
        py_file.write_text(original_source, encoding=c.Cli.ENCODING_DEFAULT)
        error = "preview rejected"

        def _reject_preview() -> None:
            raise RuntimeError(error)

        with pytest.raises(RuntimeError, match=error):
            u.Infra.preview_source_writes(
                {py_file: "VALUE = 2\n"}, post_write=_reject_preview
            )

        tm.that(py_file.read_text(encoding=c.Cli.ENCODING_DEFAULT), eq=original_source)

    def test_protected_source_write_applies_source(self, tmp_path: Path) -> None:
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

        tm.that(result, eq=())
        tm.that(
            py_file.read_text(encoding=c.Cli.ENCODING_DEFAULT).rstrip("\n"),
            eq=updated_source.rstrip("\n"),
        )

    def test_protected_source_writes_applies_transaction(self, tmp_path: Path) -> None:
        left_file = tmp_path / "left.py"
        right_file = tmp_path / "right.py"
        left_file.write_text("VALUE = 1\n", encoding=c.Cli.ENCODING_DEFAULT)
        right_file.write_text("VALUE = 10\n", encoding=c.Cli.ENCODING_DEFAULT)

        result = u.Infra.protected_source_writes(
            {left_file: "VALUE = 2\n", right_file: "VALUE = 20\n"},
            request=m.Infra.ProtectedSourceWritesRequest(workspace=tmp_path),
        )

        tm.that(result, eq=())
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

    def test_protected_source_writes_restores_all_after_callback_failure(
        self, tmp_path: Path
    ) -> None:
        left_file = tmp_path / "left.py"
        right_file = tmp_path / "right.py"
        left_file.write_text("VALUE = 1\n", encoding=c.Cli.ENCODING_DEFAULT)
        right_file.write_text("VALUE = 10\n", encoding=c.Cli.ENCODING_DEFAULT)
        error = "write rejected"

        def _reject_write() -> None:
            raise RuntimeError(error)

        with pytest.raises(RuntimeError, match=error):
            u.Infra.protected_source_writes(
                {left_file: "VALUE = 2\n", right_file: "VALUE = 20\n"},
                request=m.Infra.ProtectedSourceWritesRequest(
                    workspace=tmp_path, post_write=_reject_write
                ),
            )

        tm.that(left_file.read_text(encoding=c.Cli.ENCODING_DEFAULT), eq="VALUE = 1\n")
        tm.that(
            right_file.read_text(encoding=c.Cli.ENCODING_DEFAULT), eq="VALUE = 10\n"
        )
