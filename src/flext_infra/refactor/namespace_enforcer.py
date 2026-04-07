"""Automated namespace enforcement orchestration."""

from __future__ import annotations

from collections.abc import Callable, MutableSequence, Sequence
from pathlib import Path
from typing import override

from flext_infra import (
    FlextInfraNamespaceEnforcerPhasesMixin,
    c,
    m,
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
            py_files = list(
                project_root.rglob(c.Infra.Extensions.PYTHON_GLOB),
            )
            bak_paths: Sequence[Path] = u.Infra.backup_files(py_files) if apply else []
            report = self._enforce_project(
                project_root=project_root,
                project_name=project_root.name,
                apply=apply,
            )
            if apply and report.has_violations:
                u.Infra.restore_files(bak_paths)
            elif apply:
                u.Infra.cleanup_backups(bak_paths)
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

    @staticmethod
    @override
    def _detect_and_apply[V](
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
        post_violations: MutableSequence[V] = []
        for py_file in py_files:
            post_violations.extend(detect_fn(py_file))
        return post_violations

    @staticmethod
    def render_text(
        report: m.Infra.WorkspaceEnforcementReport,
    ) -> str:
        """Render a workspace enforcement report as plain text."""
        return u.Infra.render_namespace_enforcement_report(
            report,
        )


__all__ = ["FlextInfraNamespaceEnforcer"]
