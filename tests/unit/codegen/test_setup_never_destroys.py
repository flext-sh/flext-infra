"""``setup`` provisions the current repository without destructive Git."""

from __future__ import annotations

import re
from pathlib import Path

_TEMPLATES = Path(__file__).resolve().parents[3] / "src" / "flext_infra" / "templates"
_MAKEFILE = _TEMPLATES / "project" / "base" / "Makefile.j2"

_DESTRUCTIVE_GIT = (
    r"git\b[^\n]*\bcheckout\b",
    r"git\b[^\n]*\bpull\b",
    r"git\b[^\n]*\breset\b",
    r"git\b[^\n]*\bclean\b",
    r"git\b[^\n]*\bworktree\b[^\n]*\b(remove|prune)\b",
)


def _setup_recipe_text() -> str:
    """Return every template line ``setup`` can execute."""
    return _MAKEFILE.read_text(encoding="utf-8")


def _offending_lines(pattern: str) -> list[str]:
    """Return executable recipe lines that match one destructive pattern."""
    return [
        stripped
        for line in _setup_recipe_text().splitlines()
        if (stripped := line.strip())
        and re.search(pattern, stripped)
        and not stripped.startswith(("printf", "echo", "#"))
    ]


def test_setup_never_runs_a_destructive_git_operation() -> None:
    """No reachable ``setup`` line may checkout, reset, pull, or clean."""
    offenders = {
        pattern: lines
        for pattern in _DESTRUCTIVE_GIT
        if (lines := _offending_lines(pattern))
    }

    assert not offenders, f"setup reaches destructive git operations: {offenders}"


def test_setup_never_clears_the_virtualenv() -> None:
    """A present virtualenv is repaired in place, never recreated."""
    offenders = _offending_lines(r"venv\b[^\n]*--clear")

    assert not offenders, f"setup clears the virtualenv: {offenders}"


__all__: tuple[str, ...] = ()
