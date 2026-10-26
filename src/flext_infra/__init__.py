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
    from flext_cli import (
        build_lazy_import_map,
        cleanup_submodule_namespace,
        cli,
        core,
        d,
        e,
        h,
        install_lazy_exports,
        lazy,
        lazy_getattr,
        lazy_member,
        main,
        merge_lazy_imports,
        normalize_lazy_imports,
        r,
        resolve_lazy_members,
        x,
    )

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
    from flext_infra._base_payload import FlextInfraCommandPayloadMixin
    from flext_infra._base_projects import FlextInfraProjectSelectionMixin
    from flext_infra._config import FlextInfraConfig, config
    from flext_infra._conform_wiring import FlextInfraConformWiring
    from flext_infra._preview_wiring import FlextInfraPreviewWiring
    from flext_infra._pytest_clock import FlextInfraPytestClock
    from flext_infra._pytest_collection import FlextInfraPytestCollection
    from flext_infra._pytest_entry import FlextInfraPytestEntry
    from flext_infra._pytest_profile_child import FlextInfraPytestProfileChild
    from flext_infra._settings import FlextInfraSettings, settings
    from flext_infra.api import FlextInfra, infra
    from flext_infra.base import FlextInfraServiceBase, s
    from flext_infra.base_selection import FlextInfraProjectSelectionServiceBase
    from flext_infra.cli import FlextInfraCli
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
    "FlextInfraPytestEntry",
    "FlextInfraPytestProfile",
    "FlextInfraPytestProfileChild",
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
    "build_lazy_import_map",
    "c",
    "cleanup_submodule_namespace",
    "cli",
    "config",
    "core",
    "d",
    "e",
    "h",
    "infra",
    "install_lazy_exports",
    "lazy",
    "lazy_getattr",
    "lazy_member",
    "m",
    "main",
    "merge_lazy_imports",
    "normalize_lazy_imports",
    "p",
    "r",
    "resolve_lazy_members",
    "s",
    "settings",
    "t",
    "u",
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
        "FlextInfraPytestEntry": "._pytest_entry",
        "FlextInfraPytestProfile": ".pytest_profile",
        "FlextInfraPytestProfileChild": "._pytest_profile_child",
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
        "build_lazy_import_map": "flext_cli",
        "c": ".constants",
        "cleanup_submodule_namespace": "flext_cli",
        "cli": "flext_cli",
        "config": "._config",
        "core": "flext_cli",
        "d": "flext_cli",
        "e": "flext_cli",
        "h": "flext_cli",
        "infra": ".api",
        "install_lazy_exports": "flext_cli",
        "lazy": "flext_cli",
        "lazy_getattr": "flext_cli",
        "lazy_member": "flext_cli",
        "m": ".models",
        "main": "flext_cli",
        "merge_lazy_imports": "flext_cli",
        "normalize_lazy_imports": "flext_cli",
        "p": ".protocols",
        "r": "flext_cli",
        "resolve_lazy_members": "flext_cli",
        "s": ".base",
        "settings": "._settings",
        "t": ".typings",
        "u": ".utilities",
        "x": "flext_cli",
    }),
    public_exports=__all__,
)

if not TYPE_CHECKING:
    from flext_infra.__version__ import __version__
