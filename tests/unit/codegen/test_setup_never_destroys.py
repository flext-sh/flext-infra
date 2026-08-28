"""``setup`` provisions tooling and never destroys tracked working trees.

``setup`` is invoked automatically, from every verb and from the pre-commit
hook, so anything it mutates it mutates constantly and unattended. That makes
it the one verb allowed to *create* what is missing and forbidden to *destroy*
what exists.

``git checkout`` and ``git reset`` are completely prohibited on the setup path.
Absent checkouts are initialized with ``submodule update --init`` only; detached
HEAD is attached via ``branch -f`` + ``symbolic-ref`` so dirty work is carried.
"""

from __future__ import annotations

import re
from pathlib import Path

_TEMPLATES = Path(__file__).resolve().parents[3] / "src" / "flext_infra" / "templates"
_MAKEFILE = _TEMPLATES / "project" / "base" / "Makefile.j2"
_SUBMODULES = _TEMPLATES / "project" / "base" / "submodule_setup_recipe.j2"

_DESTRUCTIVE_GIT = (
    r"git\b[^\n]*\bcheckout\b",
    r"git\b[^\n]*\bpull\b",
    r"git\b[^\n]*\breset\b",
    r"git\b[^\n]*\bclean\b",
    r"git\b[^\n]*\bworktree\b[^\n]*\b(remove|prune)\b",
)


def _setup_recipe_text() -> str:
    """Return every template line ``setup`` can execute."""
    return f"{_MAKEFILE.read_text(encoding='utf-8')}\n{_SUBMODULES.read_text(encoding='utf-8')}"


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
