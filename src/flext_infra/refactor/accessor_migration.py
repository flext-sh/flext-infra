"""Accessor migration orchestration for get_/set_/is_ modernization."""

from __future__ import annotations

import ast
import difflib
import json
from collections.abc import MutableSequence, Sequence
from pathlib import Path
from tempfile import TemporaryDirectory
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
        default="lint,pyrefly,mypy,pyright",
        description="Comma-separated lint gates for preview/apply validation",
    )

    _AUTOMATED_RULES: ClassVar[tuple[tuple[str, str, str], ...]] = (
        (
            "def is_success_result($$$ARGS):",
            "def successful_result($$$ARGS):",
            "Rename result helper to the canonical success helper",
        ),
        (
            "def is_failure_result($$$ARGS):",
            "def failed_result($$$ARGS):",
            "Rename result helper to the canonical failure helper",
        ),
        (
            "from $MOD import is_success_result",
            "from $MOD import successful_result",
            "Rewrite result helper import to the canonical success helper",
        ),
        (
            "from $MOD import is_failure_result",
            "from $MOD import failed_result",
            "Rewrite result helper import to the canonical failure helper",
        ),
        (
            "is_success_result($$$ARGS)",
            "successful_result($$$ARGS)",
            "Rewrite result helper call to the canonical success helper",
        ),
        (
            "is_failure_result($$$ARGS)",
            "failed_result($$$ARGS)",
            "Rewrite result helper call to the canonical failure helper",
        ),
        (
            "$TARGET.is_success_result($$$ARGS)",
            "$TARGET.successful_result($$$ARGS)",
            "Rewrite qualified result helper call to the canonical success helper",
        ),
        (
            "$TARGET.is_failure_result($$$ARGS)",
            "$TARGET.failed_result($$$ARGS)",
            "Rewrite qualified result helper call to the canonical failure helper",
        ),
        (
            "$VALUE.is_success",
            "$VALUE.success",
            "Rename boolean result predicate to the canonical success field",
        ),
        (
            "$VALUE.is_failure",
            "$VALUE.failure",
            "Rename boolean result predicate to the canonical failure field",
        ),
    )
    _AUTOMATED_NAMES: ClassVar[frozenset[str]] = frozenset({
        "is_success_result",
        "is_failure_result",
    })

    @property
    def project_names(self) -> t.StrSequence:
        return [name.strip() for name in self.projects if name.strip()]

    @property
    def gate_names(self) -> t.StrSequence:
        return [gate.strip() for gate in self.gates.split(",") if gate.strip()]

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
        for py_file in iter_result.value:
            file_report = self._process_file(py_file)
            automated_change_count += len(file_report.automated_changes)
            warning_count += len(file_report.warnings)
            if file_report.automated_changes:
                files_with_changes += 1
            if (file_report.automated_changes or file_report.warnings) and len(
                previews
            ) < self.preview_limit:
                previews.append(file_report)
        return r[m.Infra.AccessorMigrationReport].ok(
            m.Infra.AccessorMigrationReport(
                workspace=str(self.workspace_root),
                dry_run=self.dry_run,
                files_scanned=len(iter_result.value),
                files_with_changes=files_with_changes,
                automated_change_count=automated_change_count,
                warning_count=warning_count,
                files=tuple(previews),
            )
        )

    def _process_file(self, py_file: Path) -> m.Infra.AccessorMigrationFile:
        source = py_file.read_text(encoding=c.Infra.ENCODING_DEFAULT)
        updated_source, automated_changes = self._apply_automated_rewrites(
            py_file, source
        )
        warnings = self._collect_manual_warnings(py_file, source)
        lint_before: dict[str, tuple[str, ...]] = {}
        lint_after: dict[str, tuple[str, ...]] = {}
        new_lint_errors: dict[str, tuple[str, ...]] = {}
        if automated_changes:
            if self.dry_run:
                before, after = FlextInfraUtilitiesProtectedEdit.preview_source_lint(
                    py_file,
                    self.workspace_root,
                    updated_source=updated_source,
                    gates=self.gate_names,
                )
            else:
                before = FlextInfraUtilitiesProtectedEdit.lint_snapshot(
                    py_file,
                    self.workspace_root,
                    gates=self.gate_names,
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
                after = FlextInfraUtilitiesProtectedEdit.lint_snapshot(
                    py_file,
                    self.workspace_root,
                    gates=self.gate_names,
                )
            lint_before = self._freeze_lints(before)
            lint_after = self._freeze_lints(after)
            new_lint_errors = self._freeze_lints(
                FlextInfraUtilitiesProtectedEdit.lint_new_errors(before, after)
            )
        return m.Infra.AccessorMigrationFile(
            file=str(py_file),
            automated_changes=tuple(automated_changes),
            warnings=tuple(warnings),
            diff=self._diff(py_file, source, updated_source)
            if automated_changes
            else "",
            lint_before=lint_before,
            lint_after=lint_after,
            new_lint_errors=new_lint_errors,
        )

    def _apply_automated_rewrites(
        self,
        py_file: Path,
        source: str,
    ) -> tuple[str, Sequence[m.Infra.AccessorMigrationChange]]:
        with TemporaryDirectory(prefix="flext-accessor-") as tmp_dir:
            temp_file = Path(tmp_dir) / py_file.name
            temp_file.write_text(source, encoding=c.Infra.ENCODING_DEFAULT)
            changes: MutableSequence[m.Infra.AccessorMigrationChange] = []
            for pattern, rewrite, reason in self._AUTOMATED_RULES:
                matches = self._sg_matches(temp_file, pattern, rewrite)
                if not matches:
                    continue
                for match in matches:
                    line = int(match["range"]["start"]["line"]) + 1
                    original_name = str(match.get("text", "")).split("(", 1)[0].strip()
                    changes.append(
                        m.Infra.AccessorMigrationChange(
                            file=str(py_file),
                            line=line,
                            original_name=original_name or pattern,
                            replacement_name=str(match.get("replacement", rewrite)),
                            automated=True,
                            reason=reason,
                        )
                    )
                self._sg_apply(temp_file, pattern, rewrite)
            updated_source = temp_file.read_text(encoding=c.Infra.ENCODING_DEFAULT)
        return updated_source, changes

    def _collect_manual_warnings(
        self,
        py_file: Path,
        source: str,
    ) -> Sequence[m.Infra.AccessorMigrationChange]:
        try:
            tree = ast.parse(source)
        except SyntaxError as exc:
            return [
                m.Infra.AccessorMigrationChange(
                    file=str(py_file),
                    line=exc.lineno or 0,
                    original_name="syntax_error",
                    replacement_name="",
                    automated=False,
                    reason=f"Manual review required: file does not parse ({exc.msg})",
                )
            ]
        parents = {
            id(child): parent
            for parent in ast.walk(tree)
            for child in ast.iter_child_nodes(parent)
        }
        warnings: MutableSequence[m.Infra.AccessorMigrationChange] = []
        for node in ast.walk(tree):
            if not isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
                continue
            if not isinstance(parents.get(id(node)), ast.Module | ast.ClassDef):
                continue
            if node.name.startswith("_") or node.name in self._AUTOMATED_NAMES:
                continue
            if node.name.startswith("get_"):
                required = [
                    arg.arg for arg in node.args.args if arg.arg not in {"self", "cls"}
                ]
                reason = (
                    f"Public getter without external input: migrate to field or @computed_field '{node.name[4:]}'"
                    if not required
                    and not node.args.kwonlyargs
                    and node.args.vararg is None
                    and node.args.kwarg is None
                    else f"Public getter with inputs: classify manually as resolve_{node.name[4:]}(...) or fetch_{node.name[4:]}(...)"
                )
                replacement = node.name[4:] if not required else ""
            elif node.name.startswith("set_"):
                reason = "Public setter: migrate to validated assignment, model_copy(update=...), or a domain verb"
                replacement = ""
            elif node.name.startswith("is_"):
                reason = f"Public predicate: rename to boolean/status field '{node.name[3:]}' or a canonical status enum"
                replacement = node.name[3:]
            else:
                continue
            warnings.append(
                m.Infra.AccessorMigrationChange(
                    file=str(py_file),
                    line=node.lineno,
                    original_name=node.name,
                    replacement_name=replacement,
                    automated=False,
                    reason=reason,
                )
            )
        return warnings

    def _sg_matches(
        self,
        file_path: Path,
        pattern: str,
        rewrite: str,
    ) -> Sequence[dict[str, object]]:
        result = u.Cli.run_raw(
            [
                c.Infra.SG,
                "run",
                "--pattern",
                pattern,
                "--rewrite",
                rewrite,
                "--lang",
                "python",
                "--json=compact",
                str(file_path),
            ],
            cwd=file_path.parent,
            timeout=c.Infra.TIMEOUT_SHORT,
        )
        if result.failure:
            return []
        try:
            return json.loads(result.value.stdout or "[]")
        except json.JSONDecodeError:
            return []

    def _sg_apply(self, file_path: Path, pattern: str, rewrite: str) -> None:
        _ = u.Cli.run_raw(
            [
                c.Infra.SG,
                "run",
                "--pattern",
                pattern,
                "--rewrite",
                rewrite,
                "--lang",
                "python",
                "-U",
                str(file_path),
            ],
            cwd=file_path.parent,
            timeout=c.Infra.TIMEOUT_SHORT,
        )

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
        lines: MutableSequence[str] = [
            "Accessor Migration",
            f"workspace: {report.workspace}",
            f"mode: {'dry-run' if report.dry_run else 'apply'}",
            f"files_scanned: {report.files_scanned}",
            f"files_with_changes: {report.files_with_changes}",
            f"automated_changes: {report.automated_change_count}",
            f"warnings: {report.warning_count}",
        ]
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
            for tool, issues in file_report.lint_after.items():
                lines.append(f"  lint-after:{tool}")
                if not issues:
                    lines.append("    ok")
                    continue
                lines.extend(f"    {issue}" for issue in issues[:4])
            for tool, issues in file_report.new_lint_errors.items():
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
