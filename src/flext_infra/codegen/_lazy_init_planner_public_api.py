"""Public-API static helpers for the lazy-init planner."""

from __future__ import annotations

from typing import TYPE_CHECKING, override

from flext_infra.codegen._lazy_init_planner_public_root import (
    FlextInfraCodegenLazyInitPlannerPublicRootMixin,
)

if TYPE_CHECKING:
    from pathlib import Path


class FlextInfraCodegenLazyInitPlannerPublicApiMixin(
    FlextInfraCodegenLazyInitPlannerPublicRootMixin,
):
    """Root public contract helpers for the lazy-init planner."""

    @staticmethod
    @override
    def _root_public_contract_exports(pkg_dir: Path) -> frozenset[str]:
        """Root public contracts are generated into ``__init__.py`` only."""
        _ = pkg_dir
        return frozenset()


__all__: list[str] = ["FlextInfraCodegenLazyInitPlannerPublicApiMixin"]
