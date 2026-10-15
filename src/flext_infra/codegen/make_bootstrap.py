"""Hermetic declared Make bootstrap surface for stale generated dispatchers.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import Annotated, override

from flext_infra import c, m, p, r, u
from flext_infra.codegen import FlextInfraCodegenExecutionBase
from flext_infra.codegen.conform import FlextInfraCodegenConform


class FlextInfraCodegenMakeBootstrap(FlextInfraCodegenExecutionBase[bool]):
    """Delegate declared Make bootstrap surface exclusively to codegen conform."""

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
        conformed = FlextInfraCodegenConform.execute_request(
            m.Infra.CodegenConformRequest(
                root=requested,
                what=c.Infra.CodegenConformSurface.MAKEFILE,
                scope=c.Infra.CodegenConformScope.SELF,
                mode=mode,
                declaration_kind=self.kind,
            ),
            ports=None,
        )
        if conformed.failure:
            return r[bool].from_failure(conformed)
        if mode is c.Infra.CodegenConformMode.APPLY and (
            conformed.value.publication_receipt is None
        ):
            return r[bool].fail(
                f"Makefile bootstrap has no completed publication receipt: {requested}",
            )
        return r[bool].ok(value=True)


__all__: list[str] = ["FlextInfraCodegenMakeBootstrap"]
