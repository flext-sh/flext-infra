"""Public tests for terminal capability detection."""

from __future__ import annotations

import os
from collections.abc import Generator
from contextlib import contextmanager
from typing import TYPE_CHECKING

from flext_tests import tm


class _Stream:
    def __init__(self, *, tty: bool) -> None:
        self._tty = tty

    def isatty(self) -> bool:
        return self._tty

    def write(self, msg: str, /) -> int:
        return len(msg)

    def flush(self) -> None:
        return None


@contextmanager
def _env(**updates: str | None) -> Generator[None]:
    original = os.environ.copy()
    try:
        os.environ.clear()
        for key, value in updates.items():
            if value is not None:
                os.environ[key] = value
        yield
    finally:
        os.environ.clear()
        os.environ.update(original)


class TestsFlextInfraIoInfraTerminalDetection:
    """Behavior contract for test_infra_terminal_detection."""

    def test_stream_reports_tty_state(self) -> None:
        tm.that(_Stream(tty=True).isatty(), eq=True)
        tm.that(_Stream(tty=False).isatty(), eq=False)

    def test_env_applies_and_restores_environment(self) -> None:
        os.environ["FLEXT_KEEP"] = "yes"
        with _env(FLEXT_KEEP=None, FLEXT_TEST="1"):
            tm.that(os.environ.get("FLEXT_TEST"), eq="1")
            tm.that(os.environ, lacks="FLEXT_KEEP")
        tm.that(os.environ.get("FLEXT_KEEP"), eq="yes")
        os.environ.pop("FLEXT_KEEP", None)
