"""Shared workspace and requirement fixtures for topology-source contracts.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from difflib import unified_diff
from pathlib import Path
from typing import TYPE_CHECKING

from flext_infra import config
from tests import c, m, tm, u

if TYPE_CHECKING:
    from tests import p


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
    def _integration(
        repository_root: Path | None = None,
    ) -> u.Infra.PyprojectConformOptions:
        """Declare the conform options carrying the detected integration line.

        Returns:
            The options naming the fixture integration line and ``repository_root``.

        """
        line = u.Tests.integration()
        if repository_root is None:
            return u.Infra.PyprojectConformOptions(flext_line=line)
        return u.Infra.PyprojectConformOptions(
            repository_root=repository_root,
            flext_line=line,
        )

    def _conform(
        self,
        source: str,
        workspace: m.Infra.WorkspaceSpec,
        options: u.Infra.PyprojectConformOptions | None = None,
    ) -> p.Result[str]:
        """Run the real conformance over ``source`` with the fleet toolchain keys.

        Returns:
            The conformed document or the typed failure.

        """
        return u.Infra.pyproject_conform(
            source,
            workspace=workspace,
            required_dev_dependencies=(),
            uv_resolution=self._toolchain_resolution(),
            options=options,
        )

    def _assert_fixed_point(
        self,
        rendered: str,
        workspace: m.Infra.WorkspaceSpec,
        options: u.Infra.PyprojectConformOptions | None = None,
        *,
        source: str | None = None,
    ) -> None:
        """Require conforming ``source`` (default ``rendered``) to reproduce ``rendered``."""
        actual = tm.ok(
            self._conform(rendered if source is None else source, workspace, options),
        )
        tm.that(
            actual,
            eq=rendered,
            msg="\n".join(unified_diff(rendered.splitlines(), actual.splitlines())),
        )

    def _write_member(
        self,
        root: Path,
        member: m.Infra.RepositoryRef,
        groups: str = "",
    ) -> None:
        """Write the declared metadata of ``member`` under ``root``."""
        path = root / member.path / c.PYPROJECT_FILENAME
        path.parent.mkdir(parents=True)
        path.write_text(
            f'[project]\nname = "{member.distribution}"\nversion = "1.0.0"\n{groups}',
            encoding="utf-8",
        )

    def _candidate_workspace(
        self,
        *members: m.Infra.RepositoryRef,
        candidate: m.Infra.RepositoryRef,
        commit: str,
        url: str | None = None,
    ) -> m.Infra.WorkspaceSpec:
        """Declare a standalone workspace pinning ``candidate`` at ``commit``.

        Returns:
            The workspace carrying one candidate dependency commit.

        """
        return self._workspace(*members, role=self._ROLE.STANDALONE).model_copy(
            update={
                "candidate_dependencies": (
                    m.Infra.DependencyCommitSourceSpec(
                        distribution=candidate.distribution,
                        url=candidate.url if url is None else url,
                        commit=commit,
                    ),
                ),
            },
        )

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
