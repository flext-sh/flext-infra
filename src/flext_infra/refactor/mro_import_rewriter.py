"""Workspace-wide MRO migration orchestration and reference rewriting."""

from __future__ import annotations

from collections.abc import MutableMapping
from pathlib import Path
from typing import ClassVar

from flext_infra import m, t, u
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

        model_config: ClassVar[m.ConfigDict] = m.ConfigDict(
            arbitrary_types_allowed=True
        )

        file_moves: t.MappingKV[Path, t.MappingKV[str, t.Pair[str, t.StrMapping]]]
        pending_sources: t.MappingKV[Path, str]

    @classmethod
    def migrate_workspace(
        cls,
        *,
        workspace_root: Path,
        scan_results: t.SequenceOf[m.Infra.MROScanReport],
        apply: bool,
        project_names: t.StrSequence | None = None,
    ) -> t.Triple[
        t.SequenceOf[m.Infra.MROFileMigration],
        t.SequenceOf[m.Infra.MRORewriteResult],
        t.StrSequence,
    ]:
        """Transform migrated files and propagate consumer rewrites across the workspace."""
        errors: list[str] = []
        migrations: list[m.Infra.MROFileMigration] = []
        module_moves: MutableMapping[str, t.Pair[str, t.StrMapping]] = {}
        pending_sources: MutableMapping[Path, str] = {}
        for scan_result in scan_results:
            try:
                updated_source, migration, symbol_map = u.Infra.migrate_file(
                    scan_result=scan_result
                )
            except OSError as exc:
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
        if apply and errors:
            return (tuple(migrations), (), tuple(errors))
        rewrites, rewrite_errors = cls.rewrite_workspace(
            workspace_root=workspace_root,
            module_moves=module_moves,
            pending_sources=pending_sources,
            apply=apply,
            project_names=project_names,
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
    ) -> tuple[t.SequenceOf[m.Infra.MRORewriteResult], t.StrSequence]:
        """Rewrite consumer imports/usages using rope occurrence discovery + source transforms."""
        if not module_moves:
            return ((), ())
        try:
            file_moves = cls._collect_file_moves(
                workspace_root=workspace_root,
                module_moves=module_moves,
                project_names=project_names,
            )
        except RuntimeError as exc:
            return ((), (str(exc),))
        missing_owners = tuple(sorted(set(pending_sources) - set(file_moves)))
        if missing_owners:
            details = ", ".join(str(path) for path in missing_owners)
            return (
                (),
                (f"MRO owners missing from consumer rewrite plan: {details}",),
            )
        rewrites, rewrite_errors, updates = cls._rewrite_files(
            request=cls.RewriteFilesInput(
                file_moves=file_moves,
                pending_sources=pending_sources,
            )
        )
        if rewrite_errors:
            return ((), rewrite_errors)
        if apply:
            try:
                u.Infra.protected_source_writes(
                    {**pending_sources, **updates},
                    request=m.Infra.ProtectedSourceWritesRequest(
                        workspace=workspace_root
                    ),
                )
            except OSError as exc:
                return ((), (str(exc),))
        return (rewrites, ())

    @classmethod
    def _rewrite_files(
        cls, *, request: RewriteFilesInput
    ) -> tuple[
        t.SequenceOf[m.Infra.MRORewriteResult],
        t.StrSequence,
        t.MappingKV[Path, str],
    ]:
        """Rewrite files."""
        rewrites: list[m.Infra.MRORewriteResult] = []
        errors: list[str] = []
        updates: MutableMapping[Path, str] = {}
        for file_path in sorted(request.file_moves):
            source = request.pending_sources.get(file_path)
            if source is None:
                read = u.Cli.files_read_text(file_path)
                if read.failure:
                    error = read.error
                    if error is None:
                        msg = f"source read failed without an error: {file_path}"
                        raise RuntimeError(msg)
                    errors.append(error)
                    continue
                source = read.value
            transformer = FlextInfraRefactorMROSymbolPropagator(
                module_moves=request.file_moves[file_path]
            )
            updated_source, changes = transformer.rewrite_source(source)
            if updated_source == source:
                continue
            updates[file_path] = updated_source
            rewrites.append(
                m.Infra.MRORewriteResult(file=str(file_path), replacements=len(changes))
            )
        return (tuple(rewrites), tuple(errors), dict(updates))


__all__: list[str] = ["FlextInfraRefactorMROImportRewriter"]
