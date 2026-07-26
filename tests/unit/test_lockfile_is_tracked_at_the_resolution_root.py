"""Tests that the uv lockfile is committable wherever it is the resolution SSOT.

``uv.lock`` pins the exact resolved dependency graph. A uv *workspace member*
does not own one -- resolution happens once at the workspace root -- but the
root itself, and any standalone distribution, must commit theirs or every
checkout re-resolves and the build stops being reproducible.

The workspace ``.gitignore`` blocks everything with ``/*`` and re-allows paths
explicitly, and it never re-allowed ``uv.lock``. The lockfile was therefore
unversionable at the exact place where it is authoritative: regenerating it
after a dependency change produced a file git refused to see.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import tempfile
from pathlib import Path

from flext_tests import tm

from flext_infra import c, config, u


def _ssot_patterns() -> tuple[str, ...]:
    """Return every ignore pattern declared by the config SSOT."""
    return tuple(
        pattern
        for section in config.Infra.codegen.gitignore_sections
        for pattern in section.patterns
    )


def _is_allowed_by_policy(relative_path: str) -> bool:
    """Return whether git would track *relative_path* under the SSOT policy."""
    rendered = "\n".join(_ssot_patterns()) + "\n"
    with tempfile.TemporaryDirectory() as raw_root:
        root = Path(raw_root)
        tm.ok(u.Cli.run_checked(["git", "init", "-q", str(root)]))
        (root / ".gitignore").write_text(rendered, encoding="utf-8")
        target = root / relative_path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("", encoding="utf-8")
        # `git check-ignore` exits 0 when the path IS ignored, so a failed run
        # is the success case for a file that must stay trackable.
        probe = u.Cli.run_checked(
            ["git", "check-ignore", "-q", relative_path], cwd=root
        )
    return probe.failure


class TestsFlextInfraLockfileIsTrackedAtTheResolutionRoot:
    def test_lockfile_is_committable_under_the_ignore_policy(self) -> None:
        """The ignore policy never blocks the uv lockfile."""
        tm.that(_is_allowed_by_policy(c.Infra.UV_LOCK_FILENAME), eq=True)
