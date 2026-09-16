# AUTO-GENERATED FILE — Regenerate with: make gen
"""Flext Infra. Models. Codegen package."""

from __future__ import annotations

from types import MappingProxyType
from typing import TYPE_CHECKING

from flext_core.lazy import build_lazy_import_map, install_lazy_exports

if TYPE_CHECKING:
    from .base import (
        FlextInfraModelsCodegenCensus,
        FlextInfraModelsCodegenFixModels,
        FlextInfraModelsCodegenJournal,
        FlextInfraModelsCodegenLazyInitModels,
        FlextInfraModelsCodegenPipelineModels,
        FlextInfraModelsCodegenPolicy,
        FlextInfraModelsCodegenResults,
        FlextInfraModelsCodegenScaffoldModels,
        FlextInfraModelsCodegenSession,
    )
__all__: tuple[str, ...] = (
    "FlextInfraModelsCodegenCensus",
    "FlextInfraModelsCodegenFixModels",
    "FlextInfraModelsCodegenJournal",
    "FlextInfraModelsCodegenLazyInitModels",
    "FlextInfraModelsCodegenPipelineModels",
    "FlextInfraModelsCodegenPolicy",
    "FlextInfraModelsCodegenResults",
    "FlextInfraModelsCodegenScaffoldModels",
    "FlextInfraModelsCodegenSession",
)

_LAZY_IMPORTS = MappingProxyType(
    build_lazy_import_map(
        MappingProxyType({
            ".base": (
                "FlextInfraModelsCodegenCensus",
                "FlextInfraModelsCodegenFixModels",
                "FlextInfraModelsCodegenJournal",
                "FlextInfraModelsCodegenLazyInitModels",
                "FlextInfraModelsCodegenPipelineModels",
                "FlextInfraModelsCodegenPolicy",
                "FlextInfraModelsCodegenResults",
                "FlextInfraModelsCodegenScaffoldModels",
                "FlextInfraModelsCodegenSession",
            )
        }),
        alias_groups=MappingProxyType({}),
        sort_keys=False,
    )
)

install_lazy_exports(__name__, globals(), _LAZY_IMPORTS, public_exports=__all__)
