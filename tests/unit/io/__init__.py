# AUTO-GENERATED FILE — Regenerate with: make gen
"""Tests.unit.io package."""

from __future__ import annotations

from typing import TYPE_CHECKING

from types import MappingProxyType

from flext_core.lazy import build_lazy_import_map, install_lazy_exports

if TYPE_CHECKING:
    from flext_tests import c, d, e, h, m, p, r, s, t, td, tf, tk, tm, tv, u, x

    from .test_infra_terminal_detection import TestsFlextInfraIoInfraTerminalDetection
__all__: tuple[str, ...] = (
    "TestsFlextInfraIoInfraTerminalDetection",
    "c",
    "d",
    "e",
    "h",
    "m",
    "p",
    "r",
    "s",
    "t",
    "td",
    "tf",
    "tk",
    "tm",
    "tv",
    "u",
    "x",
)

install_lazy_exports(
    __name__,
    globals(),
    MappingProxyType(
        build_lazy_import_map(
            MappingProxyType({
                ".test_infra_terminal_detection": (
                    "TestsFlextInfraIoInfraTerminalDetection",
                ),
                "flext_tests": (
                    "c",
                    "d",
                    "e",
                    "h",
                    "m",
                    "p",
                    "r",
                    "s",
                    "t",
                    "td",
                    "tf",
                    "tk",
                    "tm",
                    "tv",
                    "u",
                    "x",
                ),
            }),
            alias_groups=MappingProxyType({}),
            sort_keys=False,
        )
    ),
    public_exports=__all__,
)
