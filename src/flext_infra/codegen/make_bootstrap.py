"""Hermetic Makefile-only bootstrap for stale generated dispatchers."""

from __future__ import annotations

from typing import TYPE_CHECKING, override

from .. import c, m, r, s
from . import FlextInfraCodegenConform

if TYPE_CHECKING:
    from .. import p


class FlextInfraCodegenMakeBootstrap(s[bool]):
    """Delegate one Makefile projection exclusively to codegen conform."""

    @override
    def execute(self) -> p.Result[bool]:
        """Apply or check only this checkout's canonical Makefile projection."""
        mode = (
            c.Infra.CodegenConformMode.CHECK
            if self.effective_dry_run
            else c.Infra.CodegenConformMode.APPLY
        )
        conformed = FlextInfraCodegenConform.execute_request(
            m.Infra.CodegenConformRequest(
                root=self.repository_root,
                what=c.Infra.CodegenConformSurface.MAKEFILE,
                scope=c.Infra.CodegenConformScope.SELF,
                mode=mode,
            )
        )
        if conformed.failure:
            return r[bool].from_failure(conformed)
        return r[bool].ok(True)


__all__: list[str] = ["FlextInfraCodegenMakeBootstrap"]
