# @generated AUTO-GENERATED FILE — Regenerate with: make gen
"""Flext Tests package."""

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
    from flext_infra import d as d, e as e, h as h, r as r, x as x

    from ._config import FlextTestsConfig as FlextTestsConfig, config as config
    from ._settings import (
        FlextTestsSettings as FlextTestsSettings,
        settings as settings,
    )
    from .base import (
        FlextTestsCase as FlextTestsCase,
        FlextTestsServiceBase as FlextTestsServiceBase,
    )
    from ._fixtures.settings import reset_settings as reset_settings

    s: type[FlextTestsServiceBase]
    from .constants import FlextTestsConstants as FlextTestsConstants

    c: type[FlextTestsConstants]
    from .docker import FlextTestsDocker as FlextTestsDocker, tk as tk
    from .domains import FlextTestsDomains as FlextTestsDomains, td as td
    from .files import FlextTestsFiles as FlextTestsFiles, tf as tf
    from .models import FlextTestsModels as FlextTestsModels

    m: type[FlextTestsModels]
    from .protocols import FlextTestsProtocols as FlextTestsProtocols

    p: type[FlextTestsProtocols]
    from .tmatchers import (
        FlextTestsMatchersUtilities as FlextTestsMatchersUtilities,
        tm as tm,
    )
    from .typings import FlextTestsTypes as FlextTestsTypes

    t: type[FlextTestsTypes]
    from .utilities import FlextTestsUtilities as FlextTestsUtilities

    u: type[FlextTestsUtilities]
    from .validator import FlextTestsValidator as FlextTestsValidator, tv as tv

_LAZY_MODULES: dict[str, tuple[str, ...]] = {
    "._config": ("FlextTestsConfig", "config"),
    "._settings": ("FlextTestsSettings", "settings"),
    ".base": ("FlextTestsCase", "FlextTestsServiceBase", "s"),
    "._fixtures.settings": ("reset_settings",),
    ".constants": ("FlextTestsConstants", "c"),
    ".docker": ("FlextTestsDocker", "tk"),
    ".domains": ("FlextTestsDomains", "td"),
    ".files": ("FlextTestsFiles", "tf"),
    ".models": ("FlextTestsModels", "m"),
    ".protocols": ("FlextTestsProtocols", "p"),
    ".tmatchers": ("FlextTestsMatchersUtilities", "tm"),
    ".typings": ("FlextTestsTypes", "t"),
    ".utilities": ("FlextTestsUtilities", "u"),
    ".validator": ("FlextTestsValidator", "tv"),
    "flext_infra": ("d", "e", "h", "r", "x"),
}


_LAZY_ALIAS_GROUPS: dict[str, tuple[tuple[str, str], ...]] = {}


_LAZY_IMPORTS = build_lazy_import_map(
    _LAZY_MODULES, alias_groups=_LAZY_ALIAS_GROUPS, sort_keys=False
)

_PUBLIC_EXPORTS: tuple[str, ...] = (
    "FlextTestsCase",
    "FlextTestsConfig",
    "FlextTestsConstants",
    "FlextTestsDocker",
    "FlextTestsDomains",
    "FlextTestsFiles",
    "FlextTestsMatchersUtilities",
    "FlextTestsModels",
    "FlextTestsProtocols",
    "FlextTestsServiceBase",
    "FlextTestsSettings",
    "FlextTestsTypes",
    "FlextTestsUtilities",
    "FlextTestsValidator",
    "__author__",
    "__author_email__",
    "__description__",
    "__license__",
    "__title__",
    "__url__",
    "__version__",
    "__version_info__",
    "c",
    "config",
    "d",
    "e",
    "h",
    "m",
    "p",
    "r",
    "reset_settings",
    "s",
    "settings",
    "t",
    "td",
    "tf",
    "tk",
    "tm",
    "tv",
    "u",
    "x",
)

__all__: tuple[str, ...] = tuple(_PUBLIC_EXPORTS)

install_lazy_exports(__name__, globals(), _LAZY_IMPORTS, public_exports=__all__)
