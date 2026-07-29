# AUTO-GENERATED FILE — Regenerate with: make gen
"""Tests package."""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_core.lazy import build_lazy_import_map, install_lazy_exports

if TYPE_CHECKING:
    from flext_tests import d, e, h, r, td, tf, tk, tm, tv, x

    from .base import TestsFlextInfraServiceBase, TestsFlextInfraServiceBase as s
    from .constants import TestsFlextInfraConstants, TestsFlextInfraConstants as c
    from .models import TestsFlextInfraModels, TestsFlextInfraModels as m
    from .protocols import TestsFlextInfraProtocols, TestsFlextInfraProtocols as p
    from .typings import TestsFlextInfraTypes, TestsFlextInfraTypes as t
    from .utilities import TestsFlextInfraUtilities, TestsFlextInfraUtilities as u

    _ = (
        d,
        e,
        h,
        r,
        td,
        tf,
        tk,
        tm,
        tv,
        x,
        TestsFlextInfraServiceBase,
        s,
        TestsFlextInfraConstants,
        c,
        TestsFlextInfraModels,
        m,
        TestsFlextInfraProtocols,
        p,
        TestsFlextInfraTypes,
        t,
        TestsFlextInfraUtilities,
        u,
    )


_LAZY_MODULES: dict[str, tuple[str, ...]] = {
    ".base": ("TestsFlextInfraServiceBase", "s"),
    ".constants": ("TestsFlextInfraConstants", "c"),
    ".models": ("TestsFlextInfraModels", "m"),
    ".protocols": ("TestsFlextInfraProtocols", "p"),
    ".typings": ("TestsFlextInfraTypes", "t"),
    ".utilities": ("TestsFlextInfraUtilities", "u"),
    "flext_tests": ("d", "e", "h", "r", "td", "tf", "tk", "tm", "tv", "x"),
}


_LAZY_ALIAS_GROUPS: dict[str, tuple[tuple[str, str], ...]] = {}


_LAZY_IMPORTS = build_lazy_import_map(
    _LAZY_MODULES, alias_groups=_LAZY_ALIAS_GROUPS, sort_keys=False
)

_DIRECT_IMPORTS: tuple[str, ...] = (
    "TestsFlextInfraConstants",
    "TestsFlextInfraModels",
    "TestsFlextInfraProtocols",
    "TestsFlextInfraServiceBase",
    "TestsFlextInfraTypes",
    "TestsFlextInfraUtilities",
    "build_lazy_import_map",
    "c",
    "d",
    "e",
    "h",
    "install_lazy_exports",
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


install_lazy_exports(__name__, globals(), _LAZY_IMPORTS, public_exports=__all__)
