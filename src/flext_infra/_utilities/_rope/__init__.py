# AUTO-GENERATED FILE — Regenerate with: make gen
"""Flext Infra. Utilities. Rope package."""

from __future__ import annotations

from types import MappingProxyType
from typing import TYPE_CHECKING

from flext_core.lazy import build_lazy_import_map, install_lazy_exports

if TYPE_CHECKING:
    from .analysis import FlextInfraUtilitiesRopeAnalysisAnalysis
    from .ast import FlextInfraUtilitiesRopeAnalysisAst
    from .base import FlextInfraUtilitiesRopeAnalysisBase
    from .imports import FlextInfraUtilitiesRopeAnalysisImports
    from .nodes import FlextInfraUtilitiesRopeAnalysisNodes
    from .pep695_patch import FlextInfraUtilitiesRopePep695Patch
    from .project import FlextInfraRopeProject
    from .scope import FlextInfraUtilitiesRopeAnalysisScope
    from .source import FlextInfraUtilitiesRopeAnalysisSource
__all__: tuple[str, ...] = (
    "FlextInfraRopeProject",
    "FlextInfraUtilitiesRopeAnalysisAnalysis",
    "FlextInfraUtilitiesRopeAnalysisAst",
    "FlextInfraUtilitiesRopeAnalysisBase",
    "FlextInfraUtilitiesRopeAnalysisImports",
    "FlextInfraUtilitiesRopeAnalysisNodes",
    "FlextInfraUtilitiesRopeAnalysisScope",
    "FlextInfraUtilitiesRopeAnalysisSource",
    "FlextInfraUtilitiesRopePep695Patch",
)

_LAZY_IMPORTS = MappingProxyType(
    build_lazy_import_map(
        MappingProxyType({
            ".analysis": ("FlextInfraUtilitiesRopeAnalysisAnalysis",),
            ".ast": ("FlextInfraUtilitiesRopeAnalysisAst",),
            ".base": ("FlextInfraUtilitiesRopeAnalysisBase",),
            ".imports": ("FlextInfraUtilitiesRopeAnalysisImports",),
            ".nodes": ("FlextInfraUtilitiesRopeAnalysisNodes",),
            ".pep695_patch": ("FlextInfraUtilitiesRopePep695Patch",),
            ".project": ("FlextInfraRopeProject",),
            ".scope": ("FlextInfraUtilitiesRopeAnalysisScope",),
            ".source": ("FlextInfraUtilitiesRopeAnalysisSource",),
        }),
        alias_groups=MappingProxyType({}),
        sort_keys=False,
    )
)

install_lazy_exports(__name__, globals(), _LAZY_IMPORTS, public_exports=__all__)
