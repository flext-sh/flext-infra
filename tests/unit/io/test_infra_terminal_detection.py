"""Public tests for terminal capability detection."""

from __future__ import annotations

import os
from collections.abc import (
    Generator,
)
from contextlib import contextmanager


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
