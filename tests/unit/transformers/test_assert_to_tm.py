"""Differential contract for the syntax-aware assert-to-tm codemod."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from flext_infra.transformers.assert_to_tm import FlextInfraAssertToTmTransformer
from flext_tests import tm

if TYPE_CHECKING:
    from collections.abc import Sequence


def _transform(source: str) -> str:
    """Return source transformed through the public codemod contract."""
    transformed: tuple[str, Sequence[str]] = (
        FlextInfraAssertToTmTransformer().apply_to_source(source)
    )
    return transformed[0]


class TestsFlextInfraAssertToTmTransformer:
    """The codemod preserves Python condition evaluation and CST trivia."""

    def test_conditions_remain_one_python_boolean_expression(self) -> None:
        """Truth, comparison, identity, membership and calls keep their operators."""
        source = '''"""Tests."""
from __future__ import annotations

def check(a: object, b: object, items: object) -> None:
    assert a
    assert not a
    assert a == b
    assert a is not None
    assert a in items
    assert isinstance(a, str)
'''

        transformed = _transform(source)

        tm.that(
            transformed,
            eq='''"""Tests."""
from __future__ import annotations
from flext_tests import tm

def check(a: object, b: object, items: object) -> None:
    tm.that(bool(a), eq = True)
    tm.that(bool(not a), eq = True)
    tm.that(bool(a == b), eq = True)
    tm.that(bool(a is not None), eq = True)
    tm.that(bool(a in items), eq = True)
    tm.that(bool(isinstance(a, str)), eq = True)
''',
        )

    def test_comment_and_existing_import_are_preserved_idempotently(self) -> None:
        """An existing flext_tests import owns tm exactly once on every pass."""
        source = """from flext_tests import fixtures

def check(value: object) -> None:
    assert value  # decisive comment
"""

        first = _transform(source)
        second = _transform(first)

        tm.that(first, has="from flext_tests import fixtures, tm")
        tm.that(first, has="# decisive comment")
        tm.that(first.count("tm"), eq=2)
        tm.that(second, eq=first)

    def test_short_circuit_and_operand_evaluation_match_python_assert(self) -> None:
        """The original condition is evaluated once with native short-circuiting."""
        source = """from flext_tests import tm

events = []

def probe(name: str, value: bool) -> bool:
    events.append(name)
    return value

def check() -> None:
    assert probe("left", True) or probe("right", False)
"""
        namespace: dict[str, object] = {}

        exec(_transform(source), namespace)
        check = namespace["check"]
        tm.that(callable(check), eq=True)
        check()

        tm.that(namespace["events"], eq=["left"])

    def test_dynamic_message_is_lazy_and_evaluated_once_on_failure(self) -> None:
        """Dynamic assert messages retain lazy success and single failure evaluation."""
        source = """from flext_tests import tm

events = []

def message() -> str:
    events.append("message")
    return "dynamic"

def check(value: bool) -> None:
    assert value, message()
"""
        namespace: dict[str, object] = {}
        exec(_transform(source), namespace)
        check = namespace["check"]
        tm.that(callable(check), eq=True)

        check(True)
        tm.that(namespace["events"], eq=[])
        with pytest.raises(AssertionError, match="dynamic"):
            check(False)
        tm.that(namespace["events"], eq=["message"])

    def test_unsupported_async_message_fails_before_returning_source(self) -> None:
        """A message that cannot move into a lambda fails with source location."""
        source = """async def check(value: bool, message: object) -> None:
    assert value, await message
"""
        transformer = FlextInfraAssertToTmTransformer()

        with pytest.raises(SyntaxError, match="line 2, column 4"):
            transformer.apply_to_source(source)
