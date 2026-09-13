# AUTO-GENERATED FILE — Regenerate with: make gen
"""Flext Infra.deps package."""

from __future__ import annotations

from types import MappingProxyType
from typing import TYPE_CHECKING

from flext_core.lazy import build_lazy_import_map, install_lazy_exports

if TYPE_CHECKING:
    from . import phases
    from ._detection_runners import FlextInfraDependencyDetectionRunnersMixin
    from ._detector_runtime_steps import FlextInfraDependencyDetectorRuntimeSteps
    from ._extra_paths_sync import FlextInfraExtraPathsSyncMixin
    from ._floor_profile_writer import FlextInfraDepsFloorProfileWriter
    from ._modernizer_document import FlextInfraPyprojectModernizerDocumentMixin
    from ._modernizer_payload import FlextInfraPyprojectModernizerPayloadMixin
    from ._modernizer_run import FlextInfraPyprojectModernizerRunMixin
    from ._pyrefly_fix_steps import FlextInfraConfigFixerSteps
    from ._toml_phase_ops import FlextInfraTomlPhaseOps
    from .detection import FlextInfraDependencyDetectionService
    from .detection_analysis import FlextInfraDependencyDetectionAnalysis
    from .detector import FlextInfraRuntimeDevDependencyDetector
    from .detector_runtime import FlextInfraDependencyDetectorRuntime
    from .extra_paths import FlextInfraExtraPathsManager
    from .fix_pyrefly_config import FlextInfraConfigFixer
    from .modernizer import FlextInfraPyprojectModernizer
    from .phases.consolidate_groups import FlextInfraConsolidateGroupsPhase
    from .phases.ensure_coverage import FlextInfraEnsureCoverageConfigPhase
    from .phases.ensure_formatting import FlextInfraEnsureFormattingToolingPhase
    from .phases.ensure_mypy import FlextInfraEnsureMypyConfigPhase
    from .phases.ensure_namespace import FlextInfraEnsureNamespaceToolingPhase
    from .phases.ensure_packaging import FlextInfraEnsurePackagingPhase
    from .phases.ensure_pydantic_mypy import FlextInfraEnsurePydanticMypyConfigPhase
    from .phases.ensure_pyrefly import FlextInfraEnsurePyreflyConfigPhase
    from .phases.ensure_pyright import FlextInfraEnsurePyrightConfigPhase
    from .phases.ensure_pytest import FlextInfraEnsurePytestConfigPhase
    from .phases.ensure_ruff import FlextInfraEnsureRuffConfigPhase
    from .phases.ensure_vulture import FlextInfraEnsureVultureConfigPhase
    from .phases.inject_comments import FlextInfraInjectCommentsPhase
    from .toml_phase import FlextInfraTomlPhaseService
__all__: tuple[str, ...] = (
    "FlextInfraConfigFixer",
    "FlextInfraConfigFixerSteps",
    "FlextInfraConsolidateGroupsPhase",
    "FlextInfraDependencyDetectionAnalysis",
    "FlextInfraDependencyDetectionRunnersMixin",
    "FlextInfraDependencyDetectionService",
    "FlextInfraDependencyDetectorRuntime",
    "FlextInfraDependencyDetectorRuntimeSteps",
    "FlextInfraDepsFloorProfileWriter",
    "FlextInfraEnsureCoverageConfigPhase",
    "FlextInfraEnsureFormattingToolingPhase",
    "FlextInfraEnsureMypyConfigPhase",
    "FlextInfraEnsureNamespaceToolingPhase",
    "FlextInfraEnsurePackagingPhase",
    "FlextInfraEnsurePydanticMypyConfigPhase",
    "FlextInfraEnsurePyreflyConfigPhase",
    "FlextInfraEnsurePyrightConfigPhase",
    "FlextInfraEnsurePytestConfigPhase",
    "FlextInfraEnsureRuffConfigPhase",
    "FlextInfraEnsureVultureConfigPhase",
    "FlextInfraExtraPathsManager",
    "FlextInfraExtraPathsSyncMixin",
    "FlextInfraInjectCommentsPhase",
    "FlextInfraPyprojectModernizer",
    "FlextInfraPyprojectModernizerDocumentMixin",
    "FlextInfraPyprojectModernizerPayloadMixin",
    "FlextInfraPyprojectModernizerRunMixin",
    "FlextInfraRuntimeDevDependencyDetector",
    "FlextInfraTomlPhaseOps",
    "FlextInfraTomlPhaseService",
    "phases",
)

_LAZY_IMPORTS = MappingProxyType(
    build_lazy_import_map(
        MappingProxyType({
            "._detection_runners": ("FlextInfraDependencyDetectionRunnersMixin",),
            "._detector_runtime_steps": ("FlextInfraDependencyDetectorRuntimeSteps",),
            "._extra_paths_sync": ("FlextInfraExtraPathsSyncMixin",),
            "._floor_profile_writer": ("FlextInfraDepsFloorProfileWriter",),
            "._modernizer_document": ("FlextInfraPyprojectModernizerDocumentMixin",),
            "._modernizer_payload": ("FlextInfraPyprojectModernizerPayloadMixin",),
            "._modernizer_run": ("FlextInfraPyprojectModernizerRunMixin",),
            "._pyrefly_fix_steps": ("FlextInfraConfigFixerSteps",),
            "._toml_phase_ops": ("FlextInfraTomlPhaseOps",),
            ".detection": ("FlextInfraDependencyDetectionService",),
            ".detection_analysis": ("FlextInfraDependencyDetectionAnalysis",),
            ".detector": ("FlextInfraRuntimeDevDependencyDetector",),
            ".detector_runtime": ("FlextInfraDependencyDetectorRuntime",),
            ".extra_paths": ("FlextInfraExtraPathsManager",),
            ".fix_pyrefly_config": ("FlextInfraConfigFixer",),
            ".modernizer": ("FlextInfraPyprojectModernizer",),
            ".phases": ("phases",),
            ".phases.consolidate_groups": ("FlextInfraConsolidateGroupsPhase",),
            ".phases.ensure_coverage": ("FlextInfraEnsureCoverageConfigPhase",),
            ".phases.ensure_formatting": ("FlextInfraEnsureFormattingToolingPhase",),
            ".phases.ensure_mypy": ("FlextInfraEnsureMypyConfigPhase",),
            ".phases.ensure_namespace": ("FlextInfraEnsureNamespaceToolingPhase",),
            ".phases.ensure_packaging": ("FlextInfraEnsurePackagingPhase",),
            ".phases.ensure_pydantic_mypy": (
                "FlextInfraEnsurePydanticMypyConfigPhase",
            ),
            ".phases.ensure_pyrefly": ("FlextInfraEnsurePyreflyConfigPhase",),
            ".phases.ensure_pyright": ("FlextInfraEnsurePyrightConfigPhase",),
            ".phases.ensure_pytest": ("FlextInfraEnsurePytestConfigPhase",),
            ".phases.ensure_ruff": ("FlextInfraEnsureRuffConfigPhase",),
            ".phases.ensure_vulture": ("FlextInfraEnsureVultureConfigPhase",),
            ".phases.inject_comments": ("FlextInfraInjectCommentsPhase",),
            ".toml_phase": ("FlextInfraTomlPhaseService",),
        }),
        alias_groups=MappingProxyType({}),
        sort_keys=False,
    )
)

install_lazy_exports(__name__, globals(), _LAZY_IMPORTS, public_exports=__all__)
