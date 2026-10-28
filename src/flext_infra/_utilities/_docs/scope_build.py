"""Docs scope construction helpers.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import (
    Iterable,
    Iterator,
    Mapping,
    MutableMapping,
    MutableSequence,
    Sequence,
)

from collections.abc import Sequence
from typing import TYPE_CHECKING

from flext_infra import c, m, r
from flext_infra._utilities import (
    FlextInfraUtilitiesBase,
    FlextInfraUtilitiesWorkspaceManifest,
)
from flext_infra._utilities._docs import (
    FlextInfraUtilitiesDocsScope,
    FlextInfraUtilitiesDocsScopeSelection,
)
from flext_infra._utilities._pyproject import FlextInfraUtilitiesPyprojectConform

if TYPE_CHECKING:
    from pathlib import Path

    from flext_infra import p


class FlextInfraUtilitiesDocsScopeBuild(
    FlextInfraUtilitiesDocsScopeSelection,
):
    """Build canonical DocScope models for docs commands."""

    @staticmethod
    def _selected_project_names(
        repository_root: Path,
        projects: Sequence[str] | None,
    ) -> list[str]:
        """Return normalized project filters for docs-scoped operations.

        Returns:
            Normalized project filters for docs-scoped operations.

        Raises:
            ValueError: If an explicit project selection is empty.

        """
        if projects is None:
            return []
        selected = FlextInfraUtilitiesBase.normalize_sequence_values(projects)
        if not selected:
            msg = f"docs project selection is empty for {repository_root}"
            raise ValueError(msg)
        return list(selected)

    @staticmethod
    def build_scopes(
        repository_root: Path,
        projects: Sequence[str] | None,
        output_dir: Path | str,
        *,
        include_root: bool = True,
    ) -> p.Result[Sequence[m.Infra.DocScope]]:
        """Build DocScope objects for repository root and selected projects.

        ``include_root`` governs only whether the workspace root itself is
        rendered as a docs OUTPUT scope; root guides/pyproject remain readable
        SOURCES for member projects regardless.

        Returns:
            The resulting ``p.Result[Sequence[m.Infra.DocScope]]``.

        """
        try:
            scopes = FlextInfraUtilitiesDocsScopeBuild._build_scopes_unchecked(
                repository_root,
                projects,
                output_dir,
                include_root=include_root,
            )
        except c.EXC_OS_TYPE_VALUE as exc:
            return r[Sequence[m.Infra.DocScope]].fail_op("scope resolution", exc)
        return r[Sequence[m.Infra.DocScope]].ok(scopes)

    @staticmethod
    def _build_scopes_unchecked(
        repository_root: Path,
        projects: Sequence[str] | None,
        output_dir: Path | str,
        *,
        include_root: bool,
    ) -> Sequence[m.Infra.DocScope]:
        """Build docs scopes without exception wrapping.

        Returns:
            The resulting ``Sequence[m.Infra.DocScope]``.

        """
        resolved_root = repository_root.resolve()
        project_state = FlextInfraUtilitiesDocsScope.project_state(resolved_root)
        is_enabled = FlextInfraUtilitiesDocsScope.docs_scope_enabled(
            project_state.docs_meta,
        )
        discovered = FlextInfraUtilitiesDocsScopeBuild._discover_projects(
            resolved_root,
        )
        has_declared_members = bool(
            FlextInfraUtilitiesPyprojectConform.workspace_project_paths(resolved_root),
        )
        has_child_projects = any(
            project.path.resolve() != resolved_root for project in discovered
        )
        # Git declarations own workspace composition. A standalone project's
        # configuration cannot turn its documentation into an aggregate scope.
        has_workspace_topology = FlextInfraUtilitiesWorkspaceManifest.fleet_umbrella(
            resolved_root,
        )
        if (
            (resolved_root / c.PYPROJECT_FILENAME).is_file()
            and not has_declared_members
            and not has_child_projects
            and not has_workspace_topology
            and is_enabled
        ):
            selected_names = FlextInfraUtilitiesDocsScopeBuild._selected_project_names(
                resolved_root,
                projects,
            )
            if selected_names:
                return FlextInfraUtilitiesDocsScopeBuild._selected_project_scopes(
                    resolved_root,
                    discovered,
                    selected_names,
                    output_dir,
                )
            return (
                FlextInfraUtilitiesDocsScopeBuild._governed_scope(
                    resolved_root,
                    output_dir,
                    repository_root=resolved_root,
                ),
            )
        return FlextInfraUtilitiesDocsScopeBuild._workspace_scopes(
            resolved_root,
            projects,
            output_dir,
            discovered,
            include_root=include_root,
        )

    @staticmethod
    def _workspace_scopes(
        repository_root: Path,
        projects: Sequence[str] | None,
        output_dir: Path | str,
        discovered: Sequence[m.Infra.ProjectInfo],
        *,
        include_root: bool,
    ) -> Sequence[m.Infra.DocScope]:
        """Build docs scopes for a repository root plus child projects.

        The root scope is an OUTPUT participant only when ``include_root`` is
        true; excluding it never affects source discovery (root guides,
        pyproject, config) which is derived independently from the physical
        repository root.

        Returns:
            The resulting ``Sequence[m.Infra.DocScope]``.

        """
        scopes: list[m.Infra.DocScope] = (
            [
                m.Infra.DocScope(
                    name=c.Infra.RK_ROOT,
                    path=repository_root,
                    report_dir=(repository_root / output_dir).resolve(),
                    project_class="root",
                    package_name="",
                ),
            ]
            if include_root
            else []
        )
        selected_names = FlextInfraUtilitiesDocsScopeBuild._selected_project_names(
            repository_root,
            projects,
        )
        if selected_names:
            scopes.extend(
                FlextInfraUtilitiesDocsScopeBuild._selected_project_scopes(
                    repository_root,
                    discovered,
                    selected_names,
                    output_dir,
                ),
            )
            return tuple(scopes)
        scopes.extend(
            FlextInfraUtilitiesDocsScopeBuild._doc_scope(
                project=project,
                output_dir=output_dir,
                repository_root=repository_root,
            )
            for project in discovered
        )
        return tuple(scopes)

    @staticmethod
    def _discover_projects(repository_root: Path) -> Sequence[m.Infra.ProjectInfo]:
        """Discover workspace projects or raise a typed value error.

        Returns:
            The resulting ``Sequence[m.Infra.ProjectInfo]``.

        Raises:
            ValueError: If ``discovered_result.failure``.

        """
        discovered_result = FlextInfraUtilitiesDocsScope.resolve_projects(
            repository_root,
            (),
        )
        if discovered_result.failure:
            msg = discovered_result.error or "project discovery failed"
            raise ValueError(msg)
        return discovered_result.value


__all__: list[str] = ["FlextInfraUtilitiesDocsScopeBuild"]
