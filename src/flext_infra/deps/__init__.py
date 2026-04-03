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
    import flext_infra.deps._phases.consolidate_groups as _flext_infra_deps__phases_consolidate_groups

    consolidate_groups = _flext_infra_deps__phases_consolidate_groups
    import flext_infra.deps._phases.ensure_coverage as _flext_infra_deps__phases_ensure_coverage
    from flext_infra.deps._phases.consolidate_groups import (
        FlextInfraConsolidateGroupsPhase,
    )

    ensure_coverage = _flext_infra_deps__phases_ensure_coverage
    import flext_infra.deps._phases.ensure_extra_paths as _flext_infra_deps__phases_ensure_extra_paths
    from flext_infra.deps._phases.ensure_coverage import (
        FlextInfraEnsureCoverageConfigPhase,
    )

    ensure_extra_paths = _flext_infra_deps__phases_ensure_extra_paths
    import flext_infra.deps._phases.ensure_formatting as _flext_infra_deps__phases_ensure_formatting
    from flext_infra.deps._phases.ensure_extra_paths import (
        FlextInfraEnsureExtraPathsPhase,
    )

    ensure_formatting = _flext_infra_deps__phases_ensure_formatting
    import flext_infra.deps._phases.ensure_mypy as _flext_infra_deps__phases_ensure_mypy
    from flext_infra.deps._phases.ensure_formatting import (
        FlextInfraEnsureFormattingToolingPhase,
    )

    ensure_mypy = _flext_infra_deps__phases_ensure_mypy
    import flext_infra.deps._phases.ensure_namespace as _flext_infra_deps__phases_ensure_namespace
    from flext_infra.deps._phases.ensure_mypy import FlextInfraEnsureMypyConfigPhase

    ensure_namespace = _flext_infra_deps__phases_ensure_namespace
    import flext_infra.deps._phases.ensure_pydantic_mypy as _flext_infra_deps__phases_ensure_pydantic_mypy
    from flext_infra.deps._phases.ensure_namespace import (
        FlextInfraEnsureNamespaceToolingPhase,
    )

    ensure_pydantic_mypy = _flext_infra_deps__phases_ensure_pydantic_mypy
    import flext_infra.deps._phases.ensure_pyrefly as _flext_infra_deps__phases_ensure_pyrefly
    from flext_infra.deps._phases.ensure_pydantic_mypy import (
        FlextInfraEnsurePydanticMypyConfigPhase,
    )

    ensure_pyrefly = _flext_infra_deps__phases_ensure_pyrefly
    import flext_infra.deps._phases.ensure_pyright as _flext_infra_deps__phases_ensure_pyright
    from flext_infra.deps._phases.ensure_pyrefly import (
        FlextInfraEnsurePyreflyConfigPhase,
    )

    ensure_pyright = _flext_infra_deps__phases_ensure_pyright
    import flext_infra.deps._phases.ensure_pyright_envs as _flext_infra_deps__phases_ensure_pyright_envs
    from flext_infra.deps._phases.ensure_pyright import (
        FlextInfraEnsurePyrightConfigPhase,
    )

    ensure_pyright_envs = _flext_infra_deps__phases_ensure_pyright_envs
    import flext_infra.deps._phases.ensure_pytest as _flext_infra_deps__phases_ensure_pytest
    from flext_infra.deps._phases.ensure_pyright_envs import FlextInfraEnsurePyrightEnvs

    ensure_pytest = _flext_infra_deps__phases_ensure_pytest
    import flext_infra.deps._phases.ensure_ruff as _flext_infra_deps__phases_ensure_ruff
    from flext_infra.deps._phases.ensure_pytest import FlextInfraEnsurePytestConfigPhase

    ensure_ruff = _flext_infra_deps__phases_ensure_ruff
    import flext_infra.deps._phases.inject_comments as _flext_infra_deps__phases_inject_comments
    from flext_infra.deps._phases.ensure_ruff import FlextInfraEnsureRuffConfigPhase

    inject_comments = _flext_infra_deps__phases_inject_comments
    import flext_infra.deps.cli as _flext_infra_deps_cli
    from flext_infra.deps._phases.inject_comments import FlextInfraInjectCommentsPhase

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
        "main": "flext_infra.deps.detector",
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
    "c",
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
    "m",
    "main",
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
