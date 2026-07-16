"""Workspace-wide MRO migration orchestration and reference rewriting."""

from __future__ import annotations

from collections.abc import MutableMapping
from pathlib import Path
from typing import ClassVar

from flext_infra import m, p, t, u
from flext_infra.refactor._mro_import_collect import (
    FlextInfraRefactorMROImportRewriterFileOpsMixin,
)
from flext_infra.transformers.mro_symbol_propagator import (
    FlextInfraRefactorMROSymbolPropagator,
)


class FlextInfraRefactorMROImportRewriter(
    FlextInfraRefactorMROImportRewriterFileOpsMixin
):
    """Rewrite imports/references after MRO symbol absorption into facade classes."""

    class RewriteFilesInput(m.BaseModel):
        """Typed input envelope for workspace rewrite execution."""

        model_config: ClassVar[t.ConfigDict] = m.ConfigDict(
            arbitrary_types_allowed=True
        )

        workspace_root: Path
        file_moves: t.MappingKV[Path, t.MappingKV[str, t.Pair[str, t.StrMapping]]]
        pending_sources: t.MappingKV[Path, str]
        apply: bool
        gates: t.StrSequence | None = None

    @classmethod
    def migrate_workspace(
        cls,
        *,
        workspace_root: Path,
        scan_results: t.SequenceOf[p.Infra.MROScanReport],
        apply: bool,
        project_names: t.StrSequence | None = None,
        gates: t.StrSequence | None = None,
    ) -> t.Triple[
        t.SequenceOf[p.Infra.MROFileMigration],
        t.SequenceOf[p.Infra.MRORewriteResult],
        t.StrSequence,
    ]:
        """Transform migrated files and propagate consumer rewrites across the workspace."""
        errors: list[str] = []
        migrations: list[p.Infra.MROFileMigration] = []
        module_moves: MutableMapping[str, t.Pair[str, t.StrMapping]] = {}
        module_source_paths: MutableMapping[str, Path] = {}
        pending_sources: MutableMapping[Path, str] = {}
        for scan_result in scan_results:
            try:
                updated_source, migration, symbol_map = u.Infra.migrate_file(
                    scan_result=scan_result
                )
            except Exception as exc:
                errors.append(f"{scan_result.file}: {exc}")
                continue
            if not migration.moved_symbols:
                continue
            migrations.append(migration)
            source_path = Path(scan_result.file).resolve()
            pending_sources[source_path] = updated_source
            module_moves[scan_result.module] = (
                scan_result.facade_alias or "c",
                symbol_map,
            )
            module_source_paths[scan_result.module] = source_path
        if apply:
            write_errors, failed_paths = cls._write_pending_sources(
                workspace_root=workspace_root,
                pending_sources=pending_sources,
                gates=gates,
            )
            errors.extend(write_errors)
            if failed_paths:
                failed_set = frozenset(failed_paths)
                migrations = [
                    migration
                    for migration in migrations
                    if Path(migration.file).resolve() not in failed_set
                ]
                module_moves = {
                    module_name: move
                    for module_name, move in module_moves.items()
                    if module_source_paths.get(module_name) not in failed_set
                }
        rewrites, rewrite_errors = cls.rewrite_workspace(
            workspace_root=workspace_root,
            module_moves=module_moves,
            pending_sources=pending_sources,
            apply=apply,
            project_names=project_names,
            gates=gates,
        )
        errors.extend(rewrite_errors)
        return (tuple(migrations), tuple(rewrites), tuple(errors))

    @classmethod
    def rewrite_workspace(
        cls,
        *,
        workspace_root: Path,
        module_moves: t.MappingKV[str, t.Pair[str, t.StrMapping]],
        pending_sources: t.MappingKV[Path, str],
        apply: bool,
        project_names: t.StrSequence | None = None,
        gates: t.StrSequence | None = None,
    ) -> tuple[t.SequenceOf[p.Infra.MRORewriteResult], t.StrSequence]:
        """Rewrite consumer imports/usages using rope occurrence discovery + source transforms."""
        if not module_moves:
            return ((), ())
        file_moves = cls._collect_file_moves(
            workspace_root=workspace_root,
            module_moves=module_moves,
            project_names=project_names,
        )
        return cls._rewrite_files(
            request=cls.RewriteFilesInput(
                workspace_root=workspace_root,
                file_moves=file_moves,
                pending_sources=pending_sources,
                apply=apply,
                gates=gates,
            )
        )

    @classmethod
    def _rewrite_files(
        cls, *, request: RewriteFilesInput
    ) -> tuple[t.SequenceOf[p.Infra.MRORewriteResult], t.StrSequence]:
        """Rewrite files."""
        rewrites: list[p.Infra.MRORewriteResult] = []
        errors: list[str] = []
        for file_path in sorted(request.file_moves):
            source = request.pending_sources.get(file_path)
            if source is None:
                read = u.Cli.files_read_text(file_path)
                if read.failure:
                    errors.append(read.error or f"failed to read {file_path}")
                    continue
                source = read.value
            transformer = FlextInfraRefactorMROSymbolPropagator(
                module_moves=request.file_moves[file_path]
            )
            updated_source, changes = transformer.rewrite_source(source)
            if updated_source == source:
                continue
            if request.apply:
                ok, report = cls._protected_source_write(
                    workspace_root=request.workspace_root,
                    file_path=file_path,
                    updated_source=updated_source,
                    gates=request.gates,
                )
                if not ok:
                    errors.extend(
                        f"{file_path}: {line.strip()}" for line in report[:10]
                    )
                    continue
            rewrites.append(
                m.Infra.MRORewriteResult(file=str(file_path), replacements=len(changes))
            )
        return (tuple(rewrites), tuple(errors))


__all__: list[str] = ["FlextInfraRefactorMROImportRewriter"]
