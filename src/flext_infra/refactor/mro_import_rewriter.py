"""Workspace-wide MRO migration orchestration and reference rewriting."""

from __future__ import annotations

from collections.abc import Mapping, MutableMapping, Sequence
from pathlib import Path

from flext_infra import (
    FlextInfraConstantsBase,
    FlextInfraConstantsRefactor,
    FlextInfraModelsRefactorGrep,
    FlextInfraRefactorMROSymbolPropagator,
    FlextInfraTypes,
    FlextInfraTypesBase,
    FlextInfraTypesRope,
    FlextInfraUtilitiesIteration,
    FlextInfraUtilitiesProtectedEdit,
    FlextInfraUtilitiesRefactorMroTransform,
    FlextInfraUtilitiesRope,
)


class FlextInfraRefactorMROImportRewriter:
    """Rewrite imports/references after MRO symbol absorption into facade classes."""

    @classmethod
    def migrate_workspace(
        cls,
        *,
        workspace_root: Path,
        scan_results: Sequence[FlextInfraModelsRefactorGrep.MROScanReport],
        apply: bool,
    ) -> FlextInfraTypes.Infra.Triple[
        Sequence[FlextInfraModelsRefactorGrep.MROFileMigration],
        Sequence[FlextInfraModelsRefactorGrep.MRORewriteResult],
        FlextInfraTypes.StrSequence,
    ]:
        """Transform migrated files and propagate consumer rewrites across the workspace."""
        errors: list[str] = []
        migrations: list[FlextInfraModelsRefactorGrep.MROFileMigration] = []
        module_moves: MutableMapping[
            str, FlextInfraTypesBase.Pair[str, FlextInfraTypes.StrMapping]
        ] = {}
        module_source_paths: MutableMapping[str, Path] = {}
        pending_sources: MutableMapping[Path, str] = {}
        for scan_result in scan_results:
            try:
                updated_source, migration, symbol_map = (
                    FlextInfraUtilitiesRefactorMroTransform.migrate_file(
                        scan_result=scan_result,
                    )
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
        )
        errors.extend(rewrite_errors)
        return (tuple(migrations), tuple(rewrites), tuple(errors))

    @classmethod
    def rewrite_workspace(
        cls,
        *,
        workspace_root: Path,
        module_moves: Mapping[
            str, FlextInfraTypesBase.Pair[str, FlextInfraTypes.StrMapping]
        ],
        pending_sources: Mapping[Path, str],
        apply: bool,
    ) -> tuple[
        Sequence[FlextInfraModelsRefactorGrep.MRORewriteResult],
        FlextInfraTypes.StrSequence,
    ]:
        """Rewrite consumer imports/usages using rope occurrence discovery + source transforms."""
        if not module_moves:
            return ((), ())
        file_moves = cls._collect_file_moves(
            workspace_root=workspace_root,
            module_moves=module_moves,
        )
        return cls._rewrite_files(
            workspace_root=workspace_root,
            file_moves=file_moves,
            pending_sources=pending_sources,
            apply=apply,
        )

    @classmethod
    def _collect_file_moves(
        cls,
        *,
        workspace_root: Path,
        module_moves: Mapping[
            str, FlextInfraTypesBase.Pair[str, FlextInfraTypes.StrMapping]
        ],
    ) -> Mapping[
        Path,
        Mapping[str, FlextInfraTypesBase.Pair[str, FlextInfraTypes.StrMapping]],
    ]:
        rope_project = FlextInfraUtilitiesRope.init_rope_project(workspace_root)
        module_file_moves: MutableMapping[
            Path,
            MutableMapping[
                str, FlextInfraTypesBase.Pair[str, FlextInfraTypes.StrMapping]
            ],
        ] = {}
        try:
            for module_name, module_move in module_moves.items():
                cls._collect_module_occurrences(
                    rope_project,
                    module_name,
                    module_move,
                    module_file_moves,
                )
        finally:
            rope_project.close()
        return cls._expand_file_moves(
            workspace_root=workspace_root,
            file_moves=cls._merge_file_moves(module_file_moves),
            module_moves=module_moves,
        )

    @staticmethod
    def _collect_module_occurrences(
        rope_project: FlextInfraTypesRope.RopeProject,
        module_name: str,
        module_move: FlextInfraTypesBase.Pair[str, FlextInfraTypes.StrMapping],
        module_file_moves: MutableMapping[
            Path,
            MutableMapping[
                str, FlextInfraTypesBase.Pair[str, FlextInfraTypes.StrMapping]
            ],
        ],
    ) -> None:
        """Find rope occurrences for one module's symbols and merge into file_moves."""
        resource = rope_project.find_module(module_name)
        if resource is None:
            return
        facade_alias, symbol_paths = module_move
        for symbol_name, target_path in symbol_paths.items():
            offset = FlextInfraUtilitiesRope.find_definition_offset(
                rope_project,
                resource,
                symbol_name,
            )
            if offset is None:
                continue
            for occurrence in FlextInfraUtilitiesRope.find_occurrences(
                rope_project,
                resource,
                offset,
            ):
                resource_like = getattr(occurrence, "resource", None)
                if resource_like is None:
                    continue
                real_path = getattr(resource_like, "real_path", None)
                if real_path is None:
                    continue
                file_path = Path(str(real_path)).resolve()
                per_file = module_file_moves.setdefault(file_path, {})
                existing_move = per_file.get(module_name)
                existing_paths: FlextInfraTypes.MutableStrMapping = (
                    dict(existing_move[1]) if existing_move is not None else {}
                )
                existing_paths[symbol_name] = target_path
                per_file[module_name] = (facade_alias, existing_paths)

    @staticmethod
    def _merge_file_moves(
        file_moves: Mapping[
            Path,
            MutableMapping[
                str, FlextInfraTypesBase.Pair[str, FlextInfraTypes.StrMapping]
            ],
        ],
    ) -> Mapping[
        Path,
        Mapping[str, FlextInfraTypesBase.Pair[str, FlextInfraTypes.StrMapping]],
    ]:
        return {
            file_path: {
                module_name: (facade_alias, dict(symbol_paths))
                for module_name, (facade_alias, symbol_paths) in per_module.items()
            }
            for file_path, per_module in file_moves.items()
        }

    @classmethod
    def _expand_file_moves(
        cls,
        *,
        workspace_root: Path,
        file_moves: Mapping[
            Path,
            Mapping[str, FlextInfraTypesBase.Pair[str, FlextInfraTypes.StrMapping]],
        ],
        module_moves: Mapping[
            str, FlextInfraTypesBase.Pair[str, FlextInfraTypes.StrMapping]
        ],
    ) -> Mapping[
        Path,
        Mapping[str, FlextInfraTypesBase.Pair[str, FlextInfraTypes.StrMapping]],
    ]:
        expanded: MutableMapping[
            Path,
            Mapping[str, FlextInfraTypesBase.Pair[str, FlextInfraTypes.StrMapping]],
        ] = dict(file_moves)
        for file_path in cls._iter_workspace_python_files(
            workspace_root=workspace_root
        ):
            expanded.setdefault(file_path.resolve(), module_moves)
        return expanded

    @staticmethod
    def _iter_workspace_python_files(*, workspace_root: Path) -> Sequence[Path]:
        paths: list[Path] = []
        for project_root in FlextInfraUtilitiesIteration.discover_project_roots(
            workspace_root=workspace_root
        ):
            iter_result = FlextInfraUtilitiesIteration.iter_python_files(
                workspace_root=workspace_root,
                project_roots=[project_root],
                src_dirs=frozenset(FlextInfraConstantsRefactor.MRO_SCAN_DIRECTORIES),
            )
            if iter_result.failure:
                continue
            paths.extend(iter_result.value)
        return paths

    @classmethod
    def _rewrite_files(
        cls,
        *,
        workspace_root: Path,
        file_moves: Mapping[
            Path,
            Mapping[str, FlextInfraTypesBase.Pair[str, FlextInfraTypes.StrMapping]],
        ],
        pending_sources: Mapping[Path, str],
        apply: bool,
    ) -> tuple[
        Sequence[FlextInfraModelsRefactorGrep.MRORewriteResult],
        FlextInfraTypes.StrSequence,
    ]:
        rewrites: list[FlextInfraModelsRefactorGrep.MRORewriteResult] = []
        errors: list[str] = []
        for file_path in sorted(file_moves):
            source = pending_sources.get(file_path)
            if source is None:
                try:
                    source = file_path.read_text(
                        encoding=FlextInfraConstantsBase.Encoding.DEFAULT
                    )
                except OSError:
                    continue
            transformer = FlextInfraRefactorMROSymbolPropagator(
                module_moves=file_moves[file_path],
            )
            updated_source, changes = transformer.rewrite_source(source)
            if updated_source == source:
                continue
            if apply:
                ok, report = cls._protected_source_write(
                    workspace_root=workspace_root,
                    file_path=file_path,
                    updated_source=updated_source,
                )
                if not ok:
                    errors.extend(
                        f"{file_path}: {line.strip()}" for line in report[:10]
                    )
                    continue
            rewrites.append(
                FlextInfraModelsRefactorGrep.MRORewriteResult(
                    file=str(file_path),
                    replacements=len(changes),
                ),
            )
        return (tuple(rewrites), tuple(errors))

    @staticmethod
    def _protected_source_write(
        *,
        workspace_root: Path,
        file_path: Path,
        updated_source: str,
    ) -> FlextInfraTypesBase.EditResult:
        return FlextInfraUtilitiesProtectedEdit.protected_source_write(
            file_path,
            workspace=workspace_root,
            updated_source=updated_source,
            keep_backup=True,
        )

    @classmethod
    def _write_pending_sources(
        cls,
        *,
        workspace_root: Path,
        pending_sources: Mapping[Path, str],
    ) -> tuple[FlextInfraTypes.StrSequence, Sequence[Path]]:
        errors: list[str] = []
        failed_paths: list[Path] = []
        for file_path, source in pending_sources.items():
            ok, report = cls._protected_source_write(
                workspace_root=workspace_root,
                file_path=file_path,
                updated_source=source,
            )
            if ok:
                continue
            failed_paths.append(file_path)
            errors.extend(f"{file_path}: {line.strip()}" for line in report[:10])
        return (tuple(errors), tuple(failed_paths))


__all__ = ["FlextInfraRefactorMROImportRewriter"]
