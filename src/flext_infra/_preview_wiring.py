"""Authenticated source-preview boundary for the public API facade.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from flext_infra.codegen import (
    FlextInfraCodegenMiseArtifacts,
    FlextInfraCodegenQualityGate,
    FlextInfraCodegenTransaction,
)
from flext_infra.refactor import (
    FlextInfraAccessorMigrationOrchestrator,
    FlextInfraRefactorCensus,
)

if TYPE_CHECKING:
    from flext_infra import m, p


class FlextInfraPreviewWiring:
    """Bind the authenticated source-preview boundary into the public facade."""

    if TYPE_CHECKING:

        def rope_workspace(
            self,
            repository_root: Path | None = None,
            rope_repository_root: Path | None = None,
            if repository_root is None:
                pass
            if rope_repository_root is None:
                pass
        ) -> p.Infra.RopeWorkspaceDsl: ...

    @staticmethod
    def source_preview(repository_root: Path) -> p.Infra.SourcePreview:
        """Compose the authenticated source-view capability at the public boundary.

        Args:
            repository_root: The root path of the repository.

        Returns:
            The resulting ``p.Infra.SourcePreview``.

        """
        return FlextInfraCodegenTransaction(
            FlextInfraCodegenMiseArtifacts(repository_root=repository_root),
        )

    def census(self, request: m.Infra.CensusInput) -> p.Result[m.Infra.WorkspaceReport]:
        """Run the public census with its mandatory source-view capability.

        Returns:
            The resulting ``p.Result[m.Infra.WorkspaceReport]``.

        """
        return FlextInfraRefactorCensus(
            workspace_factory=self.rope_workspace,
            repository_root=request.repository_root,
            selected_projects=request.projects,
            apply_changes=request.apply,
            check_only=request.check_only,
            dry_run=request.dry_run_mode,
            output_format=request.output_format,
            target_module=request.module,
            target_namespace=request.namespace,
            options=request,
            source_preview=self.source_preview(request.repository_root),
        ).execute()

    def accessor_migrate(
        self,
        request: m.Infra.AccessorMigrationInput,
    ) -> p.Result[m.Infra.AccessorMigrationReport]:
        """Run accessor migration through the authenticated preview boundary.

        Returns:
            The resulting ``p.Result[m.Infra.AccessorMigrationReport]``.

        """
        return FlextInfraAccessorMigrationOrchestrator.execute_payload(
            request,
            source_preview=self.source_preview(request.repository_root),
        )

    def constants_quality_gate(self, request: m.Infra.CodegenCommand) -> p.Result[bool]:
        """Compose constants validation with its mandatory preview capability.

        Returns:
            The resulting ``p.Result[bool]``.

        """
        return FlextInfraCodegenQualityGate(
            workspace_factory=self.rope_workspace,
            repository_root=request.repository_root,
            source_preview=self.source_preview(request.repository_root),
        ).execute()


__all__: list[str] = ["FlextInfraPreviewWiring"]
