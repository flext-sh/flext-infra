# AUTO-GENERATED FILE — DO NOT EDIT MANUALLY.
# Regenerate with: make gen
#
"""Deps package."""

from __future__ import annotations

import typing as _t

from flext_core.lazy import install_lazy_exports, merge_lazy_imports

if _t.TYPE_CHECKING:
    import flext_infra.deps._constants as _flext_infra_deps__constants

    _constants = _flext_infra_deps__constants
    import flext_infra.deps._detector_runtime as _flext_infra_deps__detector_runtime
    from flext_infra.deps._constants import FlextInfraDepsConstants

    _detector_runtime = _flext_infra_deps__detector_runtime
    import flext_infra.deps._extra_paths_resolution as _flext_infra_deps__extra_paths_resolution
    from flext_infra.deps._detector_runtime import FlextInfraDependencyDetectorRuntime

    _extra_paths_resolution = _flext_infra_deps__extra_paths_resolution
    import flext_infra.deps._internal_sync_repo as _flext_infra_deps__internal_sync_repo
    from flext_infra.deps._extra_paths_resolution import (
        FlextInfraExtraPathsResolutionMixin,
    )

    _internal_sync_repo = _flext_infra_deps__internal_sync_repo
    import flext_infra.deps._models as _flext_infra_deps__models
    from flext_infra.deps._internal_sync_repo import FlextInfraInternalSyncRepoMixin

    _models = _flext_infra_deps__models
    import flext_infra.deps._models_tool_config as _flext_infra_deps__models_tool_config
    from flext_infra.deps._models import FlextInfraDepsModels

    _models_tool_config = _flext_infra_deps__models_tool_config
    import flext_infra.deps._models_tool_config_linters as _flext_infra_deps__models_tool_config_linters
    from flext_infra.deps._models_tool_config import FlextInfraDepsModelsToolConfig

    _models_tool_config_linters = _flext_infra_deps__models_tool_config_linters
    import flext_infra.deps._models_tool_config_type_checkers as _flext_infra_deps__models_tool_config_type_checkers
    from flext_infra.deps._models_tool_config_linters import (
        MypyConfig,
        MypyOverrideConfig,
        PydanticMypyConfig,
        RuffConfig,
        RuffFormatConfig,
        RuffIsortConfig,
        RuffLintConfig,
    )

    _models_tool_config_type_checkers = (
        _flext_infra_deps__models_tool_config_type_checkers
    )
    import flext_infra.deps._phases as _flext_infra_deps__phases
    from flext_infra.deps._models_tool_config_type_checkers import (
        PyreflyConfig,
        PyrightConfig,
    )

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
        consolidate_groups,
        ensure_coverage,
        ensure_extra_paths,
        ensure_formatting,
        ensure_mypy,
        ensure_namespace,
        ensure_pydantic_mypy,
        ensure_pyrefly,
        ensure_pyright,
        ensure_pyright_envs,
        ensure_pytest,
        ensure_ruff,
        inject_comments,
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
    from flext_infra.deps.detector import FlextInfraRuntimeDevDependencyDetector, main

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
    from flext_core.decorators import FlextDecorators as d
    from flext_core.exceptions import FlextExceptions as e
    from flext_core.handlers import FlextHandlers as h
    from flext_core.mixins import FlextMixins as x
    from flext_core.result import FlextResult as r
    from flext_core.service import FlextService as s
    from flext_infra.deps.path_sync_rewrite import FlextInfraDependencyPathSyncRewrite
