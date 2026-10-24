"""Declared initial generation and bounded Make dispatcher recovery.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import Annotated, override

from flext_infra import c, m, p, r, u
from flext_infra._conform_wiring import FlextInfraConformWiring
from flext_infra.codegen import (
    FlextInfraCodegenConform,
    FlextInfraCodegenExecutionBase,
    FlextInfraCodegenFileLeases,
    FlextInfraMiseArtifactsVerification,
)
from flext_infra.workspace import FlextInfraWorkspaceDetector


class FlextInfraCodegenMakeBootstrap(
    FlextInfraConformWiring,
    FlextInfraCodegenExecutionBase[bool],
):
    """Compose the existing Make planner, publisher and receipt verifier."""

    model_config = m.ConfigDict(use_enum_values=False)
    kind: Annotated[
        c.Infra.ProjectKind | None,
        m.Field(
            description=(
                "Explicit governance kind belonging only to the requested target"
            ),
        ),
    ] = None

    @override
    def execute(self) -> p.Result[bool]:
        """Publish an admitted new tree or this existing target's Make bootstrap.

        Returns:
            A completed native publication receipt or the original failure.

        """
        requested = self.repository_root.expanduser().absolute()
        identity = u.Infra.exact_worktree_root(requested)
        if identity.failure:
            return r[bool].from_failure(identity)
        metadata = requested / c.PYPROJECT_FILENAME
        new_project = not metadata.exists() and not metadata.is_symlink()
        if new_project:
            admitted = FlextInfraWorkspaceDetector.load_workspace_spec(requested)
            if admitted.failure:
                return r[bool].from_failure(admitted)
            if (
                self.kind is not None
                and self.kind is not admitted.value.repository.kind
            ):
                return r[bool].fail(
                    "bootstrap kind conflicts with the new target's own declaration: "
                    f"{requested}",
                )
        mode = (
            c.Infra.CodegenConformMode.CHECK
            if self.effective_dry_run
            else c.Infra.CodegenConformMode.APPLY
        )
        request = m.Infra.CodegenConformRequest(
            root=requested,
            what=(
                c.Infra.CodegenConformSurface.ALL
                if new_project
                else c.Infra.CodegenConformSurface.MAKEFILE
            ),
            scope=c.Infra.CodegenConformScope.SELF,
            mode=mode,
            declaration_kind=None if new_project else self.kind,
        )
        if mode is c.Infra.CodegenConformMode.CHECK:
            with FlextInfraCodegenFileLeases.mutation_lease(requested):
                return FlextInfraMiseArtifactsVerification.publication_current(
                    request,
                ).map(lambda _: True)
        conformed = FlextInfraCodegenConform.execute_request(
            request,
            execution_context=self if new_project else None,
            generation_only=new_project,
        )
        if conformed.success and conformed.value.publication_receipt is None:
            return r[bool].fail(
                f"Makefile bootstrap has no completed publication receipt: {requested}",
            )
        return conformed.map(lambda _: True)


__all__: list[str] = ["FlextInfraCodegenMakeBootstrap"]
