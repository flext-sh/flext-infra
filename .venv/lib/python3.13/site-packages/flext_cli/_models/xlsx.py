"""Private MRO composition for generic XLSX models."""

from __future__ import annotations

from .xlsx_archive import FlextCliModelsXlsxArchive
from .xlsx_cells import FlextCliModelsXlsxCells
from .xlsx_layout import FlextCliModelsXlsxLayout
from .xlsx_recalc import FlextCliModelsXlsxRecalc
from .xlsx_rules import FlextCliModelsXlsxRules
from .xlsx_snapshot import FlextCliModelsXlsxSnapshot
from .xlsx_style_catalog import FlextCliModelsXlsxStyleCatalog
from .xlsx_styles import FlextCliModelsXlsxStyles
from .xlsx_tables import FlextCliModelsXlsxTables
from .xlsx_validation import FlextCliModelsXlsxValidation
from .xlsx_workbook import FlextCliModelsXlsxWorkbook


class FlextCliModelsXlsx(
    FlextCliModelsXlsxSnapshot,
    FlextCliModelsXlsxRecalc,
    FlextCliModelsXlsxWorkbook,
    FlextCliModelsXlsxArchive,
    FlextCliModelsXlsxStyleCatalog,
    FlextCliModelsXlsxRules,
    FlextCliModelsXlsxValidation,
    FlextCliModelsXlsxTables,
    FlextCliModelsXlsxLayout,
    FlextCliModelsXlsxStyles,
    FlextCliModelsXlsxCells,
):
    """Canonical private XLSX model namespace."""

    # NOTE (multi-agent, mro-j2yt.1): snapshot declarations join the existing
    # XLSX namespace without a parallel public model surface.


__all__: tuple[str, ...] = ("FlextCliModelsXlsx",)
