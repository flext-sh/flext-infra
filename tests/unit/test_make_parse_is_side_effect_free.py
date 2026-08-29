"""Tests that parsing a Make surface never runs a subprocess.

GNU Make expands every ``:=`` assignment while it parses, before it knows which
target was requested. A ``$(shell ...)`` that starts a Python interpreter is
therefore paid by *every* invocation -- ``make help`` included -- and, because
the verb dispatcher re-enters make for hook probing, it is paid several times
per command.

Every ``$(shell ...)`` is fail-open at parse time: GNU Make substitutes an empty
string when discovery fails unless each call reconstructs status propagation.
Discovery belongs in the recipe that consumes it, where the shell preserves the
exact command status without a second execution path.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import re
from pathlib import Path

from flext_tests import tm
from tests import u as test_u

_SHELL_CALL = re.compile(r"\$\(shell\b")


def _workspace_root() -> Path:
    """Return the workspace root that owns this checkout."""
    return Path(__file__).resolve().parents[2]


def _parse_time_subprocesses(surface: Path) -> tuple[str, ...]:
    """Return every Make shell expansion executed while parsing."""
    return tuple(
        f"{surface.name}:{number}: {line.strip()}"
        for number, line in enumerate(
            surface.read_text(encoding="utf-8").splitlines(), start=1
        )
        if _SHELL_CALL.search(line) is not None
    )


class TestsFlextInfraMakeParseIsSideEffectFree:
    def test_no_surface_starts_a_subprocess_while_parsing(self) -> None:
        """No Make surface hides discovery failure behind shell expansion."""
        offenders = {
            surface.name: lines
            for surface in test_u.Tests.make_surfaces(_workspace_root())
            if (lines := _parse_time_subprocesses(surface))
        }

        tm.that(len(offenders), eq=0)
