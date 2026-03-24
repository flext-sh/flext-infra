# AUTO-GENERATED FILE — DO NOT EDIT MANUALLY.
# Regenerate with: make codegen
#
"""Phase modules for pyproject dependency detector standardization."""

from __future__ import annotations

from collections.abc import Mapping, MutableMapping, Sequence
from typing import TYPE_CHECKING

from flext_core.lazy import cleanup_submodule_namespace, lazy_getattr

if TYPE_CHECKING:
    from flext_core import FlextTypes

    from flext_infra.deps._phases.consolidate_groups import (
        ConsolidateGroupsPhase,
        FlextInfraConsolidateGroupsPhase,
    )
    from flext_infra.deps._phases.ensure_coverage import (
        EnsureCoverageConfigPhase,
        FlextInfraEnsureCoverageConfigPhase,
    )
    from flext_infra.deps._phases.ensure_extra_paths import (
        EnsureExtraPathsPhase,
        FlextInfraEnsureExtraPathsPhase,
    )
    from flext_infra.deps._phases.ensure_formatting import (
        EnsureFormattingToolingPhase,
        FlextInfraEnsureFormattingToolingPhase,
    )
    from flext_infra.deps._phases.ensure_mypy import (
        EnsureMypyConfigPhase,
        FlextInfraEnsureMypyConfigPhase,
    )
    from flext_infra.deps._phases.ensure_namespace import (
        EnsureNamespaceToolingPhase,
        FlextInfraEnsureNamespaceToolingPhase,
    )
    from flext_infra.deps._phases.ensure_pydantic_mypy import (
        EnsurePydanticMypyConfigPhase,
        FlextInfraEnsurePydanticMypyConfigPhase,
    )
    from flext_infra.deps._phases.ensure_pyrefly import (
        EnsurePyreflyConfigPhase,
        FlextInfraEnsurePyreflyConfigPhase,
    )
    from flext_infra.deps._phases.ensure_pyright import (
        EnsurePyrightConfigPhase,
        FlextInfraEnsurePyrightConfigPhase,
    )
    from flext_infra.deps._phases.ensure_pytest import (
        EnsurePytestConfigPhase,
        FlextInfraEnsurePytestConfigPhase,
    )
    from flext_infra.deps._phases.ensure_ruff import (
        EnsureRuffConfigPhase,
        FlextInfraEnsureRuffConfigPhase,
    )
    from flext_infra.deps._phases.inject_comments import (
        FlextInfraInjectCommentsPhase,
        InjectCommentsPhase,
    )

