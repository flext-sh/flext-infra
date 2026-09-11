"""Tests that the uv lockfile is committable wherever it is the resolution SSOT.

``uv.lock`` pins the exact resolved dependency graph. A UV workspace project
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

from pathlib import Path

import flext_infra
from flext_infra import c
from flext_tests import tm
from tests import u as test_u


def _workspace_root() -> Path:
    """Return the repository root that owns the imported package."""
    return Path(flext_infra.__file__).resolve().parents[2]


def _is_allowed_by_policy(relative_path: str) -> bool:
    """Return whether git would track *relative_path* under the SSOT policy."""
    rendered = "\n".join(test_u.Tests.ignore_patterns_for(_workspace_root())) + "\n"
    return test_u.Tests.is_tracked_under(rendered, relative_path)


class TestsFlextInfraLockfileIsTrackedAtTheResolutionRoot:
    def test_lockfile_is_committable_under_the_ignore_policy(self) -> None:
        """The ignore policy never blocks the uv lockfile."""
        tm.that(_is_allowed_by_policy(c.Infra.UV_LOCK_FILENAME), eq=True)
