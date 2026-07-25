"""Tests that the workspace ``.gitignore`` is reproducible from the config SSOT.

``.gitignore`` is declared a managed artifact, but the workspace root uses a
whitelist strategy (``/*`` blocks everything, then explicit ``!`` negations
re-allow the governed paths) that was never declared in
``codegen.gitignore_sections``. The generator therefore rendered a conventional
blacklist instead, and ``codegen conform`` proposed replacing 371 lines with
~76 — which would un-ignore hundreds of paths.

That single unexpressed policy blocks the whole conform transaction, so no
other generator fix can reach the tree. The strategy must live in the SSOT so
the rendered output equals the governed file.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

from flext_tests import tm

from flext_infra import config


def _workspace_root() -> Path:
    """Return the workspace root that owns this checkout."""
    return Path(__file__).resolve().parents[3]


def _ssot_patterns() -> tuple[str, ...]:
    """Return every ignore pattern declared by the config SSOT."""
    return tuple(
        pattern
        for section in config.Infra.codegen.gitignore_sections
        for pattern in section.patterns
    )


def _live_patterns() -> tuple[str, ...]:
    """Return every meaningful line of the governed ``.gitignore``."""
    text = (_workspace_root() / ".gitignore").read_text(encoding="utf-8")
    return tuple(
        stripped
        for line in text.splitlines()
        if (stripped := line.strip()) and not stripped.startswith("#")
    )


class TestsFlextInfraGitignoreIsGeneratedFromSsot:
    def test_ssot_declares_every_governed_ignore_pattern(self) -> None:
        """No pattern exists on disk that the SSOT cannot reproduce."""
        declared = frozenset(_ssot_patterns())
        missing = tuple(
            pattern for pattern in _live_patterns() if pattern not in declared
        )

        tm.that(missing, eq=())

    def test_ssot_reproduces_the_governed_pattern_order(self) -> None:
        """The SSOT projection equals the governed file, order included.

        A whitelist is order-sensitive: everything before ``/*`` is dead, and a
        directory ignored before its own ``!`` negation is never re-allowed.
        Set equality is therefore not enough -- the projection the generator
        feeds the template must be the governed sequence itself.
        """
        tm.that(_ssot_patterns(), eq=_live_patterns())
