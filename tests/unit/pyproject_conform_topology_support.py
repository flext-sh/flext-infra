"""Shared workspace and requirement fixtures for topology-source contracts.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

from flext_infra import config
from tests import c, m, tm, u


class TestsFlextInfraPyprojectConformTopologySupport:
    """Declare members, workspaces, and requirement forms for topology contracts."""

    _ROLE = c.Infra.MakeProfile

    @staticmethod
    def _conform_options(
        root: Path,
        workspace: m.Infra.WorkspaceSpec,
    ) -> u.Infra.PyprojectConformOptions:
        """Capture each declared package through the public atomic file owner.

        Returns:
            Conform inputs bound to the workspace and its captured metadata.

        """
        return u.Infra.PyprojectConformOptions(
            repository_root=root,
            flext_line=workspace.integration,
            member_declarations=tuple(
                tm.ok(
                    u.Cli.atomic_read_binary_file_state(
                        root / member.path / c.PYPROJECT_FILENAME,
                        required=True,
                    )
                )
                for member in workspace.subprojects
                if member.package
            ),
        )

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

    @staticmethod
    def _conform(
        source: str,
        *,
        workspace: m.Infra.WorkspaceSpec,
        options: u.Infra.PyprojectConformOptions | None = None,
    ) -> str:
        """Conform one document through the public owner with standard inputs.

        Returns:
            The resulting rendered ``str``.

        """
        return tm.ok(
            u.Infra.pyproject_conform(
                source,
                workspace=workspace,
                required_dev_dependencies=(),
                uv_resolution=TestsFlextInfraPyprojectConformTopologySupport._toolchain_resolution(),
                options=options,
            ),
        )

    def _conform_integration(
        self,
        source: str,
        workspace: m.Infra.WorkspaceSpec,
    ) -> str:
        """Conform without captured member declarations.

        Returns:
            The resulting rendered ``str``.

        """
        return self._conform(
            source,
            workspace=workspace,
            options=u.Infra.PyprojectConformOptions(
                flext_line=u.Tests.integration(),
            ),
        )

    @staticmethod
    def _overlay(source: str, rendered: str) -> str:
        """Merge one render through the preserved-overlay owner.

        Returns:
            The resulting merged ``str``.

        """
        return tm.ok(u.Infra.overlay_preserved(source, rendered))
