"""Public-API static helpers for the lazy-init planner."""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_infra import c
from flext_infra.codegen._lazy_init_planner_public_root import (
    FlextInfraCodegenLazyInitPlannerPublicRootMixin,
)

from pathlib import Path

from flext_infra import p


class FlextInfraCodegenLazyInitPlannerPublicApiMixin(
    FlextInfraCodegenLazyInitPlannerPublicRootMixin
):
    """Root public contract helpers for the lazy-init planner."""

    # mro-wkii.17.26 (codex): preserve the declared ABI while one scaffold
    # template replaces project-specific root initializer implementations.
    def _root_public_contract_exports(self, pkg_dir: Path) -> frozenset[str]:
        """Return the root ``__all__`` contract resolved by Rope."""
        init_path = pkg_dir / c.Infra.INIT_PY
        if self.rope_workspace.resource(init_path) is None:
            return frozenset()
        return frozenset(self.rope_workspace.exports(init_path))

    if TYPE_CHECKING:
        rope_workspace: p.Infra.RopeWorkspaceDsl


__all__: list[str] = ["FlextInfraCodegenLazyInitPlannerPublicApiMixin"]
