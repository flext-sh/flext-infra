# AUTO-GENERATED FILE — Regenerate with: make gen
"""Phases package."""

from __future__ import annotations

from flext_core.lazy import build_lazy_import_map, install_lazy_exports

_LAZY_IMPORTS = build_lazy_import_map(
    {
        ".consolidate_groups": ("FlextInfraConsolidateGroupsPhase",),
        ".ensure_coverage": ("FlextInfraEnsureCoverageConfigPhase",),
        ".ensure_formatting": ("FlextInfraEnsureFormattingToolingPhase",),
        ".ensure_mypy": ("FlextInfraEnsureMypyConfigPhase",),
        ".ensure_namespace": ("FlextInfraEnsureNamespaceToolingPhase",),
        ".ensure_pydantic_mypy": ("FlextInfraEnsurePydanticMypyConfigPhase",),
        ".ensure_pyrefly": ("FlextInfraEnsurePyreflyConfigPhase",),
        ".ensure_pyright": ("FlextInfraEnsurePyrightConfigPhase",),
        ".ensure_pytest": ("FlextInfraEnsurePytestConfigPhase",),
        ".ensure_ruff": ("FlextInfraEnsureRuffConfigPhase",),
        ".inject_comments": ("FlextInfraInjectCommentsPhase",),
    },
)


install_lazy_exports(__name__, globals(), _LAZY_IMPORTS, publish_all=False)
