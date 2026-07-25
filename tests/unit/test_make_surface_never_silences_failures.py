"""Tests that no Make surface silences a command failure.

A recipe line ending in ``|| true`` discards the command's exit code, so a
crashed tool, a missing binary or a malformed rule file is reported to the
operator as success. That is indistinguishable from a real pass, which makes
every gate built on it untrustworthy.

The pattern is sometimes defended as "the scanner exits non-zero when it finds
something". That defence is false for the scanner this workspace uses:
``ast-grep scan`` exits 0 both with and without findings, and reserves non-zero
for genuine errors (6 = unreadable rule, 127 = binary absent). ``|| true``
therefore masks *only* real failures and protects nothing.

Read-only verbs that must not fail the build on findings express that by
reporting explicitly, never by discarding the exit code.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

from flext_tests import tm

from flext_infra import c


def _workspace_root() -> Path:
    """Return the workspace root that owns this checkout."""
    return Path(__file__).resolve().parents[3]


def _make_surfaces() -> tuple[Path, ...]:
    """Return every Make surface owned by the workspace root."""
    root = _workspace_root()
    names = (c.Infra.MAKEFILE_FILENAME, c.Infra.CUSTOM_MAKE_FILENAME, c.Infra.BASE_MK)
    return tuple(path for name in names if (path := root / name).is_file())


def _silencing_lines(surface: Path) -> tuple[str, ...]:
    """Return recipe lines that discard a command's exit status."""
    return tuple(
        f"{surface.name}:{number}: {line.strip()}"
        for number, line in enumerate(
            surface.read_text(encoding="utf-8").splitlines(), start=1
        )
        if line.startswith("\t") and "|| true" in line
    )


class TestsFlextInfraMakeSurfaceNeverSilencesFailures:
    def test_no_recipe_line_discards_a_command_exit_code(self) -> None:
        """No Make recipe swallows a failure with `|| true`."""
        offenders = {
            surface.name: lines
            for surface in _make_surfaces()
            if (lines := _silencing_lines(surface))
        }

        tm.that(offenders, eq={})
