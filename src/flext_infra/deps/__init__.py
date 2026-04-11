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
            ".extra_paths_pyrefly": ("FlextInfraExtraPathsPyrefly",),
            ".fix_pyrefly_config": ("FlextInfraConfigFixer",),
            ".internal_sync": ("FlextInfraInternalDependencySyncService",),
            ".modernizer": ("FlextInfraPyprojectModernizer",),
            ".path_sync_rewrite": ("FlextInfraDependencyPathSyncRewrite",),
            "flext_infra._utilities.deps_path_sync": (
                "FlextInfraUtilitiesDependencyPathSync",
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
