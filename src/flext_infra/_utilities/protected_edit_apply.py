"""Apply, backup, and structural validation for protected source edits."""

from __future__ import annotations

import difflib
import shutil
from collections.abc import MutableMapping
from pathlib import Path

from flext_infra._utilities.protected_edit_preview import (
    FlextInfraUtilitiesProtectedEditPreview,
)
from flext_infra.constants import c
from flext_infra.models import m
from flext_infra.typings import t


class FlextInfraUtilitiesProtectedEditApply(FlextInfraUtilitiesProtectedEditPreview):
    """Apply, rollback, backup, and structural validation for protected edits."""

    @staticmethod
    def _backup_paths_for_updates(
        updates: t.MappingKV[Path, str], *, keep_backup: bool
    ) -> MutableMapping[Path, Path]:
        """Backup paths for updates."""
        if not keep_backup:
            return {}
        backup_paths: MutableMapping[Path, Path] = {}
        for path in updates:
            backup_path = FlextInfraUtilitiesProtectedEditApply._preserve_backup(path)
            if backup_path is not None:
                backup_paths[path] = backup_path
        return backup_paths

    @staticmethod
    def _protected_write_reports(
        updates: t.MappingKV[Path, str],
        before_sources: t.MappingKV[Path, str | None],
        before_lints: t.MappingKV[Path, t.Infra.LintSnapshot],
        request: m.Infra.ProtectedSourceWritesRequest,
    ) -> t.Infra.EditResult:
        """Protected write reports."""
        reports: list[str] = []
        failed = False
        after_lints = FlextInfraUtilitiesProtectedEditApply.lint_snapshots(
            tuple(updates), request.workspace
        )
        for path in updates:
            new_errors = FlextInfraUtilitiesProtectedEditApply.lint_new_errors(
                before_lints[path], after_lints[path]
            )
            if not new_errors:
                continue
            failed = True
            reports.extend(
                FlextInfraUtilitiesProtectedEditApply._reverted_report_lines(
                    path, request.workspace, before_sources[path] or "", new_errors
                )
            )
        return (not failed, reports)

    @staticmethod
    def _backup_reports(
        backup_paths: t.MappingKV[Path, Path], workspace: Path
    ) -> list[str]:
        """Backup reports."""
        return [
            "  BACKUP "
            f"{FlextInfraUtilitiesProtectedEditApply._relative_path(path, workspace)}"
            f" -> {backup.name}"
            for path, backup in backup_paths.items()
        ]

    @staticmethod
    def _preserve_backup(py_file: Path) -> Path | None:
        """Preserve backup."""
        if not py_file.exists():
            return None
        backup_path = py_file.with_suffix(
            py_file.suffix + c.Infra.SAFE_EXECUTION_BAK_SUFFIX
        )
        if not backup_path.exists():
            shutil.copy2(py_file, backup_path)
        return backup_path

    @staticmethod
    def protected_file_edit(
        py_file: Path, *, request: m.Infra.ProtectedFileEditRequest
    ) -> t.Infra.EditResult:
        """Apply one edit, validate syntax deltas, and restore on failure."""
        rel = FlextInfraUtilitiesProtectedEditApply._relative_path(
            py_file, request.workspace
        )
        before = FlextInfraUtilitiesProtectedEditApply.lint_snapshot(
            py_file, request.workspace
        )
        backup_path = (
            FlextInfraUtilitiesProtectedEditApply._preserve_backup(py_file)
            if request.keep_backup
            else None
        )

        def _restore() -> None:
            """Restore."""
            if request.restore_fn is not None:
                request.restore_fn()
                return
            py_file.write_text(request.before_source, encoding=c.Cli.ENCODING_DEFAULT)

        edit_completed = False
        try:
            request.edit_fn()
            edit_completed = True
        finally:
            if not edit_completed:
                _restore()

        new_errors = FlextInfraUtilitiesProtectedEditApply.lint_new_errors(
            before,
            FlextInfraUtilitiesProtectedEditApply.lint_snapshot(
                py_file, request.workspace
            ),
        )
        if not new_errors:
            if backup_path is None:
                return (True, [])
            return (True, [f"  BACKUP {rel} -> {backup_path.name}"])

        modified = py_file.read_text(encoding=c.Cli.ENCODING_DEFAULT)
        diff = list(
            difflib.unified_diff(
                request.before_source.splitlines(keepends=True),
                modified.splitlines(keepends=True),
                fromfile=f"a/{rel}",
                tofile=f"b/{rel}",
                n=3,
            )
        )
        _restore()
        report: t.MutableSequenceOf[str] = [f"  REVERTED {rel}:"]
        report.extend(f"    {line.rstrip()}" for line in diff[:30])
        for validator, messages in new_errors.items():
            report.extend((
                f"    NEW {validator} errors:",
                *(f"      {message}" for message in messages[:5]),
            ))
        return (False, report)

    @staticmethod
    def protected_source_write(
        py_file: Path, *, request: m.Infra.ProtectedSourceWriteRequest
    ) -> t.Infra.EditResult:
        """Write validated source content with protected validation and rollback."""
        original_source = py_file.read_text(encoding=c.Cli.ENCODING_DEFAULT)
        if request.updated_source == original_source:
            return (True, [])

        def _write_updated() -> None:
            """Write updated."""
            py_file.write_text(request.updated_source, encoding=c.Cli.ENCODING_DEFAULT)

        def _restore_original() -> None:
            """Restore original."""
            py_file.write_text(original_source, encoding=c.Cli.ENCODING_DEFAULT)

        return FlextInfraUtilitiesProtectedEditApply.protected_file_edit(
            py_file,
            request=m.Infra.ProtectedFileEditRequest(
                workspace=request.workspace,
                before_source=original_source,
                edit_fn=_write_updated,
                restore_fn=_restore_original,
                keep_backup=request.keep_backup,
            ),
        )

    @staticmethod
    def protected_source_writes(
        updates: t.MappingKV[Path, str],
        *,
        request: m.Infra.ProtectedSourceWritesRequest,
    ) -> t.Infra.EditResult:
        """Write multiple files transactionally with syntax delta validation."""
        if not updates:
            return (True, [])

        normalized_updates = {
            path.resolve(): content
            for path, content in sorted(updates.items(), key=lambda item: str(item[0]))
        }
        before_sources, before_lints = (
            FlextInfraUtilitiesProtectedEditApply._preview_write_baselines(
                normalized_updates, request.workspace
            )
        )
        backup_paths = FlextInfraUtilitiesProtectedEditApply._backup_paths_for_updates(
            normalized_updates, keep_backup=request.keep_backup
        )

        write_completed = False
        try:
            for path, updated_source in normalized_updates.items():
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(updated_source, encoding=c.Cli.ENCODING_DEFAULT)
            if request.post_write is not None:
                request.post_write()
            write_completed = True
        finally:
            if not write_completed:
                FlextInfraUtilitiesProtectedEditApply._restore_preview_sources(
                    before_sources
                )

        ok, reports = FlextInfraUtilitiesProtectedEditApply._protected_write_reports(
            normalized_updates, before_sources, before_lints, request
        )
        if not ok:
            FlextInfraUtilitiesProtectedEditApply._restore_preview_sources(
                before_sources
            )
            return (False, reports)

        if not backup_paths:
            return (True, [])
        return (
            True,
            FlextInfraUtilitiesProtectedEditApply._backup_reports(
                backup_paths, request.workspace
            ),
        )


__all__: list[str] = ["FlextInfraUtilitiesProtectedEditApply"]
