"""Accessor-rename phase of the codemod fixed-point loop.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

from flext_infra import m, p, r, u
from flext_infra.codemod.semantic_apply import FlextInfraCodemodSemanticApply
from flext_infra.refactor import (
    FlextInfraAccessorMigrationReportMixin,
    FlextInfraAccessorMigrationRewriteMixin,
)


class FlextInfraAccessorRenamePhase(
    FlextInfraAccessorMigrationRewriteMixin,
    FlextInfraAccessorMigrationReportMixin,
):
    """Accessor callback: origin-owned rename catalog repairs in the loop.

    Reuses the accessor migration's origin-aware rewrite, so a homonym the
    catalog does not own is never renamed inside the loop either.
    """

    name: str = "accessor-rename"

    def __init__(self, *, source_preview: p.Infra.SourcePreview) -> None:
        """Receive the same authenticated candidate capability as the public verb."""
        self.source_preview = source_preview

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
        iter_result = u.Infra.iter_python_files(
            m.Infra.SourceScanRequest(
                project_roots=tuple(u.Infra.governed_project_roots(root)),
            ),
        )
        if iter_result.failure:
            return r[bool].from_failure(iter_result)
        original: dict[Path, str] = {}
        for py_file in iter_result.value:
            read = u.Cli.files_read_text(py_file)
            if read.failure:
                return r[bool].from_failure(read)
            original[py_file] = read.value
        snapshot = u.Infra.snapshot_project(rope_workspace.rope_project, original)
        edits: list[m.Infra.SemanticMigrationEdit] = []
        for py_file, source in original.items():
            updated_source, rewrite_changes = self._apply_automated_rewrites(
                snapshot,
                py_file,
                source,
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
        return FlextInfraCodemodSemanticApply.publish_planned_edits(root, edits)


__all__: list[str] = ["FlextInfraAccessorRenamePhase"]
