"""Accessor migration orchestration for get_/set_/is_ modernization."""

from __future__ import annotations

import difflib
import io
from operator import itemgetter
from pathlib import Path
from tokenize import NAME, generate_tokens
from typing import Annotated, ClassVar, override

from flext_cli import cli
from flext_infra import (
    FlextInfraProjectSelectionServiceBase,
    c,
    m,
    p,
    r,
    t,
    u,
)


class FlextInfraAccessorMigrationOrchestrator(
    FlextInfraProjectSelectionServiceBase[m.Infra.AccessorMigrationReport],
):
    """Dry-run/apply orchestrator for public accessor migration candidates."""

    preview_limit: Annotated[
        int,
        m.Field(
            description="Maximum number of file previews to include in the report",
        ),
    ] = 10
    gates: Annotated[
        str,
        m.Field(
            description="Comma-separated lint gates for preview/apply validation",
        ),
    ] = c.Infra.SAFE_EXECUTION_DEFAULT_GATES

    # Rename rules sourced from c.ENFORCEMENT_ACCESSOR_RENAMES (flext-core SSOT).
    # All entries target flext-core surface (origin="flext_core"); adding a
    # rename = one entry in flext-core's enforcement constant, never duplicated
    # here. Token-level rename is idempotent — once source_name has been
    # renamed, subsequent passes find zero matching tokens.
    _AUTOMATED_RULES: ClassVar[tuple[m.Infra.AccessorMigrationRule, ...]] = tuple(
        m.Infra.AccessorMigrationRule(
            source_name=src,
            replacement_name=repl,
            reason=reason,
            origin="flext_core",
        )
        for src, (repl, reason) in c.ENFORCEMENT_ACCESSOR_RENAMES.items()
    )
    _AUTOMATED_NAMES: ClassVar[frozenset[str]] = frozenset(
        c.ENFORCEMENT_ACCESSOR_RENAMES
    )
    _MANUAL_WARNING_REASON: ClassVar[str] = (
        "Public {prefix}-prefixed accessor: rename to canonical verb "
        "(drop the prefix or use resolve_/fetch_/build_/etc.)"
    )

    @property
    def gate_names(self) -> t.StrSequence:
        """Return normalized lint gate names."""
        return u.Infra.normalize_cli_values(self.gates)

    @property
    def lint_tool_names(self) -> t.StrSequence:
        """Return selected lint tool names resolved from gate names."""
        return u.Infra.selected_lint_tool_names(
            self.gate_names,
        )

    @override
    def execute(self) -> p.Result[m.Infra.AccessorMigrationReport]:
        """Execute."""
        resolved = u.Infra.resolve_projects(
            self.workspace_root,
            self.project_names or (),
        )
        if resolved.failure:
            return r[m.Infra.AccessorMigrationReport].fail(
                resolved.error or "project resolution failed",
            )
        iter_result = u.Infra.iter_python_files(
            self.workspace_root,
            project_roots=[project.path for project in resolved.value],
        )
        if iter_result.failure:
            return r[m.Infra.AccessorMigrationReport].fail(
                iter_result.error or "python file iteration failed",
            )
        previews: t.MutableSequenceOf[m.Infra.AccessorMigrationFile] = []
        files_with_changes = 0
        automated_change_count = 0
        warning_count = 0
        lint_before_totals: dict[str, int] = {}
        lint_after_totals: dict[str, int] = {}
        new_lint_error_totals: dict[str, int] = {}
        with u.Infra.open_project(self.workspace_root) as rope_project:
            for py_file in iter_result.value:
                source = py_file.read_text(encoding=c.Cli.ENCODING_DEFAULT)
                updated_source, automated_changes = self._apply_automated_rewrites(
                    rope_project,
                    py_file,
                    source,
                )
                warnings = list(self._collect_manual_warnings(py_file, source))
                file_report = self._process_file(
                    py_file,
                    source=source,
                    updated_source=updated_source,
                    automated_changes=automated_changes,
                    warnings=warnings,
                    include_preview=(bool(automated_changes or warnings))
                    and len(previews) < self.preview_limit,
                )
                automated_change_count += len(file_report.automated_changes)
                warning_count += len(file_report.warnings)
                if file_report.automated_changes:
                    files_with_changes += 1
                if (file_report.automated_changes or file_report.warnings) and len(
                    previews
                ) < self.preview_limit:
                    previews.append(file_report)
                self._accumulate_lint_totals(
                    lint_before_totals,
                    file_report.lint_before,
                )
                self._accumulate_lint_totals(
                    lint_after_totals,
                    file_report.lint_after,
                )
                self._accumulate_lint_totals(
                    new_lint_error_totals,
                    file_report.new_lint_errors,
                )
        return r[m.Infra.AccessorMigrationReport].ok(
            m.Infra.AccessorMigrationReport(
                workspace=str(self.workspace_root),
                dry_run=self.dry_run,
                files_scanned=len(iter_result.value),
                files_with_changes=files_with_changes,
                automated_change_count=automated_change_count,
                warning_count=warning_count,
                lint_tools=tuple(self.lint_tool_names),
                lint_before_totals=lint_before_totals,
                lint_after_totals=lint_after_totals,
                new_lint_error_totals=new_lint_error_totals,
                files=tuple(previews),
            )
        )

    @classmethod
    @override
    def execute_command(
        cls,
        params: m.Infra.AccessorMigrationInput,
    ) -> p.Result[m.Infra.AccessorMigrationReport]:
        """Execute accessor migration from the validated command service."""
        workspace_root = getattr(params, "workspace_root", None)
        if workspace_root is None:
            workspace_root = getattr(params, "workspace", None)

        selected_projects = getattr(params, "selected_projects", None)
        if selected_projects is None:
            selected_projects = getattr(params, "projects", None)

        apply_changes = getattr(params, "apply_changes", None)
        if apply_changes is None:
            apply_changes = getattr(params, "apply", False)

        target_module = getattr(params, "module", None)
        if target_module is None:
            target_module = getattr(params, "target_module", None)

        target_namespace = getattr(params, "namespace", None)
        if target_namespace is None:
            target_namespace = getattr(params, "target_namespace", None)

        result = cls.model_validate({
            "workspace_root": workspace_root,
            "selected_projects": selected_projects,
            "apply_changes": apply_changes,
            "fail_fast": params.fail_fast,
            "target_module": target_module,
            "target_namespace": target_namespace,
            "preview_limit": params.preview_limit,
            "gates": ",".join(params.gates),
        }).execute()
        if result.failure:
            return r[m.Infra.AccessorMigrationReport].fail(
                result.error or "accessor migration execution failed",
            )
        cli.display_text(cls.render_text(result.value))
        return r[m.Infra.AccessorMigrationReport].ok(result.value)

    @staticmethod
    def _accumulate_lint_totals(
        totals: dict[str, int],
        snapshot: t.Infra.LintSnapshot,
    ) -> None:
        """Accumulate lint totals."""
        for tool, lines in snapshot.items():
            totals[tool] = totals.get(tool, 0) + len(tuple(lines))

    def _process_file(
        self,
        py_file: Path,
        *,
        source: str,
        updated_source: str,
        automated_changes: t.SequenceOf[m.Infra.AccessorMigrationChange],
        warnings: t.MutableSequenceOf[m.Infra.AccessorMigrationChange],
        include_preview: bool,
    ) -> m.Infra.AccessorMigrationFile:
        """Process file."""
        lint_before: dict[str, t.StrSequence] = {}
        lint_after: dict[str, t.StrSequence] = {}
        new_lint_errors: dict[str, t.StrSequence] = {}
        before: t.Infra.LintSnapshot = {}
        after: t.Infra.LintSnapshot = {}
        if automated_changes:
            if self.dry_run and include_preview:
                before, after = u.Infra.preview_source_lint(
                    py_file,
                    self.workspace_root,
                    updated_source=updated_source,
                    gates=self.gate_names,
                )
            elif not self.dry_run:
                before = (
                    u.Infra.lint_snapshot(
                        py_file,
                        self.workspace_root,
                        gates=self.gate_names,
                    )
                    if include_preview
                    else {}
                )
                ok, report = u.Infra.protected_source_write(
                    py_file,
                    request=m.Infra.ProtectedSourceWriteRequest(
                        workspace=self.workspace_root,
                        updated_source=updated_source,
                        gates=self.gate_names,
                    ),
                )
                if not ok:
                    warnings.append(
                        m.Infra.AccessorMigrationChange(
                            file=str(py_file),
                            line=0,
                            original_name="protected_write",
                            replacement_name="",
                            automated=False,
                            reason=" ; ".join(report[:3]) or "protected write failed",
                        )
                    )
                after = (
                    u.Infra.lint_snapshot(
                        py_file,
                        self.workspace_root,
                        gates=self.gate_names,
                    )
                    if include_preview
                    else {}
                )
            else:
                before = {}
                after = {}
            if include_preview:
                lint_before = self._freeze_lints(before)
                lint_after = self._freeze_lints(after)
                new_lint_errors = self._freeze_lints(
                    u.Infra.lint_new_errors(before, after)
                )
        return m.Infra.AccessorMigrationFile(
            file=str(py_file),
            lint_tools=tuple(self.lint_tool_names)
            if automated_changes and include_preview
            else (),
            automated_changes=tuple(automated_changes),
            warnings=tuple(warnings),
            diff=self._diff(py_file, source, updated_source)
            if automated_changes and include_preview
            else "",
            lint_before=lint_before,
            lint_after=lint_after,
            new_lint_errors=new_lint_errors,
        )

    def _apply_automated_rewrites(
        self,
        rope_project: t.Infra.RopeProject,
        py_file: Path,
        source: str,
    ) -> tuple[str, t.SequenceOf[m.Infra.AccessorMigrationChange]]:
        """Apply automated rewrites."""
        resource = u.Infra.get_resource_from_path(rope_project, py_file)
        if resource is None:
            return source, ()
        updated_source = source
        changes: t.MutableSequenceOf[m.Infra.AccessorMigrationChange] = []
        for rule in self._AUTOMATED_RULES:
            updated_source, rule_changes = self._rename_symbol_tokens(
                rope_project,
                resource,
                updated_source,
                source_name=rule.source_name,
                replacement_name=rule.replacement_name,
                reason=rule.reason,
                file_path=py_file,
            )
            changes.extend(rule_changes)
        return updated_source, changes

    @staticmethod
    def _rename_symbol_tokens(
        rope_project: t.Infra.RopeProject,
        resource: t.Infra.RopeResource,
        source: str,
        *,
        source_name: str,
        replacement_name: str,
        reason: str,
        file_path: Path,
    ) -> tuple[str, t.SequenceOf[m.Infra.AccessorMigrationChange]]:
        """Rename symbol tokens."""
        token_lines: t.MutableSequenceOf[m.Infra.AccessorMigrationChange] = []
        rewrite_ranges: t.MutableSequenceOf[tuple[int, int, str]] = []
        for token in generate_tokens(io.StringIO(source).readline):
            if token.type != NAME or token.string != source_name:
                continue
            line, column = token.start
            start = FlextInfraAccessorMigrationOrchestrator._offset_from_position(
                source,
                line,
                column,
            )
            end = start + len(source_name)
            rewrite_ranges.append((start, end, replacement_name))
            token_lines.append(
                m.Infra.AccessorMigrationChange(
                    file=str(file_path),
                    line=line,
                    original_name=source_name,
                    replacement_name=replacement_name,
                    automated=True,
                    reason=reason,
                )
            )
        if not rewrite_ranges:
            return source, ()
        del rope_project
        del resource
        updated_source = source
        for start, end, replacement in sorted(
            rewrite_ranges,
            key=itemgetter(0),
            reverse=True,
        ):
            updated_source = updated_source[:start] + replacement + updated_source[end:]
        return updated_source, tuple(token_lines)

    @staticmethod
    def _offset_from_position(source: str, line: int, column: int) -> int:
        """Offset from position."""
        source_lines = source.splitlines(keepends=True)
        line_offset = sum(len(item) for item in source_lines[: line - 1])
        return line_offset + column

    def _collect_manual_warnings(
        self,
        py_file: Path,
        source: str,
    ) -> t.SequenceOf[m.Infra.AccessorMigrationChange]:
        """Collect manual warnings."""
        lines = source.splitlines()
        warnings: t.MutableSequenceOf[m.Infra.AccessorMigrationChange] = []
        scope_stack: t.MutableSequenceOf[tuple[str, int]] = []
        for line_index, line_text in enumerate(lines, start=1):
            stripped = line_text.lstrip()
            if not stripped or stripped.startswith("#"):
                continue
            indent = len(line_text) - len(stripped)
            while scope_stack and indent <= scope_stack[-1][1]:
                scope_stack.pop()
            if stripped.startswith("class "):
                class_name = (
                    stripped
                    .split("class ", maxsplit=1)[1]
                    .split("(", maxsplit=1)[0]
                    .split(":", maxsplit=1)[0]
                    .strip()
                )
                scope_stack.append((f"class:{class_name}", indent))
                continue
            function_prefix = ""
            if stripped.startswith("def "):
                function_prefix = "def "
            elif stripped.startswith("async def "):
                function_prefix = "async def "
            if not function_prefix:
                continue
            function_name = (
                stripped
                .split(function_prefix, maxsplit=1)[1]
                .split("(", maxsplit=1)[0]
                .strip()
            )
            parent_scope = scope_stack[-1][0] if scope_stack else "module"
            scope_stack.append((f"def:{function_name}", indent))
            if parent_scope.startswith("def:"):
                continue
            if function_name.startswith("_") or function_name in self._AUTOMATED_NAMES:
                continue
            matched_prefix = next(
                (
                    p
                    for p in c.Infra.ACCESSOR_WARNING_PREFIXES
                    if function_name.startswith(p)
                ),
                None,
            )
            if matched_prefix is None:
                continue
            warnings.append(
                m.Infra.AccessorMigrationChange(
                    file=str(py_file),
                    line=line_index,
                    original_name=function_name,
                    replacement_name=function_name[len(matched_prefix) :],
                    automated=False,
                    reason=self._MANUAL_WARNING_REASON.format(
                        prefix=matched_prefix.rstrip("_"),
                    ),
                )
            )
        return warnings

    @staticmethod
    def _freeze_lints(snapshot: t.Infra.LintSnapshot) -> dict[str, t.StrSequence]:
        """Freeze lints."""
        return {tool: tuple(lines) for tool, lines in snapshot.items()}

    @staticmethod
    def _diff(py_file: Path, before: str, after: str) -> str:
        """Diff."""
        diff_lines = list(
            difflib.unified_diff(
                before.splitlines(keepends=True),
                after.splitlines(keepends=True),
                fromfile=f"a/{py_file}",
                tofile=f"b/{py_file}",
                n=3,
            )
        )
        return "".join(diff_lines[:80])

    @staticmethod
    def render_text(report: m.Infra.AccessorMigrationReport) -> str:
        """Render an accessor migration report as CLI text."""
        lines: t.MutableSequenceOf[str] = [
            "Accessor Migration",
            f"workspace: {report.workspace}",
            f"mode: {'dry-run' if report.dry_run else 'apply'}",
            f"files_scanned: {report.files_scanned}",
            f"files_with_changes: {report.files_with_changes}",
            f"automated_changes: {report.automated_change_count}",
            f"warnings: {report.warning_count}",
            f"lint_tools: {', '.join(report.lint_tools)}",
        ]
        for tool in report.lint_tools:
            lines.append(
                f"lint-totals:{tool} before={report.lint_before_totals.get(tool, 0)} after={report.lint_after_totals.get(tool, 0)} new={report.new_lint_error_totals.get(tool, 0)}"
            )
        for file_report in report.files:
            lines.append(f"\n{file_report.file}")
            for change in file_report.automated_changes:
                lines.append(
                    f"  auto:{change.line} {change.original_name} -> {change.replacement_name}",
                )
            for warning in file_report.warnings:
                target = (
                    f" -> {warning.replacement_name}"
                    if warning.replacement_name
                    else ""
                )
                lines.append(f"  warn:{warning.line} {warning.original_name}{target}")
                lines.append(f"    {warning.reason}")
            for tool in file_report.lint_tools:
                issues = tuple(file_report.lint_after.get(tool, ()))
                lines.append(f"  lint-after:{tool}")
                if not issues:
                    lines.append("    ok")
                    continue
                lines.extend(f"    {issue}" for issue in issues[:4])
            for tool in file_report.lint_tools:
                issues = tuple(file_report.new_lint_errors.get(tool, ()))
                if not issues:
                    continue
                lines.append(f"  new-lint:{tool}")
                lines.extend(f"    {issue}" for issue in issues[:4])
            if file_report.diff:
                lines.append("  diff:")
                lines.extend(
                    f"    {line}"
                    for line in file_report.diff.rstrip().splitlines()[:40]
                )
        return "\n".join(lines)


__all__: list[str] = ["FlextInfraAccessorMigrationOrchestrator"]
