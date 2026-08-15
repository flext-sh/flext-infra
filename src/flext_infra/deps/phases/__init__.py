# AUTO-GENERATED FILE — Regenerate with: make gen
"""Flext Infra.deps.phases package."""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_core.lazy import build_lazy_import_map, install_lazy_exports

if TYPE_CHECKING:
    from .consolidate_groups import FlextInfraConsolidateGroupsPhase
    from .ensure_coverage import FlextInfraEnsureCoverageConfigPhase
    from .ensure_formatting import FlextInfraEnsureFormattingToolingPhase
    from .ensure_mypy import FlextInfraEnsureMypyConfigPhase
    from .ensure_namespace import FlextInfraEnsureNamespaceToolingPhase
    from .ensure_packaging import FlextInfraEnsurePackagingPhase
    from .ensure_pydantic_mypy import FlextInfraEnsurePydanticMypyConfigPhase
    from .ensure_pyrefly import FlextInfraEnsurePyreflyConfigPhase
    from .ensure_pyright import FlextInfraEnsurePyrightConfigPhase
    from .ensure_pytest import FlextInfraEnsurePytestConfigPhase
    from .ensure_ruff import FlextInfraEnsureRuffConfigPhase
    from .ensure_vulture import FlextInfraEnsureVultureConfigPhase
    from .inject_comments import FlextInfraInjectCommentsPhase

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

__all__: tuple[str, ...] = (
    "FlextInfraConsolidateGroupsPhase",
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
    "FlextInfraInjectCommentsPhase",
)

install_lazy_exports(__name__, globals(), _LAZY_IMPORTS, public_exports=__all__)
