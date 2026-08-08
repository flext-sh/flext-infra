# @generated AUTO-GENERATED FILE — Regenerate with: make gen
"""Flext Cli.services package."""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_core.lazy import build_lazy_import_map, install_lazy_exports

if TYPE_CHECKING:
    from . import _cli_parts as _cli_parts
    from .auth import FlextCliAuth as FlextCliAuth
    from .cli import FlextCliCli as FlextCliCli
    from .cli_params import FlextCliCommonParams as FlextCliCommonParams
    from .cmd import FlextCliCmd as FlextCliCmd
    from .docx import FlextCliDocx as FlextCliDocx
    from .file_tools import FlextCliFileTools as FlextCliFileTools
    from .formatters import FlextCliFormatters as FlextCliFormatters
    from .output import FlextCliOutput as FlextCliOutput
    from .pipeline import FlextCliPipeline as FlextCliPipeline
    from .pptx import FlextCliPptx as FlextCliPptx
    from .prompts import FlextCliPrompts as FlextCliPrompts
    from .rules import FlextCliRules as FlextCliRules
    from .runtime import FlextCliRuntime as FlextCliRuntime
    from .tables import FlextCliTables as FlextCliTables
    from .xlsx import FlextCliXlsx as FlextCliXlsx
    from .yaml_model import FlextCliYamlModel as FlextCliYamlModel

_LAZY_MODULES: dict[str, tuple[str, ...]] = {
    "._cli_parts": ("_cli_parts",),
    ".auth": ("FlextCliAuth",),
    ".cli": ("FlextCliCli",),
    ".cli_params": ("FlextCliCommonParams",),
    ".cmd": ("FlextCliCmd",),
    ".docx": ("FlextCliDocx",),
    ".file_tools": ("FlextCliFileTools",),
    ".formatters": ("FlextCliFormatters",),
    ".output": ("FlextCliOutput",),
    ".pipeline": ("FlextCliPipeline",),
    ".pptx": ("FlextCliPptx",),
    ".prompts": ("FlextCliPrompts",),
    ".rules": ("FlextCliRules",),
    ".runtime": ("FlextCliRuntime",),
    ".tables": ("FlextCliTables",),
    ".xlsx": ("FlextCliXlsx",),
    ".yaml_model": ("FlextCliYamlModel",),
}


_LAZY_ALIAS_GROUPS: dict[str, tuple[tuple[str, str], ...]] = {}


_LAZY_IMPORTS = build_lazy_import_map(
    _LAZY_MODULES, alias_groups=_LAZY_ALIAS_GROUPS, sort_keys=False
)

_PUBLIC_EXPORTS: tuple[str, ...] = (
    "FlextCliAuth",
    "FlextCliCli",
    "FlextCliCmd",
    "FlextCliCommonParams",
    "FlextCliDocx",
    "FlextCliFileTools",
    "FlextCliFormatters",
    "FlextCliOutput",
    "FlextCliPipeline",
    "FlextCliPptx",
    "FlextCliPrompts",
    "FlextCliRules",
    "FlextCliRuntime",
    "FlextCliTables",
    "FlextCliXlsx",
    "FlextCliYamlModel",
    "_cli_parts",
)

__all__: tuple[str, ...] = tuple(_PUBLIC_EXPORTS)

install_lazy_exports(__name__, globals(), _LAZY_IMPORTS, public_exports=__all__)
