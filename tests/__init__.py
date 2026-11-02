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
    from flext_tests import api, d, e, h, r, td, tf, tk, tm, x

    from flext_infra import config, infra, settings
    from tests.base import TestsFlextInfraServiceBase, s
    from tests.constants import TestsFlextInfraConstants, c
    from tests.constants_scan import TestsFlextInfraConstantsScan
    from tests.models import TestsFlextInfraModels, m
    from tests.protocols import TestsFlextInfraProtocols, p
    from tests.typings import TestsFlextInfraTypes, t
    from tests.utilities import TestsFlextInfraUtilities, u
    from tests.utilities_codegen import TestsFlextInfraUtilitiesCodegen
    from tests.utilities_conform import TestsFlextInfraUtilitiesConform
    from tests.utilities_deps import TestsFlextInfraUtilitiesDeps
    from tests.utilities_fixture_docs import TestsFlextInfraUtilitiesDocsFixture
    from tests.utilities_fixture_project import TestsFlextInfraUtilitiesProjectFixture
    from tests.utilities_fixture_tooling import TestsFlextInfraUtilitiesToolingFixture
    from tests.utilities_fixture_workspace import (
        TestsFlextInfraUtilitiesWorkspaceFixture,
    )
    from tests.utilities_gates import TestsFlextInfraUtilitiesGates
    from tests.utilities_git import TestsFlextInfraUtilitiesGit
    from tests.utilities_hermetic_git import TestsFlextInfraUtilitiesHermeticGit
    from tests.utilities_promoted import TestsFlextInfraUtilitiesPromoted
    from tests.utilities_release import TestsFlextInfraUtilitiesRelease
    from tests.utilities_toml import TestsFlextInfraUtilitiesToml
    from tests.utilities_workspace_env import TestsFlextInfraUtilitiesWorkspaceEnv


__all__: tuple[str, ...] = (
    "TestsFlextInfraConstants",
    "TestsFlextInfraConstantsScan",
    "TestsFlextInfraModels",
    "TestsFlextInfraProtocols",
    "TestsFlextInfraServiceBase",
    "TestsFlextInfraTypes",
    "TestsFlextInfraUtilities",
    "TestsFlextInfraUtilitiesCodegen",
    "TestsFlextInfraUtilitiesConform",
    "TestsFlextInfraUtilitiesDeps",
    "TestsFlextInfraUtilitiesDocsFixture",
    "TestsFlextInfraUtilitiesGates",
    "TestsFlextInfraUtilitiesGit",
    "TestsFlextInfraUtilitiesHermeticGit",
    "TestsFlextInfraUtilitiesProjectFixture",
    "TestsFlextInfraUtilitiesPromoted",
    "TestsFlextInfraUtilitiesRelease",
    "TestsFlextInfraUtilitiesToml",
    "TestsFlextInfraUtilitiesToolingFixture",
    "TestsFlextInfraUtilitiesWorkspaceEnv",
    "TestsFlextInfraUtilitiesWorkspaceFixture",
    "api",
    "c",
    "config",
    "d",
    "e",
    "h",
    "infra",
    "m",
    "p",
    "r",
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
        "TestsFlextInfraConstantsScan": ".constants_scan",
        "TestsFlextInfraModels": ".models",
        "TestsFlextInfraProtocols": ".protocols",
        "TestsFlextInfraServiceBase": ".base",
        "TestsFlextInfraTypes": ".typings",
        "TestsFlextInfraUtilities": ".utilities",
        "TestsFlextInfraUtilitiesCodegen": ".utilities_codegen",
        "TestsFlextInfraUtilitiesConform": ".utilities_conform",
        "TestsFlextInfraUtilitiesDeps": ".utilities_deps",
        "TestsFlextInfraUtilitiesDocsFixture": ".utilities_fixture_docs",
        "TestsFlextInfraUtilitiesGates": ".utilities_gates",
        "TestsFlextInfraUtilitiesGit": ".utilities_git",
        "TestsFlextInfraUtilitiesHermeticGit": ".utilities_hermetic_git",
        "TestsFlextInfraUtilitiesProjectFixture": ".utilities_fixture_project",
        "TestsFlextInfraUtilitiesPromoted": ".utilities_promoted",
        "TestsFlextInfraUtilitiesRelease": ".utilities_release",
        "TestsFlextInfraUtilitiesToml": ".utilities_toml",
        "TestsFlextInfraUtilitiesToolingFixture": ".utilities_fixture_tooling",
        "TestsFlextInfraUtilitiesWorkspaceEnv": ".utilities_workspace_env",
        "TestsFlextInfraUtilitiesWorkspaceFixture": ".utilities_fixture_workspace",
        "api": "flext_tests",
        "c": ".constants",
        "config": "flext_infra",
        "d": "flext_tests",
        "e": "flext_tests",
        "h": "flext_tests",
        "infra": "flext_infra",
        "m": ".models",
        "p": ".protocols",
        "r": "flext_tests",
        "s": ".base",
        "settings": "flext_infra",
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
