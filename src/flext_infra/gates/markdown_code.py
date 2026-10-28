"""FLEXT embedded-code gate: ruff format over fenced blocks and docstring examples.

The code inside documentation is still code — parseable embedded sources are
held to the ruff-format contract. This gate extracts fenced ``python`` blocks
and doctest examples into one temporary source tree and runs ONE ruff format
invocation per verb (single-pass law): ``check`` renders the format verdict
read-only, ``fix`` — reached from ``make fix`` — writes formatting back into
fenced blocks when every block of a file round-trips cleanly. Invalid Python
fences fail loudly; docstring write-back stays a human decision.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import (
    Iterable,
    Iterator,
    Mapping,
    MutableMapping,
    MutableSequence,
    Sequence,
)

import tempfile
import time
from collections.abc import Mapping, MutableMapping, MutableSequence, Sequence
from pathlib import Path
from typing import TYPE_CHECKING, ClassVar, override

from flext_infra import c, m, u
from flext_infra.gates import (
    FlextInfraGate,
    FlextInfraMarkdownCodeSources,
    FlextInfraMarkdownGateBase,
)

if TYPE_CHECKING:
    from flext_infra import p


class FlextInfraMarkdownCodeGate(FlextInfraGate):
    """Embedded documentation-code gate."""

    gate_id: ClassVar[str] = c.Infra.MARKDOWN_CODE
    gate_name: ClassVar[str] = "Markdown Code"
    can_fix: ClassVar[bool] = True

    def _format_command(
        self,
        project_dir: Path,
        sources_dir: Path,
        *,
        write: bool,
    ) -> Sequence[str]:
        """Build one ruff format invocation (verdict with ``--check``, write otherwise).

        The project's own ``pyproject.toml`` is the format contract owner: embedded
        blocks must satisfy the exact same configuration (notably ``preview``) that
        ``make fmt`` and ``refactor mod`` apply to authored source. ``--isolated``
        ignored that contract and produced a second, divergent formatting, so a
        documented block could never satisfy both surfaces at once.

        Returns:
            The resulting ``Sequence[str]``.

        """
        args = ["format", "--no-cache", "--output-format", "concise"]
        config_path = project_dir / c.PYPROJECT_FILENAME
        args += (
            ["--config", str(config_path)] if config_path.is_file() else ["--isolated"]
        )
        return self._python_console_script_command(
            c.Infra.RUFF,
            *args,
            *(("--check",) if not write else ()),
            str(sources_dir),
        )

    def _origin_issue(
        self,
        origin: Mapping[str, tuple[str, int]],
        location: tuple[str, int],
        message: str,
    ) -> m.Infra.Issue | None:
        """Map one extracted-source finding back to its documentation location.

        Returns:
            The resulting ``m.Infra.Issue | None``.

        """
        source, line = location
        if (documented := origin.get(Path(source).name)) is None:
            return None
        return m.Infra.Issue(
            file=documented[0],
            line=documented[1] + line - 1,
            column=1,
            code=self.gate_id,
            message=message,
        )

    def _issues_from_ruff(
        self,
        project_dir: Path,
        result: p.Cli.CommandOutput,
        origin: Mapping[str, tuple[str, int]],
        *,
        default_message: str,
    ) -> Sequence[m.Infra.Issue]:
        """Translate one ruff result into origin-mapped findings coded with this gate.

        Every ruff line that names an extracted source (verdict, parse error or
        any other diagnostic) maps to its documentation file and line, carrying
        the ruff line as evidence. A failed run naming no source never reads
        as a clean pass: the tool-level error becomes the finding.

        Returns:
            The resulting ``Sequence[m.Infra.Issue]``.

        """
        issues: MutableSequence[m.Infra.Issue] = []
        for line in (result.stdout + "\n" + result.stderr).splitlines():
            match = c.Infra.MARKDOWN_CODE_SOURCE_RE.search(line)
            issue = (
                self._origin_issue(
                    origin,
                    (match.group("file"), int(match.group("line") or 1)),
                    f"{default_message}: {line.strip()}",
                )
                if match
                else None
            )
            if issue is not None:
                issues.append(issue)
        if not u.Cli.process_succeeded(result.outcome) and not issues:
            issues.append(
                self._command_error_issue(result, c.Infra.RUFF, str(project_dir)),
            )
        return issues

    @staticmethod
    def _embedded_sources(
        project_dir: Path,
        scope_facts: p.Infra.GitScopeFacts | None,
    ) -> Mapping[str, tuple[str, tuple[str, int]]]:
        """Name every embedded source with its text and documentation origin.

        Returns:
            The resulting ``Mapping[str, tuple[str, tuple[str, int]]]``.

        """
        markdown_files = FlextInfraMarkdownGateBase.collect_markdown_files(
            project_dir, scope_facts
        )
        return {
            name: (text, origin)
            for name, text, origin in (
                *FlextInfraMarkdownCodeSources.fenced_block_sources(
                    project_dir,
                    markdown_files,
                ),
                *FlextInfraMarkdownCodeSources.docstring_sources(
                    project_dir,
                    scope_facts,
                ),
            )
        }

    @override
    def selected_for(self, project_dir: Path, ctx: m.Infra.GateContext) -> bool:
        """A project with either input kind of embedded code selects the gate.

        Applicability is the cheap derivation of the declared input kinds:
        governed Markdown or first-party Python. Extraction belongs to the
        gate's execution, which examines those inputs once and reports a
        project without embedded code as clean.

        Returns:
            The resulting ``bool``.

        """
        return bool(
            FlextInfraMarkdownGateBase.collect_markdown_files(
                project_dir,
                ctx.scope_facts,
            )
        ) or bool(self._python_targets(project_dir))

    def _run_extracted(
        self,
        project_dir: Path,
        ctx: m.Infra.GateContext,
        *,
        fix: bool,
    ) -> tuple[bool, bool, Sequence[m.Infra.Issue]]:
        """Run the single format operation over extracted sources.

        Returns ``(ran, passed, issues)``: ``ran`` is False when the project
        carries no parseable embedded documentation code, which the checker
        never selects. Only the format contract lives here — syntax ownership
        belongs to the flext-tests markdown validator, so unparseable fragments
        never enter the extracted tree and cannot turn into gate findings.

        Returns:
            The resulting ``tuple[bool, bool, Sequence[m.Infra.Issue]]``.

        """
        findings: MutableSequence[m.Infra.Issue] = []
        embedded = self._embedded_sources(project_dir, ctx.scope_facts)
        if not embedded:
            return False, False, ()
        with tempfile.TemporaryDirectory(prefix="flext-markdown-code-") as tmp:
            sources_dir = Path(tmp)
            origin: MutableMapping[str, tuple[str, int]] = {}
            for name, (text, located) in embedded.items():
                (sources_dir / name).write_text(text, c.DEFAULT_ENCODING)
                origin[name] = located
            ran = True
            formatted = self._run(
                self._format_command(project_dir, sources_dir, write=fix),
                project_dir,
                ctx,
            )
            format_ok = u.Cli.process_succeeded(formatted.outcome)
            if fix:
                findings.extend(
                    self._issues_from_ruff(
                        project_dir,
                        formatted,
                        origin,
                        default_message=(
                            "embedded block does not survive the format round-trip"
                        ),
                    ),
                )
                if format_ok:
                    self._splice_formatted_blocks(
                        project_dir,
                        sources_dir,
                        ctx.scope_facts,
                    )
                    # Docstrings are not written back: staged formatting is
                    # native success, but their unchanged sources still block.
                    findings.extend(
                        m.Infra.Issue(
                            file=location[0],
                            line=location[1],
                            column=1,
                            code=self.gate_id,
                            message=(
                                "docstring example requires formatting; "
                                "source was not rewritten"
                            ),
                        )
                        for name, (text, location) in embedded.items()
                        if Path(location[0]).suffix == c.Infra.EXT_PYTHON
                        and (sources_dir / name).read_text(c.DEFAULT_ENCODING) != text
                    )
            else:
                findings.extend(
                    self._issues_from_ruff(
                        project_dir,
                        formatted,
                        origin,
                        default_message=(
                            "embedded code is not ruff-formatted (fix via `make fmt`)"
                        ),
                    ),
                )
            passed = format_ok
        return ran, passed, findings

    def _splice_formatted_blocks(
        self,
        project_dir: Path,
        sources_dir: Path,
        scope_facts: p.Infra.GitScopeFacts | None,
    ) -> Sequence[Path]:
        """Write formatted blocks back into docs whose round-trip recompiles cleanly.

        Enumeration matches the extractor exactly: only parseable non-``notest``
        blocks own a staged source, share its index, and take part in the
        all-or-nothing splice; fragments stay byte-identical.

        Returns:
            The resulting ``Sequence[Path]``.

        """
        rewritten: MutableSequence[Path] = []
        for md_path in FlextInfraMarkdownGateBase.collect_markdown_files(
            project_dir, scope_facts
        ):
            spliced = self._splice_document(md_path, project_dir, sources_dir)
            if spliced is not None:
                rewritten.append(spliced)
        return rewritten

    def _splice_document(
        self,
        md_path: Path,
        project_dir: Path,
        sources_dir: Path,
    ) -> Path | None:
        """Write one document's formatted blocks back when its round-trip holds.

        Returns:
            The rewritten path, or ``None`` when the document stayed identical.

        """
        content = md_path.read_text(c.DEFAULT_ENCODING)
        relative_posix = md_path.relative_to(project_dir).as_posix()
        staged = FlextInfraMarkdownCodeSources.formattable_fences(content, md_path)
        if not staged:
            return None
        blocks, round_trips = self._formatted_blocks(
            tuple(index for index, _fence in staged),
            relative_posix,
            sources_dir,
            md_path,
        )
        if not round_trips:
            return None
        updated = u.Cli.markdown_rewrite_fences(
            content,
            {
                fence: (fence.info, block)
                for (_index, fence), block in zip(staged, blocks, strict=True)
                if block != fence.code
            },
        )
        if updated == content:
            return None
        md_path.write_text(updated, c.DEFAULT_ENCODING)
        return md_path

    @staticmethod
    def _formatted_blocks(
        staged: Sequence[int],
        relative_posix: str,
        sources_dir: Path,
        md_path: Path,
    ) -> tuple[list[str], bool]:
        """Read the formatted sources of one document's parseable blocks.

        Returns:
            The ``(blocks, round_trips)`` pair; a missing or non-recompilable
            staged source ends the round trip.

        """
        blocks: MutableSequence[str] = []
        for index in staged:
            source = sources_dir / FlextInfraMarkdownCodeSources.source_name(
                relative_posix,
                index,
            )
            if not source.is_file():
                return (list(blocks), False)
            formatted = source.read_text(c.DEFAULT_ENCODING)
            if FlextInfraMarkdownCodeSources.syntax_broken(formatted, md_path):
                return (list(blocks), False)
            blocks.append(formatted)
        return (list(blocks), True)

    def _clean_without_embedded_code(
        self,
        project_dir: Path,
        ctx: m.Infra.GateContext,
        started: float,
    ) -> m.Infra.GateExecution:
        """Report examined inputs that carry no embedded code as clean.

        Returns:
            A passing execution whose receipt records the examined absence.

        """
        return self._build_gate_execution(
            m.Infra.GateExecutionParams(
                project_dir=project_dir,
                verdict=True,
                issues=(),
                raw_output=f"{self.gate_id}: no embedded documentation code in the "
                "governed Markdown and first-party Python inputs",
                started=started,
            ),
            ctx,
        )

    @override
    def check(
        self,
        project_dir: Path,
        ctx: m.Infra.GateContext,
    ) -> m.Infra.GateExecution:
        """Validate embedded sources read-only when documentation code exists.

        Returns:
            The resulting ``m.Infra.GateExecution``.

        """
        started = time.monotonic()
        ran, passed, issues = self._run_extracted(project_dir, ctx, fix=False)
        if not ran:
            return self._clean_without_embedded_code(project_dir, ctx, started)
        return self._build_gate_execution(
            m.Infra.GateExecutionParams(
                project_dir=project_dir,
                verdict=passed,
                issues=tuple(issues),
                raw_output="\n".join(issue.formatted for issue in issues),
                started=started,
            ),
            ctx,
        )

    @override
    def fix(self, project_dir: Path, ctx: m.Infra.GateContext) -> m.Infra.GateExecution:
        """Run the single mutating pass: format blocks and splice clean docs back.

        Returns:
            The resulting ``m.Infra.GateExecution``.

        Raises:
            ValueError: If the context does not request a mutating operation.

        """
        if ctx.check_only or not ctx.apply_fixes:
            msg = "repair requires apply_fixes=True and check_only=False"
            raise ValueError(msg)
        started = time.monotonic()
        with u.Cli.file_changes_lock(u.Infra.mutation_lock_path(project_dir).unwrap()):
            ran, passed, issues = self._run_extracted(project_dir, ctx, fix=True)
        if not ran:
            return self._clean_without_embedded_code(project_dir, ctx, started)
        return self._build_gate_execution(
            m.Infra.GateExecutionParams(
                project_dir=project_dir,
                verdict=passed and not issues,
                issues=tuple(issues),
                raw_output="\n".join(issue.formatted for issue in issues),
                outcome=(
                    c.Infra.ToolOutcome.ERROR
                    if not passed
                    else c.Infra.ToolOutcome.FINDINGS
                    if issues
                    else c.Infra.ToolOutcome.CLEAN
                ),
                started=started,
            ),
            ctx=ctx,
        )


__all__: list[str] = ["FlextInfraMarkdownCodeGate"]
