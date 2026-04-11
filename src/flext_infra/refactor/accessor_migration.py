"""Accessor migration orchestration for get_/set_/is_ modernization."""

from __future__ import annotations

import difflib
import io
from collections.abc import MutableSequence, Sequence
from operator import itemgetter
from pathlib import Path
from tokenize import NAME, generate_tokens
from typing import ClassVar, override

from pydantic import Field

from flext_core import r
from flext_infra import c, m, s, t, u
from flext_infra._utilities.protected_edit import FlextInfraUtilitiesProtectedEdit


class FlextInfraAccessorMigrationOrchestrator(s[m.Infra.AccessorMigrationReport]):
    """Dry-run/apply orchestrator for public accessor migration candidates."""

    projects: t.StrSequence = Field(
        default_factory=list,
        description="Workspace projects to scan; empty means all discovered projects",
    )
    preview_limit: int = Field(
        default=10,
        description="Maximum number of file previews to include in the report",
    )
    gates: str = Field(
        default=c.Infra.SAFE_EXECUTION_DEFAULT_GATES,
        description="Comma-separated lint gates for preview/apply validation",
    )

    _AUTOMATED_RULES: ClassVar[tuple[m.Infra.AccessorMigrationRule, ...]] = (
        m.Infra.AccessorMigrationRule(
            source_name="is_success_result",
            replacement_name="successful_result",
            reason="Rename result helper to the canonical success helper",
            origin="flext_core.result",
        ),
        m.Infra.AccessorMigrationRule(
            source_name="is_failure_result",
            replacement_name="failed_result",
            reason="Rename result helper to the canonical failure helper",
            origin="flext_core.result",
        ),
        m.Infra.AccessorMigrationRule(
            source_name="is_success_result",
            replacement_name="successful_result",
            reason="Rewrite result helper import to the canonical success helper",
            origin="flext_core.result",
        ),
        m.Infra.AccessorMigrationRule(
            source_name="is_failure_result",
            replacement_name="failed_result",
            reason="Rewrite result helper import to the canonical failure helper",
            origin="flext_core.result",
        ),
        m.Infra.AccessorMigrationRule(
            source_name="is_success_result",
            replacement_name="successful_result",
            reason="Rewrite result helper call to the canonical success helper",
            origin="flext_core.result",
        ),
        m.Infra.AccessorMigrationRule(
            source_name="is_failure_result",
            replacement_name="failed_result",
            reason="Rewrite result helper call to the canonical failure helper",
            origin="flext_core.result",
        ),
        m.Infra.AccessorMigrationRule(
            source_name="is_success_result",
            replacement_name="successful_result",
            reason="Rewrite qualified result helper call to the canonical success helper",
            origin="flext_core.result",
        ),
        m.Infra.AccessorMigrationRule(
            source_name="is_failure_result",
            replacement_name="failed_result",
            reason="Rewrite qualified result helper call to the canonical failure helper",
            origin="flext_core.result",
        ),
        m.Infra.AccessorMigrationRule(
            source_name="is_success",
            replacement_name="success",
            reason="Rename boolean result predicate to the canonical success field",
            origin="flext_core.result",
        ),
        m.Infra.AccessorMigrationRule(
            source_name="is_failure",
            replacement_name="failure",
            reason="Rename boolean result predicate to the canonical failure field",
            origin="flext_core.result",
        ),
        m.Infra.AccessorMigrationRule(
            source_name="set_attribute",
            replacement_name="update_attribute",
            reason="Rewrite attribute mutator to the canonical update verb",
            origin="flext_core.logging",
        ),
        m.Infra.AccessorMigrationRule(
            source_name="get_beartype_conf",
            replacement_name="build_beartype_conf",
            reason="Rewrite beartype config accessor to the canonical build verb",
            origin="flext_core.beartype",
        ),
        m.Infra.AccessorMigrationRule(
            source_name="get_message_route",
            replacement_name="resolve_message_route",
            reason="Rewrite route accessor to the canonical resolve helper",
            origin="flext_core.dispatcher",
        ),
        m.Infra.AccessorMigrationRule(
            source_name="set_container_adapter",
            replacement_name="container_set_adapter",
            reason="Rewrite type adapter accessor to the canonical container_* name",
            origin="flext_core.typings",
        ),
        m.Infra.AccessorMigrationRule(
            source_name="set_str_adapter",
            replacement_name="string_set_adapter",
            reason="Rewrite type adapter accessor to the canonical string_* name",
            origin="flext_core.typings",
        ),
        m.Infra.AccessorMigrationRule(
            source_name="set_scalar_adapter",
            replacement_name="scalar_set_adapter",
            reason="Rewrite type adapter accessor to the canonical scalar_* name",
            origin="flext_core.typings",
        ),
        m.Infra.AccessorMigrationRule(
            source_name="get_logger",
            replacement_name="fetch_logger",
            reason="Rewrite logger facade accessor to the canonical fetch verb",
            origin="flext_core.loggings",
        ),
        m.Infra.AccessorMigrationRule(
            source_name="get_logger",
            replacement_name="fetch_logger",
            reason="Rewrite logger utility accessor to the canonical fetch verb",
            origin="flext_core.loggings",
        ),
        m.Infra.AccessorMigrationRule(
            source_name="is_structlog_configured",
            replacement_name="structlog_configured",
            reason="Rewrite structlog predicate to the canonical boolean helper",
            origin="flext_core.loggings",
        ),
        m.Infra.AccessorMigrationRule(
            source_name="get_log_level_from_config",
            replacement_name="resolve_log_level_from_config",
            reason="Rewrite log-level accessor to the canonical resolve helper",
            origin="flext_core.configuration",
        ),
        m.Infra.AccessorMigrationRule(
            source_name="get_version_string",
            replacement_name="resolve_version_string",
            reason="Rewrite version accessor to the canonical resolve helper",
            origin="flext_core.version",
        ),
        m.Infra.AccessorMigrationRule(
            source_name="get_version_info",
            replacement_name="resolve_version_info",
            reason="Rewrite version info accessor to the canonical resolve helper",
            origin="flext_core.version",
        ),
        m.Infra.AccessorMigrationRule(
            source_name="get_package_info",
            replacement_name="resolve_package_info",
            reason="Rewrite package info accessor to the canonical resolve helper",
            origin="flext_core.version",
        ),
        m.Infra.AccessorMigrationRule(
            source_name="is_version_at_least",
            replacement_name="version_at_least",
            reason="Rewrite version predicate to the canonical boolean helper",
            origin="flext_core.version",
        ),
    )
    _AUTOMATED_NAMES: ClassVar[frozenset[str]] = frozenset({
        "get_beartype_conf",
        "get_message_route",
        "is_failure",
        "is_success",
        "is_success_result",
        "is_failure_result",
        "set_attribute",
        "set_container_adapter",
        "set_scalar_adapter",
        "set_str_adapter",
    })

    @property
    def project_names(self) -> t.StrSequence:
        """Return normalized selected project names."""
        return [name.strip() for name in self.projects if name.strip()]

    @property
    def gate_names(self) -> t.StrSequence:
        """Return normalized lint gate names."""
        return [gate.strip() for gate in self.gates.split(",") if gate.strip()]

    @property
    def lint_tool_names(self) -> t.StrSequence:
        """Return selected lint tool names resolved from gate names."""
        return FlextInfraUtilitiesProtectedEdit.selected_lint_tool_names(
            self.gate_names,
        )

    @override
    def execute(self) -> r[m.Infra.AccessorMigrationReport]:
        resolved = u.Infra.resolve_projects(self.workspace_root, self.project_names)
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
        previews: MutableSequence[m.Infra.AccessorMigrationFile] = []
        files_with_changes = 0
        automated_change_count = 0
        warning_count = 0
        lint_before_totals: dict[str, int] = {}
        lint_after_totals: dict[str, int] = {}
        new_lint_error_totals: dict[str, int] = {}
        with u.Infra.open_project(self.workspace_root) as rope_project:
            for py_file in iter_result.value:
                source = py_file.read_text(encoding=c.Infra.ENCODING_DEFAULT)
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

    @staticmethod
    def _accumulate_lint_totals(
        totals: dict[str, int],
        snapshot: t.Infra.LintSnapshot,
    ) -> None:
        for tool, lines in snapshot.items():
            totals[tool] = totals.get(tool, 0) + len(tuple(lines))

    def _process_file(
        self,
        py_file: Path,
        *,
        source: str,
        updated_source: str,
        automated_changes: Sequence[m.Infra.AccessorMigrationChange],
        warnings: MutableSequence[m.Infra.AccessorMigrationChange],
        include_preview: bool,
    ) -> m.Infra.AccessorMigrationFile:
        lint_before: dict[str, tuple[str, ...]] = {}
        lint_after: dict[str, tuple[str, ...]] = {}
        new_lint_errors: dict[str, tuple[str, ...]] = {}
        if automated_changes:
            if self.dry_run and include_preview:
                before, after = FlextInfraUtilitiesProtectedEdit.preview_source_lint(
                    py_file,
                    self.workspace_root,
                    updated_source=updated_source,
                    gates=self.gate_names,
                )
            elif not self.dry_run:
                before: t.Infra.LintSnapshot = {}
                before = (
                    FlextInfraUtilitiesProtectedEdit.lint_snapshot(
                        py_file,
                        self.workspace_root,
                        gates=self.gate_names,
                    )
                    if include_preview
                    else {}
                )
                ok, report = FlextInfraUtilitiesProtectedEdit.protected_source_write(
                    py_file,
                    workspace=self.workspace_root,
                    updated_source=updated_source,
                    gates=self.gate_names,
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
                after: t.Infra.LintSnapshot = {}
                after = (
                    FlextInfraUtilitiesProtectedEdit.lint_snapshot(
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
                    FlextInfraUtilitiesProtectedEdit.lint_new_errors(before, after)
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
    ) -> tuple[str, Sequence[m.Infra.AccessorMigrationChange]]:
        resource = u.Infra.get_resource_from_path(rope_project, py_file)
        if resource is None:
            return source, ()
        updated_source = source
        changes: MutableSequence[m.Infra.AccessorMigrationChange] = []
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
    ) -> tuple[str, Sequence[m.Infra.AccessorMigrationChange]]:
        token_lines: MutableSequence[m.Infra.AccessorMigrationChange] = []
        rewrite_ranges: MutableSequence[tuple[int, int, str]] = []
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
        source_lines = source.splitlines(keepends=True)
        line_offset = sum(len(item) for item in source_lines[: line - 1])
        return line_offset + column

    def _collect_manual_warnings(
        self,
        py_file: Path,
        source: str,
    ) -> Sequence[m.Infra.AccessorMigrationChange]:
        lines = source.splitlines()
        warnings: MutableSequence[m.Infra.AccessorMigrationChange] = []
        scope_stack: MutableSequence[tuple[str, int]] = []
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
            signature = stripped.split(":", maxsplit=1)[0]
            signature_args = (
                signature.split("(", maxsplit=1)[1].rsplit(")", maxsplit=1)[0]
                if "(" in signature and ")" in signature
                else ""
            )
            normalized_args = [
                arg.strip().split(":", maxsplit=1)[0].split("=", maxsplit=1)[0]
                for arg in signature_args.split(",")
                if arg.strip()
            ]
            required = [name for name in normalized_args if name not in {"self", "cls"}]
            has_varargs = any(name.startswith("*") for name in normalized_args)
            if function_name.startswith("get_"):
                reason = (
                    f"Public getter without external input: migrate to field or @computed_field '{function_name[4:]}'"
                    if not required and not has_varargs
                    else f"Public getter with inputs: classify manually as resolve_{function_name[4:]}(...) or fetch_{function_name[4:]}(...)"
                )
                replacement = function_name[4:] if not required else ""
            elif function_name.startswith("set_"):
                reason = "Public setter: migrate to validated assignment, model_copy(update=...), or a domain verb"
                replacement = ""
            elif function_name.startswith("is_"):
                reason = f"Public predicate: rename to boolean/status field '{function_name[3:]}' or a canonical status enum"
                replacement = function_name[3:]
            else:
                continue
            warnings.append(
                m.Infra.AccessorMigrationChange(
                    file=str(py_file),
                    line=line_index,
                    original_name=function_name,
                    replacement_name=replacement,
                    automated=False,
                    reason=reason,
                )
            )
        return warnings

    @staticmethod
    def _freeze_lints(snapshot: t.Infra.LintSnapshot) -> dict[str, tuple[str, ...]]:
        return {tool: tuple(lines) for tool, lines in snapshot.items()}

    @staticmethod
    def _diff(py_file: Path, before: str, after: str) -> str:
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
        lines: MutableSequence[str] = [
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


__all__ = ["FlextInfraAccessorMigrationOrchestrator"]
