"""Shared workspace and requirement fixtures for topology-source contracts.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

from flext_infra import config
from tests import c, m, u


class TestsFlextInfraPyprojectConformTopologySupport:
    """Declare members, workspaces, and requirement forms for topology contracts."""

    _ROLE = c.Infra.MakeProfile

    def _member_ref(self, distribution: str, path: str) -> m.Infra.RepositoryRef:
        """Declare one standalone-capable member through the provider contract.

        Returns:
            The resulting ``m.Infra.RepositoryRef``.

        """
        return u.Tests.repository_ref(
            distribution,
            role=self._ROLE.STANDALONE,
            path=Path(path),
        )

    @staticmethod
    def _workspace(
        *members: m.Infra.RepositoryRef,
        role: c.Infra.MakeProfile = c.Infra.MakeProfile.WORKSPACE,
    ) -> m.Infra.WorkspaceSpec:
        """Compose one workspace fixture from its declared member references.

        Returns:
            The resulting ``m.Infra.WorkspaceSpec``.

        """
        return u.Tests.workspace_spec(
            u.Tests.repository_ref("workspace", role=role),
            subprojects=tuple(members),
        )

    @staticmethod
    def _inline_requirement(ref: m.Infra.RepositoryRef) -> str:
        """Render the direct-source form derived from the declared fixture branch.

        Returns:
            The resulting ``str``.

        """
        return f"{ref.distribution} @ git+{ref.url}@{u.Tests.provider_branch()}"

    @staticmethod
    def _toolchain_resolution() -> m.Infra.UvResolutionSpec:
        """Declare the fleet toolchain's uv resolver keys with no exclusions.

        Returns:
            The resulting ``m.Infra.UvResolutionSpec``.

        """
        toolchain = config.Infra.codegen.toolchain
        return m.Infra.UvResolutionSpec(
            link_mode=toolchain.uv_link_mode,
            constraint_dependencies=tuple(toolchain.uv_constraint_dependencies),
            environments=tuple(toolchain.uv_environments),
        )
