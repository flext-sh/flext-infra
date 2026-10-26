"""Refactor transport for the canonical import-law utility capability.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_infra import u

if TYPE_CHECKING:
    from pathlib import Path

    from flext_infra import m, p, t


class FlextInfraImportNormalization:
    """Delegate refactor consumers to the shared source import owner."""

    @staticmethod
    def normalize_source(
        *,
        project_root: Path,
        file_path: Path,
        source: str,
        import_graph: t.MappingKV[str, frozenset[str]] | None = None,
        sources: t.MappingKV[Path, str] | None = None,
    ) -> str | None:
        """Return the shared utility's canonical module imports.

        Returns:
            Canonical source, or no change at the fixed point.

        """
        return u.Infra.normalize_import_source(
            project_root=project_root,
            file_path=file_path,
            source=source,
            import_graph=import_graph,
            sources=sources,
        )

    @staticmethod
    def plan_files(
        project_root: Path,
        files: t.SequenceOf[Path],
        *,
        sources: t.MappingKV[Path, str],
        snapshot: p.Infra.WorkspaceSnapshot,
    ) -> p.Result[t.VariadicTuple[m.Infra.CodegenFilePlan]]:
        """Return import plans from the injected source epoch.

        Returns:
            Typed source import plans, retaining original file authority.

        """
        return u.Infra.plan_import_normalization(
            project_root,
            files,
            sources=sources,
            snapshot=snapshot,
        )


__all__: list[str] = ["FlextInfraImportNormalization"]
