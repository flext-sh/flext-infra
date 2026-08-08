# @generated AUTO-GENERATED FILE — Regenerate with: make gen
"""Flext Cli. Utilities. Xlxx package."""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_core.lazy import build_lazy_import_map, install_lazy_exports

if TYPE_CHECKING:
    from .xlsx_addresses import (
        FlextCliUtilitiesXlsxAddresses as FlextCliUtilitiesXlsxAddresses,
    )
    from .xlsx_archive import (
        FlextCliUtilitiesXlsxArchive as FlextCliUtilitiesXlsxArchive,
    )
    from .xlsx_archive_checks import (
        FlextCliUtilitiesXlsxArchiveChecks as FlextCliUtilitiesXlsxArchiveChecks,
    )
    from .xlsx_cells import FlextCliUtilitiesXlsxCells as FlextCliUtilitiesXlsxCells
    from .xlsx_conditional import (
        FlextCliUtilitiesXlsxConditional as FlextCliUtilitiesXlsxConditional,
    )
    from .xlsx_defined_name_values import (
        FlextCliUtilitiesXlsxDefinedNameValues as FlextCliUtilitiesXlsxDefinedNameValues,
    )
    from .xlsx_formula_codec import (
        FlextCliUtilitiesXlsxFormulaCodec as FlextCliUtilitiesXlsxFormulaCodec,
    )
    from .xlsx_layout import FlextCliUtilitiesXlsxLayout as FlextCliUtilitiesXlsxLayout
    from .xlsx_protection import (
        FlextCliUtilitiesXlsxProtection as FlextCliUtilitiesXlsxProtection,
    )
    from .xlsx_recalc import FlextCliUtilitiesXlsxRecalc as FlextCliUtilitiesXlsxRecalc
    from .xlsx_recalc_evidence import (
        FlextCliUtilitiesXlsxRecalcEvidence as FlextCliUtilitiesXlsxRecalcEvidence,
    )
    from .xlsx_renderer import (
        FlextCliUtilitiesXlsxRenderer as FlextCliUtilitiesXlsxRenderer,
    )
    from .xlsx_rules import FlextCliUtilitiesXlsxRules as FlextCliUtilitiesXlsxRules
    from .xlsx_snapshot import (
        FlextCliUtilitiesXlsxSnapshot as FlextCliUtilitiesXlsxSnapshot,
    )
    from .xlsx_snapshot_sheet import (
        FlextCliUtilitiesXlsxSnapshotSheet as FlextCliUtilitiesXlsxSnapshotSheet,
    )
    from .xlsx_snapshot_structure import (
        FlextCliUtilitiesXlsxSnapshotStructure as FlextCliUtilitiesXlsxSnapshotStructure,
    )
    from .xlsx_snapshot_values import (
        FlextCliUtilitiesXlsxSnapshotValues as FlextCliUtilitiesXlsxSnapshotValues,
    )
    from .xlsx_style_builders import (
        FlextCliUtilitiesXlsxStyleBuilders as FlextCliUtilitiesXlsxStyleBuilders,
    )
    from .xlsx_style_catalog import (
        FlextCliUtilitiesXlsxStyleCatalog as FlextCliUtilitiesXlsxStyleCatalog,
    )
    from .xlsx_style_codec import (
        FlextCliUtilitiesXlsxStyleCodec as FlextCliUtilitiesXlsxStyleCodec,
    )
    from .xlsx_style_readers import (
        FlextCliUtilitiesXlsxStyleReaders as FlextCliUtilitiesXlsxStyleReaders,
    )
    from .xlsx_tables import FlextCliUtilitiesXlsxTables as FlextCliUtilitiesXlsxTables
    from .xlsx_validations import (
        FlextCliUtilitiesXlsxValidations as FlextCliUtilitiesXlsxValidations,
    )
    from .xlsx_workbook_io import (
        FlextCliUtilitiesXlsxWorkbookIo as FlextCliUtilitiesXlsxWorkbookIo,
    )
    from .xlsx_workbook_plan import (
        FlextCliUtilitiesXlsxWorkbookPlan as FlextCliUtilitiesXlsxWorkbookPlan,
    )

