# AUTO-GENERATED FILE — Regenerate with: make gen
"""Tests package.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_core.lazy import (
    build_lazy_import_map as _build_lazy_import_map,
    install_lazy_exports as _install_lazy_exports,
)

if TYPE_CHECKING:
    from flext_tests import d, e, h, r, td, tf, tk, tm, tv, x

    from .base import TestsFlextInfraServiceBase, s
    from .constants import TestsFlextInfraConstants, c
    from .models import TestsFlextInfraModels, m
    from .protocols import TestsFlextInfraProtocols, p
    from .typings import TestsFlextInfraTypes, t
    from .utilities import TestsFlextInfraUtilities, u

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

_LAZY_IMPORTS = _build_lazy_import_map(
    _LAZY_MODULES, alias_groups=_LAZY_ALIAS_GROUPS, sort_keys=False
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

_install_lazy_exports(__name__, globals(), _LAZY_IMPORTS, public_exports=__all__)
