# AUTO-GENERATED FILE — Regenerate with: make gen
"""Flext Infra package."""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_core.lazy import build_lazy_import_map, install_lazy_exports

from .__version__ import __author__ as __author__
from .__version__ import __author_email__ as __author_email__
from .__version__ import __description__ as __description__
from .__version__ import __license__ as __license__
from .__version__ import __title__ as __title__
from .__version__ import __url__ as __url__
from .__version__ import __version__ as __version__
from .__version__ import __version_info__ as __version_info__

if TYPE_CHECKING:
    from . import basemk as basemk
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
    from .worktree import FlextInfraWorktreeService

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
    ".worktree": ("FlextInfraWorktreeService",),
    "flext_cli": ("d", "e", "h", "r", "x"),
}


_LAZY_ALIAS_GROUPS: dict[str, tuple[tuple[str, str], ...]] = {}


_LAZY_IMPORTS = build_lazy_import_map(
    _LAZY_MODULES, alias_groups=_LAZY_ALIAS_GROUPS, sort_keys=False
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
    "FlextInfraWorktreeService",
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
