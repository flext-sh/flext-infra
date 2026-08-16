# AUTO-GENERATED FILE — Regenerate with: make gen
"""Tests.unit.github package."""

from __future__ import annotations

from typing import TYPE_CHECKING

from types import MappingProxyType

from flext_core.lazy import build_lazy_import_map, install_lazy_exports

if TYPE_CHECKING:
    from . import main_cli_tests as main_cli_tests
    from . import main_dispatch_tests as main_dispatch_tests
    from . import main_integration_tests as main_integration_tests
    from flext_tests import c, d, e, h, m, p, r, s, t, td, tf, tk, tm, tv, u, x

    from .main_tests import TestsInfraGithub
__all__: tuple[str, ...] = (
    "TestsInfraGithub",
    "c",
    "d",
    "e",
    "h",
    "m",
    "main_cli_tests",
    "main_dispatch_tests",
    "main_integration_tests",
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
                ".main_cli_tests": ("main_cli_tests",),
                ".main_dispatch_tests": ("main_dispatch_tests",),
                ".main_integration_tests": ("main_integration_tests",),
                ".main_tests": ("TestsInfraGithub",),
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
