# AUTO-GENERATED FILE — Regenerate with: make gen
"""Flext Infra package.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_core.lazy import (
    build_lazy_import_map as _build_lazy_import_map,
    install_lazy_exports as _install_lazy_exports,
)
from flext_infra.__version__ import (
    __author__,
    __author_email__,
    __description__,
    __license__,
    __title__,
    __url__,
    __version__,
    __version_info__,
)

# mro-wkii.17.26.2 (codex): root PEP 562 exports need static declarations,
# while runtime resolution must remain lazy to prevent facade import cycles.
if TYPE_CHECKING:
    from flext_cli import d, e, h, r, x

    from . import basemk
    from ._config import config
    from ._settings import settings
    from .api import FlextInfra, infra
    from .base import FlextInfraServiceBase, FlextInfraServiceBase as s
    from .base_selection import FlextInfraProjectSelectionServiceBase
    from .cli import FlextInfraCli, docs_main, main
    from .constants import FlextInfraConstants, FlextInfraConstants as c
    from .models import FlextInfraModels, FlextInfraModels as m
    from .protocols import FlextInfraProtocols, FlextInfraProtocolsBase, p
    from .typings import FlextInfraTypes, FlextInfraTypes as t
    from .utilities import FlextInfraUtilities, FlextInfraUtilities as u

_LAZY_MODULES: dict[str, tuple[str, ...]] = {
    "._config": ("config",),
    "._settings": ("settings",),
    ".api": ("FlextInfra", "infra"),
    ".base": ("FlextInfraServiceBase", "s"),
    ".base_selection": ("FlextInfraProjectSelectionServiceBase",),
    ".basemk": ("basemk",),
    ".cli": ("FlextInfraCli", "docs_main", "main"),
    ".constants": ("FlextInfraConstants", "c"),
    ".models": ("FlextInfraModels", "m"),
    ".protocols": ("FlextInfraProtocols", "FlextInfraProtocolsBase", "p"),
    ".typings": ("FlextInfraTypes", "t"),
    ".utilities": ("FlextInfraUtilities", "u"),
    "flext_cli": ("d", "e", "h", "r", "x"),
}

_LAZY_ALIAS_GROUPS: dict[str, tuple[tuple[str, str], ...]] = {}

_LAZY_IMPORTS = _build_lazy_import_map(
    _LAZY_MODULES, alias_groups=_LAZY_ALIAS_GROUPS, sort_keys=False
)

__all__: tuple[str, ...] = (
    "FlextInfra",
    "FlextInfraCli",
    "FlextInfraConstants",
    "FlextInfraModels",
    "FlextInfraProjectSelectionServiceBase",
    "FlextInfraProtocols",
    "FlextInfraProtocolsBase",
    "FlextInfraServiceBase",
    "FlextInfraTypes",
    "FlextInfraUtilities",
    "__author__",
    "__author_email__",
    "__description__",
    "__license__",
    "__title__",
    "__url__",
    "__version__",
    "__version_info__",
    "basemk",
    "c",
    "config",
    "d",
    "docs_main",
    "e",
    "h",
    "infra",
    "m",
    "main",
    "p",
    "r",
    "s",
    "settings",
    "t",
    "u",
    "x",
)

_install_lazy_exports(__name__, globals(), _LAZY_IMPORTS, public_exports=__all__)
