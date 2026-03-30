"""FLEXT infrastructure workspace checker."""

from __future__ import annotations

import argparse
import os
import shlex
import time
from collections.abc import MutableSequence, Sequence
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
    t,
    u,
)


class FlextInfraWorkspaceChecker(s[bool]):
    """Run workspace quality gates and generate reports."""

    def __init__(self, workspace_root: Path | None = None) -> None:
        """Initialize workspace checker services and paths."""
        super().__init__()
        self._workspace_root = self._resolve_workspace_root(workspace_root)
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
    def generate_sarif_report(
        results: Sequence[m.Infra.ProjectResult],
        gates: t.StrSequence,
    ) -> JsonValue:
        """Generate a SARIF payload from gate results."""
        return u.Infra.generate_sarif(results, gates)

    @staticmethod
    def parse_gate_csv(raw: str) -> t.StrSequence:
        """Parse a comma-separated gate list."""
        return [gate.strip() for gate in raw.split(",") if gate.strip()]

    @staticmethod
    def parse_tool_args(raw: str | None) -> t.StrSequence:
        """Parse extra gate arguments passed as a shell-style string."""
        if raw is None:
            return []
        return [item for item in shlex.split(raw) if item]

    @staticmethod
    def resolve_gates(gates: t.StrSequence) -> r[t.StrSequence]:
        """Resolve and validate requested gate names."""
        resolved: MutableSequence[str] = []
        for gate in gates:
            name = gate.strip()
            if not name:
                continue
            mapped = c.Infra.PYREFLY if name == c.Infra.TYPE_ALIAS else name
            if mapped not in c.Infra.ALLOWED_GATES:
                return r[t.StrSequence].fail(f"ERROR: unknown gate '{gate}'")
            if mapped not in resolved:
                resolved.append(mapped)
        return r[t.StrSequence].ok(resolved)

    @override
    def execute(self) -> r[bool]:
        return r[bool].fail("Use run() or run_projects() directly")

    def format(self, project_dir: Path) -> r[m.Infra.GateResult]:
        """Run format checks for one project."""
        return r[m.Infra.GateResult].ok(
            self._run_gate(c.Infra.FORMAT, project_dir).result,
        )

    def generate_markdown_report(
        self,
        results: Sequence[m.Infra.ProjectResult],
        gates: t.StrSequence,
        timestamp: str,
    ) -> str:
        """Generate a markdown summary report for check results."""
        return u.Infra.generate_markdown(results, gates, timestamp)

    def lint(self, project_dir: Path) -> r[m.Infra.GateResult]:
        """Run lint checks for one project."""
        return r[m.Infra.GateResult].ok(
            self._run_gate(c.Infra.LINT, project_dir).result,
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
            include_apply=False,
            subcommand_flags={
                "fix-pyrefly-config": {
                    "include_apply": True,
                    "include_diff": False,
                },
            },
        )
        _ = subs[c.Infra.Verbs.RUN].add_argument(
            "--gates",
            default=c.Infra.DEFAULT_CSV,
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
        _ = subs[c.Infra.Verbs.RUN].add_argument("--fix", action="store_true")
        _ = subs[c.Infra.Verbs.RUN].add_argument("--check-only", action="store_true")
        _ = subs[c.Infra.Verbs.RUN].add_argument("--ruff-args")
        _ = subs[c.Infra.Verbs.RUN].add_argument("--pyright-args")
        _ = subs["fix-pyrefly-config"].add_argument("projects", nargs="*")
        _ = subs["fix-pyrefly-config"].add_argument("--verbose", action="store_true")
        return parser

    @staticmethod
    def run_cli(argv: t.StrSequence | None = None) -> int:
        """Run the subcommand-based workspace check CLI."""
        parser = FlextInfraWorkspaceChecker.build_parser()
        args = u.Infra.parse_subcommand_args(parser, argv)
        cli = u.Infra.resolve(args)
        if args.command == c.Infra.Verbs.RUN:
            env_workspace = os.getenv("FLEXT_WORKSPACE_ROOT")
            checker_workspace = (
                Path(env_workspace).resolve() if env_workspace else cli.workspace
            )
            checker = FlextInfraWorkspaceChecker(workspace_root=checker_workspace)
            gates = FlextInfraWorkspaceChecker.parse_gate_csv(args.gates)
            ruff_args = FlextInfraWorkspaceChecker.parse_tool_args(args.ruff_args)
            pyright_args = FlextInfraWorkspaceChecker.parse_tool_args(
                args.pyright_args,
            )
            reports_dir = Path(args.reports_dir).expanduser()
            if not reports_dir.is_absolute():
                reports_dir = (Path.cwd() / reports_dir).resolve()
            run_result = checker.run_projects(
                projects=args.project,
                gates=gates,
                reports_dir=reports_dir,
                fail_fast=args.fail_fast,
                fix=args.fix,
                check_only=args.check_only,
                ruff_args=ruff_args,
                pyright_args=pyright_args,
            )
            if run_result.is_failure:
                output.error(run_result.error or "check failed")
                return 2
            run_results: Sequence[m.Infra.ProjectResult] = run_result.value
            failed_projects = [project for project in run_results if not project.passed]
            return 1 if failed_projects else 0
        if args.command == "fix-pyrefly-config":
            fixer = FlextInfraConfigFixer()
            fix_result: r[t.StrSequence] = fixer.run(
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
    def main(argv: t.StrSequence | None = None) -> int:
        """Run the legacy workspace check CLI entrypoint."""
        parser = u.Infra.create_parser(
            "flext-infra check-workspace",
            "FLEXT Workspace Check",
            include_apply=False,
        )
        _ = parser.add_argument("projects", nargs="*")
        _ = parser.add_argument("--gates", default=c.Infra.DEFAULT_CSV)
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
        gates: t.StrSequence,
    ) -> r[Sequence[m.Infra.ProjectResult]]:
        """Run selected gates for one project."""
        return self.run_projects([project], list(gates)).map(lambda value: value)

    @staticmethod
    def _write_reports_and_summary(
        results: Sequence[m.Infra.ProjectResult],
        resolved_gates: t.StrSequence,
        report_base: Path,
        *,
        failed: int,
        skipped: int,
        total_elapsed: float,
    ) -> r[Sequence[m.Infra.ProjectResult]]:
        """Write markdown/SARIF reports and print summary to output."""
        timestamp = datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S UTC")
        md_path = report_base / "check-report.md"
        _ = md_path.write_text(
            u.Infra.generate_markdown(results, resolved_gates, timestamp),
            encoding=c.Infra.Encoding.DEFAULT,
        )
        sarif_path = report_base / "check-report.sarif"
        sarif_payload = u.Infra.generate_sarif(results, resolved_gates)
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
                    if gate in project.gates and project.gates[gate].issues
                )
                output.error(
                    f"{project.project:30s} {project.total_errors:6d}  ({breakdown})",
                )
        return r[Sequence[m.Infra.ProjectResult]].ok(results)

    def run_projects(
        self,
        projects: t.StrSequence,
        gates: t.StrSequence,
        *,
        reports_dir: Path | None = None,
        fail_fast: bool = False,
        fix: bool = False,
        check_only: bool = False,
        ruff_args: t.StrSequence | None = None,
        pyright_args: t.StrSequence | None = None,
    ) -> r[Sequence[m.Infra.ProjectResult]]:
        """Run selected gates for multiple projects."""
        resolved_gates_result = self.resolve_gates(gates)
        if resolved_gates_result.is_failure:
            return r[Sequence[m.Infra.ProjectResult]].fail(
                resolved_gates_result.error or "invalid gates",
            )
        resolved_gates: t.StrSequence = resolved_gates_result.value
        report_base = reports_dir or self._default_reports_dir
        report_base.mkdir(parents=True, exist_ok=True)
        ctx = self._gate_ctx(
            report_base,
            apply_fixes=fix,
            check_only=check_only,
            ruff_args=ruff_args,
            pyright_args=pyright_args,
        )
        results: MutableSequence[m.Infra.ProjectResult] = []
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
            project_result = self._check_project_with_ctx(
                project_dir,
                resolved_gates,
                ctx,
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
        return self._write_reports_and_summary(
            results,
            resolved_gates,
            report_base,
            failed=failed,
            skipped=skipped,
            total_elapsed=total_elapsed,
        )

    def _gate_ctx(
        self,
        reports_dir: Path | None = None,
        *,
        apply_fixes: bool = False,
        check_only: bool = False,
        ruff_args: t.StrSequence | None = None,
        pyright_args: t.StrSequence | None = None,
    ) -> m.Infra.GateContext:
        return m.Infra.GateContext(
            workspace_root=self._workspace_root,
            reports_dir=reports_dir or self._default_reports_dir,
            apply_fixes=apply_fixes,
            check_only=check_only,
            ruff_args=tuple(ruff_args or ()),
            pyright_args=tuple(pyright_args or ()),
        )

    def _run_pyrefly(
        self, project_dir: Path, reports_dir: Path | None = None
    ) -> m.Infra.GateExecution:
        return self._run_gate(c.Infra.PYREFLY, project_dir, reports_dir)

    def _run_mypy(
        self, project_dir: Path, reports_dir: Path | None = None
    ) -> m.Infra.GateExecution:
        return self._run_gate(c.Infra.MYPY, project_dir, reports_dir)

    def _run_pyright(
        self, project_dir: Path, reports_dir: Path | None = None
    ) -> m.Infra.GateExecution:
        return self._run_gate(c.Infra.PYRIGHT, project_dir, reports_dir)

    def _run_bandit(
        self, project_dir: Path, reports_dir: Path | None = None
    ) -> m.Infra.GateExecution:
        return self._run_gate(c.Infra.SECURITY, project_dir, reports_dir)

    def _run_markdown(
        self, project_dir: Path, reports_dir: Path | None = None
    ) -> m.Infra.GateExecution:
        return self._run_gate(c.Infra.MARKDOWN, project_dir, reports_dir)

    def _run_go(
        self, project_dir: Path, reports_dir: Path | None = None
    ) -> m.Infra.GateExecution:
        return self._run_gate(c.Infra.GO, project_dir, reports_dir)

    def _run_ruff_format(
        self, project_dir: Path, reports_dir: Path | None = None
    ) -> m.Infra.GateExecution:
        return self._run_gate(c.Infra.FORMAT, project_dir, reports_dir)

    def _run_ruff_lint(
        self, project_dir: Path, reports_dir: Path | None = None
    ) -> m.Infra.GateExecution:
        return self._run_gate(c.Infra.LINT, project_dir, reports_dir)

    def _run_gate(
        self,
        gate_id: str,
        project_dir: Path,
        reports_dir: Path | None = None,
        *,
        ctx: m.Infra.GateContext | None = None,
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
        return gate.check(project_dir, ctx or self._gate_ctx(reports_dir))

    def _check_project_with_ctx(
        self,
        project_dir: Path,
        gates: t.StrSequence,
        ctx: m.Infra.GateContext,
    ) -> m.Infra.ProjectResult:
        """Run gates for one project using a pre-built GateContext."""
        result = m.Infra.ProjectResult(project=project_dir.name)
        for gate in gates:
            gate_instance = self._registry.create(gate, self._workspace_root)
            if gate_instance is None:
                continue
            if ctx.apply_fixes and (not ctx.check_only) and gate_instance.can_fix:
                fix_execution = gate_instance.fix(project_dir, ctx)
                if not fix_execution.result.passed:
                    result.gates[gate] = fix_execution
                    output.gate_result(
                        gate,
                        len(fix_execution.issues),
                        fix_execution.result.passed,
                        fix_execution.result.duration,
                    )
                    continue
            execution = gate_instance.check(project_dir, ctx)
            result.gates[gate] = execution
            output.gate_result(
                gate,
                len(execution.issues),
                execution.result.passed,
                execution.result.duration,
            )
        return result

    def _check_project(
        self,
        project_dir: Path,
        gates: t.StrSequence,
        reports_dir: Path,
        *,
        fix: bool = False,
        check_only: bool = False,
        ruff_args: t.StrSequence | None = None,
        pyright_args: t.StrSequence | None = None,
    ) -> m.Infra.ProjectResult:
        ctx = self._gate_ctx(
            reports_dir,
            apply_fixes=fix,
            check_only=check_only,
            ruff_args=ruff_args,
            pyright_args=pyright_args,
        )
        return self._check_project_with_ctx(project_dir, gates, ctx)

    def _resolve_workspace_root(self, workspace_root: Path | None) -> Path:
        if workspace_root is not None:
            return workspace_root.resolve()
        result = u.Infra.workspace_root()
        return result.value if result.is_success else Path.cwd().resolve()


build_parser = FlextInfraWorkspaceChecker.build_parser
run_cli = FlextInfraWorkspaceChecker.run_cli
main = FlextInfraWorkspaceChecker.main


__all__ = ["FlextInfraWorkspaceChecker", "build_parser", "main", "run_cli"]
