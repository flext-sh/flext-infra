# AUTO-GENERATED FILE — Regenerate with: make gen
"""Tests package.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_core.lazy import install_lazy_exports

if TYPE_CHECKING:
    from flext_tests import td, tf, tk, tm

    from flext_infra import (
        FlextInfra,
        FlextInfraCli,
        FlextInfraConfig,
        FlextInfraConstants,
        FlextInfraFlextInfraConfig,
        FlextInfraFlextInfraConform,
        FlextInfraFlextInfraCprofile,
        FlextInfraFlextInfraPreview,
        FlextInfraFlextInfraPytest,
        FlextInfraGitLanes,
        FlextInfraGitService,
        FlextInfraModels,
        FlextInfraProjectSelectionServiceBase,
        FlextInfraPromoted,
        FlextInfraProtocols,
        FlextInfraPytestProfile,
        FlextInfraServiceBase,
        FlextInfraSettings,
        FlextInfraTypes,
        FlextInfraUtilities,
        FlextInfraVersion,
        FlextInfraWorktreeService,
        __author__,
        __author_email__,
        __description__,
        __license__,
        __title__,
        __url__,
        __version__,
        __version_info__,
        config,
        d,
        e,
        h,
        infra,
        r,
        settings,
        x,
    )
    from tests._constants import TestsFlextInfraConstantsSemanticCutover
    from tests._models import (
        TestsFlextInfraModelsBase,
        TestsFlextInfraModelsSemanticCutover,
    )
    from tests._protocols import (
        TestsFlextInfraProtocolsBase,
        TestsFlextInfraProtocolsSemanticCutover,
    )
    from tests._utilities import TestsFlextInfraUtilitiesSemanticCutover
    from tests.base import TestsFlextInfraServiceBase, s
    from tests.constants import TestsFlextInfraConstants, c
    from tests.constants_scan import TestsFlextInfraConstantsScan
    from tests.fixtures import (
        TestsFlextInfraGateAdmissionHolder,
        TestsImportedModelCollision,
        TestsImportedModelReference,
    )
    from tests.models import TestsFlextInfraModels, m
    from tests.protocols import TestsFlextInfraProtocols, p
    from tests.refactor import TestsFlextInfraRefactorRopeStubs
    from tests.typings import TestsFlextInfraTypes, t
    from tests.unit import TestsFlextInfraModelsPytestMarkdown
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
    "FlextInfraPytestProfile",
    "FlextInfraServiceBase",
    "FlextInfraSettings",
    "FlextInfraTypes",
    "FlextInfraUtilities",
    "FlextInfraVersion",
    "FlextInfraWorktreeService",
    "TestsFlextInfraConstants",
    "TestsFlextInfraConstantsScan",
    "TestsFlextInfraConstantsSemanticCutover",
    "TestsFlextInfraGateAdmissionHolder",
    "TestsFlextInfraModels",
    "TestsFlextInfraModelsBase",
    "TestsFlextInfraModelsPytestMarkdown",
    "TestsFlextInfraModelsSemanticCutover",
    "TestsFlextInfraProtocols",
    "TestsFlextInfraProtocolsBase",
    "TestsFlextInfraProtocolsSemanticCutover",
    "TestsFlextInfraRefactorRopeStubs",
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
    "TestsFlextInfraUtilitiesSemanticCutover",
    "TestsFlextInfraUtilitiesToml",
    "TestsFlextInfraUtilitiesToolingFixture",
    "TestsFlextInfraUtilitiesWorkspaceEnv",
    "TestsFlextInfraUtilitiesWorkspaceFixture",
    "TestsImportedModelCollision",
    "TestsImportedModelReference",
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
    {
        "FlextInfra": "flext_infra",
        "FlextInfraCli": "flext_infra",
        "FlextInfraConfig": "flext_infra",
        "FlextInfraConstants": "flext_infra",
        "FlextInfraFlextInfraConfig": "flext_infra",
        "FlextInfraFlextInfraConform": "flext_infra",
        "FlextInfraFlextInfraCprofile": "flext_infra",
        "FlextInfraFlextInfraPreview": "flext_infra",
        "FlextInfraFlextInfraPytest": "flext_infra",
        "FlextInfraGitLanes": "flext_infra",
        "FlextInfraGitService": "flext_infra",
        "FlextInfraModels": "flext_infra",
        "FlextInfraProjectSelectionServiceBase": "flext_infra",
        "FlextInfraPromoted": "flext_infra",
        "FlextInfraProtocols": "flext_infra",
        "FlextInfraPytestProfile": "flext_infra",
        "FlextInfraServiceBase": "flext_infra",
        "FlextInfraSettings": "flext_infra",
        "FlextInfraTypes": "flext_infra",
        "FlextInfraUtilities": "flext_infra",
        "FlextInfraVersion": "flext_infra",
        "FlextInfraWorktreeService": "flext_infra",
        "TestsFlextInfraConstants": ".constants",
        "TestsFlextInfraConstantsScan": ".constants_scan",
        "TestsFlextInfraConstantsSemanticCutover": "._constants",
        "TestsFlextInfraGateAdmissionHolder": ".fixtures",
        "TestsFlextInfraModels": ".models",
        "TestsFlextInfraModelsBase": "._models",
        "TestsFlextInfraModelsPytestMarkdown": ".unit",
        "TestsFlextInfraModelsSemanticCutover": "._models",
        "TestsFlextInfraProtocols": ".protocols",
        "TestsFlextInfraProtocolsBase": "._protocols",
        "TestsFlextInfraProtocolsSemanticCutover": "._protocols",
        "TestsFlextInfraRefactorRopeStubs": ".refactor",
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
        "TestsFlextInfraUtilitiesSemanticCutover": "._utilities",
        "TestsFlextInfraUtilitiesToml": ".utilities_toml",
        "TestsFlextInfraUtilitiesToolingFixture": ".utilities_fixture_tooling",
        "TestsFlextInfraUtilitiesWorkspaceEnv": ".utilities_workspace_env",
        "TestsFlextInfraUtilitiesWorkspaceFixture": ".utilities_fixture_workspace",
        "TestsImportedModelCollision": ".fixtures",
        "TestsImportedModelReference": ".fixtures",
        "__author__": "flext_infra",
        "__author_email__": "flext_infra",
        "__description__": "flext_infra",
        "__license__": "flext_infra",
        "__title__": "flext_infra",
        "__url__": "flext_infra",
        "__version__": "flext_infra",
        "__version_info__": "flext_infra",
        "c": ".constants",
        "config": "flext_infra",
        "d": "flext_infra",
        "e": "flext_infra",
        "h": "flext_infra",
        "infra": "flext_infra",
        "m": ".models",
        "p": ".protocols",
        "r": "flext_infra",
        "s": ".base",
        "settings": "flext_infra",
        "t": ".typings",
        "td": "flext_tests",
        "tf": "flext_tests",
        "tk": "flext_tests",
        "tm": "flext_tests",
        "u": ".utilities",
        "x": "flext_infra",
    },
    public_exports=__all__,
)
