# AUTO-GENERATED FILE — Regenerate with: make gen
"""Deps package."""

from __future__ import annotations

import typing as _t

from flext_core.lazy import (
    build_lazy_import_map,
    install_lazy_exports,
    merge_lazy_imports,
)

if _t.TYPE_CHECKING:
    from flext_infra.deps.detection import (
        FlextInfraDependencyDetectionService as FlextInfraDependencyDetectionService,
    )
    from flext_infra.deps.detection_analysis import (
        FlextInfraDependencyDetectionAnalysis as FlextInfraDependencyDetectionAnalysis,
    )
    from flext_infra.deps.detector import (
        FlextInfraRuntimeDevDependencyDetector as FlextInfraRuntimeDevDependencyDetector,
    )
    from flext_infra.deps.detector_runtime import (
        FlextInfraDependencyDetectorRuntime as FlextInfraDependencyDetectorRuntime,
    )
    from flext_infra.deps.extra_paths import (
        FlextInfraExtraPathsManager as FlextInfraExtraPathsManager,
    )
    from flext_infra.deps.fix_pyrefly_config import (
        FlextInfraConfigFixer as FlextInfraConfigFixer,
    )
    from flext_infra.deps.internal_sync import (
        FlextInfraInternalDependencySyncService as FlextInfraInternalDependencySyncService,
    )
    from flext_infra.deps.modernizer import (
        FlextInfraPyprojectModernizer as FlextInfraPyprojectModernizer,
    )
    from flext_infra.deps.phase_engine import (
        FlextInfraPhaseEngine as FlextInfraPhaseEngine,
    )
    from flext_infra.deps.phases import (
        FlextInfraConsolidateGroupsPhase as FlextInfraConsolidateGroupsPhase,
        FlextInfraEnsureCoverageConfigPhase as FlextInfraEnsureCoverageConfigPhase,
        FlextInfraEnsureFormattingToolingPhase as FlextInfraEnsureFormattingToolingPhase,
        FlextInfraEnsureMypyConfigPhase as FlextInfraEnsureMypyConfigPhase,
        FlextInfraEnsureNamespaceToolingPhase as FlextInfraEnsureNamespaceToolingPhase,
        FlextInfraEnsurePydanticMypyConfigPhase as FlextInfraEnsurePydanticMypyConfigPhase,
        FlextInfraEnsurePyreflyConfigPhase as FlextInfraEnsurePyreflyConfigPhase,
        FlextInfraEnsurePyrightConfigPhase as FlextInfraEnsurePyrightConfigPhase,
        FlextInfraEnsurePytestConfigPhase as FlextInfraEnsurePytestConfigPhase,
        FlextInfraEnsureRuffConfigPhase as FlextInfraEnsureRuffConfigPhase,
        FlextInfraInjectCommentsPhase as FlextInfraInjectCommentsPhase,
    )
_LAZY_IMPORTS = merge_lazy_imports(
    (".phases",),
    build_lazy_import_map(
        {
            ".detection": ("FlextInfraDependencyDetectionService",),
            ".detection_analysis": ("FlextInfraDependencyDetectionAnalysis",),
            ".detector": ("FlextInfraRuntimeDevDependencyDetector",),
            ".detector_runtime": ("FlextInfraDependencyDetectorRuntime",),
            ".extra_paths": ("FlextInfraExtraPathsManager",),
            ".fix_pyrefly_config": ("FlextInfraConfigFixer",),
            ".internal_sync": ("FlextInfraInternalDependencySyncService",),
            ".modernizer": ("FlextInfraPyprojectModernizer",),
            ".path_sync": ("path_sync",),
            ".phase_engine": ("FlextInfraPhaseEngine",),
            ".phases": ("phases",),
            ".phases.consolidate_groups": ("FlextInfraConsolidateGroupsPhase",),
            ".phases.ensure_coverage": ("FlextInfraEnsureCoverageConfigPhase",),
            ".phases.ensure_formatting": ("FlextInfraEnsureFormattingToolingPhase",),
            ".phases.ensure_mypy": ("FlextInfraEnsureMypyConfigPhase",),
            ".phases.ensure_namespace": ("FlextInfraEnsureNamespaceToolingPhase",),
            ".phases.ensure_pydantic_mypy": (
                "FlextInfraEnsurePydanticMypyConfigPhase",
            ),
            ".phases.ensure_pyrefly": ("FlextInfraEnsurePyreflyConfigPhase",),
            ".phases.ensure_pyright": ("FlextInfraEnsurePyrightConfigPhase",),
            ".phases.ensure_pytest": ("FlextInfraEnsurePytestConfigPhase",),
            ".phases.ensure_ruff": ("FlextInfraEnsureRuffConfigPhase",),
            ".phases.inject_comments": ("FlextInfraInjectCommentsPhase",),
        },
    ),
    exclude_names=(
        "cleanup_submodule_namespace",
        "install_lazy_exports",
        "lazy_getattr",
        "logger",
        "merge_lazy_imports",
        "output",
        "output_reporting",
        "pytest_addoption",
        "pytest_collect_file",
        "pytest_collection_modifyitems",
        "pytest_configure",
        "pytest_runtest_setup",
        "pytest_runtest_teardown",
        "pytest_sessionfinish",
        "pytest_sessionstart",
        "pytest_terminal_summary",
        "pytest_warning_recorded",
    ),
    module_name=__name__,
)


install_lazy_exports(__name__, globals(), _LAZY_IMPORTS, publish_all=False)
