# AUTO-GENERATED FILE — Regenerate with: make gen
"""Tests package.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from types import MappingProxyType
from typing import TYPE_CHECKING

from flext_core.lazy import install_lazy_exports

if TYPE_CHECKING:
    from flext_tests import (
        api,
        build_lazy_import_map,
        cleanup_submodule_namespace,
        cli,
        config,
        core,
        d,
        e,
        h,
        install_lazy_exports,
        install_local_packages,
        lazy,
        lazy_getattr,
        lazy_member,
        main,
        merge_lazy_imports,
        normalize_lazy_imports,
        r,
        resolve_lazy_members,
        settings,
        td,
        tf,
        tk,
        tm,
        x,
    )

    from flext_infra import infra
    from tests.base import TestsFlextInfraServiceBase, s
    from tests.constants import TestsFlextInfraConstants, c
    from tests.constants_scan import TestsFlextInfraConstantsScanMixin
    from tests.models import TestsFlextInfraModels, m
    from tests.protocols import TestsFlextInfraProtocols, p
    from tests.typings import TestsFlextInfraTypes, t
    from tests.utilities import TestsFlextInfraUtilities, u
    from tests.utilities_codegen import TestsFlextInfraUtilitiesCodegenMixin
    from tests.utilities_conform import TestsFlextInfraUtilitiesConform
    from tests.utilities_deps import TestsFlextInfraUtilitiesDepsMixin
    from tests.utilities_fixture_docs import TestsFlextInfraUtilitiesDocsFixtureMixin
    from tests.utilities_fixture_project import (
        TestsFlextInfraUtilitiesProjectFixtureMixin,
    )
    from tests.utilities_fixture_tooling import (
        TestsFlextInfraUtilitiesToolingFixtureMixin,
    )
    from tests.utilities_fixture_workspace import (
        TestsFlextInfraUtilitiesWorkspaceFixtureMixin,
    )
    from tests.utilities_gates import TestsFlextInfraUtilitiesGatesMixin
    from tests.utilities_git import TestsFlextInfraUtilitiesGitMixin
    from tests.utilities_hermetic_git import TestsFlextInfraUtilitiesHermeticGitMixin
    from tests.utilities_promoted import TestsFlextInfraUtilitiesPromotedMixin
    from tests.utilities_release import TestsFlextInfraUtilitiesReleaseMixin
    from tests.utilities_toml import TestsFlextInfraUtilitiesTomlMixin
    from tests.utilities_workspace_env import TestsFlextInfraUtilitiesWorkspaceEnvMixin


__all__: tuple[str, ...] = (
    "TestsFlextInfraConstants",
    "TestsFlextInfraConstantsScanMixin",
    "TestsFlextInfraModels",
    "TestsFlextInfraProtocols",
    "TestsFlextInfraServiceBase",
    "TestsFlextInfraTypes",
    "TestsFlextInfraUtilities",
    "TestsFlextInfraUtilitiesCodegenMixin",
    "TestsFlextInfraUtilitiesConform",
    "TestsFlextInfraUtilitiesDepsMixin",
    "TestsFlextInfraUtilitiesDocsFixtureMixin",
    "TestsFlextInfraUtilitiesGatesMixin",
    "TestsFlextInfraUtilitiesGitMixin",
    "TestsFlextInfraUtilitiesHermeticGitMixin",
    "TestsFlextInfraUtilitiesProjectFixtureMixin",
    "TestsFlextInfraUtilitiesPromotedMixin",
    "TestsFlextInfraUtilitiesReleaseMixin",
    "TestsFlextInfraUtilitiesTomlMixin",
    "TestsFlextInfraUtilitiesToolingFixtureMixin",
    "TestsFlextInfraUtilitiesWorkspaceEnvMixin",
    "TestsFlextInfraUtilitiesWorkspaceFixtureMixin",
    "api",
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
    "install_local_packages",
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
    "td",
    "tf",
    "tk",
    "tm",
    "u",
    "x",
)

install_lazy_exports(
    __name__,
    globals(),
    MappingProxyType({
        "TestsFlextInfraConstants": ".constants",
        "TestsFlextInfraConstantsScanMixin": ".constants_scan",
        "TestsFlextInfraModels": ".models",
        "TestsFlextInfraProtocols": ".protocols",
        "TestsFlextInfraServiceBase": ".base",
        "TestsFlextInfraTypes": ".typings",
        "TestsFlextInfraUtilities": ".utilities",
        "TestsFlextInfraUtilitiesCodegenMixin": ".utilities_codegen",
        "TestsFlextInfraUtilitiesConform": ".utilities_conform",
        "TestsFlextInfraUtilitiesDepsMixin": ".utilities_deps",
        "TestsFlextInfraUtilitiesDocsFixtureMixin": ".utilities_fixture_docs",
        "TestsFlextInfraUtilitiesGatesMixin": ".utilities_gates",
        "TestsFlextInfraUtilitiesGitMixin": ".utilities_git",
        "TestsFlextInfraUtilitiesHermeticGitMixin": ".utilities_hermetic_git",
        "TestsFlextInfraUtilitiesProjectFixtureMixin": ".utilities_fixture_project",
        "TestsFlextInfraUtilitiesPromotedMixin": ".utilities_promoted",
        "TestsFlextInfraUtilitiesReleaseMixin": ".utilities_release",
        "TestsFlextInfraUtilitiesTomlMixin": ".utilities_toml",
        "TestsFlextInfraUtilitiesToolingFixtureMixin": ".utilities_fixture_tooling",
        "TestsFlextInfraUtilitiesWorkspaceEnvMixin": ".utilities_workspace_env",
        "TestsFlextInfraUtilitiesWorkspaceFixtureMixin": ".utilities_fixture_workspace",
        "api": "flext_tests",
        "build_lazy_import_map": "flext_tests",
        "c": ".constants",
        "cleanup_submodule_namespace": "flext_tests",
        "cli": "flext_tests",
        "config": "flext_tests",
        "core": "flext_tests",
        "d": "flext_tests",
        "e": "flext_tests",
        "h": "flext_tests",
        "infra": "flext_infra",
        "install_lazy_exports": "flext_tests",
        "install_local_packages": "flext_tests",
        "lazy": "flext_tests",
        "lazy_getattr": "flext_tests",
        "lazy_member": "flext_tests",
        "m": ".models",
        "main": "flext_tests",
        "merge_lazy_imports": "flext_tests",
        "normalize_lazy_imports": "flext_tests",
        "p": ".protocols",
        "r": "flext_tests",
        "resolve_lazy_members": "flext_tests",
        "s": ".base",
        "settings": "flext_tests",
        "t": ".typings",
        "td": "flext_tests",
        "tf": "flext_tests",
        "tk": "flext_tests",
        "tm": "flext_tests",
        "u": ".utilities",
        "x": "flext_tests",
    }),
    public_exports=__all__,
)
