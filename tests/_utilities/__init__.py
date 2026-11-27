# AUTO-GENERATED FILE — Regenerate with: make check
"""Tests. Utilities package.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_core.lazy import install_lazy_exports

if TYPE_CHECKING:
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
    from tests._utilities.semantic_cutover import (
        TestsFlextInfraUtilitiesSemanticCutover,
    )
    from tests._utilities.toml_documents import TestsFlextInfraUtilitiesToml
    from tests._utilities.workspace_env import TestsFlextInfraUtilitiesWorkspaceEnv


__all__: tuple[str, ...] = (
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
)

install_lazy_exports(
    __name__,
    globals(),
    {
        "TestsFlextInfraUtilitiesCodegen": ".codegen",
        "TestsFlextInfraUtilitiesConform": ".conform",
        "TestsFlextInfraUtilitiesDeps": ".deps",
        "TestsFlextInfraUtilitiesDocsFixture": ".fixture_docs",
        "TestsFlextInfraUtilitiesGates": ".gates",
        "TestsFlextInfraUtilitiesGit": ".git",
        "TestsFlextInfraUtilitiesHermeticGit": ".hermetic_git",
        "TestsFlextInfraUtilitiesProjectFixture": ".fixture_project",
        "TestsFlextInfraUtilitiesPromoted": ".promoted",
        "TestsFlextInfraUtilitiesRelease": ".release",
        "TestsFlextInfraUtilitiesSemanticCutover": ".semantic_cutover",
        "TestsFlextInfraUtilitiesToml": ".toml_documents",
        "TestsFlextInfraUtilitiesToolingFixture": ".fixture_tooling",
        "TestsFlextInfraUtilitiesWorkspaceEnv": ".workspace_env",
        "TestsFlextInfraUtilitiesWorkspaceFixture": ".fixture_workspace",
    },
    public_exports=__all__,
    deferred_members=(
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
    ),
)
