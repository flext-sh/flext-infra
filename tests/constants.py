"""Constants for FLEXT infra tests.

Provides TestsFlextInfraConstants, extending FlextTestsConstants with
infra-specific constants for infrastructure testing, project names, and test
markers.

Copyright (FlextTestsConstants) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from types import MappingProxyType
from typing import TYPE_CHECKING, ClassVar

from flext_tests import FlextTestsConstants

from flext_infra import FlextInfraConstants
from tests.constants_scan import TestsFlextInfraConstantsScanMixin

if TYPE_CHECKING:
    from flext_infra import t


class TestsFlextInfraConstants(FlextTestsConstants, FlextInfraConstants):
    """Constants for FLEXT infra tests - extends FlextTestsConstants.

    Architecture layer: Layer 0 foundation constants with infra test extensions.
    Architecture: Extends FlextTestsConstants with infra-specific constants.
    All base constants from FlextTestsConstants are available through inheritance.
    """

    class Tests(TestsFlextInfraConstantsScanMixin, FlextTestsConstants.Tests):
        """Flat constants optimized for data-driven infra tests."""

        GIT_LOCAL_ENV_KEYS: ClassVar[t.StrSequence] = (
            "GIT_ALTERNATE_OBJECT_DIRECTORIES",
            "GIT_CONFIG",
            "GIT_CONFIG_PARAMETERS",
            "GIT_CONFIG_COUNT",
            "GIT_OBJECT_DIRECTORY",
            "GIT_DIR",
            "GIT_WORK_TREE",
            "GIT_IMPLICIT_WORK_TREE",
            "GIT_GRAFT_FILE",
            "GIT_INDEX_FILE",
            "GIT_NO_REPLACE_OBJECTS",
            "GIT_REPLACE_REF_BASE",
            "GIT_PREFIX",
            "GIT_SHALLOW_FILE",
            "GIT_COMMON_DIR",
        )
        """Repository-local variables Git exports to hooks and aliases."""

        MAKE_ISOLATION_ENV_KEYS: ClassVar[t.StrSequence] = (
            "BASH_ENV",
            "CHANGED_ONLY",
            "CHECK_GATES",
            "CHECK_ONLY",
            "FILE",
            "FILES",
            "FIX",
            "FLEXT_INFRA_PYTHON",
            "FLEXT_ROOT",
            "FLEXT_STANDALONE",
            "FLEXT_REPOSITORY_ROOT",
            "MATCH",
            "PROJECT",
            "PROJECTS",
            "PYRIGHT_ARGS",
            "PYTEST_ARGS",
            "RUFF_ARGS",
            "UV",
            "VALIDATE_GATES",
            "WHAT",
            "REPOSITORY_ROOT",
            *FlextInfraConstants.Infra.ORCHESTRATOR_REMOVE_ENV_KEYS,
        )
        """Environment inherited from an outer Make invocation to discard in tests."""

        # ClassVar, not Final: these rebindings live on a Pydantic model
        # class, and Pydantic 2.11 deprecates final-annotated defaults
        # (filterwarnings=error turns that into a collection failure).
        RELEASE_PHASE_PLAN: ClassVar[str] = FlextInfraConstants.Infra.ReleasePhase.PLAN
        RELEASE_PHASE_VERSION: ClassVar[str] = (
            FlextInfraConstants.Infra.ReleasePhase.VERSION
        )
        RELEASE_PHASE_TAG: ClassVar[str] = FlextInfraConstants.Infra.ReleasePhase.TAG
        RELEASE_PHASE_BUILD: ClassVar[str] = (
            FlextInfraConstants.Infra.ReleasePhase.BUILD
        )
        RELEASE_PHASE_PUBLISH: ClassVar[str] = (
            FlextInfraConstants.Infra.ReleasePhase.PUBLISH
        )

        INFRA_PUBLIC_ROOT_EXPORTS: ClassVar[t.StrSequence] = (
            "FlextInfra",
            "c",
            "infra",
            "m",
            "main",
            "p",
            "s",
            "t",
            "u",
        )
        INFRA_PUBLIC_WRAPPER_MODULES: ClassVar[t.StrSequence] = (
            "flext_infra.__version__",
            "flext_infra.constants",
            "flext_infra.models",
            "flext_infra.protocols",
            "flext_infra.typings",
            "flext_infra.utilities",
        )
        INFRA_PUBLIC_ROOT_ALIAS_EXPECTATIONS: ClassVar[
            t.VariadicTuple[t.Pair[str, str]]
        ] = (
            ("c", "FlextInfraConstants"),
            ("m", "FlextInfraModels"),
            ("p", "FlextInfraProtocols"),
            ("s", "FlextInfraServiceBase"),
            ("t", "FlextInfraTypes"),
            ("u", "FlextInfraUtilities"),
        )
        INFRA_PUBLIC_WRAPPER_ALIAS_EXPECTATIONS: ClassVar[
            t.VariadicTuple[t.Triple[str, str, str]]
        ] = (
            ("flext_infra.constants", "c", "FlextInfraConstants"),
            ("flext_infra.models", "m", "FlextInfraModels"),
            ("flext_infra.protocols", "p", "FlextInfraProtocols"),
            ("flext_infra.typings", "t", "FlextInfraTypes"),
            ("flext_infra.utilities", "u", "FlextInfraUtilities"),
        )
        INFRA_PUBLIC_NAMESPACE_ALIAS_NAMES: ClassVar[t.StrSequence] = (
            "c",
            "m",
            "p",
            "t",
            "u",
        )
        INFRA_PUBLIC_UTILITY_NAMESPACE_METHODS: ClassVar[t.StrSequence] = (
            "plan_semantic_cutover",
            "current_workspace_version",
            "parse_semver",
        )

        WORKSPACE_PROJECT_NAME: ClassVar[str] = "workspace"
        DEMO_PROJECT_NAME: ClassVar[str] = "demo-project"
        PROJECT_A_NAME: ClassVar[str] = "proj-a"
        PROJECT_B_NAME: ClassVar[str] = "proj-b"
        PROJECT_NO_SRC_NAME: ClassVar[str] = "no-src"
        PROJECT_MEMBERS_BY_SCENARIO: ClassVar[t.MappingKV[str, t.StrSequence]] = (
            MappingProxyType({
                "single": (DEMO_PROJECT_NAME,),
                "filtered": (PROJECT_A_NAME, PROJECT_B_NAME),
                "missing_src": (PROJECT_NO_SRC_NAME,),
            })
        )

        CODEGEN_NAMESPACE_FILES: ClassVar[frozenset[str]] = frozenset({
            "__init__.py",
            "__version__.py",
            "py.typed",
        })
        CODEGEN_SKIPPED_DIRS: ClassVar[frozenset[str]] = frozenset({
            ".hidden",
            "vendor",
            "node_modules",
            ".venv",
        })

        REFACTOR_SCAN_FILE_COUNT: ClassVar[int] = 1000
        REFACTOR_SCAN_MAX_SECONDS: ClassVar[float] = 30.0
        REFACTOR_MEMORY_FILE_COUNT: ClassVar[int] = 500
        REFACTOR_MEMORY_MAX_MB: ClassVar[float] = 500.0
        REFACTOR_RULE_ITERATIONS: ClassVar[int] = 100
        REFACTOR_RULE_MAX_SECONDS: ClassVar[float] = 0.1

        # flext-perf.4: gen pipeline performance thresholds (lazy-init stage).
        GEN_PIPELINE_PROJECT_COUNT: ClassVar[int] = 20
        GEN_PIPELINE_MODULES_PER_PROJECT: ClassVar[int] = 5
        GEN_PIPELINE_MAX_SECONDS: ClassVar[float] = 30.0
        GEN_PIPELINE_MEMORY_MAX_MB: ClassVar[float] = 500.0

        RELEASE_VERSION_BASE: ClassVar[str] = "0.1.0"
        RELEASE_VERSION_PATCH: ClassVar[str] = "0.1.1"
        RELEASE_VERSION_PRERELEASE: ClassVar[str] = "0.1.0rc0"
        RELEASE_PROJECTS: ClassVar[t.Pair[str, str]] = ("flext-a", "flext-b")
        # Fixture members depend on these siblings, so a release build must see
        # them to pin their declared versions.
        RELEASE_INTERNAL_DEPENDENCIES: ClassVar[t.Pair[str, str]] = (
            "flext-core",
            "flext-tests",
        )
        RELEASE_TAG_TARGET: ClassVar[str] = "v1.0.0"
        RELEASE_VERSION_TARGET: ClassVar[str] = "1.0.0"
        RELEASE_NOTES_HEADING: ClassVar[str] = "# Release v1.0.0"
        RELEASE_NOTES_CHANGE_LINE: ClassVar[str] = "- fix: release flow"
        RELEASE_INITIAL_CHANGE_LINE: ClassVar[str] = "- Initial tagged release"
        RELEASE_CHANGELOG_HEADER: ClassVar[str] = "# Changelog\n\n"


c = TestsFlextInfraConstants
__all__: list[str] = ["TestsFlextInfraConstants", "c"]
