# AUTO-GENERATED FILE — Regenerate with: make gen
"""Flext Infra package."""

from __future__ import annotations

from typing import TYPE_CHECKING

from types import MappingProxyType

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
    from . import check as check
    from . import codegen as codegen
    from . import codemod as codemod
    from . import deps as deps
    from . import detectors as detectors
    from . import docs as docs
    from . import fixers as fixers
    from . import gates as gates
    from . import maintenance as maintenance
    from . import refactor as refactor
    from . import release as release
    from . import services as services
    from . import transformers as transformers
    from . import validate as validate
    from . import workspace as workspace
    from flext_cli import d, e, h, r, x

    from ._config import config
    from ._settings import settings
    from .api import FlextInfra, infra
    from .base import FlextInfraServiceBase, FlextInfraServiceBase as s
    from .base_selection import FlextInfraProjectSelectionServiceBase
    from .cli import FlextInfraCli, docs_main, main
    from .constants import FlextInfraConstants, FlextInfraConstants as c
    from .git import FlextInfraGitService
    from .iteration import FlextInfraUtilitiesIteration
    from .models import FlextInfraModels, FlextInfraModels as m
    from .protocols import (
        FlextInfraProtocols,
        FlextInfraProtocols as p,
        FlextInfraProtocolsBase,
    )
    from .typings import FlextInfraTypes, FlextInfraTypes as t
    from .utilities import FlextInfraUtilities, FlextInfraUtilities as u
    from .worktree import FlextInfraWorktreeService
__all__: tuple[str, ...] = (
    "FlextInfra",
    "FlextInfraCli",
    "FlextInfraConstants",
    "FlextInfraGitService",
    "FlextInfraModels",
    "FlextInfraProjectSelectionServiceBase",
    "FlextInfraProtocols",
    "FlextInfraProtocolsBase",
    "FlextInfraServiceBase",
    "FlextInfraTypes",
    "FlextInfraUtilities",
    "FlextInfraUtilitiesIteration",
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
    "check",
    "codegen",
    "codemod",
    "config",
    "d",
    "deps",
    "detectors",
    "docs",
    "docs_main",
    "e",
    "fixers",
    "gates",
    "h",
    "infra",
    "m",
    "main",
    "maintenance",
    "p",
    "r",
    "refactor",
    "release",
    "s",
    "services",
    "settings",
    "t",
    "transformers",
    "u",
    "validate",
    "workspace",
    "x",
)

_LAZY_IMPORTS = MappingProxyType(
    build_lazy_import_map(
        MappingProxyType({
            "._config": ("config",),
            "._settings": ("settings",),
            ".api": ("FlextInfra", "infra"),
            ".base": ("FlextInfraServiceBase", "s"),
            ".base_selection": ("FlextInfraProjectSelectionServiceBase",),
            ".basemk": ("basemk",),
            ".check": ("check",),
            ".cli": ("FlextInfraCli", "docs_main", "main"),
            ".codegen": ("codegen",),
            ".codemod": ("codemod",),
            ".constants": ("FlextInfraConstants", "c"),
            ".deps": ("deps",),
            ".detectors": ("detectors",),
            ".docs": ("docs",),
            ".fixers": ("fixers",),
            ".gates": ("gates",),
            ".git": ("FlextInfraGitService",),
            ".iteration": ("FlextInfraUtilitiesIteration",),
            ".maintenance": ("maintenance",),
            ".models": ("FlextInfraModels", "m"),
            ".protocols": ("FlextInfraProtocols", "FlextInfraProtocolsBase", "p"),
            ".refactor": ("refactor",),
            ".release": ("release",),
            ".services": ("services",),
            ".transformers": ("transformers",),
            ".typings": ("FlextInfraTypes", "t"),
            ".utilities": ("FlextInfraUtilities", "u"),
            ".validate": ("validate",),
            ".workspace": ("workspace",),
            ".worktree": ("FlextInfraWorktreeService",),
            "flext_cli": ("d", "e", "h", "r", "x"),
        }),
        alias_groups=MappingProxyType({}),
        sort_keys=False,
    )
)

install_lazy_exports(__name__, globals(), _LAZY_IMPORTS, public_exports=__all__)
