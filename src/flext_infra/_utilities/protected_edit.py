"""Transactional protected file edits."""

from __future__ import annotations

import shutil
from collections.abc import Callable, MutableMapping
from pathlib import Path

from flext_infra.constants import c
from flext_infra.models import m
from flext_infra.typings import t


class FlextInfraUtilitiesProtectedEdit:
    """Preview or apply source mutations with deterministic restoration."""

    @staticmethod
    def _source_baselines(
        updates: t.MappingKV[Path, str],
    ) -> MutableMapping[Path, str | None]:
        """Capture the source state required to restore a transaction."""
        return {
            path: path.read_text(encoding=c.Cli.ENCODING_DEFAULT)
            if path.exists()
            else None
            for path in updates
        }

    @staticmethod
    def _restore_sources(before_sources: t.MappingKV[Path, str | None]) -> None:
        """Restore captured sources, including removal of preview-created files."""
        for path, original_source in before_sources.items():
            if original_source is None:
                if path.exists():
                    path.unlink()
                continue
            path.write_text(original_source, encoding=c.Cli.ENCODING_DEFAULT)

    @staticmethod
    def _relative_path(path: Path, workspace: Path) -> Path:
        """Return a stable transaction-relative path when possible."""
        try:
            return path.relative_to(workspace)
        except ValueError:
            return path

    @staticmethod
    def _preserve_backup(path: Path) -> Path | None:
        """Preserve one recoverable sibling copy before mutation."""
        if not path.exists():
            return None
        backup_path = path.with_suffix(path.suffix + c.Infra.SAFE_EXECUTION_BAK_SUFFIX)
        if not backup_path.exists():
            shutil.copy2(path, backup_path)
        return backup_path

    @classmethod
    def _backup_paths(
        cls, updates: t.MappingKV[Path, str], *, keep_backup: bool
    ) -> MutableMapping[Path, Path]:
        """Preserve requested backups for files that already exist."""
        if not keep_backup:
            return {}
        return {
            path: backup_path
            for path in updates
            if (backup_path := cls._preserve_backup(path)) is not None
        }

    @classmethod
    def _backup_reports(
        cls, backup_paths: t.MappingKV[Path, Path], workspace: Path
    ) -> t.StrSequence:
        """Render backup paths relative to their transaction root."""
        return tuple(
            f"  BACKUP {cls._relative_path(path, workspace)} -> {backup.name}"
            for path, backup in backup_paths.items()
        )

    @classmethod
    def preview_source_writes(
        cls,
        updates: t.MappingKV[Path, str],
        *,
        post_write: Callable[[], None] | None = None,
    ) -> None:
        """Preview multiple source writes and always restore captured state."""
        if not updates:
            return
        normalized_updates = {
            path.resolve(): content
            for path, content in sorted(updates.items(), key=lambda item: str(item[0]))
        }
        before_sources = cls._source_baselines(normalized_updates)
        try:
            for path, updated_source in normalized_updates.items():
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(updated_source, encoding=c.Cli.ENCODING_DEFAULT)
            if post_write is not None:
                post_write()
        finally:
            cls._restore_sources(before_sources)

    @classmethod
    def protected_file_edit(
        cls, path: Path, *, request: m.Infra.ProtectedFileEditRequest
    ) -> t.StrSequence:
        """Apply one callback and restore the original state if it raises."""
        backup_path = cls._preserve_backup(path) if request.keep_backup else None
        edit_completed = False
        try:
            request.edit_fn()
            edit_completed = True
        finally:
            if not edit_completed:
                request.restore_fn()
        if backup_path is None:
            return ()
        return (
            (
                f"  BACKUP {cls._relative_path(path, request.workspace)}"
                f" -> {backup_path.name}"
            ),
        )

    @classmethod
    def protected_source_write(
        cls, path: Path, *, request: m.Infra.ProtectedSourceWriteRequest
    ) -> t.StrSequence:
        """Write one existing source transactionally."""
        original_source = path.read_text(encoding=c.Cli.ENCODING_DEFAULT)
        if request.updated_source == original_source:
            return ()

        def _write_updated() -> None:
            path.write_text(request.updated_source, encoding=c.Cli.ENCODING_DEFAULT)

        def _restore_original() -> None:
            path.write_text(original_source, encoding=c.Cli.ENCODING_DEFAULT)

        return cls.protected_file_edit(
            path,
            request=m.Infra.ProtectedFileEditRequest(
                workspace=request.workspace,
                edit_fn=_write_updated,
                restore_fn=_restore_original,
                keep_backup=request.keep_backup,
            ),
        )

    @classmethod
    def protected_source_writes(
        cls,
        updates: t.MappingKV[Path, str],
        *,
        request: m.Infra.ProtectedSourceWritesRequest,
    ) -> t.StrSequence:
        """Write multiple sources and restore all paths if a callback raises."""
        if not updates:
            return ()
        normalized_updates = {
            path.resolve(): content
            for path, content in sorted(updates.items(), key=lambda item: str(item[0]))
        }
        before_sources = cls._source_baselines(normalized_updates)
        backup_paths = cls._backup_paths(
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
                cls._restore_sources(before_sources)
        return cls._backup_reports(backup_paths, request.workspace)


__all__: list[str] = ["FlextInfraUtilitiesProtectedEdit"]
