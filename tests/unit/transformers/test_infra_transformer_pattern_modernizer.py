"""Unit tests for the pattern modernizer transformer."""

from __future__ import annotations

from collections.abc import Sequence

from flext_infra import FlextInfraRefactorPatternModernizer


def _transform(source: str) -> str:
    """Apply the pattern modernizer to source text."""
    transformer = FlextInfraRefactorPatternModernizer()
    result: tuple[str, Sequence[str]] = transformer.apply_to_source(source)
    return result[0]


class TestsFlextInfraTransformersPatternModernizer:
    """Behavior contract for FlextInfraRefactorPatternModernizer."""

    def test_print_replaced_with_logger_info_and_logger_injected(self) -> None:
        source = 'from flext_core import c\n\ndef foo():\n    print("hello")\n'
        code = _transform(source)
        assert 'logger.info("hello")' in code
        assert "logger = u.fetch_logger(__name__)" in code
        assert "from flext_core import c, u" in code
        assert 'print("hello")' not in code

    def test_existing_logger_is_reused(self) -> None:
        source = 'logger = u.fetch_logger(__name__)\n\ndef foo():\n    print("hello")\n'
        code = _transform(source)
        assert code.count("logger = u.fetch_logger(__name__)") == 1
        assert 'logger.info("hello")' in code

    def test_breakpoint_replaced_with_pass(self) -> None:
        source = "def foo():\n    breakpoint()\n"
        code = _transform(source)
        assert "breakpoint()" not in code
        assert "    pass\n" in code

    def test_import_pdb_removed(self) -> None:
        source = "import pdb\n\ndef foo():\n    pdb.set_trace()\n"
        code = _transform(source)
        assert "import pdb" not in code

    def test_from_pdb_import_removed(self) -> None:
        source = "from pdb import set_trace\n\ndef foo():\n    set_trace()\n"
        code = _transform(source)
        assert "from pdb import set_trace" not in code

    def test_bare_except_fixed(self) -> None:
        source = "def foo():\n    try:\n        pass\n    except:\n        pass\n"
        code = _transform(source)
        assert "except Exception:" in code
        assert "except:\n" not in code

    def test_open_gets_encoding(self) -> None:
        source = 'def foo():\n    with open("x.txt") as f:\n        pass\n'
        code = _transform(source)
        assert 'open("x.txt", encoding="utf-8")' in code

    def test_open_with_mode_gets_encoding(self) -> None:
        source = 'def foo():\n    with open("x.txt", "w") as f:\n        pass\n'
        code = _transform(source)
        assert 'open("x.txt", "w", encoding="utf-8")' in code

    def test_open_with_encoding_unchanged(self) -> None:
        source = 'def foo():\n    with open("x.txt", encoding="latin-1") as f:\n        pass\n'
        code = _transform(source)
        assert 'encoding="latin-1"' in code
        assert 'encoding="utf-8"' not in code
