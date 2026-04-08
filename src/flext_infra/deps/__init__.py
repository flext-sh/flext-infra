# AUTO-GENERATED FILE — DO NOT EDIT MANUALLY.
# Regenerate with: make gen
#
"""Deps package."""

from __future__ import annotations

import typing as _t

from flext_core.lazy import install_lazy_exports, merge_lazy_imports

if _t.TYPE_CHECKING:
    import flext_infra.deps._detector_runtime as _flext_infra_deps__detector_runtime

    _detector_runtime = _flext_infra_deps__detector_runtime
    import flext_infra.deps._phases as _flext_infra_deps__phases
    from flext_infra.deps._detector_runtime import FlextInfraDependencyDetectorRuntime

    _phases = _flext_infra_deps__phases
    import flext_infra.deps.cli as _flext_infra_deps_cli
    from flext_infra.deps._phases import (
        FlextInfraConsolidateGroupsPhase,
        FlextInfraEnsureCoverageConfigPhase,
        FlextInfraEnsureExtraPathsPhase,
        FlextInfraEnsureFormattingToolingPhase,
        FlextInfraEnsureMypyConfigPhase,
        FlextInfraEnsureNamespaceToolingPhase,
        FlextInfraEnsurePydanticMypyConfigPhase,
        FlextInfraEnsurePyreflyConfigPhase,
        FlextInfraEnsurePyrightConfigPhase,
        FlextInfraEnsurePyrightEnvs,
        FlextInfraEnsurePytestConfigPhase,
        FlextInfraEnsureRuffConfigPhase,
        FlextInfraInjectCommentsPhase,
    )

    cli = _flext_infra_deps_cli
    import flext_infra.deps.detection as _flext_infra_deps_detection
    from flext_infra.deps.cli import FlextInfraCliDeps

    detection = _flext_infra_deps_detection
    import flext_infra.deps.detection_analysis as _flext_infra_deps_detection_analysis
    from flext_infra.deps.detection import FlextInfraDependencyDetectionService

    detection_analysis = _flext_infra_deps_detection_analysis
    import flext_infra.deps.detector as _flext_infra_deps_detector
    from flext_infra.deps.detection_analysis import (
        FlextInfraDependencyDetectionAnalysis,
    )

    detector = _flext_infra_deps_detector
    import flext_infra.deps.extra_paths as _flext_infra_deps_extra_paths
    from flext_infra.deps.detector import FlextInfraRuntimeDevDependencyDetector

    extra_paths = _flext_infra_deps_extra_paths
    import flext_infra.deps.extra_paths_pyrefly as _flext_infra_deps_extra_paths_pyrefly
    from flext_infra.deps.extra_paths import FlextInfraExtraPathsManager

    extra_paths_pyrefly = _flext_infra_deps_extra_paths_pyrefly
    import flext_infra.deps.fix_pyrefly_config as _flext_infra_deps_fix_pyrefly_config
    from flext_infra.deps.extra_paths_pyrefly import FlextInfraExtraPathsPyrefly

    fix_pyrefly_config = _flext_infra_deps_fix_pyrefly_config
    import flext_infra.deps.internal_sync as _flext_infra_deps_internal_sync
    from flext_infra.deps.fix_pyrefly_config import FlextInfraConfigFixer

    internal_sync = _flext_infra_deps_internal_sync
    import flext_infra.deps.modernizer as _flext_infra_deps_modernizer
    from flext_infra.deps.internal_sync import FlextInfraInternalDependencySyncService

    modernizer = _flext_infra_deps_modernizer
    import flext_infra.deps.path_sync as _flext_infra_deps_path_sync
    from flext_infra.deps.modernizer import FlextInfraPyprojectModernizer

    path_sync = _flext_infra_deps_path_sync
    import flext_infra.deps.path_sync_rewrite as _flext_infra_deps_path_sync_rewrite
    from flext_infra.deps.path_sync import FlextInfraDependencyPathSync

    path_sync_rewrite = _flext_infra_deps_path_sync_rewrite
    from flext_core.constants import FlextConstants as c
    from flext_core.decorators import FlextDecorators as d
    from flext_core.exceptions import FlextExceptions as e
    from flext_core.handlers import FlextHandlers as h
    from flext_core.mixins import FlextMixins as x
    from flext_core.models import FlextModels as m
    from flext_core.protocols import FlextProtocols as p
    from flext_core.result import FlextResult as r
    from flext_core.service import FlextService as s
    from flext_core.typings import FlextTypes as t
    from flext_core.utilities import FlextUtilities as u
    from flext_infra.deps.path_sync_rewrite import FlextInfraDependencyPathSyncRewrite
_LAZY_IMPORTS = merge_lazy_imports(
    ("flext_infra.deps._phases",),
    {
        "FlextInfraCliDeps": ("flext_infra.deps.cli", "FlextInfraCliDeps"),
        "FlextInfraConfigFixer": (
            "flext_infra.deps.fix_pyrefly_config",
            "FlextInfraConfigFixer",
        ),
        "FlextInfraDependencyDetectorRuntime": (
            "flext_infra.deps._detector_runtime",
            "FlextInfraDependencyDetectorRuntime",
        ),
        "FlextInfraDependencyDetectionAnalysis": (
            "flext_infra.deps.detection_analysis",
            "FlextInfraDependencyDetectionAnalysis",
        ),
        "FlextInfraDependencyDetectionService": (
            "flext_infra.deps.detection",
            "FlextInfraDependencyDetectionService",
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
        "_detector_runtime": "flext_infra.deps._detector_runtime",
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

__all__ = [
    "FlextInfraCliDeps",
    "FlextInfraConfigFixer",
    "FlextInfraConsolidateGroupsPhase",
    "FlextInfraDependencyDetectionAnalysis",
    "FlextInfraDependencyDetectionService",
    "FlextInfraDependencyDetectorRuntime",
    "FlextInfraDependencyPathSync",
    "FlextInfraDependencyPathSyncRewrite",
    "FlextInfraEnsureCoverageConfigPhase",
    "FlextInfraEnsureExtraPathsPhase",
    "FlextInfraEnsureFormattingToolingPhase",
    "FlextInfraEnsureMypyConfigPhase",
    "FlextInfraEnsureNamespaceToolingPhase",
    "FlextInfraEnsurePydanticMypyConfigPhase",
    "FlextInfraEnsurePyreflyConfigPhase",
    "FlextInfraEnsurePyrightConfigPhase",
    "FlextInfraEnsurePyrightEnvs",
    "FlextInfraEnsurePytestConfigPhase",
    "FlextInfraEnsureRuffConfigPhase",
    "FlextInfraExtraPathsManager",
    "FlextInfraExtraPathsPyrefly",
    "FlextInfraInjectCommentsPhase",
    "FlextInfraInternalDependencySyncService",
    "FlextInfraPyprojectModernizer",
    "FlextInfraRuntimeDevDependencyDetector",
    "_detector_runtime",
    "_phases",
    "c",
    "cli",
    "d",
    "detection",
    "detection_analysis",
    "detector",
    "e",
    "extra_paths",
    "extra_paths_pyrefly",
    "fix_pyrefly_config",
    "h",
    "internal_sync",
    "m",
    "modernizer",
    "p",
    "path_sync",
    "path_sync_rewrite",
    "r",
    "s",
    "t",
    "u",
    "x",
]


install_lazy_exports(__name__, globals(), _LAZY_IMPORTS)
