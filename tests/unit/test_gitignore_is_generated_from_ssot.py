"""Tests that this repository's ``.gitignore`` is reproducible from config.

The selected repository consumes one ordered policy plus its named layout
override. Topology does not change the rendered artifact.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

import flext_infra
from flext_infra import c, config
from flext_tests import tm
from tests import u as test_u


def _workspace_root() -> Path:
    """Return the workspace root that owns this checkout."""
    return Path(flext_infra.__file__).resolve().parents[2]


def _is_allowed_by_policy(relative_path: str) -> bool:
    """Return whether the shipped SSOT policy keeps *relative_path* trackable."""
    rendered = "\n".join(test_u.Tests.ignore_patterns_for(_workspace_root())) + "\n"
    return test_u.Tests.is_tracked_under(rendered, relative_path)


class TestsFlextInfraGitignoreIsGeneratedFromSsot:
    def test_every_managed_file_survives_the_ignore_policy(self) -> None:
        """No committed managed artifact is ignored by the shipped policy.

        ``codegen conform`` creates every entry of ``managed_files`` and then
        verifies the tree through git. A whitelist that blocks one of those
        paths makes the artifact untrackable, so conform re-reports it as a new
        file on every run and the whole transaction never converges.

        ``delegated`` entries are the deliberate exception: they are generated
        into each checkout rather than committed, so being ignored is correct.
        The distinction is read from the managed-file policy, never hardcoded.
        """
        committed = tuple(
            item
            for item in config.Infra.codegen.managed_files
            if item.policy != c.Infra.MANAGED_FILE_POLICY_DELEGATED
        )
        blocked = tuple(
            item.path.as_posix()
            for item in committed
            if not _is_allowed_by_policy(item.path.as_posix())
        )

        tm.that(blocked, eq=())
