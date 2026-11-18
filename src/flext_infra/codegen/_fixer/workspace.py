"""Workspace orchestration mixin for the codegen fixer service.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import TYPE_CHECKING

from flext_infra import c, m, p, u
from flext_infra.codegen._fixer import FlextInfraCodegenFixerPasses
from flext_infra.refactor import FlextInfraNamespaceEnforcer

if TYPE_CHECKING:
    from pathlib import Path


class FlextInfraCodegenFixerWorkspace(FlextInfraCodegenFixerPasses):
    """Private project iteration for codegen fixer composition."""

    if TYPE_CHECKING:
        repository_root: Path
        dry_run: bool
        rules_only: bool

        @property
        def project_names(self) -> Sequence[str] | None:
            """Normalized selected project names."""

    def _fix_project(
        self,
        project: p.Infra.ProjectInfo,
        *,
        enforce_namespace: Callable[[str], p.Infra.WorkspaceEnforcementReport],
    ) -> p.Infra.AutoFixResult:
        """Auto-fix namespace violations in a single project.

        Returns:
            The resulting ``m.Infra.AutoFixResult``.

        """
        project_path = project.path
        if not (project_path / c.Infra.DEFAULT_SRC_DIR).is_dir():
            return self._empty_result(project_path.name)
        project_layout = u.Infra.layout(project_path)
        if project_layout is None or not project_layout.class_stem:
            return self._empty_result(project_path.name)
        pkg_dir = project_layout.package_dir
        if not (pkg_dir / c.Infra.INIT_PY).is_file():
            return self._empty_result(project_path.name)
        if not pkg_dir.parent.is_dir():
            return self._empty_result(project_path.name)
        ctx = m.Infra.FixContext()
        initial_violations = self._load_initial_violations(ctx, project_path)
        if self.dry_run or self.rules_only:
            skipped_ctx = ctx.model_copy(
                update={
                    "violations_skipped": [*ctx.violations_skipped, *initial_violations]
                }
            )
            return self._build_result(project_path.name, skipped_ctx)
        u.Infra.normalize_canonical_facades(pkg_dir=pkg_dir, ctx=ctx)
        self._run_namespace_enforcement(ctx, project_path, enforce_namespace)
        self._run_lazy_init_preflight(ctx, project_path)
        # Each fixer owns Ruff-native output; no post-hoc mutation.
        ctx = self._classify_remaining_violations(ctx, project_path, initial_violations)
        self._run_import_cycle_proof(ctx, project_path)
        return self._build_result(project_path.name, ctx)

    def fix_workspace(
        self,
        *,
        projects: Sequence[p.Infra.ProjectInfo] | None = None,
    ) -> Sequence[p.Infra.AutoFixResult]:
        """Run auto-fix on selected projects.

        Returns:
            The resulting ``Sequence[p.Infra.AutoFixResult]``.

        """
        if projects is not None:
            selected_projects = tuple(projects)
        else:
            discovered = tuple(
                project
                for project in u.Infra.projects(self.repository_root).unwrap()
                if (project.path / c.Infra.DEFAULT_SRC_DIR).is_dir()
            )
            scope = frozenset(self.project_names or ())
            selected_projects = (
                tuple(p for p in discovered if p.path.name in scope)
                if scope
                else discovered
            )
        enforcer = FlextInfraNamespaceEnforcer(repository_root=self.repository_root)

        def enforce_namespace(project_name: str) -> p.Infra.WorkspaceEnforcementReport:
            return enforcer.enforce(
                apply=True,
                project_names=(project_name,),
                gates=(c.Infra.LINT,),
            )

        return [
            self._fix_project(project, enforce_namespace=enforce_namespace)
            for project in selected_projects
        ]


__all__: list[str] = ["FlextInfraCodegenFixerWorkspace"]
