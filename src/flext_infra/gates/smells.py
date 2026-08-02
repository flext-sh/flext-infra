"""qlty code-smell quality gate — smell findings as FLEXT architecture violations.

Every qlty finding is reported per project and emitted as a
``SmellViolation`` warning. The typed Make gate row owns advisory versus strict
finding posture; scanner and payload failures always fail closed.
"""

from __future__ import annotations

import time
import warnings
from pathlib import Path
from typing import TYPE_CHECKING, ClassVar, override

from flext_core import e as core_e
from flext_infra import c, m, r, t, u
from flext_infra.gates.base_gate import FlextInfraGate

from flext_infra.transformers.smells.base import smell_fixer_for, smell_tag_for_code

if TYPE_CHECKING:
    from flext_infra import p


class FlextInfraSmellsGate(FlextInfraGate):
    """Report qlty smells per project from one process-cached workspace scan.

    A single ``qlty smells --all`` scan covers the whole workspace so
    cross-project duplication clusters stay visible; per-project results are
    filtered by SARIF URI prefix. The scan output is cached per workspace
    root for the lifetime of the process (one scan per ``check run``).
    """

    gate_id: ClassVar[str] = "smells"
    gate_name: ClassVar[str] = "Code Smells"
    can_fix: ClassVar[bool] = True
    tool_name: ClassVar[str] = c.Infra.SARIF_TOOL_INFO["smells"][0]
    tool_url: ClassVar[str] = c.Infra.SARIF_TOOL_INFO["smells"][1]

    # mro-pulj: process results stay structural outside the Pydantic boundary.
    _scan_cache: ClassVar[dict[tuple[str, tuple[str, ...]], p.Cli.CommandOutput]] = {}

    @override
    def fix(self, project_dir: Path, ctx: m.Infra.GateContext) -> m.Infra.GateExecution:
        """Apply AST-based fixers for auto-fixable smell findings.

        Runs the same scan as ``check()``, then attempts a registered fixer
        for every issue whose code has ``auto=true`` in flext-core metadata.
        Only rewrites files when a fixer actually changes the source.
        """
        if ctx.check_only or not ctx.apply_fixes:
            return self._check_only_fix_result(project_dir)
        started = time.monotonic()
        scan = self._scan(project_dir, ctx)
        issues, scan_valid = self._scan_issues(scan, project_dir, ctx)
        auto_issues = (
            [issue for issue in issues if self._is_auto_fixable(issue)]
            if scan_valid
            else []
        )
        changes: list[str] = []
        for issue in auto_issues:
            tag = smell_tag_for_code(issue.code)
            fixer = smell_fixer_for(tag) if tag is not None else None
            if fixer is None:
                continue
            fixed, fix_changes = fixer.fix(project_dir, issue)
            if fixed:
                changes.extend(fix_changes)
        for issue in issues:
            warnings.warn(issue.formatted, core_e.SmellViolation, stacklevel=2)
        return self._build_gate_result(
            result=m.Infra.GateResult(
                gate=self.gate_id,
                project=project_dir.name,
                passed=scan_valid,
                errors=(
                    changes if scan_valid else [issue.formatted for issue in issues]
                ),
                duration=round(time.monotonic() - started, 3),
            ),
            issues=issues,
            raw_output="\n".join(changes) if changes else self._raw_output(scan),
        )

    @staticmethod
    def _is_auto_fixable(issue: m.Infra.Issue) -> bool:
        """Return True when flext-core marks this smell tag as auto-fixable."""
        tag = smell_tag_for_code(issue.code)
        strategy = (
            c.ENFORCEMENT_SMELL_FIX_STRATEGIES.get(tag) if tag is not None else None
        )
        return bool(strategy and strategy.get("auto"))

    @override
    def check(
        self, project_dir: Path, ctx: m.Infra.GateContext
    ) -> m.Infra.GateExecution:
        """One cached full-workspace qlty scan, filtered to ``project_dir``."""
        started = time.monotonic()
        scan = self._scan(project_dir, ctx)
        issues, scan_valid = self._scan_issues(scan, project_dir, ctx)
        for issue in issues:
            warnings.warn(issue.formatted, core_e.SmellViolation, stacklevel=2)
        return self._build_gate_result(
            result=m.Infra.GateResult(
                gate=self.gate_id,
                project=project_dir.name,
                passed=scan_valid and not issues,
                errors=[issue.formatted for issue in issues],
                duration=round(time.monotonic() - started, 3),
            ),
            issues=issues,
            raw_output=self._raw_output(scan),
            ctx=ctx if scan_valid else None,
        )

    @override
    def check_files(
        self, files: t.SequenceOf[Path], project_dir: Path, ctx: m.Infra.GateContext
    ) -> m.Infra.GateExecution:
        """Preserve workspace-level duplication analysis for changed-file checks."""
        _ = files
        return self.check(project_dir, ctx)

    @override
    def _build_check_command(
        self, project_dir: Path, ctx: m.Infra.GateContext, check_dirs: t.StrSequence
    ) -> t.StrSequence:
        """Full-workspace scan command (check() bypasses per-project dirs)."""
        _ = project_dir, check_dirs
        return ctx.gate_command

    @override
    def _parse_check_output(
        self, result: p.Cli.CommandOutput, project_dir: Path, ctx: m.Infra.GateContext
    ) -> tuple[bool, t.SequenceOf[m.Infra.Issue]]:
        """Parse SARIF stdout into per-project issues (check_files path)."""
        issues, scan_valid = self._scan_issues(result, project_dir, ctx)
        findings_pass = not issues or ctx.gate_mode == "warn"
        return scan_valid and findings_pass, issues

    def _scan(self, project_dir: Path, ctx: m.Infra.GateContext) -> p.Cli.CommandOutput:
        """Run the config-owned command once per resolved execution root."""
        command = tuple(ctx.gate_command)
        if not command:
            return m.Cli.CommandOutput(
                stdout="",
                stderr="smells gate command is absent from its configured row",
                exit_code=1,
            )
        scan_root = self._scan_root(project_dir, ctx)
        key = (str(scan_root.resolve()), command)
        cached = self._scan_cache.get(key)
        if cached is not None:
            return cached
        output = self._run(command, scan_root, timeout=c.Infra.TIMEOUT_LONG)
        self._scan_cache[key] = output
        return output

    @staticmethod
    def _scan_root(project_dir: Path, ctx: m.Infra.GateContext) -> Path:
        """Resolve the command root exclusively from the configured scope."""
        if ctx.gate_execution_scope == "workspace":
            return ctx.workspace_root
        return project_dir

    def _scan_issues(
        self, scan: p.Cli.CommandOutput, project_dir: Path, ctx: m.Infra.GateContext
    ) -> tuple[tuple[m.Infra.Issue, ...], bool]:
        """Parse one qlty execution and retain whether its contract was valid."""
        severity = self._severity(ctx)
        if scan.exit_code != 0:
            detail = scan.stderr or scan.stdout or "qlty execution failed"
            return (self._failure_issue(detail, severity),), False
        try:
            project_prefix = self._project_prefix(
                project_dir, self._scan_root(project_dir, ctx)
            )
        except ValueError as exc:
            return (self._failure_issue(str(exc), severity),), False
        parsed = self._issues_from_sarif(scan.stdout, project_prefix, severity)
        if parsed.failure:
            detail = parsed.error or "invalid qlty SARIF payload"
            return (self._failure_issue(detail, severity),), False
        return parsed.unwrap(), True

    def _failure_issue(self, message: str, severity: str) -> m.Infra.Issue:
        """Build one fail-closed scanner or SARIF contract issue."""
        return m.Infra.Issue(
            file=str(self._workspace_root),
            line=1,
            column=1,
            code=self.gate_id,
            message=message,
            severity=severity,
        )

    @staticmethod
    def _severity(ctx: m.Infra.GateContext) -> str:
        """Derive finding severity from the config-owned gate execution context."""
        if ctx.gate_mode == "warn":
            return c.Infra.GateSeverity.WARNING.value
        return c.Infra.GateSeverity.ERROR.value

    @staticmethod
    def _project_prefix(project_dir: Path, scan_root: Path) -> str:
        """Return the URI prefix qlty emits for this command root."""
        relative = project_dir.resolve().relative_to(scan_root.resolve())
        return "" if relative == Path() else f"{relative.as_posix()}/"

    @classmethod
    def _issues_from_sarif(
        cls, sarif_json: str, project_prefix: str, severity: str
    ) -> p.Result[tuple[m.Infra.Issue, ...]]:
        """Validate qlty SARIF once and extract findings for one project."""
        parsed = u.Cli.json_parse(sarif_json)
        if parsed.failure:
            return r[tuple[m.Infra.Issue, ...]].fail(
                parsed.error or "qlty did not emit JSON"
            )
        try:
            data = t.Cli.JSON_MAPPING_ADAPTER.validate_python(parsed.unwrap())
        except c.EXC_VALIDATION_TYPE as exc:
            return r[tuple[m.Infra.Issue, ...]].fail(
                f"qlty SARIF root is not an object: {type(exc).__name__}"
            )
        if u.Cli.json_pick_str(data, "version") != "2.1.0":
            return r[tuple[m.Infra.Issue, ...]].fail("qlty SARIF version must be 2.1.0")
        raw_runs = data.get("runs")
        if not isinstance(raw_runs, list):
            return r[tuple[m.Infra.Issue, ...]].fail("qlty SARIF runs must be an array")
        runs = u.Cli.json_as_mapping_list(raw_runs)
        if len(runs) != len(raw_runs):
            return r[tuple[m.Infra.Issue, ...]].fail(
                "qlty SARIF runs must contain only objects"
            )
        issues: list[m.Infra.Issue] = []
        for run in runs:
            driver = u.Cli.json_deep_mapping(run, "tool", "driver")
            tool_name = u.Cli.json_pick_str(driver, "name")
            if tool_name != "qlty":
                return r[tuple[m.Infra.Issue, ...]].fail(
                    "qlty SARIF tool.driver.name must be qlty"
                )
            raw_results = run.get("results")
            if not isinstance(raw_results, list):
                return r[tuple[m.Infra.Issue, ...]].fail(
                    "qlty SARIF results must be an array"
                )
            results = u.Cli.json_as_mapping_list(raw_results)
            if len(results) != len(raw_results):
                return r[tuple[m.Infra.Issue, ...]].fail(
                    "qlty SARIF results must contain only objects"
                )
            rule_prefix = f"{tool_name}:"
            for result in results:
                uri = cls._result_uri(result)
                rule_id = u.Cli.json_pick_str(result, "ruleId")
                message = u.Cli.json_pick_str(
                    u.Cli.json_deep_mapping(result, "message"), "text"
                )
                if not uri or not rule_id.startswith(rule_prefix) or not message:
                    return r[tuple[m.Infra.Issue, ...]].fail(
                        "qlty SARIF result requires URI, qlty ruleId, and message"
                    )
                if uri.startswith(project_prefix):
                    issues.append(
                        cls._issue_from_result(
                            result, project_prefix, rule_prefix, severity
                        )
                    )
        return r[tuple[m.Infra.Issue, ...]].ok(tuple(issues))

    @classmethod
    def _issue_from_result(
        cls, result: t.JsonMapping, project_prefix: str, rule_prefix: str, severity: str
    ) -> m.Infra.Issue:
        """Map one SARIF result to an Issue enriched with the FLEXT fix text."""
        rule_id = u.Cli.json_pick_str(result, "ruleId")
        code = rule_id.removeprefix(rule_prefix)
        physical = u.Cli.json_deep_mapping(
            cls._first_location(result), "physicalLocation"
        )
        sarif_text = u.Cli.json_pick_str(
            u.Cli.json_deep_mapping(result, "message"), "text"
        )
        return m.Infra.Issue(
            file=cls._result_uri(result).removeprefix(project_prefix),
            line=u.Cli.json_nested_int(physical, "region", "startLine", default=1),
            column=u.Cli.json_nested_int(physical, "region", "startColumn"),
            code=code,
            message=cls._enriched_message(code, sarif_text),
            severity=severity,
        )

    @classmethod
    def _result_uri(cls, result: t.JsonMapping) -> str:
        """Workspace-relative URI of the finding's first location."""
        uri: str = u.Cli.json_pick_str(
            u.Cli.json_deep_mapping(
                cls._first_location(result), "physicalLocation", "artifactLocation"
            ),
            "uri",
        )
        return uri

    @staticmethod
    def _first_location(result: t.JsonMapping) -> t.JsonMapping:
        """First SARIF location mapping (empty mapping when absent)."""
        locations = u.Cli.json_deep_mapping_list(result, "locations")
        return locations[0] if locations else {}

    @staticmethod
    def _enriched_message(code: str, sarif_text: str) -> str:
        """Append the flext-core (problem, fix) law text when the tag exists."""
        tag = smell_tag_for_code(code)
        text = c.ENFORCEMENT_RULES_TEXT.get(tag) if tag else None
        if text is None:
            return sarif_text
        problem, fix = text
        return f"{sarif_text} — {problem}. Fix: {fix}"


__all__: list[str] = ["FlextInfraSmellsGate"]
