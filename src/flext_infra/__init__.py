# AUTO-GENERATED FILE — Regenerate with: make gen
"""Flext Infra package."""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_core.lazy import build_lazy_import_map, install_lazy_exports
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

if TYPE_CHECKING:
    from . import basemk
    from flext_cli import d, e, h, r, x

    from ._config import config
    from ._settings import settings
    from .api import FlextInfra, infra
    from .base import FlextInfraServiceBase, FlextInfraServiceBase as s
    from .base_selection import FlextInfraProjectSelectionServiceBase
    from .cli import FlextInfraCli, docs_main, main
    from .constants import FlextInfraConstants, FlextInfraConstants as c
    from .models import FlextInfraModels, FlextInfraModels as m
    from .protocols import FlextInfraProtocols, FlextInfraProtocols as p
    from .typings import FlextInfraTypes, FlextInfraTypes as t
    from .utilities import FlextInfraUtilities, FlextInfraUtilities as u

    _ = (
        basemk,
        d,
        e,
        h,
        r,
        x,
        config,
        settings,
        FlextInfra,
        infra,
        FlextInfraServiceBase,
        s,
        FlextInfraProjectSelectionServiceBase,
        FlextInfraCli,
        docs_main,
        main,
        FlextInfraConstants,
        c,
        FlextInfraModels,
        m,
        FlextInfraProtocols,
        p,
        FlextInfraTypes,
        t,
        FlextInfraUtilities,
        u,
    )


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
    ".protocols": ("FlextInfraProtocols", "p"),
    ".typings": ("FlextInfraTypes", "t"),
    ".utilities": ("FlextInfraUtilities", "u"),
    "flext_cli": ("d", "e", "h", "r", "x"),
}


_LAZY_ALIAS_GROUPS: dict[str, tuple[tuple[str, str], ...]] = {}


_LAZY_IMPORTS = build_lazy_import_map(
    _LAZY_MODULES, alias_groups=_LAZY_ALIAS_GROUPS, sort_keys=False
)

_DIRECT_IMPORTS: tuple[str, ...] = (
    "FlextInfra",
    "FlextInfraCli",
    "FlextInfraConstants",
    "FlextInfraModels",
    "FlextInfraProjectSelectionServiceBase",
    "FlextInfraProtocols",
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
    "build_lazy_import_map",
    "c",
    "config",
    "d",
    "docs_main",
    "e",
    "h",
    "infra",
    "install_lazy_exports",
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

__all__: tuple[str, ...] = (
    "FlextInfra",
    "FlextInfraCli",
    "FlextInfraConstants",
    "FlextInfraModels",
    "FlextInfraProjectSelectionServiceBase",
    "FlextInfraProtocols",
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


install_lazy_exports(__name__, globals(), _LAZY_IMPORTS, public_exports=__all__)
