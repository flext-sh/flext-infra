"""Workspace-wide MRO migration orchestration and reference rewriting."""

from __future__ import annotations

from collections.abc import Mapping, MutableMapping, Sequence
from pathlib import Path

from flext_infra import (
    FlextInfraRefactorMROSymbolPropagator,
    FlextInfraUtilitiesIteration,
    FlextInfraUtilitiesRefactorMroTransform,
    FlextInfraUtilitiesRope,
    c,
    m,
    p,
    t,
)


class FlextInfraRefactorMROImportRewriter:
    """Rewrite imports/references after MRO symbol absorption into facade classes."""

    @classmethod
    def migrate_workspace(
        cls,
        *,
        workspace_root: Path,
        scan_results: Sequence[m.Infra.MROScanReport],
        apply: bool,
    ) -> t.Infra.Triple[
        Sequence[m.Infra.MROFileMigration],
        Sequence[m.Infra.MRORewriteResult],
        t.StrSequence,
    ]:
        """Transform migrated files and propagate consumer rewrites across the workspace."""
        errors: list[str] = []
        migrations: list[m.Infra.MROFileMigration] = []
        module_moves: MutableMapping[str, t.Infra.Pair[str, t.StrMapping]] = {}
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
            pending_sources[Path(scan_result.file).resolve()] = updated_source
            module_moves[scan_result.module] = (
                scan_result.facade_alias or "c",
                symbol_map,
            )
        rewrites = cls.rewrite_workspace(
            workspace_root=workspace_root,
            module_moves=module_moves,
            pending_sources=pending_sources,
            apply=apply,
        )
        return (tuple(migrations), tuple(rewrites), tuple(errors))

    @classmethod
    def rewrite_workspace(
        cls,
        *,
        workspace_root: Path,
        module_moves: Mapping[str, t.Infra.Pair[str, t.StrMapping]],
        pending_sources: Mapping[Path, str],
        apply: bool,
    ) -> Sequence[m.Infra.MRORewriteResult]:
        """Rewrite consumer imports/usages using rope occurrence discovery + source transforms."""
        if not module_moves:
            if apply:
                cls._write_pending_sources(pending_sources)
            return []
        file_moves = cls._collect_file_moves(
            workspace_root=workspace_root,
            module_moves=module_moves,
        )
        if apply:
            cls._write_pending_sources(pending_sources)
        return cls._rewrite_files(
            file_moves=file_moves,
            pending_sources=pending_sources,
            apply=apply,
        )

    @classmethod
    def _collect_file_moves(
        cls,
        *,
        workspace_root: Path,
        module_moves: Mapping[str, t.Infra.Pair[str, t.StrMapping]],
    ) -> Mapping[Path, Mapping[str, t.Infra.Pair[str, t.StrMapping]]]:
        rope_project = FlextInfraUtilitiesRope.init_rope_project(workspace_root)
        module_file_moves: MutableMapping[
            Path,
            MutableMapping[str, t.Infra.Pair[str, t.StrMapping]],
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
        rope_project: t.Infra.RopeProject,
        module_name: str,
        module_move: t.Infra.Pair[str, t.StrMapping],
        module_file_moves: MutableMapping[
            Path,
            MutableMapping[str, t.Infra.Pair[str, t.StrMapping]],
        ],
    ) -> None:
        """Find rope occurrences for one module's symbols and merge into file_moves."""
        resource = FlextInfraUtilitiesRope.get_file_resource(
            rope_project,
            module_name,
        )
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
                if not isinstance(resource_like, p.Infra.RopeResourceLike):
                    continue
                file_path = Path(resource_like.real_path).resolve()
                per_file = module_file_moves.setdefault(file_path, {})
                existing_move = per_file.get(module_name)
                existing_paths: t.MutableStrMapping = (
                    dict(existing_move[1]) if existing_move is not None else {}
                )
                existing_paths[symbol_name] = target_path
                per_file[module_name] = (facade_alias, existing_paths)

    @staticmethod
    def _merge_file_moves(
        file_moves: Mapping[
            Path,
            MutableMapping[str, t.Infra.Pair[str, t.StrMapping]],
        ],
    ) -> Mapping[Path, Mapping[str, t.Infra.Pair[str, t.StrMapping]]]:
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
        file_moves: Mapping[Path, Mapping[str, t.Infra.Pair[str, t.StrMapping]]],
        module_moves: Mapping[str, t.Infra.Pair[str, t.StrMapping]],
    ) -> Mapping[Path, Mapping[str, t.Infra.Pair[str, t.StrMapping]]]:
        expanded: MutableMapping[
            Path, Mapping[str, t.Infra.Pair[str, t.StrMapping]]
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
                src_dirs=frozenset(c.Infra.MRO_SCAN_DIRECTORIES),
            )
            if iter_result.is_failure:
                continue
            paths.extend(iter_result.value)
        return paths

    @classmethod
    def _rewrite_files(
        cls,
        *,
        file_moves: Mapping[Path, Mapping[str, t.Infra.Pair[str, t.StrMapping]]],
        pending_sources: Mapping[Path, str],
        apply: bool,
    ) -> Sequence[m.Infra.MRORewriteResult]:
        rewrites: list[m.Infra.MRORewriteResult] = []
        for file_path in sorted(file_moves):
            source = pending_sources.get(file_path)
            if source is None:
                try:
                    source = file_path.read_text(encoding=c.Infra.Encoding.DEFAULT)
                except OSError:
                    continue
            transformer = FlextInfraRefactorMROSymbolPropagator(
                module_moves=file_moves[file_path],
            )
            updated_source, changes = transformer.rewrite_source(source)
            if updated_source == source:
                continue
            if apply:
                file_path.write_text(updated_source, encoding=c.Infra.Encoding.DEFAULT)
            rewrites.append(
                m.Infra.MRORewriteResult(
                    file=str(file_path),
                    replacements=len(changes),
                ),
            )
        return rewrites

    @staticmethod
    def _write_pending_sources(pending_sources: Mapping[Path, str]) -> None:
        for file_path, source in pending_sources.items():
            file_path.write_text(source, encoding=c.Infra.Encoding.DEFAULT)


__all__ = ["FlextInfraRefactorMROImportRewriter"]
