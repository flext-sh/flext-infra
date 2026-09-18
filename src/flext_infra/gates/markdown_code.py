"""FLEXT embedded-code gate: ruff over fenced blocks and docstring examples.

The code inside documentation is still code. This gate extracts fenced
``python``` blocks and doctest examples into one temporary source tree and
runs ruff in single invocations per operation (the single-pass verb law):
``check`` runs the error-class lint plus the format verdict read-only, and
``fix`` — reached from ``make fix`` — writes ruff-format output back into
fenced blocks when every block of a file recompiles cleanly. Docstring
findings are reported for manual repair; prose-embedded rewrites stay a
human decision.
"""

from __future__ import annotations

import re
import tempfile
import time
from pathlib import Path
from typing import TYPE_CHECKING, ClassVar, override

from flext_infra import c, m, u

from .base_gate import FlextInfraGate
from .markdown_code_sources import (
    TEST_SKIP_MARKER,
    source_name,
    write_docstring_sources,
    write_fenced_block_sources,
)
from .markdown_support import collect_markdown_files

if TYPE_CHECKING:
    from flext_infra import p, t


class FlextInfraMarkdownCodeGate(FlextInfraGate):
    """Embedded documentation-code gate."""

    gate_id: ClassVar[str] = c.Infra.MARKDOWN_CODE
    gate_name: ClassVar[str] = "Markdown Code"
    can_fix: ClassVar[bool] = True

    def _lint_command(self, sources_dir: Path) -> t.StrSequence:
        """Build the single error-class lint invocation over extracted sources."""
        return self._python_console_script_command(
            c.Infra.RUFF,
            "check",
            "--isolated",
            "--no-cache",
            "--output-format",
            "concise",
            "--select",
            ",".join(c.Infra.MARKDOWN_CODE_LINT_SELECT),
            str(sources_dir),
        )

    def _format_command(self, sources_dir: Path, *, write: bool) -> t.StrSequence:
        """Build one ruff format invocation (verdict with ``--check``, write otherwise)."""
        args = ["format", "--isolated", "--no-cache"]
        return self._python_console_script_command(
            c.Infra.RUFF, *args, *(("--check",) if not write else ()), str(sources_dir)
        )

    def _origin_issue(
        self,
        origin: dict[str, tuple[str, int]],
        source: str,
        *,
        code: str,
        message: str,
        line: int = 1,
    ) -> m.Infra.Issue | None:
        """Map one extracted-source finding back to its documentation location."""
        if (location := origin.get(Path(source).name)) is None:
            return None
        return m.Infra.Issue(
            file=location[0],
            line=location[1] + line - 1,
            column=1,
            code=code,
            message=message,
        )

    def _issues_from_ruff(
        self,
        project_dir: Path,
        result: p.Cli.CommandOutput,
        origin: dict[str, tuple[str, int]],
        *,
        default_code: str,
        default_message: str,
        file_pattern: re.Pattern[str],
        fallback_on_error: bool = True,
    ) -> t.SequenceOf[m.Infra.Issue]:
        """Translate one ruff result into origin-mapped gate findings.

        ``fallback_on_error`` keeps a failed run without mapped findings from
        reading as a clean pass; a caller that already reported the same
        failed sources through another operation suppresses it so one defect
        stays one finding.
        """
        issues: t.MutableSequenceOf[m.Infra.Issue] = []
        for line in (result.stdout + "\n" + result.stderr).splitlines():
            if match := file_pattern.match(line.strip()):
                if issue := self._origin_issue(
                    origin,
                    match.group("file"),
                    code=default_code,
                    message=default_message,
                    line=int(match.groupdict().get("line", 1) or 1),
                ):
                    issues.append(issue)
        if (
            fallback_on_error
            and not u.Cli.process_succeeded(result.outcome)
            and not issues
        ):
            issues.append(
                self._command_error_issue(
                    result, tool=c.Infra.RUFF, file=str(project_dir), line=1, column=1
                )
            )
        return issues

    def _run_extracted(
        self, project_dir: Path, markdown_files: t.SequenceOf[Path], *, fix: bool
    ) -> tuple[bool, bool, t.SequenceOf[m.Infra.Issue]]:
        """Run the extracted-source operations.

        Returns ``(ran, passed, issues)``: ``ran`` is False when the project
        carries no embedded documentation code at all, which is the neutral
        skip both verbs report instead of an empty verdict.
        """
        findings: t.MutableSequenceOf[m.Infra.Issue] = []
        ran = False
        with tempfile.TemporaryDirectory(prefix="flext-markdown-code-") as tmp:
            sources_dir = Path(tmp)
            origin = write_fenced_block_sources(
                project_dir, markdown_files, sources_dir
            )
            origin.update(write_docstring_sources(project_dir, sources_dir))
            if not origin:
                return False, True, ()
            ran = True
            lint = self._run(self._lint_command(sources_dir), project_dir)
            lint_ok = u.Cli.process_succeeded(lint.outcome)
            lint_findings = list(
                self._issues_from_ruff(
                    project_dir,
                    lint,
                    origin,
                    default_code=self.gate_id,
                    default_message="embedded code fails ruff error-class lint",
                    file_pattern=c.Infra.MARKDOWN_CODE_RE,
                )
            )
            findings.extend(lint_findings)
            # A source the lint already flagged cannot also produce a distinct
            # format verdict; the format operation suppresses its fallback so
            # one defect stays one finding.
            format_fallback = not lint_findings
            if fix:
                formatted = self._run(
                    self._format_command(sources_dir, write=True), project_dir
                )
                format_ok = u.Cli.process_succeeded(formatted.outcome)
                findings.extend(
                    self._issues_from_ruff(
                        project_dir,
                        formatted,
                        origin,
                        default_code=self.gate_id,
                        default_message=(
                            "embedded block does not survive the format round-trip"
                        ),
                        file_pattern=c.Infra.MARKDOWN_CODE_FORMAT_ERROR_RE,
                        fallback_on_error=format_fallback,
                    )
                )
                if format_ok:
                    self._splice_formatted_blocks(project_dir, sources_dir)
            else:
                verdict = self._run(
                    self._format_command(sources_dir, write=False), project_dir
                )
                format_ok = u.Cli.process_succeeded(verdict.outcome)
                findings.extend(
                    self._issues_from_ruff(
                        project_dir,
                        verdict,
                        origin,
                        default_code=self.gate_id,
                        default_message=(
                            "embedded code is not ruff-formatted (repair belongs to `make fix`)"
                        ),
                        file_pattern=c.Infra.MARKDOWN_CODE_FORMAT_FILE_RE,
                        fallback_on_error=format_fallback,
                    )
                )
            passed = lint_ok and format_ok
        return ran, passed, findings

    def _splice_formatted_blocks(
        self, project_dir: Path, sources_dir: Path
    ) -> t.SequenceOf[Path]:
        """Write formatted blocks back into docs whose round-trip recompiles cleanly."""
        rewritten: t.MutableSequenceOf[Path] = []
        for md_path in collect_markdown_files(project_dir):
            content = md_path.read_text(c.Cli.ENCODING_DEFAULT)
            relative_posix = md_path.relative_to(project_dir).as_posix()
            testable = [
                match
                for match in c.Infra.MARKDOWN_PY_FENCE_RE.finditer(content)
                if TEST_SKIP_MARKER not in match.group("info")
            ]
            if not testable:
                continue
            blocks: t.MutableSequenceOf[str] = []
            round_trips = True
            for index in range(len(testable)):
                formatted = (
                    sources_dir / source_name(relative_posix, index)
                ).read_text(c.Cli.ENCODING_DEFAULT)
                try:
                    compile(formatted, str(md_path), "exec")
                except SyntaxError:
                    round_trips = False
                    break
                blocks.append(formatted)
            if not round_trips:
                continue
            blocks_iter = iter(blocks)
            updated = c.Infra.MARKDOWN_PY_FENCE_RE.sub(
                lambda match: (
                    match.group(0)
                    if TEST_SKIP_MARKER in match.group("info")
                    else match.group(0).replace(match.group("code"), next(blocks_iter))
                ),
                content,
            )
            if updated != content:
                md_path.write_text(updated, c.Cli.ENCODING_DEFAULT)
                rewritten.append(md_path)
        return rewritten

    @override
    def check(
        self, project_dir: Path, ctx: m.Infra.GateContext
    ) -> m.Infra.GateExecution:
        """Validate embedded sources read-only when documentation code exists."""
        _ = ctx
        started = time.monotonic()
        ran, passed, issues = self._run_extracted(
            project_dir, collect_markdown_files(project_dir), fix=False
        )
        if not ran:
            return self._neutral_skip_result(
                project_dir,
                started,
                message=f"{self.gate_id}: no embedded documentation code found",
            )
        return self._build_check_gate_execution(
            project_dir,
            passed=passed,
            issues=issues,
            raw_output="\n".join(issue.formatted for issue in issues),
            started=started,
        )

    @override
    def fix(self, project_dir: Path, ctx: m.Infra.GateContext) -> m.Infra.GateExecution:
        """Run the single mutating pass: format extracted blocks and splice clean docs back."""
        if ctx.check_only or not ctx.apply_fixes:
            return self._check_only_fix_result(project_dir)
        started = time.monotonic()
        ran, passed, issues = self._run_extracted(
            project_dir, collect_markdown_files(project_dir), fix=True
        )
        if not ran:
            return self._neutral_skip_result(
                project_dir,
                started,
                message=f"{self.gate_id}: no embedded documentation code found",
            )
        return self._build_check_gate_execution(
            project_dir,
            passed=passed,
            issues=issues,
            raw_output="\n".join(issue.formatted for issue in issues),
            started=started,
            accept_reported_issues=True,
        )


__all__: list[str] = ["FlextInfraMarkdownCodeGate"]
