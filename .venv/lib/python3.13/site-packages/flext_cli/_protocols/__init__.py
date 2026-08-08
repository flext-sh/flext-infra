# @generated AUTO-GENERATED FILE — Regenerate with: make gen
"""Flext Cli. Protocols package."""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_core.lazy import build_lazy_import_map, install_lazy_exports

if TYPE_CHECKING:
    from . import _base_parts as _base_parts
    from .base import FlextCliProtocolsBase as FlextCliProtocolsBase
    from .config import FlextCliProtocolsConfig as FlextCliProtocolsConfig
    from .domain import FlextCliProtocolsDomain as FlextCliProtocolsDomain
    from .framework import FlextCliProtocolsFramework as FlextCliProtocolsFramework
    from .pipeline import FlextCliProtocolsPipeline as FlextCliProtocolsPipeline
    from .xlsx import FlextCliProtocolsXlsx as FlextCliProtocolsXlsx
    from .xlsx_archive import (
        FlextCliProtocolsXlsxArchive as FlextCliProtocolsXlsxArchive,
    )
    from .xlsx_rules import FlextCliProtocolsXlsxRules as FlextCliProtocolsXlsxRules
    from .xlsx_snapshot import (
        FlextCliProtocolsXlsxSnapshot as FlextCliProtocolsXlsxSnapshot,
    )
    from .xlsx_snapshot_structure import (
        FlextCliProtocolsXlsxSnapshotStructure as FlextCliProtocolsXlsxSnapshotStructure,
    )
    from .xlsx_workbook import (
        FlextCliProtocolsXlsxWorkbook as FlextCliProtocolsXlsxWorkbook,
    )

_LAZY_MODULES: dict[str, tuple[str, ...]] = {
    "._base_parts": ("_base_parts",),
    ".base": ("FlextCliProtocolsBase",),
    ".config": ("FlextCliProtocolsConfig",),
    ".domain": ("FlextCliProtocolsDomain",),
    ".framework": ("FlextCliProtocolsFramework",),
    ".pipeline": ("FlextCliProtocolsPipeline",),
    ".xlsx": ("FlextCliProtocolsXlsx",),
    ".xlsx_archive": ("FlextCliProtocolsXlsxArchive",),
    ".xlsx_rules": ("FlextCliProtocolsXlsxRules",),
    ".xlsx_snapshot": ("FlextCliProtocolsXlsxSnapshot",),
    ".xlsx_snapshot_structure": ("FlextCliProtocolsXlsxSnapshotStructure",),
    ".xlsx_workbook": ("FlextCliProtocolsXlsxWorkbook",),
}


_LAZY_ALIAS_GROUPS: dict[str, tuple[tuple[str, str], ...]] = {}


_LAZY_IMPORTS = build_lazy_import_map(
    _LAZY_MODULES, alias_groups=_LAZY_ALIAS_GROUPS, sort_keys=False
)

_PUBLIC_EXPORTS: tuple[str, ...] = (
    "FlextCliProtocolsBase",
    "FlextCliProtocolsConfig",
    "FlextCliProtocolsDomain",
    "FlextCliProtocolsFramework",
    "FlextCliProtocolsPipeline",
    "FlextCliProtocolsXlsx",
    "FlextCliProtocolsXlsxArchive",
    "FlextCliProtocolsXlsxRules",
    "FlextCliProtocolsXlsxSnapshot",
    "FlextCliProtocolsXlsxSnapshotStructure",
    "FlextCliProtocolsXlsxWorkbook",
    "_base_parts",
)

__all__: tuple[str, ...] = tuple(_PUBLIC_EXPORTS)

install_lazy_exports(__name__, globals(), _LAZY_IMPORTS, public_exports=__all__)