_LAZY_IMPORTS: Mapping[str, tuple[str, str]] = {
    "ConsolidateGroupsPhase": ("flext_infra.deps._phases.consolidate_groups", "ConsolidateGroupsPhase"),
    "EnsureCoverageConfigPhase": ("flext_infra.deps._phases.ensure_coverage", "EnsureCoverageConfigPhase"),
    "EnsureExtraPathsPhase": ("flext_infra.deps._phases.ensure_extra_paths", "EnsureExtraPathsPhase"),
    "EnsureFormattingToolingPhase": ("flext_infra.deps._phases.ensure_formatting", "EnsureFormattingToolingPhase"),
    "EnsureMypyConfigPhase": ("flext_infra.deps._phases.ensure_mypy", "EnsureMypyConfigPhase"),
    "EnsureNamespaceToolingPhase": ("flext_infra.deps._phases.ensure_namespace", "EnsureNamespaceToolingPhase"),
    "EnsurePydanticMypyConfigPhase": ("flext_infra.deps._phases.ensure_pydantic_mypy", "EnsurePydanticMypyConfigPhase"),
    "EnsurePyreflyConfigPhase": ("flext_infra.deps._phases.ensure_pyrefly", "EnsurePyreflyConfigPhase"),
    "EnsurePyrightConfigPhase": ("flext_infra.deps._phases.ensure_pyright", "EnsurePyrightConfigPhase"),
    "EnsurePytestConfigPhase": ("flext_infra.deps._phases.ensure_pytest", "EnsurePytestConfigPhase"),
    "EnsureRuffConfigPhase": ("flext_infra.deps._phases.ensure_ruff", "EnsureRuffConfigPhase"),
    "FlextInfraConsolidateGroupsPhase": ("flext_infra.deps._phases.consolidate_groups", "FlextInfraConsolidateGroupsPhase"),
    "FlextInfraEnsureCoverageConfigPhase": ("flext_infra.deps._phases.ensure_coverage", "FlextInfraEnsureCoverageConfigPhase"),
    "FlextInfraEnsureExtraPathsPhase": ("flext_infra.deps._phases.ensure_extra_paths", "FlextInfraEnsureExtraPathsPhase"),
    "FlextInfraEnsureFormattingToolingPhase": ("flext_infra.deps._phases.ensure_formatting", "FlextInfraEnsureFormattingToolingPhase"),
    "FlextInfraEnsureMypyConfigPhase": ("flext_infra.deps._phases.ensure_mypy", "FlextInfraEnsureMypyConfigPhase"),
    "FlextInfraEnsureNamespaceToolingPhase": ("flext_infra.deps._phases.ensure_namespace", "FlextInfraEnsureNamespaceToolingPhase"),
    "FlextInfraEnsurePydanticMypyConfigPhase": ("flext_infra.deps._phases.ensure_pydantic_mypy", "FlextInfraEnsurePydanticMypyConfigPhase"),
    "FlextInfraEnsurePyreflyConfigPhase": ("flext_infra.deps._phases.ensure_pyrefly", "FlextInfraEnsurePyreflyConfigPhase"),
    "FlextInfraEnsurePyrightConfigPhase": ("flext_infra.deps._phases.ensure_pyright", "FlextInfraEnsurePyrightConfigPhase"),
    "FlextInfraEnsurePytestConfigPhase": ("flext_infra.deps._phases.ensure_pytest", "FlextInfraEnsurePytestConfigPhase"),
    "FlextInfraEnsureRuffConfigPhase": ("flext_infra.deps._phases.ensure_ruff", "FlextInfraEnsureRuffConfigPhase"),
    "FlextInfraInjectCommentsPhase": ("flext_infra.deps._phases.inject_comments", "FlextInfraInjectCommentsPhase"),
    "InjectCommentsPhase": ("flext_infra.deps._phases.inject_comments", "InjectCommentsPhase"),
}

__all__ = [
    "ConsolidateGroupsPhase",
    "EnsureCoverageConfigPhase",
    "EnsureExtraPathsPhase",
    "EnsureFormattingToolingPhase",
    "EnsureMypyConfigPhase",
    "EnsureNamespaceToolingPhase",
    "EnsurePydanticMypyConfigPhase",
    "EnsurePyreflyConfigPhase",
    "EnsurePyrightConfigPhase",
    "EnsurePytestConfigPhase",
    "EnsureRuffConfigPhase",
    "FlextInfraConsolidateGroupsPhase",
    "FlextInfraEnsureCoverageConfigPhase",
    "FlextInfraEnsureExtraPathsPhase",
    "FlextInfraEnsureFormattingToolingPhase",
    "FlextInfraEnsureMypyConfigPhase",
    "FlextInfraEnsureNamespaceToolingPhase",
    "FlextInfraEnsurePydanticMypyConfigPhase",
    "FlextInfraEnsurePyreflyConfigPhase",
    "FlextInfraEnsurePyrightConfigPhase",
    "FlextInfraEnsurePytestConfigPhase",
    "FlextInfraEnsureRuffConfigPhase",
    "FlextInfraInjectCommentsPhase",
    "InjectCommentsPhase",
]


_LAZY_CACHE: MutableMapping[str, FlextTypes.ModuleExport] = {}


def __getattr__(name: str) -> FlextTypes.ModuleExport:
    """Lazy-load module attributes on first access (PEP 562).

    A local cache ``_LAZY_CACHE`` persists resolved objects across repeated
    accesses during process lifetime.

    Args:
        name: Attribute name requested by dir()/import.

    Returns:
        Lazy-loaded module export type.

    Raises:
        AttributeError: If attribute not registered.

    """
    if name in _LAZY_CACHE:
        return _LAZY_CACHE[name]

    value = lazy_getattr(name, _LAZY_IMPORTS, globals(), __name__)
    _LAZY_CACHE[name] = value
    return value


def __dir__() -> Sequence[str]:
    """Return list of available attributes for dir() and autocomplete.

    Returns:
        List of public names from module exports.

    """
    return sorted(__all__)


cleanup_submodule_namespace(__name__, _LAZY_IMPORTS)
