"""FLEXT infrastructure workspace checker."""

from __future__ import annotations

import argparse
import importlib
import shlex
from collections.abc import MutableSequence, Sequence
from datetime import UTC, datetime
from pathlib import Path
from typing import Protocol, override

from flext_core import r, s
from flext_infra import (
    c,
    m,
    u,
    workspace_check_cli as workspace_check_cli_module,
)
from flext_infra.check._workspace_check_gates import (
    FlextInfraGateRegistry,
    FlextInfraWorkspaceCheckGatesMixin,
)


class WorkspaceLoopOutcome(Protocol):
    """Public structural view of the workspace gate loop outcome."""

    results: tuple[m.Infra.ProjectResult, ...]
    failed: int
    skipped: int
    total_elapsed: float


class FlextInfraWorkspaceChecker(FlextInfraWorkspaceCheckGatesMixin, s[bool]):
    """Run workspace quality gates and generate reports."""

    def __init__(
        self,
        workspace_root: Path | None = None,
        *,
        workspace: Path | None = None,
    ) -> None:
        """Initialize workspace checker services and paths."""
        self._workspace_root = self._resolve_workspace_root(
            workspace_root or workspace,
        )
        self._registry = FlextInfraGateRegistry.default()
        report_dir = u.Infra.get_report_dir(
            self._workspace_root,
            c.Infra.PROJECT,
            c.Infra.Verbs.CHECK,
        )
        try:
            report_dir.mkdir(parents=True, exist_ok=True)
            self._default_reports_dir = report_dir
        except OSError:
            self._default_reports_dir = (
                self._workspace_root
                / c.Infra.Reporting.REPORTS_DIR_NAME
                / c.Infra.Verbs.CHECK
            )

    @staticmethod
    def parse_gate_csv(raw: str) -> list[str]:
        """Parse a comma-separated gate list."""
        return [gate.strip() for gate in raw.split(",") if gate.strip()]

    @staticmethod
    def parse_tool_args(raw: str | None) -> list[str]:
        """Parse extra gate arguments passed as a shell-style string."""
        if raw is None:
            return list[str]()
        return [item for item in shlex.split(raw) if item]

    @staticmethod
    def resolve_gates(gates: Sequence[str]) -> r[list[str]]:
        """Resolve and validate requested gate names."""
        resolved: MutableSequence[str] = []
        for gate in gates:
            name = gate.strip()
            if not name:
                continue
            mapped = c.Infra.PYREFLY if name == c.Infra.TYPE_ALIAS else name
            if mapped not in c.Infra.ALLOWED_GATES:
                return r[list[str]].fail(f"ERROR: unknown gate '{gate}'")
            if mapped not in resolved:
                resolved.append(mapped)
        return r[list[str]].ok(list(resolved))

    @override
    def execute(self) -> r[bool]:
        return r[bool].fail("Use run() or run_projects() directly")

    def format(self, project_dir: Path) -> r[m.Infra.GateResult]:
        """Run format checks for one project."""
        return r[m.Infra.GateResult].ok(
            self._run_gate(c.Infra.FORMAT, project_dir).result,
        )

    def lint(self, project_dir: Path) -> r[m.Infra.GateResult]:
        """Run lint checks for one project."""
        return r[m.Infra.GateResult].ok(
            self._run_gate(c.Infra.LINT, project_dir).result,
        )

    @staticmethod
    def build_parser() -> argparse.ArgumentParser:
        """Build the workspace check CLI parser."""
        return workspace_check_cli_module.FlextInfraWorkspaceCheckerCli.build_parser()

    @staticmethod
    def run_cli(argv: Sequence[str] | None = None) -> int:
        """Run the subcommand-based workspace check CLI."""
        return workspace_check_cli_module.FlextInfraWorkspaceCheckerCli.run_cli(argv)

    @staticmethod
    def main(argv: Sequence[str] | None = None) -> int:
        """Run the legacy workspace check CLI entrypoint."""
        raw_argv = list(argv) if argv is not None else None
        if raw_argv:
            cli_module = importlib.import_module("flext_infra.cli")
            if raw_argv[0] in cli_module.FlextInfraCli.GROUPS:
                return cli_module.main(raw_argv)
        return workspace_check_cli_module.FlextInfraWorkspaceCheckerCli.main(argv)

    def run_project(
        self,
        project: str,
        gates: Sequence[str],
    ) -> r[Sequence[m.Infra.ProjectResult]]:
        """Run selected gates for one project."""
        return self.run_projects([project], list(gates)).map(lambda value: value)

    @staticmethod
    def _write_reports_and_summary(
        resolved_gates: Sequence[str],
        report_base: Path,
        outcome: WorkspaceLoopOutcome,
    ) -> r[Sequence[m.Infra.ProjectResult]]:
        """Write markdown/SARIF reports and print summary to output."""
        results = outcome.results
        timestamp = datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S UTC")
        md_path = report_base / "check-report.md"
        _ = md_path.write_text(
            u.Infra.generate_markdown(results, resolved_gates, timestamp),
            encoding=c.Infra.Encoding.DEFAULT,
        )
        sarif_path = report_base / "check-report.sarif"
        sarif_payload = u.Infra.generate_sarif(results, resolved_gates)
        json_write_result = u.Cli.json_write(sarif_path, sarif_payload)
        if json_write_result.is_failure:
            return r[Sequence[m.Infra.ProjectResult]].fail(
                json_write_result.error or "failed to write sarif report",
            )
        total_errors = sum(project.total_errors for project in results)
        success = len(results) - outcome.failed
        u.Infra.summary(
            m.Infra.SummaryStats(
                verb=c.Infra.Verbs.CHECK,
                total=len(results),
                success=success,
                failed=outcome.failed,
                skipped=outcome.skipped,
                elapsed=outcome.total_elapsed,
            )
        )
        u.Infra.info(f"Reports: {md_path}")
        u.Infra.info(f"         {sarif_path}")
        if total_errors > 0:
            u.Infra.info("Errors by project:")
            for project in sorted(
                results,
                key=lambda item: item.total_errors,
                reverse=True,
            ):
                if project.total_errors == 0:
                    continue
                breakdown = ", ".join(
                    f"{gate}={len(project.gates[gate].issues)}"
                    for gate in resolved_gates
                    if gate in project.gates and project.gates[gate].issues
                )
                u.Infra.error(
                    f"{project.project:30s} {project.total_errors:6d}  ({breakdown})",
                )
        return r[Sequence[m.Infra.ProjectResult]].ok(results)

    def run_projects(
        self,
        projects: Sequence[str],
        gates: Sequence[str],
        *,
        reports_dir: Path | None = None,
        fail_fast: bool = False,
        ctx: m.Infra.GateContext | None = None,
    ) -> r[Sequence[m.Infra.ProjectResult]]:
        """Run selected gates for multiple projects.

        Pass ``ctx`` to supply a pre-built GateContext.
        """
        resolved_gates_result = self.resolve_gates(gates)
        if resolved_gates_result.is_failure:
            return r[Sequence[m.Infra.ProjectResult]].fail(
                resolved_gates_result.error or "invalid gates",
            )
        resolved_gates = resolved_gates_result.value
        report_base = reports_dir or self._default_reports_dir
        report_base.mkdir(parents=True, exist_ok=True)
        effective_ctx = ctx or m.Infra.GateContext(
            workspace=self._workspace_root,
            reports_dir=report_base,
        )
        outcome = self._run_project_loop(
            projects,
            resolved_gates,
            effective_ctx,
            fail_fast=fail_fast,
        )
        return self._write_reports_and_summary(
            resolved_gates,
            report_base,
            outcome,
        )

    def _resolve_workspace_root(self, workspace_root: Path | None) -> Path:
        return u.Infra.resolve_workspace_root_or_cwd(workspace_root)


build_parser = FlextInfraWorkspaceChecker.build_parser
run_cli = FlextInfraWorkspaceChecker.run_cli
main = FlextInfraWorkspaceChecker.main

__all__ = ["FlextInfraWorkspaceChecker", "build_parser", "main", "run_cli"]
