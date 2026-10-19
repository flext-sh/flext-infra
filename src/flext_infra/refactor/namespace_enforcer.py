"""Automated namespace enforcement orchestration.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_cli import cli

from flext_infra import c, m, r, u
from flext_infra.codemod import FlextInfraModGateEngine
from flext_infra.refactor import (
    FlextInfraImportNormalization,
    FlextInfraNamespaceEnforcerProjectMixin,
    FlextInfraNamespaceRelocationCascade,
)

if TYPE_CHECKING:
    from pathlib import Path

    from flext_infra import p, t


class FlextInfraNamespaceEnforcer(FlextInfraNamespaceEnforcerProjectMixin):
    """Orchestrate namespace enforcement across a workspace."""

    def __init__(self, *, repository_root: Path) -> None:
        """Initialize with the repository root path."""
        super().__init__()
        self._repository_root = repository_root.resolve()
        self._rope_project: t.Infra.RopeProject = u.Infra.init_rope_project(
            self._repository_root,
        )

    def enforce(
        self,
        *,
        apply: bool = False,
        project_names: t.StrSequence | None = None,
        module: str | None = None,
        gates: t.StrSequence | None = None,
    ) -> m.Infra.WorkspaceEnforcementReport:
        """Run namespace enforcement across projects in the workspace.

        Args:
            apply: If True, auto-fix detected violations.
            project_names: If provided, only enforce these projects.
            module: If provided, normalize and relocate only this dotted module.
            gates: If provided, only run these enforcement gates.

        Returns:
            The resulting ``m.Infra.WorkspaceEnforcementReport``.

        Raises:
            ValueError: If namespace scope requires one owned module.

        """
        project_roots = self._resolve_project_roots(project_names=project_names)
        if not project_roots:
            return m.Infra.WorkspaceEnforcementReport(
                workspace=str(self._repository_root),
            )
        cascade = FlextInfraNamespaceRelocationCascade()
        files_by_project = {
            root: cascade.scoped_py_files(root) for root in project_roots
        }
        if module is not None:
            files_by_project = {
                root: tuple(
                    path
                    for path in paths
                    if u.Infra.module_name_for_file(path, project_root=root) == module
                )
                for root, paths in files_by_project.items()
            }
            if sum(len(paths) for paths in files_by_project.values()) != 1:
                msg = f"namespace scope requires one owned module: {module}"
                raise ValueError(msg)
            files_by_project = {
                root: paths for root, paths in files_by_project.items() if paths
            }
        scoped = frozenset(
            path for paths in files_by_project.values() for path in paths
        )
        before_plan = u.Infra.codemod_rule_plan(self._repository_root).unwrap()
        source_files = tuple(sorted(scoped)) if module is not None else None
        before = FlextInfraModGateEngine.scan(
            self._repository_root,
            fix=False,
            source_files=source_files,
        ).unwrap()
        before = before.model_copy(
            update={
                "entries": tuple(
                    entry
                    for entry in before.entries
                    if (self._repository_root / entry.file).resolve() in scoped
                ),
            }
        )
        if apply:
            for project_root, py_files in files_by_project.items():
                if module is not None:
                    FlextInfraImportNormalization.apply_files(project_root, py_files)
                relocation_ids = tuple(cascade.relocation_by_rule(project_root))
                if not relocation_ids or not py_files:
                    continue
                current = FlextInfraModGateEngine.scan(
                    project_root,
                    fix=False,
                    selection=relocation_ids,
                    source_files=py_files,
                ).unwrap()
                cascade.run(
                    project_root=project_root,
                    rope_project=self._rope_project,
                    findings=cascade.findings_from_report(
                        project_root, py_files, current.entries, scan_root=project_root
                    ),
                    py_files=py_files,
                    gates=gates,
                )
        after = (
            FlextInfraModGateEngine.scan(
                self._repository_root,
                fix=False,
                source_files=source_files,
            ).unwrap()
            if apply
            else before
        )
        after = after.model_copy(
            update={
                "entries": tuple(
                    entry
                    for entry in after.entries
                    if (self._repository_root / entry.file).resolve() in scoped
                ),
            }
        )
        after_plan = (
            u.Infra.codemod_rule_plan(self._repository_root).unwrap()
            if apply
            else before_plan
        )
        rule_ids = tuple(
            sorted({
                rule.id for plan in (before_plan, after_plan) for rule in plan.rules
            })
        )
        deltas = u.Infra.rule_deltas(
            before,
            after,
            options=m.Infra.RuleDeltaOptions(
                inventory=tuple(
                    (root.name, rule_id)
                    for root in project_roots
                    for rule_id in rule_ids
                ),
            ),
        )
        return m.Infra.WorkspaceEnforcementReport(
            workspace=str(self._repository_root),
            projects=tuple(
                self._enforce_project(
                    project_root=root,
                    py_files=py_files,
                    before=before,
                    after=after,
                    rule_deltas=tuple(
                        row for row in deltas if row.repository == root.name
                    ),
                )
                for root, py_files in files_by_project.items()
            ),
        )

    def _resolve_project_roots(
        self,
        *,
        project_names: t.StrSequence | None = None,
    ) -> t.SequenceOf[Path]:
        """Resolve the selected namespace-enabled roots through the topology owner.

        ``.`` names this repository itself; an unknown name is a caller error
        and escapes loud instead of silently enforcing nothing.

        Returns:
            The resulting ``t.SequenceOf[Path]``.

        Raises:
            ValueError: If ``resolved.failure``.

        """
        resolved = u.Infra.resolve_projects(self._repository_root, project_names or ())
        if resolved.failure:
            raise ValueError(resolved.error or "project resolution failed")
        return [
            project.path
            for project in resolved.value
            if u.Infra.namespace_enabled(project.path)
        ]

    @staticmethod
    def render_text(report: m.Infra.WorkspaceEnforcementReport) -> str:
        """Render a workspace enforcement report as plain text.

        Returns:
            The resulting ``str``.

        """
        projects = report.projects
        rows = tuple(row for project in projects for row in project.rule_deltas)
        lines = [
            "Namespace Enforcement Report",
            f"Workspace: {report.workspace}",
            f"Projects: {len(report.projects)}",
            f"Violations: {'YES' if report.has_violations else 'NO'}",
            (
                f"Catalog findings: "
                f"{sum(row.before for row in rows)}"
                " -> "
                f"{sum(row.after for row in rows)}"
            ),
            (f"Introduced occurrences: {sum(row.introduced for row in rows)}"),
            (
                f"Relocation findings: "
                f"{sum(project.relocation_findings for project in projects)}"
            ),
            (
                "Relocations resolved/persisted/introduced: "
                f"{sum(project.relocation_resolved for project in projects)}/"
                f"{sum(project.relocation_persisted for project in projects)}/"
                f"{sum(project.relocation_introduced for project in projects)}"
            ),
            (
                "Relocation files scanned: "
                f"{sum(project.files_scanned for project in projects)}"
            ),
        ]
        for project in projects:
            lines.extend(
                f"{project.project} {row.rule_id}: {row.before} -> {row.after} "
                f"resolved={row.resolved} persisted={row.persisted} "
                f"introduced={row.introduced}"
                for row in project.rule_deltas
                if row.before or row.after
            )
        return "\n".join(lines)

    @classmethod
    def execute_command(
        cls,
        params: m.Infra.RefactorNamespaceEnforceInput,
    ) -> p.Result[m.Infra.WorkspaceEnforcementReport]:
        """Execute namespace enforcement directly from the canonical payload.

        Returns:
            The resulting ``p.Result[m.Infra.WorkspaceEnforcementReport]``.

        """
        enforcer = cls(repository_root=params.repository_root)
        report = enforcer.enforce(
            apply=params.apply,
            project_names=u.Infra.normalize_sequence_values(params.projects),
            module=params.module,
            gates=params.gates,
        )
        cli.display_text(cls.render_text(report))
        published = u.Infra.publish_refactor_report_evidence(
            params.repository_root,
            report,
            relative_path=c.Infra.NAMESPACE_ENFORCE_REPORT_RELATIVE_PATH,
        )
        if published.failure:
            return r[m.Infra.WorkspaceEnforcementReport].from_failure(published)
        has_violations: bool = report.has_violations
        if has_violations:
            return r[m.Infra.WorkspaceEnforcementReport].fail(
                "Namespace violations found",
            )
        return r[m.Infra.WorkspaceEnforcementReport].ok(report)


__all__: list[str] = ["FlextInfraNamespaceEnforcer"]
