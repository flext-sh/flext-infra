# AUTO-GENERATED FILE — Regenerate with: make gen

"""Flext Infra.check package."""

from __future__ import annotations
from flext_core.lazy import build_lazy_import_map, install_lazy_exports

_LAZY_MODULES: dict[str, tuple[str, ...]] = {
    ".workspace_check": ("FlextInfraWorkspaceChecker",),
    ".workspace_check_gates": (
        "FlextInfraGateRegistry",
        "FlextInfraWorkspaceCheckGatesMixin",
    ),
}

_LAZY_ALIAS_GROUPS: dict[str, tuple[tuple[str, str], ...]] = {}

_LAZY_IMPORTS = build_lazy_import_map(
    _LAZY_MODULES, alias_groups=_LAZY_ALIAS_GROUPS, sort_keys=False
)

__all__: tuple[str, ...] = ()

install_lazy_exports(__name__, globals(), _LAZY_IMPORTS, public_exports=__all__)
