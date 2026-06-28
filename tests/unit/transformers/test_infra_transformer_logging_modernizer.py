"""Unit tests for the logging modernizer transformer."""

from __future__ import annotations

from collections.abc import Sequence

from flext_infra import FlextInfraRefactorLoggingModernizer


def _transform(source: str) -> str:
    """Apply the logging modernizer to source text."""
    transformer = FlextInfraRefactorLoggingModernizer()
    result: tuple[str, Sequence[str]] = transformer.apply_to_source(source)
    return result[0]


class TestsFlextInfraTransformersLoggingModernizer:
    """Behavior contract for FlextInfraRefactorLoggingModernizer."""

    def test_import_logging_removed(self) -> None:
        source = "import logging\n\nlogger = logging.getLogger(__name__)\n"
        code = _transform(source)
        assert "import logging" not in code
        assert "logger = u.fetch_logger(__name__)" in code

    def test_logging_getlogger_call_replaced(self) -> None:
        source = "logging.getLogger(__name__)\n"
        code = _transform(source)
        assert "u.fetch_logger(__name__)" in code
        assert "logging.getLogger" not in code

    def test_logger_assignment_replaced(self) -> None:
        source = "logger = logging.getLogger(__name__)\n"
        code = _transform(source)
        assert "logger = u.fetch_logger(__name__)" in code
        assert "logging.getLogger" not in code

    def test_logging_getlogger_with_string_replaced(self) -> None:
        source = 'logger = logging.getLogger("foo")\n'
        code = _transform(source)
        assert 'logger = u.fetch_logger("foo")' in code
        assert "logging.getLogger" not in code

    def test_from_logging_import_getlogger_removed(self) -> None:
        source = "from logging import getLogger\n\nlogger = getLogger(__name__)\n"
        code = _transform(source)
        assert "from logging import getLogger" not in code
        assert "logger = u.fetch_logger(__name__)" in code

    def test_u_import_added_when_needed(self) -> None:
        source = "logger = logging.getLogger(__name__)\n"
        code = _transform(source)
        assert "from flext_core import u" in code

    def test_no_duplicate_u_import(self) -> None:
        source = "from flext_core import c, u\n\nlogger = logging.getLogger(__name__)\n"
        code = _transform(source)
        assert code.count("from flext_core import") == 1
        assert "from flext_core import c, u" in code

    def test_existing_logger_binding_prevents_injection(self) -> None:
        source = (
            'logger = u.fetch_logger(__name__)\n\nother = logging.getLogger("other")\n'
        )
        code = _transform(source)
        assert code.count("logger = u.fetch_logger(__name__)") == 1
        assert 'u.fetch_logger("other")' in code

    def test_unchanged_source_returns_empty_changes(self) -> None:
        source = "from flext_core import u\n\nlogger = u.fetch_logger(__name__)\n"
        transformer = FlextInfraRefactorLoggingModernizer()
        result: tuple[str, Sequence[str]] = transformer.apply_to_source(source)
        assert result[0] == source
        assert result[1] == []
