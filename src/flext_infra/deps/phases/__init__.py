# AUTO-GENERATED FILE — Regenerate with: make gen

"""Flext Infra.deps.phases package."""

from __future__ import annotations
from flext_core.lazy import build_lazy_import_map, install_lazy_exports

_LAZY_MODULES: dict[str, tuple[str, ...]] = {
    ".consolidate_groups": ("FlextInfraConsolidateGroupsPhase",),
    ".ensure_coverage": ("FlextInfraEnsureCoverageConfigPhase",),
    ".ensure_formatting": ("FlextInfraEnsureFormattingToolingPhase",),
    ".ensure_mypy": ("FlextInfraEnsureMypyConfigPhase",),
    ".ensure_namespace": ("FlextInfraEnsureNamespaceToolingPhase",),
    ".ensure_packaging": ("FlextInfraEnsurePackagingPhase",),
    ".ensure_pydantic_mypy": ("FlextInfraEnsurePydanticMypyConfigPhase",),
    ".ensure_pyrefly": ("FlextInfraEnsurePyreflyConfigPhase",),
    ".ensure_pyright": ("FlextInfraEnsurePyrightConfigPhase",),
    ".ensure_pytest": ("FlextInfraEnsurePytestConfigPhase",),
    ".ensure_ruff": ("FlextInfraEnsureRuffConfigPhase",),
    ".ensure_vulture": ("FlextInfraEnsureVultureConfigPhase",),
    ".inject_comments": ("FlextInfraInjectCommentsPhase",),
}

_LAZY_ALIAS_GROUPS: dict[str, tuple[tuple[str, str], ...]] = {}

_LAZY_IMPORTS = build_lazy_import_map(
    _LAZY_MODULES, alias_groups=_LAZY_ALIAS_GROUPS, sort_keys=False
)

__all__: tuple[str, ...] = ()

install_lazy_exports(__name__, globals(), _LAZY_IMPORTS, public_exports=__all__)
