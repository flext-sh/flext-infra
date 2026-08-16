# AUTO-GENERATED FILE — Regenerate with: make gen
"""Tests package."""

from __future__ import annotations

from typing import TYPE_CHECKING

from types import MappingProxyType

from flext_core.lazy import build_lazy_import_map, install_lazy_exports

if TYPE_CHECKING:
    from flext_tests import d, e, h, r, td, tf, tk, tm, tv, x

    from .base import TestsFlextInfraServiceBase, TestsFlextInfraServiceBase as s
    from .constants import TestsFlextInfraConstants, TestsFlextInfraConstants as c
    from .models import TestsFlextInfraModels, TestsFlextInfraModels as m
    from .protocols import TestsFlextInfraProtocols, TestsFlextInfraProtocols as p
    from .typings import TestsFlextInfraTypes, TestsFlextInfraTypes as t
    from .utilities import TestsFlextInfraUtilities, TestsFlextInfraUtilities as u
__all__: tuple[str, ...] = (
    "TestsFlextInfraConstants",
    "TestsFlextInfraModels",
    "TestsFlextInfraProtocols",
    "TestsFlextInfraServiceBase",
    "TestsFlextInfraTypes",
    "TestsFlextInfraUtilities",
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
                ".base": ("TestsFlextInfraServiceBase", "s"),
                ".constants": ("TestsFlextInfraConstants", "c"),
                ".models": ("TestsFlextInfraModels", "m"),
                ".protocols": ("TestsFlextInfraProtocols", "p"),
                ".typings": ("TestsFlextInfraTypes", "t"),
                ".utilities": ("TestsFlextInfraUtilities", "u"),
                "flext_tests": ("d", "e", "h", "r", "td", "tf", "tk", "tm", "tv", "x"),
            }),
            alias_groups=MappingProxyType({}),
            sort_keys=False,
        )
    ),
    public_exports=__all__,
)
