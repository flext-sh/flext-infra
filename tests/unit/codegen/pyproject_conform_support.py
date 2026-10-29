"""Typed fixtures shared by the pyproject conformance contracts.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

from flext_infra import config
from tests import c, m, p, u


class TestsFlextInfraPyprojectConformSupport:
    """Typed fixtures shared by the pyproject conformance contracts."""

    @staticmethod
    def _repository(
        distribution: str,
        *,
        role: c.Infra.MakeProfile,
        path: str,
    ) -> m.Infra.RepositoryRef:
        provider = u.Tests.provider()
        return m.Infra.RepositoryRef(
            name=distribution,
            distribution=distribution,
            url=f"{provider.base_url}/{distribution}.git",
            path=Path(path),
            role=role,
            provider=provider.name,
            kind=c.Infra.ProjectKind.INTERNAL_FLEXT,
            codegen=c.Infra.CodegenKind.CONFORM,
            package=role is not c.Infra.MakeProfile.WORKSPACE,
            editable=role is not c.Infra.MakeProfile.WORKSPACE,
            read_only=False,
        )

    def _workspace(
        self,
        *,
        role: c.Infra.MakeProfile = c.Infra.MakeProfile.WORKSPACE,
    ) -> m.Infra.WorkspaceSpec:
        return u.Tests.workspace_spec(
            self._repository("workspace", role=role, path="."),
            subprojects=(
                (
                    self._repository(
                        "flext-core",
                        role=c.Infra.MakeProfile.STANDALONE,
                        path="flext-core",
                    ),
                )
                if role is c.Infra.MakeProfile.STANDALONE
                else ()
            ),
        )

    @staticmethod
    def _uv_resolution(
        toolchain: p.Infra.ToolchainSpec,
    ) -> m.Infra.UvResolutionSpec:
        """Route the toolchain's uv resolver keys the way conform declares them.

        Returns:
            The resulting ``m.Infra.UvResolutionSpec``.

        """
        return m.Infra.UvResolutionSpec(
            link_mode=toolchain.uv_link_mode,
            constraint_dependencies=tuple(toolchain.uv_constraint_dependencies),
            environments=tuple(toolchain.uv_environments),
        )

    @staticmethod
    def _detached_dev_floors() -> Sequence[str]:
        """SSOT dev floors seeded for a project outside the workspace overlay.

        A source-less internal dependency is legal only for the workspace
        context root; every other project must carry its declared direct Git
        source (the scaffold seeds exactly this line), so the same SSOT floor
        set is rendered the way a real detached checkout declares it.

        Returns:
            The resulting ``Sequence[str]``.

        """
        branch = u.Tests.provider_branch()
        return tuple(
            (
                f"{floor} @ git+{u.Tests.WorktreeFixture.governed_repository_url(name)}"
                f"@{branch}"
                if (name := u.Infra.dep_name(floor))
                and name.startswith("flext-")
                and "@" not in floor
                else floor
            )
            for floor in config.Infra.codegen.scaffold.project.dev
        )
