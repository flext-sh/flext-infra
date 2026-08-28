"""Tests that parsing a Make surface never runs an interpreter.

GNU Make expands every ``:=`` assignment while it parses, before it knows which
target was requested. A ``$(shell ...)`` that starts a Python interpreter is
therefore paid by *every* invocation -- ``make help`` included -- and, because
the verb dispatcher re-enters make for hook probing, it is paid several times
per command.

Values that need an interpreter belong in the recipe that consumes them, where
Make's lazy ``=`` assignment defers the cost to the one verb that needs it.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import re
from pathlib import Path

import flext_infra
from flext_infra import c
from flext_tests import tm

# ``$(shell ...)`` call marker. Assignment identity uses c.Infra.MAKE_ASSIGNMENT_RE;
# immediacy is ``:=`` / ``::=`` (name token ends with ``:`` before ``=``).
_SHELL_CALL = re.compile(r"\$\(shell\b")
# Executing an interpreter costs hundreds of milliseconds to seconds. Merely
# *locating* one (`command -v python3`) is a cheap PATH lookup and is allowed:
# the toolchain has to resolve its own interpreter before it can dispatch.
_INTERPRETER_RUN = re.compile(
    r"(?<!command -v )(?:\buv run\b|\bpython[0-9.]*\s+-[cm]\b|\bnode\s+-e\b)"
)


def _workspace_root() -> Path:
    """Return the workspace root that owns this checkout."""
    return Path(__file__).resolve().parents[2]


def _make_surfaces() -> tuple[Path, ...]:
    """Return every Make surface plus the templates that generate them."""
    root = _workspace_root()
    templates = Path(flext_infra.__file__).resolve().parent / "templates"
    return (root / c.Infra.MAKEFILE_FILENAME, *sorted(templates.rglob("*.mk.j2")))


def _is_immediate_shell_assignment(line: str) -> bool:
    """True when a column-0 Make assignment is immediate and calls $(shell)."""
    if c.Infra.MAKE_ASSIGNMENT_RE.match(line) is None:
        return False
    before_eq, sep, _after = line.partition("=")
    if sep != "=" or not before_eq.rstrip().endswith(":"):
        return False
    return (
        _SHELL_CALL.search(line) is not None
        and _INTERPRETER_RUN.search(line) is not None
    )


def _interpreter_at_parse_time(surface: Path) -> tuple[str, ...]:
    """Return immediate assignments that spawn an interpreter while parsing."""
    return tuple(
        f"{surface.name}:{number}: {line.strip()}"
        for number, line in enumerate(
            surface.read_text(encoding="utf-8").splitlines(), start=1
        )
        if _is_immediate_shell_assignment(line)
    )


class TestsFlextInfraMakeParseIsSideEffectFree:
    def test_no_surface_starts_an_interpreter_while_parsing(self) -> None:
        """No Make surface pays interpreter startup on every invocation."""
        offenders = {
            surface.name: lines
            for surface in _make_surfaces()
            if (lines := _interpreter_at_parse_time(surface))
        }

        tm.that(len(offenders), eq=0)
