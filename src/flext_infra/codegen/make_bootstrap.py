"""Hermetic declared Make bootstrap surface for stale generated dispatchers.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import TYPE_CHECKING, override

from flext_infra import c, m, r, t, u
from flext_infra.codegen import (
    FlextInfraCodegenExecutionBase,
    FlextInfraCodegenTransaction,
)
from flext_infra.codegen.conform import FlextInfraCodegenConform
from flext_infra.workspace import (
    FlextInfraWorkspaceDetector,
    FlextInfraWorkspaceEnvironmentProvenance,
)

if TYPE_CHECKING:
    from pathlib import Path

    from flext_infra import p


class FlextInfraCodegenMakeBootstrap(FlextInfraCodegenExecutionBase[bool]):
    """Delegate declared Make bootstrap surface exclusively to codegen conform."""

    @override
    def execute(self) -> p.Result[bool]:
        """Apply or check this checkout's canonical declared Make bootstrap surface.

        Returns:
            The resulting ``p.Result[bool]``.

        """
        # Why: `init` bootstraps a fresh checkout, so it must reject the same
        # non-exact/unregistered-nested roots the Mise workspace planner
        # rejects, through the shared `u.Infra.exact_worktree_root` owner.
        requested = self.repository_root.expanduser().absolute()
        identity = u.Infra.exact_worktree_root(requested)
        if identity.failure:
            return r[bool].from_failure(identity)
        mode = (
            c.Infra.CodegenConformMode.CHECK
            if self.effective_dry_run
            else c.Infra.CodegenConformMode.APPLY
        )
        roots: t.VariadicTuple[Path] = (requested,)
        context = FlextInfraWorkspaceDetector.resolution_context(requested)
        if context.failure:
            return r[bool].from_failure(context)
        if not context.value.standalone:
            members = FlextInfraWorkspaceEnvironmentProvenance.editable_members(
                requested,
            )
            if members.failure:
                return r[bool].from_failure(members)
            roots = (
                requested,
                *(requested / member.path for member in members.value),
            )
        receipts: list[m.Infra.CodegenPhaseOutcome] = []
        for root in roots:
            conformed = self.conform_target(
                root,
                surface=c.Infra.CodegenConformSurface.MAKEFILE,
                mode=mode,
                publication_receipts=receipts,
            )
            if conformed.failure:
                return conformed
        if mode is c.Infra.CodegenConformMode.APPLY and len(roots) > 1:
            qualified = FlextInfraCodegenTransaction.publish_operation_receipt(
                m.Infra.CodegenConformRequest(
                    root=requested,
                    what=c.Infra.CodegenConformSurface.MAKEFILE,
                    scope=c.Infra.CodegenConformScope.ALL,
                    mode=mode,
                ),
                tuple(receipts),
                scope_roots=roots,
                completed=True,
            )
            if qualified.failure:
                return r[bool].from_failure(qualified)
        return r[bool].ok(value=True)

    @staticmethod
    def conform_target(
        root: Path,
        *,
        surface: c.Infra.CodegenConformSurface,
        mode: c.Infra.CodegenConformMode,
        publication_receipts: t.MutableSequenceOf[m.Infra.CodegenPhaseOutcome]
        | None = None,
    ) -> p.Result[bool]:
        """Run the owned conform transaction for a checked bootstrap target.

        Returns:
            The resulting ``p.Result[bool]``.

        """
        conformed = FlextInfraCodegenConform.execute_request(
            m.Infra.CodegenConformRequest(
                root=root,
                what=surface,
                scope=c.Infra.CodegenConformScope.SELF,
                mode=mode,
            ),
            # The bootstrap surface publishes one file and never crosses into
            # the docs or fresh-import families.
            ports=None,
        )
        if conformed.failure:
            return r[bool].from_failure(conformed)
        if mode is c.Infra.CodegenConformMode.APPLY:
            receipt = conformed.value.publication_receipt
            if receipt is None:
                return r[bool].fail(
                    f"Makefile bootstrap has no completed publication receipt: {root}",
                )
            if publication_receipts is not None:
                publication_receipts.append(receipt)
        return r[bool].ok(value=True)


__all__: list[str] = ["FlextInfraCodegenMakeBootstrap"]
