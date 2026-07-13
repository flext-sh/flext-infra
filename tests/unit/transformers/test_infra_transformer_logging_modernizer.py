"""Unit tests for the logging modernizer transformer."""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_infra.transformers.logging_modernizer import (
    FlextInfraRefactorLoggingModernizer,
)
from flext_tests import tm

if TYPE_CHECKING:
    from collections.abc import Sequence


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
        tm.that(code, lacks="import logging")
        tm.that(code, has="logger = u.fetch_logger(__name__)")

    def test_logging_getlogger_call_replaced(self) -> None:
        source = "logging.getLogger(__name__)\n"
        code = _transform(source)
        tm.that(code, has="u.fetch_logger(__name__)")
        tm.that(code, lacks="logging.getLogger")

    def test_logger_assignment_replaced(self) -> None:
        source = "logger = logging.getLogger(__name__)\n"
        code = _transform(source)
        tm.that(code, has="logger = u.fetch_logger(__name__)")
        tm.that(code, lacks="logging.getLogger")

    def test_logging_getlogger_with_string_replaced(self) -> None:
        source = 'logger = logging.getLogger("foo")\n'
        code = _transform(source)
        tm.that(code, has='logger = u.fetch_logger("foo")')
        tm.that(code, lacks="logging.getLogger")

    def test_from_logging_import_getlogger_removed(self) -> None:
        source = "from logging import getLogger\n\nlogger = getLogger(__name__)\n"
        code = _transform(source)
        tm.that(code, lacks="from logging import getLogger")
        tm.that(code, has="logger = u.fetch_logger(__name__)")

    def test_u_import_added_when_needed(self) -> None:
        source = "logger = logging.getLogger(__name__)\n"
        code = _transform(source)
        tm.that(code, has="from flext_core import u")

    def test_no_duplicate_u_import(self) -> None:
        source = "from flext_core import c, u\n\nlogger = logging.getLogger(__name__)\n"
        code = _transform(source)
        tm.that(code.count("from flext_core import"), eq=1)
        tm.that(code, has="from flext_core import c, u")

    def test_existing_logger_binding_prevents_injection(self) -> None:
        source = (
            'logger = u.fetch_logger(__name__)\n\nother = logging.getLogger("other")\n'
        )
        code = _transform(source)
        tm.that(code.count("logger = u.fetch_logger(__name__)"), eq=1)
        tm.that(code, has='u.fetch_logger("other")')

    def test_unchanged_source_returns_empty_changes(self) -> None:
        source = "from flext_core import u\n\nlogger = u.fetch_logger(__name__)\n"
        transformer = FlextInfraRefactorLoggingModernizer()
        result: tuple[str, Sequence[str]] = transformer.apply_to_source(source)
        tm.that(result[0], eq=source)
        tm.that(result[1], eq=[])
