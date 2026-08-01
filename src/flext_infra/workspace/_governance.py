"""Workspace member governance derivations composed into the topology detector.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_core import r
from flext_infra import c, config, u

if TYPE_CHECKING:
    from pathlib import Path

    from flext_infra import m, p


class FlextInfraWorkspaceGovernanceMixin:
    """Derive member attachment and persistent-state ownership from typed SSOTs."""

    @staticmethod
    def _declares_attached_standalone(repository_root: Path) -> p.Result[bool]:
        """Read the ``[tool.flext.workspace] attached`` opt-in marker."""
        metadata = u.read_project_metadata(repository_root)
        if metadata.failure:
            # An absent or unreadable pyproject carries no opt-in signal; the
            # manifest and Git topology remain the authoritative classifiers.
            return r[bool].ok(False)
        return r[bool].ok(metadata.value.flext.workspace.attached)

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
