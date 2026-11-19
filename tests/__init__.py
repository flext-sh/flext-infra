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
    from tests._utilities.codegen import TestsFlextInfraUtilitiesCodegen
    from tests._utilities.conform import TestsFlextInfraUtilitiesConform
    from tests._utilities.deps import TestsFlextInfraUtilitiesDeps
    from tests._utilities.fixture_docs import TestsFlextInfraUtilitiesDocsFixture
    from tests._utilities.fixture_project import TestsFlextInfraUtilitiesProjectFixture
    from tests._utilities.fixture_tooling import TestsFlextInfraUtilitiesToolingFixture
    from tests._utilities.fixture_workspace import (
        TestsFlextInfraUtilitiesWorkspaceFixture,
    )
    from tests._utilities.gates import TestsFlextInfraUtilitiesGates
    from tests._utilities.git import TestsFlextInfraUtilitiesGit
    from tests._utilities.hermetic_git import TestsFlextInfraUtilitiesHermeticGit
    from tests._utilities.promoted import TestsFlextInfraUtilitiesPromoted
    from tests._utilities.release import TestsFlextInfraUtilitiesRelease
    from tests._utilities.toml_documents import TestsFlextInfraUtilitiesToml
    from tests._utilities.workspace_env import TestsFlextInfraUtilitiesWorkspaceEnv
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
        "TestsFlextInfraUtilitiesCodegen": "._utilities.codegen",
        "TestsFlextInfraUtilitiesConform": "._utilities.conform",
        "TestsFlextInfraUtilitiesDeps": "._utilities.deps",
        "TestsFlextInfraUtilitiesDocsFixture": "._utilities.fixture_docs",
        "TestsFlextInfraUtilitiesGates": "._utilities.gates",
        "TestsFlextInfraUtilitiesGit": "._utilities.git",
        "TestsFlextInfraUtilitiesHermeticGit": "._utilities.hermetic_git",
        "TestsFlextInfraUtilitiesProjectFixture": "._utilities.fixture_project",
        "TestsFlextInfraUtilitiesPromoted": "._utilities.promoted",
        "TestsFlextInfraUtilitiesRelease": "._utilities.release",
        "TestsFlextInfraUtilitiesSemanticCutover": "._utilities",
        "TestsFlextInfraUtilitiesToml": "._utilities.toml_documents",
        "TestsFlextInfraUtilitiesToolingFixture": "._utilities.fixture_tooling",
        "TestsFlextInfraUtilitiesWorkspaceEnv": "._utilities.workspace_env",
        "TestsFlextInfraUtilitiesWorkspaceFixture": "._utilities.fixture_workspace",
        "TestsImportedModelCollision": ".fixtures",
        "TestsImportedModelReference": ".fixtures",
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
    deferred_members=(
        "TestsFlextInfraConstantsScan",
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
    ),
)
