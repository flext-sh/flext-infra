"""Workspace project governance derivations composed into the topology detector.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_infra import c, config

if TYPE_CHECKING:
    from pathlib import Path

    from flext_infra import m


class FlextInfraWorkspaceGovernanceMixin:
    """Derive project topology and persistent-state ownership from typed SSOTs."""

    @staticmethod
    def _declares_workspace_toolchain(workspace_root: Path) -> bool:
        """Require a live infra checkout shipping ``base.mk``.

        The checkout is located on disk, not looked up in a project catalog:
        flext-infra owns generic policy, never the map of where each project
        lives. A workspace root either has the toolchain checked out beside it
        (or at its own root) or it does not.
        """
        candidates = (
            workspace_root / c.Infra.BASE_MK,
            workspace_root / config.Infra.name / c.Infra.BASE_MK,
        )
        return any(candidate.is_file() for candidate in candidates)

    @staticmethod
    def persistent_state_artifacts(
        make_profile: c.Infra.MakeProfile,
    ) -> tuple[m.Infra.CodegenArtifactSpec, ...]:
        """Project the persistent-state artifacts owned by one Make profile."""
        if make_profile is not c.Infra.MakeProfile.WORKSPACE:
            return ()
        persistent = c.Infra.PERSISTENT_STATE_ARTIFACT_NAMES
        return tuple(
            artifact
            for artifact in config.Infra.codegen.artifacts
            if artifact.name in persistent
        )


__all__: list[str] = ["FlextInfraWorkspaceGovernanceMixin"]
