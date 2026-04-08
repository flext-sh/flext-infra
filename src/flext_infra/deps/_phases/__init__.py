# AUTO-GENERATED FILE — DO NOT EDIT MANUALLY.
# Regenerate with: make gen
#
"""Phases package."""

from __future__ import annotations

from flext_core.lazy import install_lazy_exports

_LAZY_IMPORTS = {
    "FlextInfraConsolidateGroupsPhase": (
        "flext_infra.deps._phases.consolidate_groups",
        "FlextInfraConsolidateGroupsPhase",
    ),
    "FlextInfraEnsureCoverageConfigPhase": (
        "flext_infra.deps._phases.ensure_coverage",
        "FlextInfraEnsureCoverageConfigPhase",
    ),
    "FlextInfraEnsureExtraPathsPhase": (
        "flext_infra.deps._phases.ensure_extra_paths",
        "FlextInfraEnsureExtraPathsPhase",
    ),
    "FlextInfraEnsureFormattingToolingPhase": (
        "flext_infra.deps._phases.ensure_formatting",
        "FlextInfraEnsureFormattingToolingPhase",
    ),
    "FlextInfraEnsureMypyConfigPhase": (
        "flext_infra.deps._phases.ensure_mypy",
        "FlextInfraEnsureMypyConfigPhase",
    ),
    "FlextInfraEnsureNamespaceToolingPhase": (
        "flext_infra.deps._phases.ensure_namespace",
        "FlextInfraEnsureNamespaceToolingPhase",
    ),
    "FlextInfraEnsurePydanticMypyConfigPhase": (
        "flext_infra.deps._phases.ensure_pydantic_mypy",
        "FlextInfraEnsurePydanticMypyConfigPhase",
    ),
    "FlextInfraEnsurePyreflyConfigPhase": (
        "flext_infra.deps._phases.ensure_pyrefly",
        "FlextInfraEnsurePyreflyConfigPhase",
    ),
    "FlextInfraEnsurePyrightConfigPhase": (
        "flext_infra.deps._phases.ensure_pyright",
        "FlextInfraEnsurePyrightConfigPhase",
    ),
    "FlextInfraEnsurePyrightEnvs": (
        "flext_infra.deps._phases.ensure_pyright_envs",
        "FlextInfraEnsurePyrightEnvs",
    ),
    "FlextInfraEnsurePytestConfigPhase": (
        "flext_infra.deps._phases.ensure_pytest",
        "FlextInfraEnsurePytestConfigPhase",
    ),
    "FlextInfraEnsureRuffConfigPhase": (
        "flext_infra.deps._phases.ensure_ruff",
        "FlextInfraEnsureRuffConfigPhase",
    ),
    "FlextInfraInjectCommentsPhase": (
        "flext_infra.deps._phases.inject_comments",
        "FlextInfraInjectCommentsPhase",
    ),
}


install_lazy_exports(__name__, globals(), _LAZY_IMPORTS, publish_all=False)
