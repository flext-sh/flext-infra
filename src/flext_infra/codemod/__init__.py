# AUTO-GENERATED FILE — Regenerate with: make gen
"""Flext Infra.codemod package."""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_core.lazy import build_lazy_import_map, install_lazy_exports

if TYPE_CHECKING:
    from .batch_apply import FlextInfraCodemodBatchApply
    from .batch_gates import FlextInfraModGateEngine, FlextInfraModGateSnapshot
    from .discovery import discover_rule_ids, discover_rules

_LAZY_MODULES: dict[str, tuple[str, ...]] = {
    ".batch_apply": ("FlextInfraCodemodBatchApply",),
    ".batch_gates": ("FlextInfraModGateEngine", "FlextInfraModGateSnapshot"),
    ".discovery": ("discover_rule_ids", "discover_rules"),
}


_LAZY_ALIAS_GROUPS: dict[str, tuple[tuple[str, str], ...]] = {}


_LAZY_IMPORTS = build_lazy_import_map(
    _LAZY_MODULES, alias_groups=_LAZY_ALIAS_GROUPS, sort_keys=False
)

__all__: tuple[str, ...] = (
    "FlextInfraCodemodBatchApply",
    "FlextInfraModGateEngine",
    "FlextInfraModGateSnapshot",
    "discover_rule_ids",
    "discover_rules",
)

install_lazy_exports(__name__, globals(), _LAZY_IMPORTS, public_exports=__all__)
