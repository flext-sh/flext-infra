# AUTO-GENERATED FILE — Regenerate with: make gen
"""Flext Infra package.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from types import MappingProxyType
from typing import TYPE_CHECKING

from flext_core.lazy import install_lazy_exports

if TYPE_CHECKING:
    from flext_infra.__version__ import (
        FlextInfraVersion,
        __author__,
        __author_email__,
        __description__,
        __license__,
        __title__,
        __url__,
        __version__,
        __version_info__,
    )
    from flext_infra._config import FlextInfraConfig, config
    from flext_infra._pytest_clock import FlextInfraPytestClock
    from flext_infra._settings import FlextInfraSettings, settings
    from flext_infra.api import FlextInfra, infra
    from flext_infra.base import FlextInfraServiceBase, s
    from flext_infra.base_selection import FlextInfraProjectSelectionServiceBase
    from flext_infra.cli import FlextInfraCli
    from flext_infra.config import FlextInfraFlextInfraConfig
    from flext_infra.conform import FlextInfraFlextInfraConform
    from flext_infra.constants import FlextInfraConstants, c
    from flext_infra.cprofile import FlextInfraFlextInfraCprofile
    from flext_infra.git import FlextInfraGitService
    from flext_infra.git_lanes import FlextInfraGitLanes
    from flext_infra.models import FlextInfraModels, m
    from flext_infra.preview import FlextInfraFlextInfraPreview
    from flext_infra.promoted import FlextInfraPromoted
    from flext_infra.protocols import FlextInfraProtocols, FlextInfraProtocolsBase, p
    from flext_infra.pytest import FlextInfraFlextInfraPytest
    from flext_infra.pytest_profile import FlextInfraPytestProfile
    from flext_infra.typings import FlextInfraTypes, t
    from flext_infra.utilities import FlextInfraUtilities, u
    from flext_infra.worktree import FlextInfraWorktreeService


__all__: tuple[str, ...] = (
    "FlextInfra",
    "FlextInfraCli",
    "FlextInfraConfig",
    "FlextInfraConstants",
    "FlextInfraFlextInfraConfig",
    "FlextInfraFlextInfraConform",
    "FlextInfraFlextInfraCprofile",
    "FlextInfraFlextInfraPreview",
    "FlextInfraFlextInfraPytest",
    "FlextInfraGitLanes",
    "FlextInfraGitService",
    "FlextInfraModels",
    "FlextInfraProjectSelectionServiceBase",
    "FlextInfraPromoted",
    "FlextInfraProtocols",
    "FlextInfraProtocolsBase",
    "FlextInfraPytestClock",
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
    "c",
    "config",
    "infra",
    "m",
    "p",
    "s",
    "settings",
    "t",
    "u",
)

install_lazy_exports(
    __name__,
    globals(),
    MappingProxyType({
        "FlextInfra": ".api",
        "FlextInfraCli": ".cli",
        "FlextInfraConfig": "._config",
        "FlextInfraConstants": ".constants",
        "FlextInfraFlextInfraConfig": ".config",
        "FlextInfraFlextInfraConform": ".conform",
        "FlextInfraFlextInfraCprofile": ".cprofile",
        "FlextInfraFlextInfraPreview": ".preview",
        "FlextInfraFlextInfraPytest": ".pytest",
        "FlextInfraGitLanes": ".git_lanes",
        "FlextInfraGitService": ".git",
        "FlextInfraModels": ".models",
        "FlextInfraProjectSelectionServiceBase": ".base_selection",
        "FlextInfraPromoted": ".promoted",
        "FlextInfraProtocols": ".protocols",
        "FlextInfraProtocolsBase": ".protocols",
        "FlextInfraPytestClock": "._pytest_clock",
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
        "__version__": ".__version__",
        "__version_info__": ".__version__",
        "build_lazy_import_map": "flext_cli",
        "cleanup_submodule_namespace": "flext_cli",
        "cli": "flext_cli",
        "core": "flext_cli",
        "d": "flext_cli",
        "e": "flext_cli",
        "h": "flext_cli",
        "install_lazy_exports": "flext_cli",
        "lazy": "flext_cli",
        "lazy_getattr": "flext_cli",
        "lazy_member": "flext_cli",
        "main": "flext_cli",
        "merge_lazy_imports": "flext_cli",
        "normalize_lazy_imports": "flext_cli",
        "r": "flext_cli",
        "resolve_lazy_members": "flext_cli",
        "x": "flext_cli",
        "c": ".constants",
        "config": "._config",
        "infra": ".api",
        "m": ".models",
        "p": ".protocols",
        "s": ".base",
        "settings": "._settings",
        "t": ".typings",
        "u": ".utilities",
        "FlextInfraBasePayload": "._base_payload",
        "FlextInfraBaseProjects": "._base_projects",
        "FlextInfraConformWiring": "._conform_wiring",
        "FlextInfraPreviewWiring": "._preview_wiring",
        "FlextInfraPytestCollection": "._pytest_collection",
        "FlextInfraPytestEntry": "._pytest_entry",
        "FlextInfraPytestProfileChild": "._pytest_profile_child",
    }),
    public_exports=__all__,
)
