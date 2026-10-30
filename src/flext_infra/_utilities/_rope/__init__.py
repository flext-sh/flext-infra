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
    from flext_infra._utilities._rope.analysis import FlextInfraUtilitiesRopeAnalysis
    from flext_infra._utilities._rope.ast import FlextInfraUtilitiesRopeAst
    from flext_infra._utilities._rope.bindings import FlextInfraUtilitiesRopeAstBindings
    from flext_infra._utilities._rope.class_move import FlextInfraUtilitiesRopeClassMove
    from flext_infra._utilities._rope.core import FlextInfraUtilitiesRopeCore
    from flext_infra._utilities._rope.core_resources import (
        FlextInfraUtilitiesRopeCoreResources,
    )
    from flext_infra._utilities._rope.helpers import FlextInfraUtilitiesRopeHelpers
    from flext_infra._utilities._rope.imports import FlextInfraUtilitiesRopeImports
    from flext_infra._utilities._rope.inventory import FlextInfraUtilitiesRopeInventory
    from flext_infra._utilities._rope.inventory_sites import (
        FlextInfraUtilitiesRopeInventorySites,
    )
    from flext_infra._utilities._rope.method_order import (
        FlextInfraUtilitiesRopeMethodOrder,
    )
    from flext_infra._utilities._rope.module_patch import (
        FlextInfraUtilitiesRopeModulePatch,
    )
    from flext_infra._utilities._rope.move_publication import (
        FlextInfraUtilitiesRopeMovePublication,
    )
    from flext_infra._utilities._rope.native_project import FlextInfraRopeNativeProject
    from flext_infra._utilities._rope.nested_class_move import (
        FlextInfraUtilitiesRopeNestedClassMove,
    )
    from flext_infra._utilities._rope.project import FlextInfraRopeProject
    from flext_infra._utilities._rope.pymodule import (
        FlextInfraUtilitiesRopeCorePyModule,
    )
    from flext_infra._utilities._rope.restructure import FlextInfraRopeRestructure
    from flext_infra._utilities._rope.runtime import FlextInfraUtilitiesRopeRuntime
    from flext_infra._utilities._rope.runtime_base import (
        FlextInfraUtilitiesRopeRuntimeBase,
    )
    from flext_infra._utilities._rope.runtime_matching import (
        FlextInfraUtilitiesRopeRuntimeMatching,
    )
    from flext_infra._utilities._rope.runtime_module_queries import (
        FlextInfraUtilitiesRopeRuntimeModuleQueries,
    )
    from flext_infra._utilities._rope.runtime_modules import (
        FlextInfraUtilitiesRopeRuntimeModules,
    )
    from flext_infra._utilities._rope.runtime_refactors import (
        FlextInfraUtilitiesRopeRuntimeRefactors,
    )
    from flext_infra._utilities._rope.runtime_types import (
        FlextInfraUtilitiesTypesRopeRuntime,
    )
    from flext_infra._utilities._rope.source import FlextInfraUtilitiesRopeSource
    from flext_infra._utilities._rope.source_bases_aliases import (
        FlextInfraUtilitiesRopeSourceBasesAliases,
    )
    from flext_infra._utilities._rope.source_bases_inventory import (
        FlextInfraUtilitiesRopeSourceBasesInventory,
    )
    from flext_infra._utilities._rope.source_bases_inventory_collector import (
        FlextInfraUtilitiesRopeSourceBindingCollector,
    )
    from flext_infra._utilities._rope.source_bases_runtime import (
        FlextInfraUtilitiesRopeSourceBasesRuntime,
    )
    from flext_infra._utilities._rope.structure import FlextInfraUtilitiesRopeStructure


