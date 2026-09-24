# AUTO-GENERATED FILE — Regenerate with: make gen
"""Tests.unit.maintenance package."""

from __future__ import annotations

from types import MappingProxyType
from typing import TYPE_CHECKING

from flext_core.lazy import build_lazy_import_map, install_lazy_exports

if TYPE_CHECKING:
    from .sonarcloud_sync_tests import TestsFlextInfraSonarcloudSettingsSync


__all__: tuple[str, ...] = ("TestsFlextInfraSonarcloudSettingsSync",)

_LAZY_IMPORTS = MappingProxyType(
    build_lazy_import_map(
        MappingProxyType({
            ".sonarcloud_sync_tests": ("TestsFlextInfraSonarcloudSettingsSync",)
        }),
        alias_groups=MappingProxyType({}),
        sort_keys=False,
    )
)

install_lazy_exports(__name__, globals(), _LAZY_IMPORTS, public_exports=__all__)
