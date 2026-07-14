"""Unit tests for the result-flow and DI modernizer transformer."""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_infra.transformers.result_di_modernizer import (
    FlextInfraRefactorResultDiModernizer,
)
from flext_tests import tm

from collections.abc import Sequence



def _transform(source: str) -> tuple[str, Sequence[str]]:
    """Apply the result/DI modernizer to source text."""
    transformer = FlextInfraRefactorResultDiModernizer()
    result: tuple[str, Sequence[str]] = transformer.apply_to_source(source)
    return result


class TestsFlextInfraTransformersResultDiModernizer:
    """Behavior contract for FlextInfraRefactorResultDiModernizer."""

    def test_raise_value_error_rewritten_when_result_alias_imported(self) -> None:
        source = (
            "from flext_core import r\n\n"
            "def compute() -> int:\n"
            '    raise ValueError("bad")\n'
        )
        code, changes = _transform(source)
        tm.that(code, has='return r[str].fail("bad", error_code="RESULT_VALUE_ERROR")')
        tm.that(code, lacks="raise ValueError")
        tm.that(len(changes), eq=1)

    def test_raise_value_error_unchanged_without_result_alias(self) -> None:
        source = 'def compute() -> int:\n    raise ValueError("bad")\n'
        code, changes = _transform(source)
        tm.that(code, has='raise ValueError("bad")')
        assert not changes

    def test_di_root_import_rewritten(self) -> None:
        source = "from dependency_injector import containers\n"
        code, changes = _transform(source)
        tm.that(code, has="from flext_core.di import containers")
        tm.that(code, lacks="dependency_injector")
        tm.that(len(changes), eq=1)

    def test_di_providers_factory_rewritten(self) -> None:
        source = "from dependency_injector.providers import Factory\n"
        code, changes = _transform(source)
        tm.that(code, has="from flext_core.di.providers import Factory")
        tm.that(code, lacks="dependency_injector")
        tm.that(len(changes), eq=1)

    def test_di_import_untouched_when_not_dependency_injector(self) -> None:
        source = "from some_other_lib import containers\n"
        code, changes = _transform(source)
        tm.that(code, has="from some_other_lib import containers")
        assert not changes

    def test_unchanged_source_returns_empty_changes(self) -> None:
        source = (
            "from flext_core import r\n\n"
            "def compute() -> int:\n"
            "    return r[int].ok(42)\n"
        )
        code, changes = _transform(source)
        tm.that(code, eq=source)
        assert not changes
