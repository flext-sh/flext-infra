"""Automated namespace enforcement orchestration."""

from __future__ import annotations

from collections.abc import (
    Callable,
    MutableSequence,
    Sequence,
)
from pathlib import Path
from typing import override

from flext_cli import cli

from flext_infra import (
    FlextInfraNamespaceEnforcerPhasesMixin,
    m,
    p,
    r,
    t,
    u,
)


class FlextInfraNamespaceEnforcer(FlextInfraNamespaceEnforcerPhasesMixin):
    """Orchestrate namespace enforcement across a workspace."""

    def __init__(self, *, workspace_root: Path) -> None:
        """Initialize with the workspace root path."""
        super().__init__()
        self._workspace_root = workspace_root.resolve()
        self._rope_project: t.Infra.RopeProject = u.Infra.init_rope_project(
            self._workspace_root,
        )

    def _reload_rope_project(self) -> None:
        """Refresh rope state after on-disk rewrites."""
        self._rope_project.close()
        self._rope_project = u.Infra.init_rope_project(self._workspace_root)

    @override
    def enforce(
        self,
        *,
        apply: bool = False,
        project_names: t.StrSequence | None = None,
    ) -> m.Infra.WorkspaceEnforcementReport:
        """Run namespace enforcement across projects in the workspace.

        Args:
            apply: If True, auto-fix detected violations.
            project_names: If provided, only enforce these projects.

        """
        project_roots = self._resolve_project_roots(project_names=project_names)
        project_reports: list[m.Infra.ProjectEnforcementReport] = []
        for project_root in project_roots:
            report = self._enforce_project(
                project_root=project_root,
                project_name=project_root.name,
                apply=apply,
            )
            project_reports.append(report)
        return m.Infra.WorkspaceEnforcementReport.from_projects(
            workspace=str(self._workspace_root),
            projects=project_reports,
        )

    @override
    def _resolve_project_roots(
        self,
        *,
        project_names: t.StrSequence | None = None,
    ) -> Sequence[Path]:
        """Discover and optionally filter project roots."""
        project_roots = u.Infra.discover_project_roots(
            workspace_root=self._workspace_root,
        )
        project_roots = [
            project_root
            for project_root in project_roots
            if u.Infra.namespace_enabled(project_root)
        ]
        if project_names:
            name_set = set(project_names)
            project_roots = [r for r in project_roots if r.name in name_set]
        return project_roots

    @override
    def _detect_and_apply[V](
        self,
        *,
        py_files: Sequence[Path],
        detect_fn: Callable[[Path], Sequence[V]],
        rewrite_fn: Callable[[MutableSequence[V]], None] | None,
        apply: bool,
    ) -> MutableSequence[V]:
        """Run detect -> optional apply -> re-detect cycle for a violation type.

        Re-detection only runs when apply=True AND a real rewrite_fn is provided.
        """
        violations: MutableSequence[V] = []
        for py_file in py_files:
            violations.extend(detect_fn(py_file))
        if not (apply and violations and rewrite_fn is not None):
            return violations
        rewrite_fn(violations)
        self._reload_rope_project()
        post_violations: MutableSequence[V] = []
        for py_file in py_files:
            post_violations.extend(detect_fn(py_file))
        return post_violations

    @staticmethod
    def render_text(
        report: m.Infra.WorkspaceEnforcementReport,
    ) -> str:
        """Render a workspace enforcement report as plain text."""
        text: str = u.Infra.render_namespace_enforcement_report(
            report,
        )
        return text

    @classmethod
    def execute_command(
        cls,
        params: m.Infra.RefactorNamespaceEnforceInput,
    ) -> p.Result[m.Infra.WorkspaceEnforcementReport]:
        """Execute namespace enforcement directly from the canonical payload."""
        enforcer = cls(workspace_root=params.workspace_path)
        if params.diff:
            diff_output = enforcer.diff(project_names=params.project_names)
            cli.display_text(diff_output or "No changes detected.")
        report = enforcer.enforce(
            apply=params.apply,
            project_names=params.project_names,
        )
        if not params.diff:
            cli.display_text(cls.render_text(report))
        if report.has_violations:
            return r[m.Infra.WorkspaceEnforcementReport].fail(
                "Namespace violations found"
            )
        return r[m.Infra.WorkspaceEnforcementReport].ok(report)


__all__: list[str] = ["FlextInfraNamespaceEnforcer"]
