"""Accessor-rename phase of the codemod fixed-point loop.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

from flext_infra import m, p, r, u
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
        planned = self._process_files(
            rope_workspace.rope_project,
            iter_result.value,
            params=m.Infra.AccessorMigrationInput(
                repository_root=root,
                apply=True,
                gates=tuple(u.Infra.snapshot_lint_gates()),
            ),
            source_preview=self.source_preview,
            inputs=tuple(
                state
                for finding in preflight.entries
                for state in (
                    *(
                        (finding.source_state,)
                        if finding.source_state is not None
                        else ()
                    ),
                    *finding.binding_states,
                )
            ),
        )
        if planned.failure:
            return r[bool].from_failure(planned)
        return r[bool].ok(
            value=any(report.automated_changes for report in planned.value)
        )


__all__: list[str] = ["FlextInfraAccessorRenamePhase"]
