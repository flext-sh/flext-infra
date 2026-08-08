# @generated AUTO-GENERATED FILE — Regenerate with: make gen
"""Flext Tests. Utilities. Files package."""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_core.lazy import build_lazy_import_map, install_lazy_exports

if TYPE_CHECKING:
    from . import _comparison_parts as _comparison_parts
    from ._assertions import (
        FlextTestsFilesAssertionsMixin as FlextTestsFilesAssertionsMixin,
    )
    from ._batch import FlextTestsFilesBatchMixin as FlextTestsFilesBatchMixin
    from ._comparison import (
        FlextTestsFilesComparisonMixin as FlextTestsFilesComparisonMixin,
    )
    from ._contexts import FlextTestsFilesContextsMixin as FlextTestsFilesContextsMixin
    from ._creation import FlextTestsFilesCreationMixin as FlextTestsFilesCreationMixin
    from ._info import FlextTestsFilesInfoMixin as FlextTestsFilesInfoMixin
    from ._lifecycle import (
        FlextTestsFilesLifecycleMixin as FlextTestsFilesLifecycleMixin,
    )
    from ._reading import FlextTestsFilesReadingMixin as FlextTestsFilesReadingMixin

_LAZY_MODULES: dict[str, tuple[str, ...]] = {
    "._assertions": ("FlextTestsFilesAssertionsMixin",),
    "._batch": ("FlextTestsFilesBatchMixin",),
    "._comparison": ("FlextTestsFilesComparisonMixin",),
    "._comparison_parts": ("_comparison_parts",),
    "._contexts": ("FlextTestsFilesContextsMixin",),
    "._creation": ("FlextTestsFilesCreationMixin",),
    "._info": ("FlextTestsFilesInfoMixin",),
    "._lifecycle": ("FlextTestsFilesLifecycleMixin",),
    "._reading": ("FlextTestsFilesReadingMixin",),
}


_LAZY_ALIAS_GROUPS: dict[str, tuple[tuple[str, str], ...]] = {}


_LAZY_IMPORTS = build_lazy_import_map(
    _LAZY_MODULES, alias_groups=_LAZY_ALIAS_GROUPS, sort_keys=False
)

_PUBLIC_EXPORTS: tuple[str, ...] = (
    "FlextTestsFilesAssertionsMixin",
    "FlextTestsFilesBatchMixin",
    "FlextTestsFilesComparisonMixin",
    "FlextTestsFilesContextsMixin",
    "FlextTestsFilesCreationMixin",
    "FlextTestsFilesInfoMixin",
    "FlextTestsFilesLifecycleMixin",
    "FlextTestsFilesReadingMixin",
    "_comparison_parts",
)

__all__: tuple[str, ...] = tuple(_PUBLIC_EXPORTS)

install_lazy_exports(__name__, globals(), _LAZY_IMPORTS, public_exports=__all__)
