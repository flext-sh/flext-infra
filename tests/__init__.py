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
    from flext_tests import c, d, e, h, m, p, r, s, t, u, x

    _ = (c, d, e, h, m, p, r, s, t, u, x)


_LAZY_MODULES: dict[str, tuple[str, ...]] = {
    "flext_tests": ("c", "d", "e", "h", "m", "p", "r", "s", "t", "u", "x")
}


_LAZY_ALIAS_GROUPS: dict[str, tuple[tuple[str, str], ...]] = {}


_LAZY_IMPORTS = _build_lazy_import_map(
    _LAZY_MODULES, alias_groups=_LAZY_ALIAS_GROUPS, sort_keys=False
)

__all__: tuple[str, ...] = ("c", "d", "e", "h", "m", "p", "r", "s", "t", "u", "x")


_install_lazy_exports(__name__, globals(), _LAZY_IMPORTS, public_exports=__all__)
