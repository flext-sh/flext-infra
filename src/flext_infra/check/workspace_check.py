"""FLEXT infrastructure workspace checker."""

from __future__ import annotations

import shlex
from pathlib import Path
from typing import override

from flext_infra import c, m, p, r, s, t, u
from flext_infra.check._workspace_check_reports import (
    FlextInfraWorkspaceCheckReportsMixin,
)
from flext_infra.check.workspace_check_gates import (
    FlextInfraGateRegistry,
    FlextInfraWorkspaceCheckGatesMixin,
)


class FlextInfraWorkspaceChecker(
    s[bool], FlextInfraWorkspaceCheckGatesMixin, FlextInfraWorkspaceCheckReportsMixin
):
    """Run workspace quality gates and generate reports."""

    _workspace_root: Path = u.PrivateAttr()
    _registry: FlextInfraGateRegistry = u.PrivateAttr()
    _default_reports_dir: Path = u.PrivateAttr()

    def __init__(
        self, workspace_root: Path | None = None, *, workspace: Path | None = None
    ) -> None:
        """Initialize workspace checker services and paths."""
        resolved_workspace = u.Infra.resolve_workspace_root_or_cwd(
            workspace_root or workspace
        )
        super().__init__(workspace_root=resolved_workspace)
        self._workspace_root = self.workspace_root
        self._registry = FlextInfraGateRegistry.default()
        report_dir = u.Cli.resolve_report_dir(
            self._workspace_root, c.Infra.PROJECT, c.Infra.VERB_CHECK
        )
        dir_result = u.Cli.ensure_dir(report_dir)
        if dir_result.failure:
            self._default_reports_dir = (
                self._workspace_root / c.Infra.REPORTS_DIR_NAME / c.Infra.VERB_CHECK
            )
        else:
            self._default_reports_dir = report_dir

    @staticmethod
    def parse_tool_args(raw: str | None) -> t.StrSequence:
        """Parse extra gate arguments passed as a shell-style string."""
        if raw is None:
            return list[str]()
        return [item for item in shlex.split(raw) if item]

    @classmethod
    def resolve_gates(cls, gates: t.StrSequence) -> p.Result[list[str]]:
        """Resolve and validate requested gate names."""
        resolved = FlextInfraGateRegistry.default().resolve(gates)
        if resolved.failure:
            return r[list[str]].fail(resolved.error or "invalid gates")
        return r[list[str]].ok(list(resolved.value))

    @override
    def execute(self) -> p.Result[bool]:
        """Execute."""
        return r[bool].fail("Use execute_command() directly")

    @classmethod
    def execute_payload(cls, params: m.Infra.RunCommand) -> p.Result[bool]:
        """Execute quality gates from the canonical check command payload."""
        checker = cls(workspace_root=params.workspace_path)
        project_targets_result = cls._resolve_project_targets(params)
        if project_targets_result.failure:
            return r[bool].fail(
                project_targets_result.error or "project resolution failed"
            )
        project_targets = project_targets_result.value
        gates = params.gates
        gate_ctx = m.Infra.GateContext(
            workspace=params.workspace_path,
            reports_dir=params.reports_dir_path,
            fail_fast=params.fail_fast,
            ruff_args=tuple(cls.parse_tool_args(params.ruff_args)),
            pyright_args=tuple(cls.parse_tool_args(params.pyright_args)),
        )
        run_result = checker.run_projects(
            projects=project_targets,
            gates=gates,
            reports_dir=params.reports_dir_path,
            fail_fast=params.fail_fast,
            ctx=gate_ctx,
        )
        if run_result.failure:
            return r[bool].fail(run_result.error or "check failed")
        failed_projects = [
            project for project in run_result.value if not project.passed
        ]
        if failed_projects:
            failed_names = ", ".join(project.project for project in failed_projects)
            return r[bool].fail(f"quality gates failed for: {failed_names}")
        return r[bool].ok(True)

    @staticmethod
    def _resolve_project_targets(
        params: m.Infra.RunCommand,
    ) -> p.Result[t.SequenceOf[m.Infra.CheckProjectTarget]]:
        """Resolve explicit projects or discover the workspace project set."""
        requested = params.project_names
        if requested:
            return r[t.SequenceOf[m.Infra.CheckProjectTarget]].ok(
                tuple(
                    m.Infra.CheckProjectTarget.from_workspace_name(
                        params.workspace_path, project_name
                    )
                    for project_name in requested
                )
            )
        discovered = u.Infra.resolve_projects(params.workspace_path, ())
        if discovered.failure:
            return r[t.SequenceOf[m.Infra.CheckProjectTarget]].fail(
                discovered.error or "project discovery failed"
            )
        project_targets = tuple(
            m.Infra.CheckProjectTarget(name=project.name, path=project.path)
            for project in discovered.value
        )
        if not project_targets:
            return r[t.SequenceOf[m.Infra.CheckProjectTarget]].fail(
                "no projects discovered"
            )
        return r[t.SequenceOf[m.Infra.CheckProjectTarget]].ok(project_targets)

    def run_project(
        self, project: str, gates: t.StrSequence
    ) -> p.Result[t.SequenceOf[m.Infra.ProjectResult]]:
        """Run selected gates for one project."""
        return self.run_projects([project], list(gates))

    def run_projects(
        self,
        projects: t.StrSequence | t.SequenceOf[m.Infra.CheckProjectTarget],
        gates: t.StrSequence,
        *,
        reports_dir: Path | None = None,
        fail_fast: bool = False,
        ctx: m.Infra.GateContext | None = None,
    ) -> p.Result[t.SequenceOf[m.Infra.ProjectResult]]:
        """Run selected gates for multiple projects."""
        resolved_gates_result = self._registry.resolve(gates)
        if resolved_gates_result.failure:
            return r[t.SequenceOf[m.Infra.ProjectResult]].fail(
                resolved_gates_result.error or "invalid gates"
            )
        resolved_gates = resolved_gates_result.value
        report_base = reports_dir or self._default_reports_dir
        dir_ensure = u.Cli.ensure_dir(report_base)
        if dir_ensure.failure:
            return r[t.SequenceOf[m.Infra.ProjectResult]].fail(
                dir_ensure.error or "failed to create report directory"
            )
        effective_ctx = ctx or m.Infra.GateContext(
            workspace=self._workspace_root, reports_dir=report_base
        )
        targets = self._project_targets(projects)
        invalid = tuple(
            target
            for target in targets
            if not target.path.is_dir()
            or not (target.path / c.Infra.PYPROJECT_FILENAME).is_file()
        )
        if invalid:
            return r[t.SequenceOf[m.Infra.ProjectResult]].fail(
                "check targets require a project directory and pyproject.toml: "
                + ", ".join(target.name for target in invalid)
            )
        outcome = self._run_project_loop(
            targets, resolved_gates, effective_ctx, fail_fast=fail_fast
        )
        return self._write_reports_and_summary(resolved_gates, report_base, outcome)

    def _project_targets(
        self, projects: t.StrSequence | t.SequenceOf[m.Infra.CheckProjectTarget]
    ) -> t.SequenceOf[m.Infra.CheckProjectTarget]:
        """Return typed project targets from public names or internal selections."""
        targets: list[m.Infra.CheckProjectTarget] = []
        for project in projects:
            if isinstance(project, m.Infra.CheckProjectTarget):
                targets.append(project)
                continue
            targets.append(
                m.Infra.CheckProjectTarget.from_workspace_name(
                    self._workspace_root, project
                )
            )
        return tuple(targets)


__all__: list[str] = ["FlextInfraWorkspaceChecker"]
