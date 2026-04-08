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
        "_phases": "flext_infra.deps._phases",
        "c": ("flext_core.constants", "FlextConstants"),
        "cli": "flext_infra.deps.cli",
        "d": ("flext_core.decorators", "FlextDecorators"),
        "detection": "flext_infra.deps.detection",
        "detection_analysis": "flext_infra.deps.detection_analysis",
        "detector": "flext_infra.deps.detector",
        "e": ("flext_core.exceptions", "FlextExceptions"),
        "extra_paths": "flext_infra.deps.extra_paths",
        "extra_paths_pyrefly": "flext_infra.deps.extra_paths_pyrefly",
        "fix_pyrefly_config": "flext_infra.deps.fix_pyrefly_config",
        "h": ("flext_core.handlers", "FlextHandlers"),
        "internal_sync": "flext_infra.deps.internal_sync",
        "m": ("flext_core.models", "FlextModels"),
        "modernizer": "flext_infra.deps.modernizer",
        "p": ("flext_core.protocols", "FlextProtocols"),
        "path_sync": "flext_infra.deps.path_sync",
        "path_sync_rewrite": "flext_infra.deps.path_sync_rewrite",
        "r": ("flext_core.result", "FlextResult"),
        "s": ("flext_core.service", "FlextService"),
        "t": ("flext_core.typings", "FlextTypes"),
        "u": ("flext_core.utilities", "FlextUtilities"),
        "x": ("flext_core.mixins", "FlextMixins"),
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
