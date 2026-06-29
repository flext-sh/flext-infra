"""Unit tests for the result-flow and DI modernizer transformer."""

from __future__ import annotations

from collections.abc import Sequence

from flext_infra.transformers.result_di_modernizer import (
    FlextInfraRefactorResultDiModernizer,
)


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
        assert 'return r[str].fail("bad", error_code="RESULT_VALUE_ERROR")' in code
        assert "raise ValueError" not in code
        assert len(changes) == 1

    def test_raise_value_error_unchanged_without_result_alias(self) -> None:
        source = 'def compute() -> int:\n    raise ValueError("bad")\n'
        code, changes = _transform(source)
        assert 'raise ValueError("bad")' in code
        assert not changes

    def test_di_root_import_rewritten(self) -> None:
        source = "from dependency_injector import containers\n"
        code, changes = _transform(source)
        assert "from flext_core.di import containers" in code
        assert "dependency_injector" not in code
        assert len(changes) == 1

    def test_di_providers_factory_rewritten(self) -> None:
        source = "from dependency_injector.providers import Factory\n"
        code, changes = _transform(source)
        assert "from flext_core.di.providers import Factory" in code
        assert "dependency_injector" not in code
        assert len(changes) == 1

    def test_di_import_untouched_when_not_dependency_injector(self) -> None:
        source = "from some_other_lib import containers\n"
        code, changes = _transform(source)
        assert "from some_other_lib import containers" in code
        assert not changes

    def test_unchanged_source_returns_empty_changes(self) -> None:
        source = (
            "from flext_core import r\n\n"
            "def compute() -> int:\n"
            "    return r[int].ok(42)\n"
        )
        code, changes = _transform(source)
        assert code == source
        assert not changes
