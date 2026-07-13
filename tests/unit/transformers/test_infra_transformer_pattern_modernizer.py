"""Unit tests for the pattern modernizer transformer."""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_infra.transformers.pattern_modernizer import (
    FlextInfraRefactorPatternModernizer,
)
from flext_tests import tm

if TYPE_CHECKING:
    from collections.abc import Sequence


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
        tm.that(code, has='logger.info("hello")')
        tm.that(code, has="logger = u.fetch_logger(__name__)")
        tm.that(code, has="from flext_core import c, u")
        tm.that(code, lacks='print("hello")')

    def test_existing_logger_is_reused(self) -> None:
        source = 'logger = u.fetch_logger(__name__)\n\ndef foo():\n    print("hello")\n'
        code = _transform(source)
        tm.that(code.count("logger = u.fetch_logger(__name__)"), eq=1)
        tm.that(code, has='logger.info("hello")')

    def test_breakpoint_replaced_with_pass(self) -> None:
        source = "def foo():\n    breakpoint()\n"
        code = _transform(source)
        tm.that(code, lacks="breakpoint()")
        tm.that(code, has="    pass\n")

    def test_import_pdb_removed(self) -> None:
        source = "import pdb\n\ndef foo():\n    pdb.set_trace()\n"
        code = _transform(source)
        tm.that(code, lacks="import pdb")

    def test_from_pdb_import_removed(self) -> None:
        source = "from pdb import set_trace\n\ndef foo():\n    set_trace()\n"
        code = _transform(source)
        tm.that(code, lacks="from pdb import set_trace")

    def test_bare_except_fixed(self) -> None:
        source = "def foo():\n    try:\n        pass\n    except:\n        pass\n"
        code = _transform(source)
        tm.that(code, has="except Exception:")
        tm.that(code, lacks="except:\n")

    def test_open_gets_encoding(self) -> None:
        source = 'def foo():\n    with open("x.txt") as f:\n        pass\n'
        code = _transform(source)
        tm.that(code, has='open("x.txt", encoding="utf-8")')

    def test_open_with_mode_gets_encoding(self) -> None:
        source = 'def foo():\n    with open("x.txt", "w") as f:\n        pass\n'
        code = _transform(source)
        tm.that(code, has='open("x.txt", "w", encoding="utf-8")')

    def test_open_with_encoding_unchanged(self) -> None:
        source = 'def foo():\n    with open("x.txt", encoding="latin-1") as f:\n        pass\n'
        code = _transform(source)
        tm.that(code, has='encoding="latin-1"')
        tm.that(code, lacks='encoding="utf-8"')