__all__: tuple[str, ...] = (
    "FlextInfraRopeNativeProject",
    "FlextInfraRopeProject",
    "FlextInfraRopeRestructure",
    "FlextInfraUtilitiesRopeAnalysis",
    "FlextInfraUtilitiesRopeAst",
    "FlextInfraUtilitiesRopeAstBindings",
    "FlextInfraUtilitiesRopeClassMove",
    "FlextInfraUtilitiesRopeCore",
    "FlextInfraUtilitiesRopeCorePyModule",
    "FlextInfraUtilitiesRopeCoreResources",
    "FlextInfraUtilitiesRopeHelpers",
    "FlextInfraUtilitiesRopeImports",
    "FlextInfraUtilitiesRopeInventory",
    "FlextInfraUtilitiesRopeInventorySites",
    "FlextInfraUtilitiesRopeMethodOrder",
    "FlextInfraUtilitiesRopeModulePatch",
    "FlextInfraUtilitiesRopeMovePublication",
    "FlextInfraUtilitiesRopeNestedClassMove",
    "FlextInfraUtilitiesRopeRuntime",
    "FlextInfraUtilitiesRopeRuntimeBase",
    "FlextInfraUtilitiesRopeRuntimeMatching",
    "FlextInfraUtilitiesRopeRuntimeModuleQueries",
    "FlextInfraUtilitiesRopeRuntimeModules",
    "FlextInfraUtilitiesRopeRuntimeRefactors",
    "FlextInfraUtilitiesRopeSource",
    "FlextInfraUtilitiesRopeSourceBasesAliases",
    "FlextInfraUtilitiesRopeSourceBasesInventory",
    "FlextInfraUtilitiesRopeSourceBasesRuntime",
    "FlextInfraUtilitiesRopeSourceBindingCollector",
    "FlextInfraUtilitiesRopeStructure",
    "FlextInfraUtilitiesTypesRopeRuntime",
)

install_lazy_exports(
    __name__,
    globals(),
    MappingProxyType({
        "FlextInfraRopeNativeProject": ".native_project",
        "FlextInfraRopeProject": ".project",
        "FlextInfraRopeRestructure": ".restructure",
        "FlextInfraUtilitiesRopeAnalysis": ".analysis",
        "FlextInfraUtilitiesRopeAst": ".ast",
        "FlextInfraUtilitiesRopeAstBindings": ".bindings",
        "FlextInfraUtilitiesRopeClassMove": ".class_move",
        "FlextInfraUtilitiesRopeCore": ".core",
        "FlextInfraUtilitiesRopeCorePyModule": ".pymodule",
        "FlextInfraUtilitiesRopeCoreResources": ".core_resources",
        "FlextInfraUtilitiesRopeHelpers": ".helpers",
        "FlextInfraUtilitiesRopeImports": ".imports",
        "FlextInfraUtilitiesRopeInventory": ".inventory",
        "FlextInfraUtilitiesRopeInventorySites": ".inventory_sites",
        "FlextInfraUtilitiesRopeMethodOrder": ".method_order",
        "FlextInfraUtilitiesRopeModulePatch": ".module_patch",
        "FlextInfraUtilitiesRopeMovePublication": ".move_publication",
        "FlextInfraUtilitiesRopeNestedClassMove": ".nested_class_move",
        "FlextInfraUtilitiesRopeRuntime": ".runtime",
        "FlextInfraUtilitiesRopeRuntimeBase": ".runtime_base",
        "FlextInfraUtilitiesRopeRuntimeMatching": ".runtime_matching",
        "FlextInfraUtilitiesRopeRuntimeModuleQueries": ".runtime_module_queries",
        "FlextInfraUtilitiesRopeRuntimeModules": ".runtime_modules",
        "FlextInfraUtilitiesRopeRuntimeRefactors": ".runtime_refactors",
        "FlextInfraUtilitiesTypesRopeRuntime": ".runtime_types",
        "FlextInfraUtilitiesRopeSource": ".source",
        "FlextInfraUtilitiesRopeSourceBasesAliases": ".source_bases_aliases",
        "FlextInfraUtilitiesRopeSourceBasesInventory": ".source_bases_inventory",
        "FlextInfraUtilitiesRopeSourceBasesRuntime": ".source_bases_runtime",
        "FlextInfraUtilitiesRopeSourceBindingCollector": (
            ".source_bases_inventory_collector"
        ),
        "FlextInfraUtilitiesRopeStructure": ".structure",
    }),
    public_exports=__all__,
)
