"""Workspace orchestration mixin for the codegen fixer service."""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_infra import c, m, u
from flext_infra.codegen._fixer_passes import FlextInfraCodegenFixerPassesMixin

if TYPE_CHECKING:
    from pathlib import Path

    from flext_infra import p, t


class FlextInfraCodegenFixerWorkspaceMixin(FlextInfraCodegenFixerPassesMixin):
    """Private project iteration for codegen fixer composition."""

    if TYPE_CHECKING:
        workspace_root: Path
        dry_run: bool
        rules_only: bool

        @property
        def project_names(self) -> t.StrSequence | None:
            """Normalized selected project names."""

    def _fix_project(self, project: p.Infra.ProjectInfo) -> m.Infra.AutoFixResult:
        """Auto-fix namespace violations in a single project."""
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
            ctx.violations_skipped.extend(initial_violations)
            return self._build_result(project_path.name, ctx)
        u.Infra.normalize_canonical_facades(pkg_dir=pkg_dir, ctx=ctx)
        self._run_refactor_service(ctx, project_path)
        self._run_namespace_enforcement(ctx, project_path)
        self._run_lazy_init_regeneration(ctx, project_path)
        # flext-j47u (codex): each fixer owns Ruff-native output; no post-hoc mutation.
        self._classify_remaining_violations(ctx, project_path, initial_violations)
        return self._build_result(project_path.name, ctx)

    def fix_workspace(
        self, *, projects: t.SequenceOf[p.Infra.ProjectInfo] | None = None
    ) -> t.SequenceOf[m.Infra.AutoFixResult]:
        """Run auto-fix on selected projects."""
        if projects is not None:
            selected_projects = tuple(projects)
        else:
            projects_result = u.Infra.projects(
                self.workspace_root, names=self.project_names or ()
            )
            if projects_result.failure:
                raise ValueError(projects_result.error or "project resolution failed")
            selected_projects = tuple(projects_result.value)
        return [self._fix_project(project) for project in selected_projects]


__all__: list[str] = ["FlextInfraCodegenFixerWorkspaceMixin"]
