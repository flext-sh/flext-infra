# AUTO-GENERATED FILE — Regenerate with: make gen
"""Flext Infra. Protocols. Codegen package.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_core.lazy import install_lazy_exports

if TYPE_CHECKING:
    from flext_infra._protocols._codegen.fix import FlextInfraProtocolsCodegenFix
    from flext_infra._protocols._codegen.lazy_init import (
        FlextInfraProtocolsCodegenLazyInit,
    )
    from flext_infra._protocols._codegen.pipeline import (
        FlextInfraProtocolsCodegenPipeline,
    )
    from flext_infra._protocols._codegen.scaffold import (
        FlextInfraProtocolsCodegenScaffold,
    )
    from flext_infra._protocols._codegen.transaction import (
        FlextInfraProtocolsCodegenTransaction,
    )


__all__: tuple[str, ...] = (
    "FlextInfraProtocolsCodegenFix",
    "FlextInfraProtocolsCodegenLazyInit",
    "FlextInfraProtocolsCodegenPipeline",
    "FlextInfraProtocolsCodegenScaffold",
    "FlextInfraProtocolsCodegenTransaction",
)

install_lazy_exports(
    __name__,
    globals(),
    {
        "FlextInfraProtocolsCodegenFix": ".fix",
        "FlextInfraProtocolsCodegenLazyInit": ".lazy_init",
        "FlextInfraProtocolsCodegenPipeline": ".pipeline",
        "FlextInfraProtocolsCodegenScaffold": ".scaffold",
        "FlextInfraProtocolsCodegenTransaction": ".transaction",
    },
    public_exports=__all__,
    deferred_members={
        "FlextInfraProtocolsCodegenFix": (
            "AutoFixResult",
            "ConsolidatorFileResult",
            "ConsolidatorReport",
            "FacadeFamily",
            "NamespaceModulePolicy",
            "FixContext",
            "ViolationKey",
        ),
        "FlextInfraProtocolsCodegenLazyInit": (
            "PythonModuleFacts",
            "PythonModuleFactsDraft",
            "PythonModelRun",
            "LazyInitPackageContext",
            "LazyInitPlan",
            "RopeModuleIndexEntry",
            "RopePackageIndexEntry",
            "RopeWorkspaceIndex",
            "LazyInitRun",
            "RopeProjectLayout",
            "LazyInitRootRender",
            "QualityGateCheck",
            "QualityGateProjectFinding",
        ),
        "FlextInfraProtocolsCodegenPipeline": (
            "CodegenCommand",
            "CodegenAutoFixCommand",
            "CandidateBootstrapCommand",
            "CodegenRootSelection",
            "CodegenRepositoryPlanOutcome",
            "CodegenPlan",
            "CodegenResult",
            "CodegenConformPorts",
            "CodegenConformState",
        ),
        "FlextInfraProtocolsCodegenScaffold": (
            "CensusViolation",
            "CensusReport",
            "ScaffoldResult",
            "ScaffoldDirRequest",
        ),
        "FlextInfraProtocolsCodegenTransaction": (
            "CodegenFilePlan",
            "StageSourceOptions",
            "StageSourcePlan",
            "SemanticSourcePlan",
        ),
    },
)
