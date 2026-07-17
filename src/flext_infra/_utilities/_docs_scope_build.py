"""Docs scope construction helpers.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

from flext_core import r
from flext_infra import c, m, p, t
from flext_infra._utilities._docs_scope_selection import (
    FlextInfraUtilitiesDocsScopeSelectionMixin,
)
from flext_infra._utilities.base import FlextInfraUtilitiesBase
from flext_infra._utilities.docs_scope import FlextInfraUtilitiesDocsScope


class FlextInfraUtilitiesDocsScopeBuildMixin(
    FlextInfraUtilitiesDocsScopeSelectionMixin
):
    """Build canonical DocScope models for docs commands."""

    @staticmethod
    def _selected_project_names(
        workspace_root: Path, projects: t.StrSequence | None
    ) -> list[str]:
        """Return normalized project filters for docs-scoped operations."""
        _ = workspace_root
        return list(FlextInfraUtilitiesBase.normalize_sequence_values(projects) or ())

    @staticmethod
    def build_scopes(
        workspace_root: Path, projects: t.StrSequence | None, output_dir: Path | str
    ) -> p.Result[t.SequenceOf[p.Infra.DocScope]]:
        """Build DocScope objects for workspace root and selected projects."""
        try:
            scopes = FlextInfraUtilitiesDocsScopeBuildMixin._build_scopes_unchecked(
                workspace_root, projects, output_dir
            )
        except c.EXC_OS_TYPE_VALUE as exc:
            return r[t.SequenceOf[p.Infra.DocScope]].fail_op("scope resolution", exc)
        return r[t.SequenceOf[p.Infra.DocScope]].ok(scopes)

    @staticmethod
    def _build_scopes_unchecked(
        workspace_root: Path, projects: t.StrSequence | None, output_dir: Path | str
    ) -> t.SequenceOf[p.Infra.DocScope]:
        """Build docs scopes without exception wrapping."""
        resolved_root = workspace_root.resolve()
        if FlextInfraUtilitiesDocsScope.is_governed_project(
            resolved_root.name, resolved_root.parent
        ):
            return (
                FlextInfraUtilitiesDocsScopeBuildMixin._governed_scope(
                    resolved_root, output_dir
                ),
            )
        return FlextInfraUtilitiesDocsScopeBuildMixin._workspace_scopes(
            resolved_root, projects, output_dir
        )

    @staticmethod
    def _workspace_scopes(
        workspace_root: Path, projects: t.StrSequence | None, output_dir: Path | str
    ) -> t.SequenceOf[p.Infra.DocScope]:
        """Build docs scopes for a workspace root plus child projects."""
        scopes: list[p.Infra.DocScope] = [
            m.Infra.DocScope(
                name=c.Infra.RK_ROOT,
                path=workspace_root,
                report_dir=(workspace_root / output_dir).resolve(),
                project_class="root",
                package_name="",
            )
        ]
        discovered = FlextInfraUtilitiesDocsScopeBuildMixin._discover_projects(
            workspace_root
        )
        selected_names = FlextInfraUtilitiesDocsScopeBuildMixin._selected_project_names(
            workspace_root, projects
        )
        if selected_names:
            scopes.extend(
                FlextInfraUtilitiesDocsScopeBuildMixin._selected_project_scopes(
                    workspace_root, discovered, selected_names, output_dir
                )
            )
            return tuple(scopes)
        scopes.extend(
            FlextInfraUtilitiesDocsScopeBuildMixin._doc_scope(
                project=project, output_dir=output_dir
            )
            for project in discovered
        )
        return tuple(scopes)

    @staticmethod
    def _discover_projects(workspace_root: Path) -> t.SequenceOf[p.Infra.ProjectInfo]:
        """Discover workspace projects or raise a typed value error."""
        discovered_result = FlextInfraUtilitiesDocsScope.discover_projects(
            workspace_root
        )
        if discovered_result.failure:
            msg = discovered_result.error or "project discovery failed"
            raise ValueError(msg)
        return discovered_result.value


__all__: list[str] = ["FlextInfraUtilitiesDocsScopeBuildMixin"]
