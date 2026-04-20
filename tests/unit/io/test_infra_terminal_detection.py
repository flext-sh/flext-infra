"""Public tests for terminal capability detection."""

from __future__ import annotations

import os
from collections.abc import (
    Generator,
)
from contextlib import contextmanager

from tests import u


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


def test_no_color_env_disables_color() -> None:
    with _env(NO_COLOR="1"):
        assert u.Infra.terminal_should_use_color() is False


def test_no_color_beats_force_color() -> None:
    with _env(NO_COLOR="1", FORCE_COLOR="1"):
        assert u.Infra.terminal_should_use_color() is False


def test_force_color_enables_color() -> None:
    with _env(FORCE_COLOR="1"):
        assert u.Infra.terminal_should_use_color() is True


def test_ci_variables_disable_color() -> None:
    for var in ("CI", "GITHUB_ACTIONS", "GITLAB_CI"):
        with _env(**{var: "true"}):
            assert u.Infra.terminal_should_use_color() is False


def test_tty_with_xterm_enables_color() -> None:
    with _env(TERM="xterm-256color"):
        assert u.Infra.terminal_should_use_color(_Stream(tty=True)) is True


def test_tty_with_dumb_or_empty_term_disables_color() -> None:
    with _env(TERM="dumb"):
        assert u.Infra.terminal_should_use_color(_Stream(tty=True)) is False
    with _env(TERM=""):
        assert u.Infra.terminal_should_use_color(_Stream(tty=True)) is False


def test_non_tty_disables_color() -> None:
    with _env():
        assert u.Infra.terminal_should_use_color(_Stream(tty=False)) is False


def test_utf8_locale_enables_unicode() -> None:
    with _env(LANG="en_US.UTF-8"):
        assert u.Infra.terminal_should_use_unicode() is True
    with _env(LC_ALL="en_US.utf8"):
        assert u.Infra.terminal_should_use_unicode() is True


def test_non_utf8_locale_disables_unicode() -> None:
    with _env(LANG="C"):
        assert u.Infra.terminal_should_use_unicode() is False
    with _env():
        assert u.Infra.terminal_should_use_unicode() is False


def test_lc_all_takes_priority_over_lang() -> None:
    with _env(LC_ALL="en_US.UTF-8", LANG="C"):
        assert u.Infra.terminal_should_use_unicode() is True