_LAZY_MODULES: dict[str, tuple[str, ...]] = {
    ".xlsx_addresses": ("FlextCliUtilitiesXlsxAddresses",),
    ".xlsx_archive": ("FlextCliUtilitiesXlsxArchive",),
    ".xlsx_archive_checks": ("FlextCliUtilitiesXlsxArchiveChecks",),
    ".xlsx_cells": ("FlextCliUtilitiesXlsxCells",),
    ".xlsx_conditional": ("FlextCliUtilitiesXlsxConditional",),
    ".xlsx_defined_name_values": ("FlextCliUtilitiesXlsxDefinedNameValues",),
    ".xlsx_formula_codec": ("FlextCliUtilitiesXlsxFormulaCodec",),
    ".xlsx_layout": ("FlextCliUtilitiesXlsxLayout",),
    ".xlsx_protection": ("FlextCliUtilitiesXlsxProtection",),
    ".xlsx_recalc": ("FlextCliUtilitiesXlsxRecalc",),
    ".xlsx_recalc_evidence": ("FlextCliUtilitiesXlsxRecalcEvidence",),
    ".xlsx_renderer": ("FlextCliUtilitiesXlsxRenderer",),
    ".xlsx_rules": ("FlextCliUtilitiesXlsxRules",),
    ".xlsx_snapshot": ("FlextCliUtilitiesXlsxSnapshot",),
    ".xlsx_snapshot_sheet": ("FlextCliUtilitiesXlsxSnapshotSheet",),
    ".xlsx_snapshot_structure": ("FlextCliUtilitiesXlsxSnapshotStructure",),
    ".xlsx_snapshot_values": ("FlextCliUtilitiesXlsxSnapshotValues",),
    ".xlsx_style_builders": ("FlextCliUtilitiesXlsxStyleBuilders",),
    ".xlsx_style_catalog": ("FlextCliUtilitiesXlsxStyleCatalog",),
    ".xlsx_style_codec": ("FlextCliUtilitiesXlsxStyleCodec",),
    ".xlsx_style_readers": ("FlextCliUtilitiesXlsxStyleReaders",),
    ".xlsx_tables": ("FlextCliUtilitiesXlsxTables",),
    ".xlsx_validations": ("FlextCliUtilitiesXlsxValidations",),
    ".xlsx_workbook_io": ("FlextCliUtilitiesXlsxWorkbookIo",),
    ".xlsx_workbook_plan": ("FlextCliUtilitiesXlsxWorkbookPlan",),
}


_LAZY_ALIAS_GROUPS: dict[str, tuple[tuple[str, str], ...]] = {}


_LAZY_IMPORTS = build_lazy_import_map(
    _LAZY_MODULES, alias_groups=_LAZY_ALIAS_GROUPS, sort_keys=False
)

_PUBLIC_EXPORTS: tuple[str, ...] = (
    "FlextCliUtilitiesXlsxAddresses",
    "FlextCliUtilitiesXlsxArchive",
    "FlextCliUtilitiesXlsxArchiveChecks",
    "FlextCliUtilitiesXlsxCells",
    "FlextCliUtilitiesXlsxConditional",
    "FlextCliUtilitiesXlsxDefinedNameValues",
    "FlextCliUtilitiesXlsxFormulaCodec",
    "FlextCliUtilitiesXlsxLayout",
    "FlextCliUtilitiesXlsxProtection",
    "FlextCliUtilitiesXlsxRecalc",
    "FlextCliUtilitiesXlsxRecalcEvidence",
    "FlextCliUtilitiesXlsxRenderer",
    "FlextCliUtilitiesXlsxRules",
    "FlextCliUtilitiesXlsxSnapshot",
    "FlextCliUtilitiesXlsxSnapshotSheet",
    "FlextCliUtilitiesXlsxSnapshotStructure",
    "FlextCliUtilitiesXlsxSnapshotValues",
    "FlextCliUtilitiesXlsxStyleBuilders",
    "FlextCliUtilitiesXlsxStyleCatalog",
    "FlextCliUtilitiesXlsxStyleCodec",
    "FlextCliUtilitiesXlsxStyleReaders",
    "FlextCliUtilitiesXlsxTables",
    "FlextCliUtilitiesXlsxValidations",
    "FlextCliUtilitiesXlsxWorkbookIo",
    "FlextCliUtilitiesXlsxWorkbookPlan",
)

__all__: tuple[str, ...] = tuple(_PUBLIC_EXPORTS)

install_lazy_exports(__name__, globals(), _LAZY_IMPORTS, public_exports=__all__)
