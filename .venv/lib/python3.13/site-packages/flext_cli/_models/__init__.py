# @generated AUTO-GENERATED FILE — Regenerate with: make gen
"""Flext Cli. Models package."""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_core.lazy import build_lazy_import_map, install_lazy_exports

if TYPE_CHECKING:
    from . import _base_parts as _base_parts
    from .base import FlextCliModelsBase as FlextCliModelsBase
    from .config import FlextCliConfigModels as FlextCliConfigModels
    from .docx import FlextCliModelsDocx as FlextCliModelsDocx
    from .docx_document import FlextCliModelsDocxDocument as FlextCliModelsDocxDocument
    from .docx_styles import FlextCliModelsDocxStyles as FlextCliModelsDocxStyles
    from .pipeline import FlextCliModelsPipeline as FlextCliModelsPipeline
    from .pptx import FlextCliModelsPptx as FlextCliModelsPptx
    from .pptx_presentation import (
        FlextCliModelsPptxPresentation as FlextCliModelsPptxPresentation,
    )
    from .rules import FlextCliModelsRules as FlextCliModelsRules
    from .template import FlextCliModelsTemplate as FlextCliModelsTemplate
    from .xlsx import FlextCliModelsXlsx as FlextCliModelsXlsx
    from .xlsx_archive import FlextCliModelsXlsxArchive as FlextCliModelsXlsxArchive
    from .xlsx_cells import FlextCliModelsXlsxCells as FlextCliModelsXlsxCells
    from .xlsx_layout import FlextCliModelsXlsxLayout as FlextCliModelsXlsxLayout
    from .xlsx_recalc import FlextCliModelsXlsxRecalc as FlextCliModelsXlsxRecalc
    from .xlsx_rules import FlextCliModelsXlsxRules as FlextCliModelsXlsxRules
    from .xlsx_snapshot import FlextCliModelsXlsxSnapshot as FlextCliModelsXlsxSnapshot
    from .xlsx_style_catalog import (
        FlextCliModelsXlsxStyleCatalog as FlextCliModelsXlsxStyleCatalog,
    )
    from .xlsx_style_fills import (
        FlextCliModelsXlsxStyleFills as FlextCliModelsXlsxStyleFills,
    )
    from .xlsx_style_primitives import (
        FlextCliModelsXlsxStylePrimitives as FlextCliModelsXlsxStylePrimitives,
    )
    from .xlsx_styles import FlextCliModelsXlsxStyles as FlextCliModelsXlsxStyles
    from .xlsx_tables import FlextCliModelsXlsxTables as FlextCliModelsXlsxTables
    from .xlsx_validation import (
        FlextCliModelsXlsxValidation as FlextCliModelsXlsxValidation,
    )
    from .xlsx_workbook import FlextCliModelsXlsxWorkbook as FlextCliModelsXlsxWorkbook

_LAZY_MODULES: dict[str, tuple[str, ...]] = {
    "._base_parts": ("_base_parts",),
    ".base": ("FlextCliModelsBase",),
    ".config": ("FlextCliConfigModels",),
    ".docx": ("FlextCliModelsDocx",),
    ".docx_document": ("FlextCliModelsDocxDocument",),
    ".docx_styles": ("FlextCliModelsDocxStyles",),
    ".pipeline": ("FlextCliModelsPipeline",),
    ".pptx": ("FlextCliModelsPptx",),
    ".pptx_presentation": ("FlextCliModelsPptxPresentation",),
    ".rules": ("FlextCliModelsRules",),
    ".template": ("FlextCliModelsTemplate",),
    ".xlsx": ("FlextCliModelsXlsx",),
    ".xlsx_archive": ("FlextCliModelsXlsxArchive",),
    ".xlsx_cells": ("FlextCliModelsXlsxCells",),
    ".xlsx_layout": ("FlextCliModelsXlsxLayout",),
    ".xlsx_recalc": ("FlextCliModelsXlsxRecalc",),
    ".xlsx_rules": ("FlextCliModelsXlsxRules",),
    ".xlsx_snapshot": ("FlextCliModelsXlsxSnapshot",),
    ".xlsx_style_catalog": ("FlextCliModelsXlsxStyleCatalog",),
    ".xlsx_style_fills": ("FlextCliModelsXlsxStyleFills",),
    ".xlsx_style_primitives": ("FlextCliModelsXlsxStylePrimitives",),
    ".xlsx_styles": ("FlextCliModelsXlsxStyles",),
    ".xlsx_tables": ("FlextCliModelsXlsxTables",),
    ".xlsx_validation": ("FlextCliModelsXlsxValidation",),
    ".xlsx_workbook": ("FlextCliModelsXlsxWorkbook",),
}


_LAZY_ALIAS_GROUPS: dict[str, tuple[tuple[str, str], ...]] = {}


_LAZY_IMPORTS = build_lazy_import_map(
    _LAZY_MODULES, alias_groups=_LAZY_ALIAS_GROUPS, sort_keys=False
)

_PUBLIC_EXPORTS: tuple[str, ...] = (
    "FlextCliConfigModels",
    "FlextCliModelsBase",
    "FlextCliModelsDocx",
    "FlextCliModelsDocxDocument",
    "FlextCliModelsDocxStyles",
    "FlextCliModelsPipeline",
    "FlextCliModelsPptx",
    "FlextCliModelsPptxPresentation",
    "FlextCliModelsRules",
    "FlextCliModelsTemplate",
    "FlextCliModelsXlsx",
    "FlextCliModelsXlsxArchive",
    "FlextCliModelsXlsxCells",
    "FlextCliModelsXlsxLayout",
    "FlextCliModelsXlsxRecalc",
    "FlextCliModelsXlsxRules",
    "FlextCliModelsXlsxSnapshot",
    "FlextCliModelsXlsxStyleCatalog",
    "FlextCliModelsXlsxStyleFills",
    "FlextCliModelsXlsxStylePrimitives",
    "FlextCliModelsXlsxStyles",
    "FlextCliModelsXlsxTables",
    "FlextCliModelsXlsxValidation",
    "FlextCliModelsXlsxWorkbook",
    "_base_parts",
)

__all__: tuple[str, ...] = tuple(_PUBLIC_EXPORTS)

install_lazy_exports(__name__, globals(), _LAZY_IMPORTS, public_exports=__all__)
