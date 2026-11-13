# AUTO-GENERATED FILE — Regenerate with: make gen
"""Flext Infra. Models. Codegen package.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_core.lazy import install_lazy_exports

if TYPE_CHECKING:
    from flext_infra._models._codegen.base import FlextInfraCodegen
    from flext_infra._models._codegen.fix import FlextInfraModelsCodegenFix
    from flext_infra._models._codegen.lazy_init import FlextInfraModelsCodegenLazyInit
    from flext_infra._models._codegen.pipeline import FlextInfraModelsCodegenPipeline
    from flext_infra._models._codegen.scaffold import FlextInfraModelsCodegenScaffold
    from flext_infra._models._codegen.transaction import (
        FlextInfraModelsCodegenTransaction,
    )


__all__: tuple[str, ...] = (
    "FlextInfraCodegen",
    "FlextInfraModelsCodegenFix",
    "FlextInfraModelsCodegenLazyInit",
    "FlextInfraModelsCodegenPipeline",
    "FlextInfraModelsCodegenScaffold",
    "FlextInfraModelsCodegenTransaction",
)

install_lazy_exports(
    __name__,
    globals(),
    {
        "FlextInfraCodegen": ".base",
        "FlextInfraModelsCodegenFix": ".fix",
        "FlextInfraModelsCodegenLazyInit": ".lazy_init",
        "FlextInfraModelsCodegenPipeline": ".pipeline",
        "FlextInfraModelsCodegenScaffold": ".scaffold",
        "FlextInfraModelsCodegenTransaction": ".transaction",
    },
    public_exports=__all__,
    deferred_members={
        "FlextInfraCodegen": (
            "MiseToolchainProjectLayout",
            "CodegenFileParticipant",
            "MiseToolchainWorkspaceLayout",
            "MiseToolchainConfigState",
            "MiseToolchainProjectState",
            "MiseToolchainWorkspacePlan",
            "ModelProtocolRenderContext",
            "GithubWorkflowProjectRenderSpec",
            "GithubWorkflowRenderSpec",
            "MakeWorkflowRenderSpec",
            "GitHookRenderSpec",
            "DistroDockerRenderSpec",
            "EnvrcRenderSpec",
            "SonarcloudRenderSpec",
            "UvResolutionSpec",
            "MarkdownRenderSpec",
            "QltyRenderSpec",
            "ModuleSkeletonRenderContext",
            "TestModuleSkeletonRenderContext",
            "MkdocsRenderContext",
            "MkdocsProjectRenderContext",
            "CodegenFilePlan",
            "StageSourceOptions",
            "StageSourcePlan",
            "SemanticSourcePlan",
            "CensusViolation",
            "CensusReport",
            "ScaffoldResult",
            "ScaffoldDirRequest",
            "AutoFixResult",
            "ConsolidatorFileResult",
            "ConsolidatorReport",
            "FacadeFamily",
            "NamespaceModulePolicy",
            "FixContext",
            "ViolationKey",
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
        "FlextInfraModelsCodegenFix": (
            "AutoFixResult",
            "ConsolidatorFileResult",
            "ConsolidatorReport",
            "FacadeFamily",
            "NamespaceModulePolicy",
            "FixContext",
            "ViolationKey",
        ),
        "FlextInfraModelsCodegenLazyInit": (
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
        "FlextInfraModelsCodegenPipeline": (
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
        "FlextInfraModelsCodegenScaffold": (
            "CensusViolation",
            "CensusReport",
            "ScaffoldResult",
            "ScaffoldDirRequest",
        ),
        "FlextInfraModelsCodegenTransaction": (
            "CodegenFilePlan",
            "StageSourceOptions",
            "StageSourcePlan",
            "SemanticSourcePlan",
        ),
    },
)
