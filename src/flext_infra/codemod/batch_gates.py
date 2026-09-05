"""Gate measurement and ast-grep batch execution for the mod safety circuit."""

from __future__ import annotations

import sys
from collections.abc import Mapping
from pathlib import Path
from typing import Final

from flext_infra import c, m, p, r, t, u

_TOOL_TIMEOUT_SECONDS: Final[int] = 900


class FlextInfraModGateEngine:
    """Measure ruff/pyrefly counts and execute the ast-grep rule batch."""

    @staticmethod
    def fixed_point_broken(final: m.Infra.ModGateSnapshot) -> bool:
        """Return whether any required gate finding remains after the apply."""
        return bool(final.ruff_errors or final.pyrefly_errors)

    @staticmethod
    def _run_tool(root: Path, command: t.StrSequence) -> p.Result[p.Cli.CommandOutput]:
        """Run one circuit tool and tolerate its findings exit codes."""
        run = u.Cli.run_raw(
            command,
            cwd=root,
            timeout=_TOOL_TIMEOUT_SECONDS,
            remove_env_keys=(c.Infra.ORCHESTRATOR_ENV_PYTHONPATH,),
        )
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
    def _count_json_lines(stdout: str) -> p.Result[int]:
        """Count JSONL findings, rejecting the first malformed record."""
        count = 0
        for raw_line in stdout.splitlines():
            line = raw_line.strip()
            if not line:
                continue
            parsed = u.Cli.json_parse(line)
            if parsed.failure:
                return r[int].fail(parsed.error or "invalid JSONL tool output")
            count += 1
        return r[int].ok(count)

    @staticmethod
    def _rule_ids(rule: Path) -> p.Result[tuple[frozenset[str], frozenset[str]]]:
        """Return every declared rule ID and the subset owning a rewrite."""
        documents = rule.read_text(encoding="utf-8").split("\n---")
        rule_ids: set[str] = set()
        fixable_ids: set[str] = set()
        for raw_document in documents:
            if not any(
                line.strip() and not line.lstrip().startswith("#")
                for line in raw_document.splitlines()
            ):
                continue
            parsed = u.Cli.yaml_parse(raw_document)
            if parsed.failure:
                return r[tuple[frozenset[str], frozenset[str]]].fail(
                    parsed.error or f"invalid ast-grep rule document in {rule}"
                )
            rule_id = parsed.value.get("id")
            if not isinstance(rule_id, str) or not rule_id:
                return r[tuple[frozenset[str], frozenset[str]]].fail(
                    f"ast-grep rule document missing required id: {rule}"
                )
            rule_ids.add(rule_id)
            if "fix" in parsed.value:
                fixable_ids.add(rule_id)
        return r[tuple[frozenset[str], frozenset[str]]].ok((
            frozenset(rule_ids),
            frozenset(fixable_ids),
        ))

    @classmethod
    def prepare_rules(cls, rules: t.SequenceOf[Path]) -> p.Result[m.Infra.ModRuleBatch]:
        """Precompile ast-grep rule documents once per batch execution."""
        all_ids: set[str] = set()
        fixable_ids: set[str] = set()
        rule_documents: list[str] = []
        for rule in rules:
            rule_ids = cls._rule_ids(rule)
            if rule_ids.failure:
                return r[m.Infra.ModRuleBatch].from_failure(rule_ids)
            rule_all_ids, rule_fixable_ids = rule_ids.value
            all_ids.update(rule_all_ids)
            fixable_ids.update(rule_fixable_ids)
            rule_documents.append(cls._inline_rule_text(rule))
        if not rule_documents:
            return r[m.Infra.ModRuleBatch].fail("no ast-grep rules provided")
        return r[m.Infra.ModRuleBatch].ok(
            m.Infra.ModRuleBatch(
                inline_rules="\n---\n".join(rule_documents),
                rule_count=len(rule_documents),
                all_ids=frozenset(all_ids),
                fixable_ids=frozenset(fixable_ids),
            )
        )

    @staticmethod
    def _inline_rule_text(rule: Path) -> str:
        """Return a parseable inline-rule document stream for ast-grep."""
        text = rule.read_text(encoding="utf-8").strip()
        if "\n---\n" not in text:
            return text
        lines = text.splitlines()
        for index, line in enumerate(lines):
            if line.strip() == "---":
                return "\n".join(lines[index + 1 :]).strip()
        return text

    @staticmethod
    def _findings(stdout: str, accepted_ids: frozenset[str]) -> m.Infra.ModScanReport:
        """Return every semantic finding whose rule ID is in ``accepted_ids``."""
        nodes = 0
        files: set[Path] = set()
        findings: list[str] = []
        for raw_line in stdout.splitlines():
            parsed = u.Cli.json_parse(raw_line.strip())
            if parsed.failure or not isinstance(parsed.value, Mapping):
                continue
            finding = parsed.value
            if finding.get("ruleId") not in accepted_ids:
                continue
            text = finding.get("text")
            replacement = finding.get("replacement")
            file = finding.get("file")
            if not isinstance(text, str) or not isinstance(file, str):
                continue
            if isinstance(replacement, str) and text == replacement:
                continue
            nodes += 1
            files.add(Path(file))
            rule_id = finding.get("ruleId")
            range_value = finding.get("range")
            start = (
                range_value.get("start") if isinstance(range_value, Mapping) else None
            )
            line = start.get("line") if isinstance(start, Mapping) else None
            column = start.get("column") if isinstance(start, Mapping) else None
            location = (
                f"{line + 1}:{column + 1}"
                if isinstance(line, int) and isinstance(column, int)
                else "?:?"
            )
            findings.append(f"{rule_id}:{file}:{location}")
        return m.Infra.ModScanReport(
            nodes=nodes, files=frozenset(files), findings=tuple(findings)
        )

    @classmethod
    def _count_tool_errors(cls, output: p.Cli.CommandOutput) -> p.Result[int]:
        """Count exact tool findings and reject malformed or empty failures."""
        stdout = output.stdout.strip()
        if not stdout:
            if output.exit_code:
                return r[int].fail(
                    output.stderr.strip()
                    or f"tool exited with code {output.exit_code} without diagnostics"
                )
            return r[int].ok(0)
        parsed = u.Cli.json_parse(stdout)
        if parsed.success:
            value = parsed.value
            if isinstance(value, list):
                return r[int].ok(len(value))
            if isinstance(value, Mapping):
                errors = value.get("errors")
                if isinstance(errors, list):
                    return r[int].ok(len(errors))
                return r[int].fail("tool JSON object is missing an errors array")
        return cls._count_json_lines(stdout)

    @classmethod
    def measure(cls, root: Path) -> p.Result[m.Infra.ModGateSnapshot]:
        """Capture the ruff + pyrefly error counts for one project root."""
        check_targets = tuple(u.Infra.discover_python_targets(root))
        if not check_targets:
            return r[m.Infra.ModGateSnapshot].fail(
                f"mod gate measurement found no Python targets: {root}"
            )
        ruff_run = cls._run_tool(
            root,
            (
                c.Infra.RUFF,
                c.Infra.VERB_CHECK,
                *check_targets,
                "--no-fix",
                "--output-format",
                c.Infra.OUTPUT_JSON,
                "--quiet",
            ),
        )
        if ruff_run.failure:
            return r[m.Infra.ModGateSnapshot].from_failure(ruff_run)
        pyrefly_run = cls._run_tool(
            root,
            (
                c.Infra.PYREFLY,
                c.Infra.CHECK,
                *u.Infra.pyrefly_target_args(root, check_targets),
                "--config",
                c.Infra.PYPROJECT_FILENAME,
                "--python-interpreter-path",
                sys.executable,
                "--output-format",
                c.Infra.OUTPUT_JSON,
                "--summary=none",
            ),
        )
        if pyrefly_run.failure:
            return r[m.Infra.ModGateSnapshot].from_failure(pyrefly_run)
        ruff_errors = cls._count_tool_errors(ruff_run.value)
        if ruff_errors.failure:
            return r[m.Infra.ModGateSnapshot].from_failure(ruff_errors)
        pyrefly_errors = cls._count_tool_errors(pyrefly_run.value)
        if pyrefly_errors.failure:
            return r[m.Infra.ModGateSnapshot].from_failure(pyrefly_errors)
        return r[m.Infra.ModGateSnapshot].ok(
            m.Infra.ModGateSnapshot(
                ruff_errors=ruff_errors.value,
                pyrefly_errors=pyrefly_errors.value,
                ruff_output=ruff_run.value.stdout,
                pyrefly_output=pyrefly_run.value.stdout,
            )
        )

    @classmethod
    def scan(
        cls, root: Path, rules: t.SequenceOf[Path], *, fix: bool
    ) -> p.Result[m.Infra.ModScanReport]:
        """Scan or apply actionable rewrite documents."""
        prepared = cls.prepare_rules(rules)
        if prepared.failure:
            return r[m.Infra.ModScanReport].from_failure(prepared)
        return cls.scan_prepared(root, prepared.value, fix=fix)

    @classmethod
    def scan_prepared(
        cls, root: Path, prepared: m.Infra.ModRuleBatch, *, fix: bool
    ) -> p.Result[m.Infra.ModScanReport]:
        """Scan or apply a precompiled ast-grep rule batch."""
        mode = "apply" if fix else "check"
        accepted_ids = prepared.fixable_ids if fix else prepared.all_ids
        u.Cli.info(
            f"mod: phase=ast-grep mode={mode} rules={prepared.rule_count} "
            f"accepted_ids={len(accepted_ids)}"
        )
        run = cls._run_tool(
            root,
            (
                c.Infra.SG,
                c.Infra.SCAN,
                "--inline-rules",
                prepared.inline_rules,
                "--json=stream",
                ".",
            ),
        )
        if run.failure:
            return r[m.Infra.ModScanReport].from_failure(run)
        report = cls._findings(run.value.stdout, accepted_ids)
        u.Cli.info(
            f"mod: phase=ast-grep-result mode={mode} rules={prepared.rule_count} "
            f"findings={report.nodes} files={len(report.files)}"
        )
        if fix and report.nodes:
            apply_run = cls._run_tool(
                root,
                (
                    c.Infra.SG,
                    c.Infra.SCAN,
                    "--inline-rules",
                    prepared.inline_rules,
                    "--update-all",
                    ".",
                ),
            )
            if apply_run.failure:
                return r[m.Infra.ModScanReport].from_failure(apply_run)
        return r[m.Infra.ModScanReport].ok(report)


__all__: list[str] = ["FlextInfraModGateEngine"]
