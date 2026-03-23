"""FLEXT infrastructure workspace checker."""

from __future__ import annotations

import argparse
import time
from collections.abc import Sequence
from datetime import UTC, datetime
from pathlib import Path
from typing import override

from flext_core import r, s
from pydantic import JsonValue

from flext_infra import (
    FlextInfraConfigFixer,
    FlextInfraGateRegistry,
    c,
    m,
    output,
    u,
)


class FlextInfraWorkspaceChecker(s[bool]):
    """Run workspace quality gates and generate reports."""

    def __init__(self, workspace_root: Path | None = None) -> None:
        """Initialize workspace checker services and paths."""
        super().__init__(
            config_type=None,
            config_overrides=None,
            initial_context=None,
            subproject=None,
            services=None,
            factories=None,
            resources=None,
            container_overrides=None,
            wire_modules=None,
            wire_packages=None,
            wire_classes=None,
        )
        self._workspace_root = self._resolve_workspace_root(workspace_root)
        self._registry = FlextInfraGateRegistry.default()
        report_dir = u.Infra.get_report_dir(
            self._workspace_root,
            c.Infra.Toml.PROJECT,
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
    def generate_sarif_report(
        results: Sequence[m.Infra.ProjectResult],
        gates: Sequence[str],
    ) -> JsonValue:
        """Generate a SARIF payload from gate results."""
        return u.Infra.generate_sarif(results, gates)

    @staticmethod
    def parse_gate_csv(raw: str) -> Sequence[str]:
        """Parse a comma-separated gate list."""
        return [gate.strip() for gate in raw.split(",") if gate.strip()]

    @staticmethod
    def resolve_gates(gates: Sequence[str]) -> r[Sequence[str]]:
        """Resolve and validate requested gate names."""
        resolved: Sequence[str] = []
        for gate in gates:
            name = gate.strip()
            if not name:
                continue
            mapped = c.Infra.Gates.PYREFLY if name == c.Infra.Gates.TYPE_ALIAS else name
            if mapped not in c.Infra.ALLOWED_GATES:
                return r[Sequence[str]].fail(f"ERROR: unknown gate '{gate}'")
            if mapped not in resolved:
                resolved.append(mapped)
        return r[Sequence[str]].ok(resolved)

    @override
    def execute(self) -> r[bool]:
        return r[bool].fail("Use run() or run_projects() directly")

    def format(self, project_dir: Path) -> r[m.Infra.GateResult]:
        """Run format checks for one project."""
        return r[m.Infra.GateResult].ok(
            self._run_gate(c.Infra.Gates.FORMAT, project_dir).result,
        )

    def generate_markdown_report(
        self,
        results: Sequence[m.Infra.ProjectResult],
        gates: Sequence[str],
        timestamp: str,
    ) -> str:
        """Generate a markdown summary report for check results."""
        return u.Infra.generate_markdown(results, gates, timestamp)

    def lint(self, project_dir: Path) -> r[m.Infra.GateResult]:
        """Run lint checks for one project."""
        return r[m.Infra.GateResult].ok(
            self._run_gate(c.Infra.Gates.LINT, project_dir).result,
        )

    @staticmethod
    def build_parser() -> argparse.ArgumentParser:
        """Build the workspace check CLI parser."""
        parser, subs = u.Infra.create_subcommand_parser(
            "flext-infra check",
            "FLEXT check utilities",
            subcommands={
                c.Infra.Verbs.RUN: "Run quality gates",
                "fix-pyrefly-config": "Repair [tool.pyrefly] blocks",
            },
            include_apply=True,
        )
        _ = subs[c.Infra.Verbs.RUN].add_argument(
            "--gates",
            default=c.Infra.Gates.DEFAULT_CSV,
        )
        _ = subs[c.Infra.Verbs.RUN].add_argument(
            "--project",
            action="append",
            required=True,
        )
        _ = subs[c.Infra.Verbs.RUN].add_argument(
            "--reports-dir",
            default=f"{c.Infra.Reporting.REPORTS_DIR_NAME}/check",
        )
        _ = subs[c.Infra.Verbs.RUN].add_argument("--fail-fast", action="store_true")
        _ = subs["fix-pyrefly-config"].add_argument("projects", nargs="*")
        _ = subs["fix-pyrefly-config"].add_argument("--verbose", action="store_true")
        return parser

    @staticmethod
    def run_cli(argv: Sequence[str] | None = None) -> int:
        """Run the subcommand-based workspace check CLI."""
        parser = FlextInfraWorkspaceChecker.build_parser()
        args = parser.parse_args(argv)
        cli = u.Infra.resolve(args)
        if args.command == c.Infra.Verbs.RUN:
            checker = FlextInfraWorkspaceChecker(workspace_root=cli.workspace)
            gates = FlextInfraWorkspaceChecker.parse_gate_csv(args.gates)
            reports_dir = Path(args.reports_dir).expanduser()
            if not reports_dir.is_absolute():
                reports_dir = (Path.cwd() / reports_dir).resolve()
            run_result = checker.run_projects(
                projects=args.project,
                gates=gates,
                reports_dir=reports_dir,
                fail_fast=args.fail_fast,
            )
            if run_result.is_failure:
                output.error(run_result.error or "check failed")
                return 2
            run_results: Sequence[m.Infra.ProjectResult] = run_result.value
            failed_projects = [project for project in run_results if not project.passed]
            return 1 if failed_projects else 0
        if args.command == "fix-pyrefly-config":
            fixer = FlextInfraConfigFixer()
            fix_result: r[Sequence[str]] = fixer.run(
                projects=args.projects,
                dry_run=args.dry_run,
                verbose=args.verbose,
            )
            if fix_result.is_failure:
                output.error(fix_result.error or "pyrefly config fix failed")
                return 1
            return 0
        parser.print_help()
        return 1

    @staticmethod
    def main(argv: Sequence[str] | None = None) -> int:
        """Run the legacy workspace check CLI entrypoint."""
        parser = u.Infra.create_parser(
            "flext-infra check-workspace",
            "FLEXT Workspace Check",
            include_apply=False,
        )
        _ = parser.add_argument("projects", nargs="*")
        _ = parser.add_argument("--gates", default=c.Infra.Gates.DEFAULT_CSV)
        _ = parser.add_argument(
            "--reports-dir",
            default=f"{c.Infra.Reporting.REPORTS_DIR_NAME}/check",
        )
        _ = parser.add_argument("--fail-fast", action="store_true")
        args = parser.parse_args(argv)
        if not args.projects:
            output.error("no projects specified")
            return 1
        checker = FlextInfraWorkspaceChecker()
        gates = FlextInfraWorkspaceChecker.parse_gate_csv(args.gates)
        reports_dir = Path(args.reports_dir).expanduser()
        if not reports_dir.is_absolute():
            reports_dir = (Path.cwd() / reports_dir).resolve()
        result = checker.run_projects(
            projects=args.projects,
            gates=gates,
            reports_dir=reports_dir,
            fail_fast=args.fail_fast,
        )
        if result.is_failure:
            output.error(result.error or "workspace check failed")
            return 2
        projects = result.value
        failed_projects = [project for project in projects if not project.passed]
        return 1 if failed_projects else 0

    def run(
        self,
        project: str,
        gates: Sequence[str],
    ) -> r[Sequence[m.Infra.ProjectResult]]:
        """Run selected gates for one project."""
        return self.run_projects([project], list(gates)).map(lambda value: value)

    def run_projects(
        self,
        projects: Sequence[str],
        gates: Sequence[str],
        *,
        reports_dir: Path | None = None,
        fail_fast: bool = False,
    ) -> r[Sequence[m.Infra.ProjectResult]]:
        """Run selected gates for multiple projects."""
        resolved_gates_result = self.resolve_gates(gates)
        if resolved_gates_result.is_failure:
            return r[Sequence[m.Infra.ProjectResult]].fail(
                resolved_gates_result.error or "invalid gates",
            )
        resolved_gates: Sequence[str] = resolved_gates_result.value
        report_base = reports_dir or self._default_reports_dir
        report_base.mkdir(parents=True, exist_ok=True)
        results: Sequence[m.Infra.ProjectResult] = []
        total = len(projects)
        failed = 0
        skipped = 0
        loop_start = time.monotonic()
        for index, project_name in enumerate(projects, 1):
            project_dir = self._workspace_root / project_name
            pyproject_path = project_dir / c.Infra.Files.PYPROJECT_FILENAME
            if not project_dir.is_dir() or not pyproject_path.exists():
                output.progress(index, total, project_name, c.Infra.Severity.SKIP)
                skipped += 1
                continue
            output.progress(index, total, project_name, c.Infra.Verbs.CHECK)
            start = time.monotonic()
            project_result = self._check_project(
                project_dir,
                resolved_gates,
                report_base,
            )
            elapsed = time.monotonic() - start
            results.append(project_result)
            if project_result.passed:
                output.status(c.Infra.Verbs.CHECK, project_name, True, elapsed)
            else:
                output.status(c.Infra.Verbs.CHECK, project_name, False, elapsed)
                failed += 1
                if fail_fast:
                    break
        total_elapsed = time.monotonic() - loop_start
        timestamp = datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S UTC")
        md_path = report_base / "check-report.md"
        _ = md_path.write_text(
            self.generate_markdown_report(results, resolved_gates, timestamp),
            encoding=c.Infra.Encoding.DEFAULT,
        )
        sarif_path = report_base / "check-report.sarif"
        sarif_payload = self.generate_sarif_report(results, resolved_gates)
        json_write_result = u.Infra.write_json(sarif_path, sarif_payload)
        if json_write_result.is_failure:
            return r[Sequence[m.Infra.ProjectResult]].fail(
                json_write_result.error or "failed to write sarif report",
            )
        total_errors = sum(project.total_errors for project in results)
        success = len(results) - failed
        output.summary(
            c.Infra.Verbs.CHECK,
            len(results),
            success,
            failed,
            skipped,
            total_elapsed,
        )
        output.info(f"Reports: {md_path}")
        output.info(f"         {sarif_path}")
        if total_errors > 0:
            output.info("Errors by project:")
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
                    if gate in project.gates and len(project.gates[gate].issues) > 0
                )
                output.error(
                    f"{project.project:30s} {project.total_errors:6d}  ({breakdown})",
                )
        return r[Sequence[m.Infra.ProjectResult]].ok(results)

    def _gate_ctx(self, reports_dir: Path | None = None) -> m.Infra.GateContext:
        return m.Infra.GateContext(
            workspace_root=self._workspace_root,
            reports_dir=reports_dir or self._default_reports_dir,
        )

    def _run_pyrefly(
        self,
        project_dir: Path,
        reports_dir: Path | None = None,
    ) -> m.Infra.GateExecution:
        return self._run_gate(c.Infra.Gates.PYREFLY, project_dir, reports_dir)

    def _run_mypy(
        self,
        project_dir: Path,
        reports_dir: Path | None = None,
    ) -> m.Infra.GateExecution:
        return self._run_gate(c.Infra.Gates.MYPY, project_dir, reports_dir)

    def _run_pyright(
        self,
        project_dir: Path,
        reports_dir: Path | None = None,
    ) -> m.Infra.GateExecution:
        return self._run_gate(c.Infra.Gates.PYRIGHT, project_dir, reports_dir)

    def _run_bandit(
        self,
        project_dir: Path,
        reports_dir: Path | None = None,
    ) -> m.Infra.GateExecution:
        return self._run_gate(c.Infra.Gates.SECURITY, project_dir, reports_dir)

    def _run_markdown(
        self,
        project_dir: Path,
        reports_dir: Path | None = None,
    ) -> m.Infra.GateExecution:
        return self._run_gate(c.Infra.Gates.MARKDOWN, project_dir, reports_dir)

    def _run_go(
        self,
        project_dir: Path,
        reports_dir: Path | None = None,
    ) -> m.Infra.GateExecution:
        return self._run_gate(c.Infra.Gates.GO, project_dir, reports_dir)

    def _run_ruff_format(
        self,
        project_dir: Path,
        reports_dir: Path | None = None,
    ) -> m.Infra.GateExecution:
        return self._run_gate(c.Infra.Gates.FORMAT, project_dir, reports_dir)

    def _run_ruff_lint(
        self,
        project_dir: Path,
        reports_dir: Path | None = None,
    ) -> m.Infra.GateExecution:
        return self._run_gate(c.Infra.Gates.LINT, project_dir, reports_dir)

    def _run_gate(
        self,
        gate_id: str,
        project_dir: Path,
        reports_dir: Path | None = None,
    ) -> m.Infra.GateExecution:
        gate = self._registry.create(gate_id, self._workspace_root)
        if gate is None:
            return m.Infra.GateExecution(
                result=m.Infra.GateResult(
                    gate=gate_id,
                    project=project_dir.name,
                    passed=False,
                    errors=[f"{gate_id} gate not registered"],
                    duration=0.0,
                ),
                issues=[],
                raw_output=f"{gate_id} gate not registered",
            )
        return gate.check(project_dir, self._gate_ctx(reports_dir))

    def _check_project(
        self,
        project_dir: Path,
        gates: Sequence[str],
        reports_dir: Path,
    ) -> m.Infra.ProjectResult:
        result = m.Infra.ProjectResult(project=project_dir.name)
        ctx = self._gate_ctx(reports_dir)
        for gate in gates:
            gate_instance = self._registry.create(gate, self._workspace_root)
            if gate_instance is not None:
                execution = gate_instance.check(project_dir, ctx)
            else:
                continue
            result.gates[gate] = execution
            output.gate_result(
                gate,
                len(execution.issues),
                execution.result.passed,
                execution.result.duration,
            )
        return result

    def _resolve_workspace_root(self, workspace_root: Path | None) -> Path:
        if workspace_root is not None:
            return workspace_root.resolve()
        result = u.Infra.workspace_root()
        return result.value if result.is_success else Path.cwd().resolve()


build_parser = FlextInfraWorkspaceChecker.build_parser
run_cli = FlextInfraWorkspaceChecker.run_cli
main = FlextInfraWorkspaceChecker.main


__all__ = ["FlextInfraWorkspaceChecker", "build_parser", "main", "run_cli"]
