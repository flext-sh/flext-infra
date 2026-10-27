# AUTO-GENERATED FILE — Regenerate with: make gen
"""Flext Infra. Utilities. Rope package.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from types import MappingProxyType
from typing import TYPE_CHECKING

from flext_core.lazy import install_lazy_exports

if TYPE_CHECKING:
    from flext_infra._utilities._rope.inventory_sites import (
        FlextInfraUtilitiesRopeInventorySitesMixin,
    )
    from flext_infra._utilities._rope.method_order import (
        FlextInfraUtilitiesRopeMethodOrderMixin,
    )
    from flext_infra._utilities._rope.move_publication import (
        FlextInfraUtilitiesRopeMovePublication,
    )
    from flext_infra._utilities._rope.native_project import FlextInfraRopeNativeProject
    from flext_infra._utilities._rope.project import FlextInfraRopeProject
    from flext_infra._utilities._rope.pymodule import (
        FlextInfraUtilitiesRopeCorePyModuleMixin,
    )
    from flext_infra._utilities._rope.restructure import FlextInfraRopeRestructure
    from flext_infra._utilities._rope.rope_analysis import (
        FlextInfraUtilitiesRopeAnalysis,
    )
    from flext_infra._utilities._rope.rope_class_move import (
        FlextInfraUtilitiesRopeClassMove,
    )
    from flext_infra._utilities._rope.rope_core import FlextInfraUtilitiesRopeCore
    from flext_infra._utilities._rope.rope_core_resources import (
        FlextInfraUtilitiesRopeCoreResourcesMixin,
    )
    from flext_infra._utilities._rope.rope_helpers import FlextInfraUtilitiesRopeHelpers
    from flext_infra._utilities._rope.rope_imports import FlextInfraUtilitiesRopeImports
    from flext_infra._utilities._rope.rope_inventory import (
        FlextInfraUtilitiesRopeInventory,
    )
    from flext_infra._utilities._rope.rope_module_patch import (
        FlextInfraUtilitiesRopeModulePatch,
    )
    from flext_infra._utilities._rope.rope_nested_class_move import (
        FlextInfraUtilitiesRopeNestedClassMove,
    )
    from flext_infra._utilities._rope.rope_runtime import FlextInfraUtilitiesRopeRuntime
    from flext_infra._utilities._rope.rope_runtime_base import (
        FlextInfraUtilitiesRopeRuntimeBase,
    )
    from flext_infra._utilities._rope.rope_runtime_matching import (
        FlextInfraUtilitiesRopeRuntimeMatching,
    )
    from flext_infra._utilities._rope.rope_runtime_module_queries import (
        FlextInfraUtilitiesRopeRuntimeModuleQueries,
    )
    from flext_infra._utilities._rope.rope_runtime_modules import (
        FlextInfraUtilitiesRopeRuntimeModules,
    )
    from flext_infra._utilities._rope.rope_runtime_refactors import (
        FlextInfraUtilitiesRopeRuntimeRefactors,
    )
    from flext_infra._utilities._rope.rope_runtime_types import (
        FlextInfraUtilitiesRopeRuntimeTypes,
    )
    from flext_infra._utilities._rope.rope_source import FlextInfraUtilitiesRopeSource
    from flext_infra._utilities._rope.rope_source_bases_runtime import (
        FlextInfraUtilitiesRopeSourceBasesRuntime,
    )
    from flext_infra._utilities._rope.rope_structure import (
        FlextInfraUtilitiesRopeStructure,
    )
    from flext_infra._utilities._rope.source_bases_aliases import (
        FlextInfraUtilitiesRopeSourceBasesAliases,
    )
    from flext_infra._utilities._rope.source_bases_inventory import (
        FlextInfraUtilitiesRopeSourceBasesInventory,
    )
    from flext_infra._utilities._rope.source_bases_inventory_collector import (
        FlextInfraUtilitiesRopeSourceBindingCollector,
    )


__all__: tuple[str, ...] = (
    "FlextInfraRopeNativeProject",
    "FlextInfraRopeProject",
    "FlextInfraRopeRestructure",
    "FlextInfraUtilitiesRopeAnalysis",
    "FlextInfraUtilitiesRopeClassMove",
    "FlextInfraUtilitiesRopeCore",
    "FlextInfraUtilitiesRopeCorePyModuleMixin",
    "FlextInfraUtilitiesRopeCoreResourcesMixin",
    "FlextInfraUtilitiesRopeHelpers",
    "FlextInfraUtilitiesRopeImports",
    "FlextInfraUtilitiesRopeInventory",
    "FlextInfraUtilitiesRopeInventorySitesMixin",
    "FlextInfraUtilitiesRopeMethodOrderMixin",
    "FlextInfraUtilitiesRopeModulePatch",
    "FlextInfraUtilitiesRopeMovePublication",
    "FlextInfraUtilitiesRopeNestedClassMove",
    "FlextInfraUtilitiesRopeRuntime",
    "FlextInfraUtilitiesRopeRuntimeBase",
    "FlextInfraUtilitiesRopeRuntimeMatching",
    "FlextInfraUtilitiesRopeRuntimeModuleQueries",
    "FlextInfraUtilitiesRopeRuntimeModules",
    "FlextInfraUtilitiesRopeRuntimeRefactors",
    "FlextInfraUtilitiesRopeRuntimeTypes",
    "FlextInfraUtilitiesRopeSource",
    "FlextInfraUtilitiesRopeSourceBasesAliases",
    "FlextInfraUtilitiesRopeSourceBasesInventory",
    "FlextInfraUtilitiesRopeSourceBasesRuntime",
    "FlextInfraUtilitiesRopeSourceBindingCollector",
    "FlextInfraUtilitiesRopeStructure",
)

install_lazy_exports(
    __name__,
    globals(),
    MappingProxyType({
        "FlextInfraRopeNativeProject": ".native_project",
        "FlextInfraRopeProject": ".project",
        "FlextInfraRopeRestructure": ".restructure",
        "FlextInfraUtilitiesRopeAnalysis": ".rope_analysis",
        "FlextInfraUtilitiesRopeClassMove": ".rope_class_move",
        "FlextInfraUtilitiesRopeCore": ".rope_core",
        "FlextInfraUtilitiesRopeCorePyModuleMixin": ".pymodule",
        "FlextInfraUtilitiesRopeCoreResourcesMixin": ".rope_core_resources",
        "FlextInfraUtilitiesRopeHelpers": ".rope_helpers",
        "FlextInfraUtilitiesRopeImports": ".rope_imports",
        "FlextInfraUtilitiesRopeInventory": ".rope_inventory",
        "FlextInfraUtilitiesRopeInventorySitesMixin": ".inventory_sites",
        "FlextInfraUtilitiesRopeMethodOrderMixin": ".method_order",
        "FlextInfraUtilitiesRopeModulePatch": ".rope_module_patch",
        "FlextInfraUtilitiesRopeMovePublication": ".move_publication",
        "FlextInfraUtilitiesRopeNestedClassMove": ".rope_nested_class_move",
        "FlextInfraUtilitiesRopeRuntime": ".rope_runtime",
        "FlextInfraUtilitiesRopeRuntimeBase": ".rope_runtime_base",
        "FlextInfraUtilitiesRopeRuntimeMatching": ".rope_runtime_matching",
        "FlextInfraUtilitiesRopeRuntimeModuleQueries": ".rope_runtime_module_queries",
        "FlextInfraUtilitiesRopeRuntimeModules": ".rope_runtime_modules",
        "FlextInfraUtilitiesRopeRuntimeRefactors": ".rope_runtime_refactors",
        "FlextInfraUtilitiesRopeRuntimeTypes": ".rope_runtime_types",
        "FlextInfraUtilitiesRopeSource": ".rope_source",
        "FlextInfraUtilitiesRopeSourceBasesAliases": ".source_bases_aliases",
        "FlextInfraUtilitiesRopeSourceBasesInventory": ".source_bases_inventory",
        "FlextInfraUtilitiesRopeSourceBasesRuntime": ".rope_source_bases_runtime",
        "FlextInfraUtilitiesRopeSourceBindingCollector": (
            ".source_bases_inventory_collector"
        ),
        "FlextInfraUtilitiesRopeStructure": ".rope_structure",
    }),
    public_exports=__all__,
)
