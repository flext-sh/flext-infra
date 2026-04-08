# AUTO-GENERATED FILE — DO NOT EDIT MANUALLY.
# Regenerate with: make gen
#
"""Deps package."""

from __future__ import annotations

from flext_core.lazy import install_lazy_exports, merge_lazy_imports

_LAZY_IMPORTS = merge_lazy_imports(
    ("flext_infra.deps._phases",),
    {
        "FlextInfraCliDeps": ("flext_infra.deps.cli", "FlextInfraCliDeps"),
        "FlextInfraConfigFixer": (
            "flext_infra.deps.fix_pyrefly_config",
            "FlextInfraConfigFixer",
        ),
        "FlextInfraDependencyDetectionAnalysis": (
            "flext_infra.deps.detection_analysis",
            "FlextInfraDependencyDetectionAnalysis",
        ),
        "FlextInfraDependencyDetectionService": (
            "flext_infra.deps.detection",
            "FlextInfraDependencyDetectionService",
        ),
        "FlextInfraDependencyDetectorRuntime": (
            "flext_infra.deps._detector_runtime",
            "FlextInfraDependencyDetectorRuntime",
        ),
        "FlextInfraDependencyPathSync": (
            "flext_infra.deps.path_sync",
            "FlextInfraDependencyPathSync",
        ),
        "FlextInfraDependencyPathSyncRewrite": (
            "flext_infra.deps.path_sync_rewrite",
            "FlextInfraDependencyPathSyncRewrite",
        ),
        "FlextInfraExtraPathsManager": (
            "flext_infra.deps.extra_paths",
            "FlextInfraExtraPathsManager",
        ),
        "FlextInfraExtraPathsPyrefly": (
            "flext_infra.deps.extra_paths_pyrefly",
            "FlextInfraExtraPathsPyrefly",
        ),
        "FlextInfraInternalDependencySyncService": (
            "flext_infra.deps.internal_sync",
            "FlextInfraInternalDependencySyncService",
        ),
        "FlextInfraPyprojectModernizer": (
            "flext_infra.deps.modernizer",
            "FlextInfraPyprojectModernizer",
        ),
        "FlextInfraRuntimeDevDependencyDetector": (
            "flext_infra.deps.detector",
            "FlextInfraRuntimeDevDependencyDetector",
        ),
    },
)
_ = _LAZY_IMPORTS.pop("cleanup_submodule_namespace", None)
_ = _LAZY_IMPORTS.pop("install_lazy_exports", None)
_ = _LAZY_IMPORTS.pop("lazy_getattr", None)
_ = _LAZY_IMPORTS.pop("logger", None)
_ = _LAZY_IMPORTS.pop("merge_lazy_imports", None)
_ = _LAZY_IMPORTS.pop("output", None)
_ = _LAZY_IMPORTS.pop("output_reporting", None)


install_lazy_exports(__name__, globals(), _LAZY_IMPORTS, publish_all=False)
