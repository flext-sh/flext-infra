# AUTO-GENERATED FILE — Regenerate with: make gen

"""Flext Infra.deps package."""

from __future__ import annotations
from flext_core.lazy import build_lazy_import_map, install_lazy_exports

_LAZY_MODULES: dict[str, tuple[str, ...]] = {
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
    ".phases.ensure_pydantic_mypy": ("FlextInfraEnsurePydanticMypyConfigPhase",),
    ".phases.ensure_pyrefly": ("FlextInfraEnsurePyreflyConfigPhase",),
    ".phases.ensure_pyright": ("FlextInfraEnsurePyrightConfigPhase",),
    ".phases.ensure_pytest": ("FlextInfraEnsurePytestConfigPhase",),
    ".phases.ensure_ruff": ("FlextInfraEnsureRuffConfigPhase",),
    ".phases.ensure_vulture": ("FlextInfraEnsureVultureConfigPhase",),
    ".phases.inject_comments": ("FlextInfraInjectCommentsPhase",),
    ".toml_phase": ("FlextInfraTomlPhaseService",),
}

_LAZY_ALIAS_GROUPS: dict[str, tuple[tuple[str, str], ...]] = {}

_LAZY_IMPORTS = build_lazy_import_map(
    _LAZY_MODULES, alias_groups=_LAZY_ALIAS_GROUPS, sort_keys=False
)

__all__: tuple[str, ...] = ()

install_lazy_exports(__name__, globals(), _LAZY_IMPORTS, public_exports=__all__)
