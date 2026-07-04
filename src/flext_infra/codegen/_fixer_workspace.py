"""Workspace orchestration mixin for the codegen fixer service."""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_infra.codegen._fixer_passes import FlextInfraCodegenFixerPassesMixin
from flext_infra.constants import c
from flext_infra.models import m
from flext_infra.utilities import u

if TYPE_CHECKING:
    from pathlib import Path

    from flext_infra.protocols import p
    from flext_infra.typings import t


class FlextInfraCodegenFixerWorkspaceMixin(FlextInfraCodegenFixerPassesMixin):
    """Private project iteration for codegen fixer composition."""

    if TYPE_CHECKING:
        workspace_root: Path
        dry_run: bool
        rules_only: bool

        @property
        def project_names(self) -> t.StrSequence | None:
            """Normalized selected project names."""

    def _fix_project(
        self,
        project: p.Infra.ProjectInfo,
    ) -> m.Infra.AutoFixResult:
        """Auto-fix namespace violations in a single project."""
        project_path = project.path
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
            ctx.violations_skipped.extend(initial_violations)
            return self._build_result(project_path.name, ctx)
        py_files_result = u.Infra.iter_python_files(
            workspace_root=project_path,
            project_roots=[project_path],
        )
        py_files = tuple(py_files_result.value) if py_files_result.success else ()
        bak_paths = u.Infra.backup_files(py_files)
        u.Infra.normalize_canonical_facades(pkg_dir=pkg_dir, ctx=ctx)
        self._run_mro_migration(ctx, project_path)
        self._run_refactor_service(ctx, project_path)
        self._run_namespace_enforcement(ctx, project_path)
        self._run_lazy_init_regeneration(ctx, project_path)
        self._post_fix_ruff_format(ctx, bak_paths)
        self._classify_remaining_violations(ctx, project_path, initial_violations)
        return self._build_result(project_path.name, ctx)

    def fix_workspace(
        self,
        *,
        projects: t.SequenceOf[p.Infra.ProjectInfo] | None = None,
    ) -> t.SequenceOf[m.Infra.AutoFixResult]:
        """Run auto-fix on selected projects."""
        if projects is not None:
            selected_projects = tuple(projects)
        else:
            projects_result = u.Infra.projects(self.workspace_root)
            discovered = (
                tuple(projects_result.unwrap()) if projects_result.success else ()
            )
            scope = frozenset(self.project_names or ())
            selected_projects = (
                tuple(p for p in discovered if p.path.name in scope)
                if scope
                else discovered
            )
        return [self._fix_project(project) for project in selected_projects]


__all__: list[str] = ["FlextInfraCodegenFixerWorkspaceMixin"]
