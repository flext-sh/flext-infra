"""qlty code-smell quality gate — blocking evidence for smell findings.

Every qlty smell type (identical/similar-code, function/file-complexity,
function-parameters, return-statements, nested-control-flow, boolean-logic)
is reported per project as a visible warning. Scanner absence, stderr, and a
nonzero exit remain visible issues; no cache, fallback binary, or empty-output
rewrite can turn an invalid scan silent.
"""

from __future__ import annotations

import shutil
import time
import warnings
from pathlib import Path
from typing import TYPE_CHECKING, ClassVar, override

from flext_core import e as core_e
from flext_infra import c, m, u
from flext_infra.gates.base_gate import FlextInfraGate

# flext-0ftd.3.5: the empty package initializer is not a compatibility export;
# consume the declaration at its canonical owner after the lazy-init cutover.
from flext_infra.transformers.smells.base import smell_fixer_for
from flext_infra.transformers.smells.boolean_logic import FlextInfraBooleanLogicFixer

if TYPE_CHECKING:
    from flext_infra import p, t


class FlextInfraSmellsGate(FlextInfraGate):
    """Report qlty smells per project from one fresh workspace scan.

    A single ``qlty smells --all`` scan covers the whole workspace so
    cross-project duplication clusters stay visible; per-project results are
    filtered by SARIF URI prefix.
    """

    gate_id: ClassVar[str] = "smells"
    gate_name: ClassVar[str] = "Code Smells"
    can_fix: ClassVar[bool] = True
    tool_name: ClassVar[str] = c.Infra.SARIF_TOOL_INFO["smells"][0]
    tool_url: ClassVar[str] = c.Infra.SARIF_TOOL_INFO["smells"][1]

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
        scan = self._workspace_scan()
        issues = self._issues_from_scan(scan, project_dir.name)
        self._warn_issues(issues)
        if scan.exit_code != 0 or scan.stderr.strip():
            return self._build_check_gate_execution(
                project_dir,
                passed=False,
                issues=issues,
                raw_output=self._scan_output(scan),
                started=started,
            )
        auto_issues = [issue for issue in issues if self._is_auto_fixable(issue)]
        changes: list[str] = []
        for issue in auto_issues:
            tag = c.Infra.SMELLS_RULE_TAGS.get(issue.code, "")
            fixer = (
                FlextInfraBooleanLogicFixer()
                if tag == FlextInfraBooleanLogicFixer.tag
                else smell_fixer_for(tag)
            )
            if fixer is None:
                continue
            fixed, fix_changes = fixer.fix(project_dir, issue)
            if fixed:
                changes.extend(fix_changes)
        remaining = tuple(
            issue for issue in issues if not self._is_auto_fixable(issue)
        )
        self._warn_issues(remaining)
        return self._build_check_gate_execution(
            project_dir,
            passed=True,
            issues=remaining,
            raw_output="\n".join(changes) if changes else self._scan_output(scan),
            started=started,
        )

    @staticmethod
    def _is_auto_fixable(issue: m.Infra.Issue) -> bool:
        """Return True when flext-core marks this smell tag as auto-fixable."""
        tag = c.Infra.SMELLS_RULE_TAGS.get(issue.code, "")
        strategy = c.ENFORCEMENT_SMELL_FIX_STRATEGIES.get(tag)
        return bool(strategy and strategy.get("auto"))

    @override
    def check(
        self, project_dir: Path, ctx: m.Infra.GateContext
    ) -> m.Infra.GateExecution:
        """One cached full-workspace qlty scan, filtered to ``project_dir``."""
        _ = ctx
        started = time.monotonic()
        scan = self._workspace_scan()
        issues = self._issues_from_scan(scan, project_dir.name)
        self._warn_issues(issues)
        passed = not issues
        return self._build_check_gate_execution(
            project_dir,
            passed=passed,
            issues=issues,
            raw_output=self._scan_output(scan),
            started=started,
        )

    @override
    def _build_check_command(
        self, project_dir: Path, ctx: m.Infra.GateContext, check_dirs: t.StrSequence
    ) -> t.StrSequence:
        """Full-workspace scan command (check() bypasses per-project dirs)."""
        _ = project_dir, ctx, check_dirs
        binary = self._resolve_binary()
        if binary is None:
            raise FileNotFoundError(c.Infra.QLTY_BINARY)
        return [binary, *c.Infra.SMELLS_QLTY_ARGS]

    @override
    def _parse_check_output(
        self, result: p.Cli.CommandOutput, project_dir: Path, ctx: m.Infra.GateContext
    ) -> tuple[bool, t.SequenceOf[m.Infra.Issue]]:
        """Parse SARIF stdout into per-project issues (check_files path)."""
        _ = ctx
        issues = self._issues_from_scan(result, project_dir.name)
        return not issues, issues

    def _issues_from_scan(
        self, scan: p.Cli.CommandOutput, project_name: str
    ) -> tuple[m.Infra.Issue, ...]:
        """Parse valid SARIF output or expose the exact subprocess failure."""
        if scan.exit_code != 0 or scan.stderr.strip():
            return (self._tool_failure_issue(scan),)
        return self._issues_from_sarif(scan.stdout, project_name)

    @staticmethod
    def _warn_issues(issues: t.SequenceOf[m.Infra.Issue]) -> None:
        """Emit one warning per smell finding at the public gate boundary."""
        for issue in issues:
            warnings.warn(issue.formatted, core_e.SmellViolation, stacklevel=2)

    @staticmethod
    def _scan_output(scan: p.Cli.CommandOutput) -> str:
        """Preserve non-empty subprocess streams in their causal order."""
        return "\n".join(stream for stream in (scan.stdout, scan.stderr) if stream)

    def _workspace_scan(self) -> p.Cli.CommandOutput:
        """Run one fresh workspace scan and preserve its exact process result."""
        binary = self._resolve_binary()
        if binary is None:
            raise FileNotFoundError(c.Infra.QLTY_BINARY)
        return self._run(
            [binary, *c.Infra.SMELLS_QLTY_ARGS],
            self._repository_root,
            timeout=c.Infra.TIMEOUT_LONG,
        )

    @staticmethod
    def _resolve_binary() -> str | None:
        """Locate qlty on PATH; the managed environment is the sole owner."""
        found = shutil.which(c.Infra.QLTY_BINARY)
        return found if isinstance(found, str) else None

    def _tool_failure_issue(self, scan: p.Cli.CommandOutput) -> m.Infra.Issue:
        """Scanner absence/crash must never read as a clean pass."""
        return m.Infra.Issue(
            file=c.Infra.PYPROJECT_FILENAME,
            line=1,
            column=0,
            code=self.gate_id,
            message=scan.stderr or "qlty execution failed",
            severity=self._severity(),
        )

    @staticmethod
    def _severity() -> str:
        """Return the sole blocking severity."""
        return str(c.Infra.GateSeverity.ERROR.value)

    @classmethod
    def _issues_from_sarif(
        cls, sarif_json: str, project_name: str
    ) -> tuple[m.Infra.Issue, ...]:
        """Extract one Issue per smell finding inside ``project_name``.

        Pure function over a literal qlty SARIF payload (unit-testable, no
        subprocess) — same strategy as ``loc_cap._files_over_cap``.
        """
        data = u.Cli.json_as_mapping(u.Cli.json_parse(sarif_json).unwrap())
        prefix = f"{project_name}/"
        return tuple(
            cls._issue_from_result(result, prefix)
            for run in u.Cli.json_deep_mapping_list(data, "runs")
            for result in u.Cli.json_deep_mapping_list(run, "results")
            if cls._result_uri(result).startswith(prefix)
        )

    @classmethod
    def _issue_from_result(cls, result: t.JsonMapping, prefix: str) -> m.Infra.Issue:
        """Map one SARIF result to an Issue enriched with the FLEXT fix text."""
        rule_id = u.Cli.json_pick_str(result, "ruleId")
        code = rule_id.removeprefix(c.Infra.SMELLS_RULE_PREFIX)
        physical = u.Cli.json_deep_mapping(
            cls._first_location(result), "physicalLocation"
        )
        sarif_text = u.Cli.json_pick_str(
            u.Cli.json_deep_mapping(result, "message"), "text"
        )
        return m.Infra.Issue(
            file=cls._result_uri(result).removeprefix(prefix),
            line=u.Cli.json_nested_int(physical, "region", "startLine", default=1),
            column=u.Cli.json_nested_int(physical, "region", "startColumn"),
            code=code,
            message=cls._enriched_message(code, sarif_text),
            severity=cls._severity(),
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
        tag = c.Infra.SMELLS_RULE_TAGS.get(code, "")
        text = c.ENFORCEMENT_RULES_TEXT.get(tag) if tag else None
        if text is None:
            return sarif_text
        problem, fix = text
        return f"{sarif_text} — {problem}. Fix: {fix}"


__all__: list[str] = ["FlextInfraSmellsGate"]
