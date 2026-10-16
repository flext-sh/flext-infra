# AUTO-GENERATED FILE — Regenerate with: make gen
"""Flext Infra package.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from types import MappingProxyType
from typing import TYPE_CHECKING

from flext_core.lazy import install_lazy_exports

from flext_infra.__version__ import __version__

if TYPE_CHECKING:
    from flext_cli import d, e, h, r, x

    from flext_infra import (
        _constants,
        _models,
        _promoted,
        _protocols,
        _typings,
        _utilities,
        check,
        codegen,
        codemod,
        deps,
        docs,
        gates,
        maintenance,
        refactor,
        release,
        services,
        transformers,
        validate,
        workspace,
    )
    from flext_infra.__version__ import (
        FlextInfraVersion,
        __author__,
        __author_email__,
        __description__,
        __license__,
        __title__,
        __url__,
        __version_info__,
    )
    from flext_infra._base_payload import FlextInfraCommandPayloadMixin
    from flext_infra._base_projects import FlextInfraProjectSelectionMixin
    from flext_infra._config import FlextInfraConfig, config
    from flext_infra._conform_wiring import FlextInfraConformWiring
    from flext_infra._preview_wiring import FlextInfraPreviewWiring
    from flext_infra._pytest_clock import FlextInfraPytestClock
    from flext_infra._pytest_collection import FlextInfraPytestCollection
    from flext_infra._settings import FlextInfraSettings, settings
    from flext_infra.api import FlextInfra, infra
    from flext_infra.base import FlextInfraServiceBase, s
    from flext_infra.base_selection import FlextInfraProjectSelectionServiceBase
    from flext_infra.cli import FlextInfraCli, main
    from flext_infra.constants import FlextInfraConstants, c
    from flext_infra.git import FlextInfraGitService
    from flext_infra.git_lanes import FlextInfraGitLanes
    from flext_infra.models import FlextInfraModels, m
    from flext_infra.promoted import FlextInfraPromoted
    from flext_infra.protocols import FlextInfraProtocols, FlextInfraProtocolsBase, p
    from flext_infra.pytest_profile import FlextInfraPytestProfile
    from flext_infra.typings import FlextInfraTypes, t
    from flext_infra.utilities import FlextInfraUtilities, u
    from flext_infra.worktree import FlextInfraWorktreeService


__all__: tuple[str, ...] = (
    "FlextInfra",
    "FlextInfraCli",
    "FlextInfraCommandPayloadMixin",
    "FlextInfraConfig",
    "FlextInfraConformWiring",
    "FlextInfraConstants",
    "FlextInfraGitLanes",
    "FlextInfraGitService",
    "FlextInfraModels",
    "FlextInfraPreviewWiring",
    "FlextInfraProjectSelectionMixin",
    "FlextInfraProjectSelectionServiceBase",
    "FlextInfraPromoted",
    "FlextInfraProtocols",
    "FlextInfraProtocolsBase",
    "FlextInfraPytestClock",
    "FlextInfraPytestCollection",
    "FlextInfraPytestProfile",
    "FlextInfraServiceBase",
    "FlextInfraSettings",
    "FlextInfraTypes",
    "FlextInfraUtilities",
    "FlextInfraVersion",
    "FlextInfraWorktreeService",
    "__author__",
    "__author_email__",
    "__description__",
    "__license__",
    "__title__",
    "__url__",
    "__version__",
    "__version_info__",
    "_constants",
    "_models",
    "_promoted",
    "_protocols",
    "_typings",
    "_utilities",
    "c",
    "check",
    "codegen",
    "codemod",
    "config",
    "d",
    "deps",
    "docs",
    "e",
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

install_lazy_exports(
    __name__,
    globals(),
    MappingProxyType({
        "FlextInfra": ".api",
        "FlextInfraCli": ".cli",
        "FlextInfraCommandPayloadMixin": "._base_payload",
        "FlextInfraConfig": "._config",
        "FlextInfraConformWiring": "._conform_wiring",
        "FlextInfraConstants": ".constants",
        "FlextInfraGitLanes": ".git_lanes",
        "FlextInfraGitService": ".git",
        "FlextInfraModels": ".models",
        "FlextInfraPreviewWiring": "._preview_wiring",
        "FlextInfraProjectSelectionMixin": "._base_projects",
        "FlextInfraProjectSelectionServiceBase": ".base_selection",
        "FlextInfraPromoted": ".promoted",
        "FlextInfraProtocols": ".protocols",
        "FlextInfraProtocolsBase": ".protocols",
        "FlextInfraPytestClock": "._pytest_clock",
        "FlextInfraPytestCollection": "._pytest_collection",
        "FlextInfraPytestProfile": ".pytest_profile",
        "FlextInfraServiceBase": ".base",
        "FlextInfraSettings": "._settings",
        "FlextInfraTypes": ".typings",
        "FlextInfraUtilities": ".utilities",
        "FlextInfraVersion": ".__version__",
        "FlextInfraWorktreeService": ".worktree",
        "__author__": ".__version__",
        "__author_email__": ".__version__",
        "__description__": ".__version__",
        "__license__": ".__version__",
        "__title__": ".__version__",
        "__url__": ".__version__",
        "__version_info__": ".__version__",
        "_constants": "._constants",
        "_models": "._models",
        "_promoted": "._promoted",
        "_protocols": "._protocols",
        "_typings": "._typings",
        "_utilities": "._utilities",
        "c": ".constants",
        "check": ".check",
        "codegen": ".codegen",
        "codemod": ".codemod",
        "config": "._config",
        "d": "flext_cli",
        "deps": ".deps",
        "docs": ".docs",
        "e": "flext_cli",
        "gates": ".gates",
        "h": "flext_cli",
        "infra": ".api",
        "m": ".models",
        "main": ".cli",
        "maintenance": ".maintenance",
        "p": ".protocols",
        "r": "flext_cli",
        "refactor": ".refactor",
        "release": ".release",
        "s": ".base",
        "services": ".services",
        "settings": "._settings",
        "t": ".typings",
        "transformers": ".transformers",
        "u": ".utilities",
        "validate": ".validate",
        "workspace": ".workspace",
        "x": "flext_cli",
    }),
    public_exports=__all__,
)
