# AUTO-GENERATED FILE — Regenerate with: make gen
"""Phases package."""

from __future__ import annotations

from flext_core.lazy import install_lazy_exports

_LAZY_IMPORTS = {
    "FlextInfraConsolidateGroupsPhase": ".consolidate_groups",
    "FlextInfraEnsureCoverageConfigPhase": ".ensure_coverage",
    "FlextInfraEnsureExtraPathsPhase": ".ensure_extra_paths",
    "FlextInfraEnsureFormattingToolingPhase": ".ensure_formatting",
    "FlextInfraEnsureMypyConfigPhase": ".ensure_mypy",
    "FlextInfraEnsureNamespaceToolingPhase": ".ensure_namespace",
    "FlextInfraEnsurePydanticMypyConfigPhase": ".ensure_pydantic_mypy",
    "FlextInfraEnsurePyreflyConfigPhase": ".ensure_pyrefly",
    "FlextInfraEnsurePyrightConfigPhase": ".ensure_pyright",
    "FlextInfraEnsurePyrightEnvs": ".ensure_pyright_envs",
    "FlextInfraEnsurePytestConfigPhase": ".ensure_pytest",
    "FlextInfraEnsureRuffConfigPhase": ".ensure_ruff",
    "FlextInfraInjectCommentsPhase": ".inject_comments",
}


install_lazy_exports(__name__, globals(), _LAZY_IMPORTS, publish_all=False)
