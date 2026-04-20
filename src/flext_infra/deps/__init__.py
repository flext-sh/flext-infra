# AUTO-GENERATED FILE — Regenerate with: make gen
"""Deps package."""

from __future__ import annotations

from flext_core.lazy import (
    build_lazy_import_map,
    install_lazy_exports,
    merge_lazy_imports,
)

_LAZY_IMPORTS = merge_lazy_imports(
    (".phases",),
    build_lazy_import_map(
        {
            ".cli": ("FlextInfraCliDeps",),
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
            ".service_base": (
                "FlextInfraDepsProjectServiceBase",
                "FlextInfraDepsServiceBase",
            ),
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
    ),
    module_name=__name__,
)


install_lazy_exports(__name__, globals(), _LAZY_IMPORTS, publish_all=False)
