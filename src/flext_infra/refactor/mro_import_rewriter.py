"""Workspace-wide symbol rewriting for MRO migrations via rope."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from pathlib import Path

from flext_infra import m, t, u


class FlextInfraRefactorMROImportRewriter:
    """Rewrite symbol references workspace-wide after MRO class relocations.

    Delegates all rope operations to u.Infra.* — no direct rope imports here.
    """

    @classmethod
    def rewrite_workspace(
        cls,
        *,
        workspace_root: Path,
        moved_index: Mapping[str, t.StrMapping],
        apply: bool,
    ) -> Sequence[m.Infra.MRORewriteResult]:
        """Rename all moved symbols workspace-wide via u.Infra.rename_symbol_workspace."""
        rope_project = u.Infra.init_rope_project(workspace_root)
        file_replacements: t.Infra.MutableStrIndex = {}
        try:
            for module_name, symbol_map in moved_index.items():
                resource = u.Infra.get_file_resource(rope_project, module_name)
                if resource is None:
                    continue
                for old_symbol, new_path in symbol_map.items():
                    offset = u.Infra.find_definition_offset(
                        rope_project, resource, old_symbol
                    )
                    if offset is None:
                        continue
                    new_name = new_path.split(".")[-1]
                    for path in u.Infra.rename_symbol_workspace(
                        rope_project, resource, offset, new_name, apply=apply
                    ):
                        file_replacements[path] = file_replacements.get(path, 0) + 1
                    # Re-fetch resource after rename: rope_project.do() updates index
                    # and resource objects may become stale
                    refreshed = u.Infra.get_file_resource(rope_project, module_name)
                    if refreshed is not None:
                        resource = refreshed
        finally:
            rope_project.close()
        return [
            m.Infra.MRORewriteResult(file=path, replacements=count)
            for path, count in file_replacements.items()
        ]


__all__ = ["FlextInfraRefactorMROImportRewriter"]
