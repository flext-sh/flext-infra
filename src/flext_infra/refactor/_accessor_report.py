"""Accessor per-file write and report rendering."""

from __future__ import annotations

import difflib
from typing import TYPE_CHECKING

from flext_infra import m, u

if TYPE_CHECKING:
    from pathlib import Path

    from flext_infra import t


class FlextInfraAccessorMigrationReportMixin:
    """Per-file transactional write and CLI report rendering.

    Composed into FlextInfraAccessorMigrationOrchestrator via inheritance; the
    facade provides ``dry_run`` and ``workspace_root`` through MRO (declared
    below for static resolution).
    """

    if TYPE_CHECKING:
        dry_run: bool
        workspace_root: Path

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
        if automated_changes and not self.dry_run:
            u.Infra.protected_source_write(
                py_file,
                request=m.Infra.ProtectedSourceWriteRequest(
                    workspace=self.workspace_root, updated_source=updated_source
                ),
            )
        return m.Infra.AccessorMigrationFile(
            file=str(py_file),
            automated_changes=tuple(automated_changes),
            warnings=tuple(warnings),
            diff=self._diff(py_file, source, updated_source)
            if automated_changes and include_preview
            else "",
        )

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
        ]
        for file_report in report.files:
            lines.append(f"\n{file_report.file}")
            for change in file_report.automated_changes:
                lines.append(
                    f"  auto:{change.line} {change.original_name} -> {change.replacement_name}"
                )
            for warning in file_report.warnings:
                target = (
                    f" -> {warning.replacement_name}"
                    if warning.replacement_name
                    else ""
                )
                lines.append(f"  warn:{warning.line} {warning.original_name}{target}")
                lines.append(f"    {warning.reason}")
            if file_report.diff:
                lines.append("  diff:")
                lines.extend(
                    f"    {line}"
                    for line in file_report.diff.rstrip().splitlines()[:40]
                )
        return "\n".join(lines)


__all__: list[str] = ["FlextInfraAccessorMigrationReportMixin"]