_LAZY_IMPORTS = merge_lazy_imports(
    ("flext_infra.deps._phases",),
    {
        "FlextInfraCliDeps": "flext_infra.deps.cli",
        "FlextInfraConfigFixer": "flext_infra.deps.fix_pyrefly_config",
        "FlextInfraDependencyDetectionAnalysis": "flext_infra.deps.detection_analysis",
        "FlextInfraDependencyDetectionService": "flext_infra.deps.detection",
        "FlextInfraDependencyDetectorRuntime": "flext_infra.deps._detector_runtime",
        "FlextInfraDependencyPathSync": "flext_infra.deps.path_sync",
        "FlextInfraDependencyPathSyncRewrite": "flext_infra.deps.path_sync_rewrite",
        "FlextInfraDepsConstants": "flext_infra.deps._constants",
        "FlextInfraDepsModels": "flext_infra.deps._models",
        "FlextInfraDepsModelsToolConfig": "flext_infra.deps._models_tool_config",
        "FlextInfraExtraPathsManager": "flext_infra.deps.extra_paths",
        "FlextInfraExtraPathsPyrefly": "flext_infra.deps.extra_paths_pyrefly",
        "FlextInfraExtraPathsResolutionMixin": "flext_infra.deps._extra_paths_resolution",
        "FlextInfraInternalDependencySyncService": "flext_infra.deps.internal_sync",
        "FlextInfraInternalSyncRepoMixin": "flext_infra.deps._internal_sync_repo",
        "FlextInfraPyprojectModernizer": "flext_infra.deps.modernizer",
        "FlextInfraRuntimeDevDependencyDetector": "flext_infra.deps.detector",
        "MypyConfig": "flext_infra.deps._models_tool_config_linters",
        "MypyOverrideConfig": "flext_infra.deps._models_tool_config_linters",
        "PydanticMypyConfig": "flext_infra.deps._models_tool_config_linters",
        "PyreflyConfig": "flext_infra.deps._models_tool_config_type_checkers",
        "PyrightConfig": "flext_infra.deps._models_tool_config_type_checkers",
        "RuffConfig": "flext_infra.deps._models_tool_config_linters",
        "RuffFormatConfig": "flext_infra.deps._models_tool_config_linters",
        "RuffIsortConfig": "flext_infra.deps._models_tool_config_linters",
        "RuffLintConfig": "flext_infra.deps._models_tool_config_linters",
        "_constants": "flext_infra.deps._constants",
        "_detector_runtime": "flext_infra.deps._detector_runtime",
        "_extra_paths_resolution": "flext_infra.deps._extra_paths_resolution",
        "_internal_sync_repo": "flext_infra.deps._internal_sync_repo",
        "_models": "flext_infra.deps._models",
        "_models_tool_config": "flext_infra.deps._models_tool_config",
        "_models_tool_config_linters": "flext_infra.deps._models_tool_config_linters",
        "_models_tool_config_type_checkers": "flext_infra.deps._models_tool_config_type_checkers",
        "_phases": "flext_infra.deps._phases",
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
        "main": "flext_infra.deps.detector",
        "modernizer": "flext_infra.deps.modernizer",
        "path_sync": "flext_infra.deps.path_sync",
        "path_sync_rewrite": "flext_infra.deps.path_sync_rewrite",
        "r": ("flext_core.result", "FlextResult"),
        "s": ("flext_core.service", "FlextService"),
        "x": ("flext_core.mixins", "FlextMixins"),
    },
)

__all__ = [
    "FlextInfraCliDeps",
    "FlextInfraConfigFixer",
    "FlextInfraConsolidateGroupsPhase",
    "FlextInfraDependencyDetectionAnalysis",
    "FlextInfraDependencyDetectionService",
    "FlextInfraDependencyDetectorRuntime",
    "FlextInfraDependencyPathSync",
    "FlextInfraDependencyPathSyncRewrite",
    "FlextInfraDepsConstants",
    "FlextInfraDepsModels",
    "FlextInfraDepsModelsToolConfig",
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
    "FlextInfraExtraPathsResolutionMixin",
    "FlextInfraInjectCommentsPhase",
    "FlextInfraInternalDependencySyncService",
    "FlextInfraInternalSyncRepoMixin",
    "FlextInfraPyprojectModernizer",
    "FlextInfraRuntimeDevDependencyDetector",
    "MypyConfig",
    "MypyOverrideConfig",
    "PydanticMypyConfig",
    "PyreflyConfig",
    "PyrightConfig",
    "RuffConfig",
    "RuffFormatConfig",
    "RuffIsortConfig",
    "RuffLintConfig",
    "_constants",
    "_detector_runtime",
    "_extra_paths_resolution",
    "_internal_sync_repo",
    "_models",
    "_models_tool_config",
    "_models_tool_config_linters",
    "_models_tool_config_type_checkers",
    "_phases",
    "cli",
    "consolidate_groups",
    "d",
    "detection",
    "detection_analysis",
    "detector",
    "e",
    "ensure_coverage",
    "ensure_extra_paths",
    "ensure_formatting",
    "ensure_mypy",
    "ensure_namespace",
    "ensure_pydantic_mypy",
    "ensure_pyrefly",
    "ensure_pyright",
    "ensure_pyright_envs",
    "ensure_pytest",
    "ensure_ruff",
    "extra_paths",
    "extra_paths_pyrefly",
    "fix_pyrefly_config",
    "h",
    "inject_comments",
    "internal_sync",
    "main",
    "modernizer",
    "path_sync",
    "path_sync_rewrite",
    "r",
    "s",
    "x",
]


install_lazy_exports(__name__, globals(), _LAZY_IMPORTS)
