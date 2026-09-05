"""Gate measurement and ast-grep batch execution for the mod safety circuit."""

from __future__ import annotations


from collections.abc import Mapping
from pathlib import Path
from flext_infra import c, m, p, r, t, u
from flext_infra.gates.pyrefly import FlextInfraPyreflyGate
from flext_infra.gates.ruff_lint import FlextInfraRuffLintGate


class FlextInfraModGateEngine:
    """Measure ruff/pyrefly counts and execute the ast-grep rule batch."""

    @staticmethod
    def circuit_broken(
        baseline: m.Infra.ModGateSnapshot, final: m.Infra.ModGateSnapshot
    ) -> bool:
        """Return True when either gate error count increased after the apply."""
        return (
            final.ruff_errors > baseline.ruff_errors
            or final.pyrefly_errors > baseline.pyrefly_errors
        )

    @staticmethod
    def _run_tool(root: Path, command: t.StrSequence) -> p.Result[p.Cli.CommandOutput]:
        """Run one circuit tool and tolerate its findings exit codes."""
        run = u.Cli.run_raw(command, cwd=root, timeout=c.Infra.TIMEOUT_SHORT)
        if run.failure:
            return r[p.Cli.CommandOutput].fail(
                run.error or f"tool execution failed: {command[0]}"
            )
        output = run.value
        if output.exit_code not in {0, 1}:
            detail = (output.stderr or output.stdout).strip()
            return r[p.Cli.CommandOutput].fail(
                detail or f"{command[0]} exited with code {output.exit_code}"
            )
        return r[p.Cli.CommandOutput].ok(output)

    @staticmethod
    def _count_json_lines(stdout: str) -> int:
        """Count JSON-per-line findings (ast-grep ``--json=stream`` output)."""
        count = 0
        for raw_line in stdout.splitlines():
            line = raw_line.strip()
            if line and u.Cli.json_parse(line).success:
                count += 1
        return count

    @staticmethod
    def _actionable_findings(
        stdout: str, fixable_ids: frozenset[str]
    ) -> m.Infra.ModScanReport:
        nodes = 0
        files: set[Path] = set()
        for raw_line in stdout.splitlines():
            parsed = u.Cli.json_parse(raw_line.strip())
            if parsed.failure or not isinstance(parsed.value, Mapping):
                continue
            finding = parsed.value
            if finding.get("ruleId") not in fixable_ids:
                continue
            text = finding.get("text")
            replacement = finding.get("replacement")
            file = finding.get("file")
            if not isinstance(text, str) or not isinstance(replacement, str):
                continue
            if text == replacement or not isinstance(file, str):
                continue
            nodes += 1
            files.add(Path(file))
        return m.Infra.ModScanReport(nodes=nodes, files=frozenset(files))

    @classmethod
    def _count_tool_errors(cls, stdout: str) -> int:
        """Count error items from array, object-with-errors, or JSONL output."""
        parsed = u.Cli.json_parse(stdout.strip()) if stdout.strip() else None
        if parsed is not None and parsed.success:
            value = parsed.value
            if isinstance(value, list):
                return len(value)
            if isinstance(value, Mapping):
                errors = value.get("errors")
                return len(errors) if isinstance(errors, list) else 0
        return cls._count_json_lines(stdout)

    @classmethod
    def measure(cls, root: Path) -> p.Result[m.Infra.ModGateSnapshot]:
        """Capture error counts through the canonical Ruff and Pyrefly gates."""
        context = m.Infra.GateContext(
            workspace=root,
            reports_dir=root / c.Infra.REPORTS_DIR_NAME,
            gate_mode="error",
        )
        ruff_execution = FlextInfraRuffLintGate(root).check(root, context)
        pyrefly_execution = FlextInfraPyreflyGate(root).check(root, context)
        raw_diagnostics = tuple(
            diagnostic
            for execution in (ruff_execution, pyrefly_execution)
            if not execution.result.passed
            for diagnostic in (
                *execution.result.errors,
                *(issue.formatted for issue in execution.issues),
                execution.raw_output.strip(),
            )
            if diagnostic
        )
        diagnostics: list[str] = []
        for diagnostic in raw_diagnostics:
            if diagnostic not in diagnostics:
                diagnostics.append(diagnostic)
        return r[m.Infra.ModGateSnapshot].ok(
            m.Infra.ModGateSnapshot(
                ruff_errors=(
                    ruff_execution.error_count
                    if ruff_execution.result.passed
                    else max(1, ruff_execution.error_count)
                ),
                pyrefly_errors=(
                    pyrefly_execution.error_count
                    if pyrefly_execution.result.passed
                    else max(1, pyrefly_execution.error_count)
                ),
                ruff_files=frozenset(
                    path if path.is_absolute() else root / path
                    for issue in ruff_execution.issues
                    if (path := Path(issue.file)).name != "<ruff-output>"
                ),
                diagnostics=tuple(diagnostics),
            )
        )

    @staticmethod
    def normalize_imports(root: Path, file_paths: frozenset[Path]) -> p.Result[bool]:
        """Normalize AST-rewritten imports through the public Rope utility."""
        if not file_paths:
            return r[bool].ok(False)
        with u.Infra.open_project(root) as rope_project:
            return u.Infra.normalize_imports(
                rope_project,
                file_paths=tuple(sorted(file_paths)),
                preserve_canonical_aliases=True,
            )

    @staticmethod
    def _count_fixable_findings(stdout: str, fixable_ids: frozenset[str]) -> int:
        findings = 0
        for raw_line in stdout.splitlines():
            parsed = u.Cli.json_parse(raw_line.strip())
            if parsed.failure or not isinstance(parsed.value, Mapping):
                continue
            if parsed.value.get("ruleId") in fixable_ids:
                findings += 1
        return findings

    @classmethod
    def scan(
        cls, root: Path, plan: m.Infra.CodemodRulePlan, *, fix: bool
    ) -> p.Result[m.Infra.ModScanReport]:
        """Scan or apply actionable rewrite documents."""
        nodes = 0
        files: set[Path] = set()
        for ruleset in plan.rulesets:
            fixable = frozenset(ruleset.fixable_rule_ids)
            if not fixable:
                continue
            rule_filter = u.Infra.codemod_rule_filter(ruleset.fixable_rule_ids)
            command: list[str] = [
                c.Infra.SG,
                c.Infra.SCAN,
                "--config",
                str(ruleset.config),
                "--filter",
                rule_filter,
            ]
            command.extend(("--json=stream", "."))
            run = cls._run_tool(root, tuple(command))
            if run.failure:
                return r[m.Infra.ModScanReport].from_failure(run)
            report = cls._actionable_findings(run.value.stdout or "", fixable)
            nodes += report.nodes
            files.update(report.files)
            if fix and report.nodes:
                apply_run = cls._run_tool(
                    root,
                    (
                        c.Infra.SG,
                        c.Infra.SCAN,
                        "--config",
                        str(ruleset.config),
                        "--filter",
                        rule_filter,
                        "--update-all",
                        ".",
                    ),
                )
                if apply_run.failure:
                    return r[m.Infra.ModScanReport].from_failure(apply_run)
        return r[m.Infra.ModScanReport].ok(
            m.Infra.ModScanReport(nodes=nodes, files=frozenset(files))
        )


__all__: list[str] = ["FlextInfraModGateEngine"]
