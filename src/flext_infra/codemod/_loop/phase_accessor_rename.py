"""Accessor-rename phase of the codemod fixed-point loop.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

from flext_infra import c, m, p, r, t, u
from flext_infra.codemod.semantic_apply import FlextInfraCodemodSemanticApply
from flext_infra.refactor import (
    FlextInfraRefactorAccessor,
    FlextInfraRefactorAccessorOrigin,
)
from flext_infra.transformers import FlextInfraTransformersSemanticPublication


class FlextInfraCodemodLoopPhaseAccessorRename(
    FlextInfraRefactorAccessor,
):
    """Accessor callback: origin-owned rename catalog repairs in the loop.

    Reuses the accessor migration's origin-aware rewrite, so a homonym the
    catalog does not own is never renamed inside the loop either.
    """

    name: str = "accessor-rename"

    def apply(
        self,
        root: Path,
        preflight: m.Infra.ModScanReport,
        rope_workspace: p.Infra.RopeWorkspaceDsl,
    ) -> p.Result[bool]:
        """Apply the rename catalog over the governed files of the repository.

        Returns:
            The resulting ``p.Result[bool]`` — ``True`` marks changed sources.

        """
        sources = {
            path: path.read_text(encoding=c.DEFAULT_ENCODING)
            for path in FlextInfraCodemodSemanticApply.source_inventory(root, preflight)
        }
        planned = self.plan(root, preflight, rope_workspace, sources=sources)
        if planned.failure:
            return r[bool].from_failure(planned)
        return u.Infra.publish_codegen_plans(root, planned.value).map(bool)

    def plan_edits(
        self,
        root: Path,
        rope_workspace: p.Infra.RopeWorkspaceDsl,
        sources: t.MappingKV[Path, str],
    ) -> tuple[m.Infra.SemanticMigrationEdit, ...]:
        """Plan origin-owned accessors on a separate immutable working view.

        Returns:
            The planned migration edits.

        """
        snapshot = u.Infra.snapshot_project(rope_workspace.rope_project, sources)
        resolver = FlextInfraRefactorAccessorOrigin(snapshot)
        edits: list[m.Infra.SemanticMigrationEdit] = []
        for py_file, source in sources.items():
            if not py_file.is_relative_to(root) or py_file.suffix not in {
                c.Infra.EXT_PYTHON,
                c.Infra.EXT_PYTHON_STUB,
            }:
                continue
            updated_source, rewrite_changes = self._apply_automated_rewrites(
                snapshot,
                py_file,
                source,
                resolver=resolver,
            )
            if not any(change.automated for change in rewrite_changes):
                continue
            edits.append(
                m.Infra.SemanticMigrationEdit(
                    file_path=py_file,
                    original_source=source,
                    updated_source=updated_source,
                    changes=tuple(
                        change.reason for change in rewrite_changes if change.automated
                    ),
                ),
            )
        return tuple(edits)

    def plan(
        self,
        root: Path,
        preflight: m.Infra.ModScanReport,
        rope_workspace: p.Infra.RopeWorkspaceDsl,
        *,
        sources: t.MappingKV[Path, str],
    ) -> p.Result[tuple[m.Infra.CodegenFilePlan, ...]]:
        """Plan accessor effects as final file plans.

        Returns:
            The accessor file plans, or the first destination read failure.

        """
        del preflight
        return FlextInfraTransformersSemanticPublication.edit_file_plans(
            root, self.plan_edits(root, rope_workspace, sources), owner=self.name
        )


__all__: list[str] = ["FlextInfraCodemodLoopPhaseAccessorRename"]
