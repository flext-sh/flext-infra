"""Unit tests for the enforcement fixer transformers.

Covers the small, targeted source-to-source transformers used by the
flext-infra enforcement pipeline.
"""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

from flext_infra.transformers.bare_except import FlextInfraRefactorBareExcept
from flext_infra.transformers.future_import import FlextInfraRefactorFutureImport
from flext_infra.transformers.open_encoding import FlextInfraRefactorOpenEncoding
from flext_infra.transformers.print_to_logger import FlextInfraRefactorPrintToLogger
from flext_infra.transformers.remove_breakpoint import (
    FlextInfraRefactorRemoveBreakpoint,
)


def _transform(
    source: str,
    transformer: FlextInfraRefactorBareExcept
    | FlextInfraRefactorFutureImport
    | FlextInfraRefactorOpenEncoding
    | FlextInfraRefactorRemoveBreakpoint,
) -> tuple[str, Sequence[str]]:
    """Apply a stateless transformer to source text."""
    result: tuple[str, Sequence[str]] = transformer.apply_to_source(source)
    return result


def _transform_print(tmp_path: Path, source: str) -> tuple[str, Sequence[str]]:
    """Apply the print-to-logger transformer with a synthetic package path."""
    package_root = tmp_path / "flext_core" / "src" / "flext_core"
    package_root.mkdir(parents=True)
    file_path = package_root / "module.py"
    transformer = FlextInfraRefactorPrintToLogger(file_path=file_path)
    result: tuple[str, Sequence[str]] = transformer.apply_to_source(source)
    return result


class TestsFlextInfraTransformersFutureImport:
    """Behavior contract for FlextInfraRefactorFutureImport."""

    def test_future_import_already_present_is_unchanged(self) -> None:
        source = "from __future__ import annotations\n\nx = 1\n"
        code, changes = _transform(source, FlextInfraRefactorFutureImport())
        assert code == source
        assert changes == []

    def test_future_import_inserted_at_top_when_absent(self) -> None:
        source = "x = 1\n"
        code, changes = _transform(source, FlextInfraRefactorFutureImport())
        assert code == "from __future__ import annotations\nx = 1\n"
        assert changes

    def test_future_import_inserted_after_shebang_and_comments(self) -> None:
        source = (
            "#!/usr/bin/env python3\n"
            "# -*- coding: utf-8 -*-\n"
            "# leading comment\n"
            "\n"
            "x = 1\n"
        )
        code, changes = _transform(source, FlextInfraRefactorFutureImport())
        expected = (
            "#!/usr/bin/env python3\n"
            "# -*- coding: utf-8 -*-\n"
            "# leading comment\n"
            "\n"
            "from __future__ import annotations\n"
            "x = 1\n"
        )
        assert code == expected
        assert changes


class TestsFlextInfraTransformersBareExcept:
    """Behavior contract for FlextInfraRefactorBareExcept."""

    def test_bare_except_rewritten_to_exception(self) -> None:
        source = "def foo():\n    try:\n        pass\n    except:\n        pass\n"
        code, changes = _transform(source, FlextInfraRefactorBareExcept())
        assert "    except Exception:\n" in code
        assert "    except:\n" not in code
        assert changes

    def test_bare_except_preserves_indentation(self) -> None:
        source = "try:\n    pass\nexcept:\n    pass\n"
        code, _ = _transform(source, FlextInfraRefactorBareExcept())
        assert "except Exception:\n" in code
        assert "except:\n" not in code

    def test_specific_except_unchanged(self) -> None:
        source = (
            "def foo():\n    try:\n        pass\n    except ValueError:\n        pass\n"
        )
        code, changes = _transform(source, FlextInfraRefactorBareExcept())
        assert code == source
        assert changes == []


class TestsFlextInfraTransformersRemoveBreakpoint:
    """Behavior contract for FlextInfraRefactorRemoveBreakpoint."""

    def test_breakpoint_call_removed(self) -> None:
        source = "def foo():\n    breakpoint()\n    x = 1\n"
        code, changes = _transform(source, FlextInfraRefactorRemoveBreakpoint())
        assert "breakpoint()" not in code
        assert "x = 1\n" in code
        assert changes

    def test_import_pdb_set_trace_removed(self) -> None:
        source = "import pdb; pdb.set_trace()\n"
        code, changes = _transform(source, FlextInfraRefactorRemoveBreakpoint())
        assert "import pdb" not in code
        assert "pdb.set_trace()" not in code
        assert changes

    def test_adjacent_blank_lines_preserved(self) -> None:
        source = "x = 1\n\nbreakpoint()\n\ny = 2\n"
        code, _ = _transform(source, FlextInfraRefactorRemoveBreakpoint())
        assert "breakpoint()" not in code
        assert "x = 1\n" in code
        assert "y = 2\n" in code
        assert "\n" in code


class TestsFlextInfraTransformersOpenEncoding:
    """Behavior contract for FlextInfraRefactorOpenEncoding."""

    def test_open_without_encoding_gets_utf8(self) -> None:
        source = 'with open("x.txt") as f:\n    pass\n'
        code, changes = _transform(source, FlextInfraRefactorOpenEncoding())
        assert 'open("x.txt", encoding="utf-8")' in code
        assert changes

    def test_open_with_mode_gets_utf8(self) -> None:
        source = 'with open("x.txt", "w") as f:\n    pass\n'
        code, changes = _transform(source, FlextInfraRefactorOpenEncoding())
        assert 'open("x.txt", "w", encoding="utf-8")' in code
        assert changes

    def test_open_with_multiple_args_gets_utf8(self) -> None:
        source = 'with open("x.txt", "w", buffering=1) as f:\n    pass\n'
        code, changes = _transform(source, FlextInfraRefactorOpenEncoding())
        assert 'open("x.txt", "w", buffering=1, encoding="utf-8")' in code
        assert changes

    def test_open_with_encoding_unchanged(self) -> None:
        source = 'with open("x.txt", encoding="latin-1") as f:\n    pass\n'
        code, changes = _transform(source, FlextInfraRefactorOpenEncoding())
        assert code == source
        assert changes == []


class TestsFlextInfraTransformersPrintToLogger:
    """Behavior contract for FlextInfraRefactorPrintToLogger."""

    def test_print_rewritten_to_fetch_logger_info(self, tmp_path: Path) -> None:
        source = 'print("hello")\n'
        code, changes = _transform_print(tmp_path, source)
        assert 'u.fetch_logger(__name__).info("hello")' in code
        assert "print(" not in code
        assert changes

    def test_u_import_added_when_missing(self, tmp_path: Path) -> None:
        source = 'print("hello")\n'
        code, changes = _transform_print(tmp_path, source)
        assert "from flext_core import u" in code
        assert changes

    def test_u_import_not_duplicated(self, tmp_path: Path) -> None:
        source = 'from flext_core import c, u\n\nprint("hello")\n'
        code, changes = _transform_print(tmp_path, source)
        assert code.count("from flext_core import") == 1
        assert "from flext_core import c, u" in code
        assert 'u.fetch_logger(__name__).info("hello")' in code
        assert changes
