# AUTO-GENERATED FILE — Regenerate with: make gen
"""Tests.unit.io package."""

from __future__ import annotations

from typing import TYPE_CHECKING

from types import MappingProxyType

from flext_core.lazy import build_lazy_import_map, install_lazy_exports

if TYPE_CHECKING:
    from .test_infra_terminal_detection import TestsFlextInfraIoInfraTerminalDetection
__all__: tuple[str, ...] = ("TestsFlextInfraIoInfraTerminalDetection",)

_LAZY_IMPORTS = MappingProxyType(
    build_lazy_import_map(
        MappingProxyType({
            ".test_infra_terminal_detection": (
                "TestsFlextInfraIoInfraTerminalDetection",
            )
        }),
        alias_groups=MappingProxyType({}),
        sort_keys=False,
    )
)

install_lazy_exports(__name__, globals(), _LAZY_IMPORTS, public_exports=__all__)
