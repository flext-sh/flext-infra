# AUTO-GENERATED FILE — DO NOT EDIT MANUALLY.
# Regenerate with: make gen
#
"""Deps package."""

from __future__ import annotations

from flext_core.lazy import install_lazy_exports, merge_lazy_imports

_LAZY_IMPORTS = merge_lazy_imports(
    ("._phases",),
    {
        "FlextInfraCliDeps": ".cli",
        "FlextInfraConfigFixer": ".fix_pyrefly_config",
        "FlextInfraDependencyDetectionAnalysis": ".detection_analysis",
        "FlextInfraDependencyDetectionService": ".detection",
        "FlextInfraDependencyDetectorRuntime": "._detector_runtime",
        "FlextInfraDependencyPathSync": ".path_sync",
        "FlextInfraDependencyPathSyncRewrite": ".path_sync_rewrite",
        "FlextInfraExtraPathsManager": ".extra_paths",
        "FlextInfraExtraPathsPyrefly": ".extra_paths_pyrefly",
        "FlextInfraInternalDependencySyncService": ".internal_sync",
        "FlextInfraPyprojectModernizer": ".modernizer",
        "FlextInfraRuntimeDevDependencyDetector": ".detector",
    },
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
