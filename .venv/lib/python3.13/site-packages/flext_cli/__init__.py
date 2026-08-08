# @generated AUTO-GENERATED FILE — Regenerate with: make gen
"""Flext Cli package."""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_core.lazy import build_lazy_import_map, install_lazy_exports

from .__version__ import (
    __author__ as __author__,
    __author_email__ as __author_email__,
    __description__ as __description__,
    __license__ as __license__,
    __title__ as __title__,
    __url__ as __url__,
    __version__ as __version__,
    __version_info__ as __version_info__,
)

if TYPE_CHECKING:
    from flext_core import d as d, e as e, h as h, r as r, x as x

    from ._config import FlextCliConfig as FlextCliConfig, config as config
    from ._settings import FlextCliSettings as FlextCliSettings
    from ._settings import settings as settings
    from .api import FlextCli as FlextCli, cli as cli
    from .base import FlextCliServiceBase as FlextCliServiceBase, FlextCliServiceBase as s
    from .constants import FlextCliConstants as FlextCliConstants, FlextCliConstants as c
    from .models import FlextCliModels as FlextCliModels, FlextCliModels as m
    from .protocols import FlextCliProtocols as FlextCliProtocols, FlextCliProtocols as p
    from .typings import FlextCliTypes as FlextCliTypes, FlextCliTypes as t
    from .utilities import FlextCliUtilities as FlextCliUtilities, FlextCliUtilities as u

_LAZY_MODULES: dict[str, tuple[str, ...]] = {
    ".api": ("FlextCli", "cli"),
    ".base": ("FlextCliServiceBase", "s"),
    ".constants": ("FlextCliConstants", "c"),
    ".models": ("FlextCliModels", "m"),
    ".protocols": ("FlextCliProtocols", "p"),
    "._config": ("FlextCliConfig", "config"),
    "._settings": ("FlextCliSettings", "settings"),
    ".typings": ("FlextCliTypes", "t"),
    ".utilities": ("FlextCliUtilities", "u"),
    "flext_core": ("d", "e", "h", "r", "x"),
}


_LAZY_ALIAS_GROUPS: dict[str, tuple[tuple[str, str], ...]] = {}


_LAZY_IMPORTS = build_lazy_import_map(
    _LAZY_MODULES, alias_groups=_LAZY_ALIAS_GROUPS, sort_keys=False
)

_PUBLIC_EXPORTS: tuple[str, ...] = (
    "FlextCli",
    "FlextCliConfig",
    "FlextCliConstants",
    "FlextCliModels",
    "FlextCliProtocols",
    "FlextCliServiceBase",
    "FlextCliSettings",
    "FlextCliTypes",
    "FlextCliUtilities",
    "__author__",
    "__author_email__",
    "__description__",
    "__license__",
    "__title__",
    "__url__",
    "__version__",
    "__version_info__",
    "c",
    "cli",
    "config",
    "d",
    "e",
    "h",
    "m",
    "p",
    "r",
    "s",
    "settings",
    "t",
    "u",
    "x",
)

__all__: tuple[str, ...] = tuple(_PUBLIC_EXPORTS)

install_lazy_exports(__name__, globals(), _LAZY_IMPORTS, public_exports=__all__)
