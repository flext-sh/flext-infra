# @generated AUTO-GENERATED FILE — Regenerate with: make gen
"""Flext Cli.services. Cli Parts package."""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_core.lazy import build_lazy_import_map, install_lazy_exports

if TYPE_CHECKING:
    from .flextclicli_part_05 import FlextCliCli as FlextCliCli

_LAZY_MODULES: dict[str, tuple[str, ...]] = {".flextclicli_part_05": ("FlextCliCli",)}


_LAZY_ALIAS_GROUPS: dict[str, tuple[tuple[str, str], ...]] = {}


_LAZY_IMPORTS = build_lazy_import_map(
    _LAZY_MODULES, alias_groups=_LAZY_ALIAS_GROUPS, sort_keys=False
)

_PUBLIC_EXPORTS: tuple[str, ...] = ("FlextCliCli",)

__all__: tuple[str, ...] = tuple(_PUBLIC_EXPORTS)

install_lazy_exports(__name__, globals(), _LAZY_IMPORTS, public_exports=__all__)
