# @generated AUTO-GENERATED FILE — Regenerate with: make gen
"""Flext Tests. Models package."""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_core.lazy import build_lazy_import_map, install_lazy_exports

if TYPE_CHECKING:
    from .base import FlextTestsBaseModelsMixin as FlextTestsBaseModelsMixin
    from .batch import FlextTestsBatchModelsMixin as FlextTestsBatchModelsMixin
    from .docker import FlextTestsDockerModelsMixin as FlextTestsDockerModelsMixin
    from .domains import FlextTestsDomainModelsMixin as FlextTestsDomainModelsMixin
    from .filesystem import (
        FlextTestsFilesystemModelsMixin as FlextTestsFilesystemModelsMixin,
    )
    from .make import FlextTestsMakeModelsMixin as FlextTestsMakeModelsMixin
    from .matchers import FlextTestsMatchersModelsMixin as FlextTestsMatchersModelsMixin
    from .validator import (
        FlextTestsValidatorModelsMixin as FlextTestsValidatorModelsMixin,
    )
    from .workspace_cleanup import (
        FlextTestsWorkspaceCleanupModelsMixin as FlextTestsWorkspaceCleanupModelsMixin,
    )

_LAZY_MODULES: dict[str, tuple[str, ...]] = {
    ".base": ("FlextTestsBaseModelsMixin",),
    ".batch": ("FlextTestsBatchModelsMixin",),
    ".docker": ("FlextTestsDockerModelsMixin",),
    ".domains": ("FlextTestsDomainModelsMixin",),
    ".filesystem": ("FlextTestsFilesystemModelsMixin",),
    ".make": ("FlextTestsMakeModelsMixin",),
    ".matchers": ("FlextTestsMatchersModelsMixin",),
    ".validator": ("FlextTestsValidatorModelsMixin",),
    ".workspace_cleanup": ("FlextTestsWorkspaceCleanupModelsMixin",),
}


_LAZY_ALIAS_GROUPS: dict[str, tuple[tuple[str, str], ...]] = {}


_LAZY_IMPORTS = build_lazy_import_map(
    _LAZY_MODULES, alias_groups=_LAZY_ALIAS_GROUPS, sort_keys=False
)

_PUBLIC_EXPORTS: tuple[str, ...] = (
    "FlextTestsBaseModelsMixin",
    "FlextTestsBatchModelsMixin",
    "FlextTestsDockerModelsMixin",
    "FlextTestsDomainModelsMixin",
    "FlextTestsFilesystemModelsMixin",
    "FlextTestsMakeModelsMixin",
    "FlextTestsMatchersModelsMixin",
    "FlextTestsValidatorModelsMixin",
    "FlextTestsWorkspaceCleanupModelsMixin",
)

__all__: tuple[str, ...] = tuple(_PUBLIC_EXPORTS)

install_lazy_exports(__name__, globals(), _LAZY_IMPORTS, public_exports=__all__)
