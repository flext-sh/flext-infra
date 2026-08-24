"""Workspace member governance derivations composed into the topology detector.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_infra import c, config

if TYPE_CHECKING:
    from flext_infra import m


class FlextInfraWorkspaceGovernanceMixin:
    """Derive persistent-state ownership from typed SSOTs."""

    @staticmethod
    def persistent_state_artifacts(
        make_profile: c.Infra.MakeProfile,
    ) -> tuple[m.Infra.CodegenArtifactSpec, ...]:
        """Project the persistent-state artifacts owned by one Make profile."""
        if make_profile is not c.Infra.MakeProfile.WORKSPACE_ROOT:
            return ()
        persistent = c.Infra.PERSISTENT_STATE_ARTIFACT_NAMES
        return tuple(
            artifact
            for artifact in config.Infra.codegen.artifacts
            if artifact.name in persistent
        )


__all__: list[str] = ["FlextInfraWorkspaceGovernanceMixin"]
