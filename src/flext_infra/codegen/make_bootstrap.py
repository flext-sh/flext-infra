"""Hermetic declared Make bootstrap surface for stale generated dispatchers.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import Annotated, override

from flext_infra import c, m, p, r, u
from flext_infra.codegen import (
    FlextInfraCodegenConform,
    FlextInfraCodegenExecutionBase,
    FlextInfraCodegenFileLeases,
    FlextInfraMiseArtifactsVerification,
)


class FlextInfraCodegenMakeBootstrap(FlextInfraCodegenExecutionBase[bool]):
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
        """Publish this target's declaration and canonical Make bootstrap.

        Returns:
            A completed native publication receipt or the original failure.

        """
        requested = self.repository_root.expanduser().absolute()
        identity = u.Infra.exact_worktree_root(requested)
        if identity.failure:
            return r[bool].from_failure(identity)
        mode = (
            c.Infra.CodegenConformMode.CHECK
            if self.effective_dry_run
            else c.Infra.CodegenConformMode.APPLY
        )
        request = m.Infra.CodegenConformRequest(
            root=requested,
            what=c.Infra.CodegenConformSurface.MAKEFILE,
            scope=c.Infra.CodegenConformScope.SELF,
            mode=mode,
            declaration_kind=self.kind,
        )
        if mode is c.Infra.CodegenConformMode.CHECK:
            with FlextInfraCodegenFileLeases.mutation_lease(requested):
                return FlextInfraMiseArtifactsVerification.publication_current(
                    request,
                ).map(lambda _: True)
        conformed = FlextInfraCodegenConform.execute_request(
            request,
            execution_context=None,
        )
        if conformed.failure:
            return r[bool].from_failure(conformed)
        if conformed.value.publication_receipt is None:
            return r[bool].fail(
                f"Makefile bootstrap has no completed publication receipt: {requested}",
            )
        return r[bool].ok(value=True)


__all__: list[str] = ["FlextInfraCodegenMakeBootstrap"]
