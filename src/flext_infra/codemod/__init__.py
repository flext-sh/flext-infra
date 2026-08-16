# AUTO-GENERATED FILE — Regenerate with: make gen
"""Flext Infra.codemod package."""

from __future__ import annotations

from typing import TYPE_CHECKING

from types import MappingProxyType

from flext_core.lazy import build_lazy_import_map, install_lazy_exports

if TYPE_CHECKING:
    from .apply_renames import FlextInfraApplyRenames
    from .batch_apply import FlextInfraCodemodBatchApply
    from .batch_gates import (
        FlextInfraModGateEngine,
        FlextInfraModGateSnapshot,
        FlextInfraModScanReport,
    )
    from .discovery import discover_rule_ids, discover_rules
__all__: tuple[str, ...] = (
    "FlextInfraApplyRenames",
    "FlextInfraCodemodBatchApply",
    "FlextInfraModGateEngine",
    "FlextInfraModGateSnapshot",
    "FlextInfraModScanReport",
    "discover_rule_ids",
    "discover_rules",
)

install_lazy_exports(
    __name__,
    globals(),
    MappingProxyType(
        build_lazy_import_map(
            MappingProxyType({
                ".apply_renames": ("FlextInfraApplyRenames",),
                ".batch_apply": ("FlextInfraCodemodBatchApply",),
                ".batch_gates": (
                    "FlextInfraModGateEngine",
                    "FlextInfraModGateSnapshot",
                    "FlextInfraModScanReport",
                ),
                ".discovery": ("discover_rule_ids", "discover_rules"),
            }),
            alias_groups=MappingProxyType({}),
            sort_keys=False,
        )
    ),
    public_exports=__all__,
)
