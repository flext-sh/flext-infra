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
    from flext_infra._base.payload import FlextInfraBasePayload
    from flext_infra._base.projects import FlextInfraBaseProjects
    from flext_infra._config import FlextInfraConfig, config
    from flext_infra._conform.wiring import FlextInfraConformWiring
    from flext_infra._pytest.clock import FlextInfraPytestClock
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
    "FlextInfraBasePayload",
    "FlextInfraBaseProjects",
    "FlextInfraCli",
    "FlextInfraConfig",
    "FlextInfraConformWiring",
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
        "__author__": ".__version__",
        "__author_email__": ".__version__",
        "__description__": ".__version__",
        "__license__": ".__version__",
        "__title__": ".__version__",
        "__url__": ".__version__",
        "__version__": ".__version__",
        "__version_info__": ".__version__",
        "build_lazy_import_map": "flext_cli",
        "c": ".constants",
        "check": ".check",
        "cleanup_submodule_namespace": "flext_cli",
        "cli": "flext_cli",
        "codegen": ".codegen",
        "codemod": ".codemod",
        "config": "._config",
        "core": "flext_cli",
        "d": "flext_cli",
        "deps": ".deps",
        "e": "flext_cli",
        "FlextInfra": ".api",
        "FlextInfraBasePayload": "._base.payload",
        "FlextInfraBaseProjects": "._base.projects",
        "FlextInfraCli": ".cli",
        "FlextInfraConfig": "._config",
        "FlextInfraConformWiring": "._conform.wiring",
        "FlextInfraConstants": ".constants",
        "FlextInfraFlextInfraConfig": ".config",
        "FlextInfraFlextInfraConform": ".conform",
        "FlextInfraFlextInfraCprofile": ".cprofile",
        "FlextInfraFlextInfraPreview": ".preview",
        "FlextInfraFlextInfraPytest": ".pytest",
        "FlextInfraGitLanes": ".git_lanes",
        "FlextInfraGitService": ".git",
        "FlextInfraModels": ".models",
        "FlextInfraPreviewWiring": "._preview.wiring",
        "FlextInfraProjectSelectionServiceBase": ".base_selection",
        "FlextInfraPromoted": ".promoted",
        "FlextInfraProtocols": ".protocols",
        "FlextInfraProtocolsBase": ".protocols",
        "FlextInfraPytestClock": "._pytest.clock",
        "FlextInfraPytestCollection": "._pytest.collection",
        "FlextInfraPytestEntry": "._pytest.entry",
        "FlextInfraPytestProfile": ".pytest_profile",
        "FlextInfraPytestProfileChild": "._pytest.profile_child",
        "FlextInfraServiceBase": ".base",
        "FlextInfraSettings": "._settings",
        "FlextInfraTypes": ".typings",
        "FlextInfraUtilities": ".utilities",
        "FlextInfraVersion": ".__version__",
        "FlextInfraWorktreeService": ".worktree",
        "h": "flext_cli",
        "infra": ".api",
        "install_lazy_exports": "flext_cli",
        "lazy_getattr": "flext_cli",
        "lazy_member": "flext_cli",
        "lazy": "flext_cli",
        "m": ".models",
        "main": "flext_cli",
        "merge_lazy_imports": "flext_cli",
        "normalize_lazy_imports": "flext_cli",
        "p": ".protocols",
        "r": "flext_cli",
        "release": ".release",
        "resolve_lazy_members": "flext_cli",
        "s": ".base",
        "services": ".services",
        "settings": "._settings",
        "t": ".typings",
        "u": ".utilities",
        "validate": ".validate",
        "workspace": ".workspace",
        "x": "flext_cli",
    }),
    public_exports=__all__,
)
