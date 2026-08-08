# @generated AUTO-GENERATED FILE — Regenerate with: make gen
"""Flext Cli. Constants package."""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_core.lazy import build_lazy_import_map, install_lazy_exports

if TYPE_CHECKING:
    from .base import FlextCliConstantsBase as FlextCliConstantsBase
    from .config import FlextCliConstantsConfig as FlextCliConstantsConfig
    from .docx import FlextCliConstantsDocx as FlextCliConstantsDocx
    from .enums import FlextCliConstantsEnums as FlextCliConstantsEnums
    from .errors import FlextCliConstantsErrors as FlextCliConstantsErrors
    from .exceptions import (
        CliDefinitionError as CliDefinitionError,
        CliValidationError as CliValidationError,
        FlextCliConstantsExceptions as FlextCliConstantsExceptions,
    )
    from .files import FlextCliConstantsFiles as FlextCliConstantsFiles
    from .output import FlextCliConstantsOutput as FlextCliConstantsOutput
    from .pipeline import FlextCliConstantsPipeline as FlextCliConstantsPipeline
    from .pptx import FlextCliConstantsPptx as FlextCliConstantsPptx
    from .settings import FlextCliConstantsSettings as FlextCliConstantsSettings
    from .xlsx import FlextCliConstantsXlsx as FlextCliConstantsXlsx
    from .xlsx_future_functions import (
        FlextCliConstantsXlsxFutureFunctions as FlextCliConstantsXlsxFutureFunctions,
    )

_LAZY_MODULES: dict[str, tuple[str, ...]] = {
    ".base": ("FlextCliConstantsBase",),
    ".config": ("FlextCliConstantsConfig",),
    ".docx": ("FlextCliConstantsDocx",),
    ".enums": ("FlextCliConstantsEnums",),
    ".errors": ("FlextCliConstantsErrors",),
    ".exceptions": (
        "CliDefinitionError",
        "CliValidationError",
        "FlextCliConstantsExceptions",
    ),
    ".files": ("FlextCliConstantsFiles",),
    ".output": ("FlextCliConstantsOutput",),
    ".pipeline": ("FlextCliConstantsPipeline",),
    ".pptx": ("FlextCliConstantsPptx",),
    ".settings": ("FlextCliConstantsSettings",),
    ".xlsx": ("FlextCliConstantsXlsx",),
    ".xlsx_future_functions": ("FlextCliConstantsXlsxFutureFunctions",),
}


_LAZY_ALIAS_GROUPS: dict[str, tuple[tuple[str, str], ...]] = {}


_LAZY_IMPORTS = build_lazy_import_map(
    _LAZY_MODULES, alias_groups=_LAZY_ALIAS_GROUPS, sort_keys=False
)

_PUBLIC_EXPORTS: tuple[str, ...] = (
    "CliDefinitionError",
    "CliValidationError",
    "FlextCliConstantsBase",
    "FlextCliConstantsConfig",
    "FlextCliConstantsDocx",
    "FlextCliConstantsEnums",
    "FlextCliConstantsErrors",
    "FlextCliConstantsExceptions",
    "FlextCliConstantsFiles",
    "FlextCliConstantsOutput",
    "FlextCliConstantsPipeline",
    "FlextCliConstantsPptx",
    "FlextCliConstantsSettings",
    "FlextCliConstantsXlsx",
    "FlextCliConstantsXlsxFutureFunctions",
)

__all__: tuple[str, ...] = tuple(_PUBLIC_EXPORTS)

install_lazy_exports(__name__, globals(), _LAZY_IMPORTS, public_exports=__all__)
