"""Constants for FLEXT infra tests.

Provides TestsFlextInfraConstants, extending FlextTestsConstants with
infra-specific constants for infrastructure testing, project names, and test
markers.

Copyright (FlextTestsConstants) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import re
from types import MappingProxyType
from typing import ClassVar, Final

from flext_tests import FlextTestsConstants

from flext_infra import c, t


class TestsFlextInfraConstants(
    FlextTestsConstants,
    c,
):
    """Constants for FLEXT infra tests - extends FlextTestsConstants.

    Architecture layer: Layer 0 foundation constants with infra test extensions.
    Architecture: Extends FlextTestsConstants with infra-specific constants.
    All base constants from FlextTestsConstants are available through inheritance.
    """

    class Tests(FlextTestsConstants.Tests):
        """Flat constants optimized for data-driven infra tests."""

        RELEASE_PHASE_VALIDATE: Final[str] = c.Infra.VERB_VALIDATE
        RELEASE_PHASE_VERSION: Final[str] = c.Infra.VERSION
        RELEASE_PHASE_BUILD: Final[str] = c.Infra.DIR_BUILD
        RELEASE_PHASE_PUBLISH: Final[str] = c.Infra.VERB_PUBLISH

        ALL_PHASES: Final[tuple[str, ...]] = (
            RELEASE_PHASE_VALIDATE,
            RELEASE_PHASE_VERSION,
            RELEASE_PHASE_BUILD,
            RELEASE_PHASE_PUBLISH,
        )

        LOG_NOISE_LINES: Final[tuple[str, ...]] = (
            "make[1]: Nothing to be done",
            "INFO: running tests",
            "warning: ignoring duplicate",
            "Success: 5 passed",
            "make[2]: Entering directory",
        )
        LOG_ERROR_LINES: Final[tuple[str, ...]] = (
            "ERROR: something went wrong",
            "FAIL: test_foo failed",
            "error: compilation failed",
            "E  AssertionError: mismatch",
            "FAILED tests/test_foo.py::test_bar",
        )
        LOG_PATTERN_CASES: ClassVar[tuple[tuple[str, int], ...]] = (
            ("error: compilation failed", 1),
            ("E  AssertionError: mismatch", 1),
            ("FAILED tests/test_foo.py::test_bar", 1),
            ("make[2]: Entering directory", 0),
            ("warning: ignoring duplicate", 0),
            ("Success: 5 passed", 0),
        )
        LOG_ERROR_PREFIX_RE: ClassVar[re.Pattern[str]] = re.compile(
            r"^(ERROR|FAIL|error|E\s+AssertionError|FAILED)",
        )
        LOG_MIXED_SCENARIO_LINES: Final[tuple[str, ...]] = (
            "make[1]: running",
            "ERROR: build failed",
            "INFO: post-build",
            "FAIL: test broken",
            "Total: 2 failed",
        )

        WORKSPACE_PROJECT_NAME: Final[str] = "workspace"
        DEMO_PROJECT_NAME: Final[str] = "demo-project"
        PROJECT_A_NAME: Final[str] = "proj-a"
        PROJECT_B_NAME: Final[str] = "proj-b"
        PROJECT_NO_SRC_NAME: Final[str] = "no-src"
        PROJECT_MEMBERS_BY_SCENARIO: ClassVar[t.MappingKV[str, tuple[str, ...]]] = (
            MappingProxyType({
                "single": (DEMO_PROJECT_NAME,),
                "filtered": (PROJECT_A_NAME, PROJECT_B_NAME),
                "missing_src": (PROJECT_NO_SRC_NAME,),
            })
        )

        CODEGEN_NAMESPACE_FILES: Final[frozenset[str]] = frozenset({
            "__init__.py",
            "__version__.py",
            "py.typed",
        })
        CODEGEN_SKIPPED_DIRS: Final[frozenset[str]] = frozenset({
            ".hidden",
            "vendor",
            "node_modules",
            ".venv",
        })

        RELEASE_VERSION_BASE: Final[str] = "0.1.0"
        RELEASE_VERSION_SELECTED: Final[str] = "1.2.0"
        RELEASE_VERSION_TARGET: Final[str] = "1.0.0"
        RELEASE_VERSION_NEXT_DEV: Final[str] = "1.1.0-dev"
        RELEASE_BUMP_MINOR: Final[str] = "minor"
        RELEASE_PROJECTS: Final[tuple[str, str]] = (
            "flext-a",
            "flext-b",
        )
        RELEASE_TAG_TARGET: Final[str] = "v1.0.0"
        RELEASE_NOTES_FILENAME: Final[str] = "RELEASE_NOTES.md"
        RELEASE_NOTES_HEADING: Final[str] = "# Release v1.0.0"
        RELEASE_NOTES_CHANGE_LINE: Final[str] = "- abc123 fix release flow"
        RELEASE_INITIAL_CHANGE_LINE: Final[str] = "- Initial tagged release"
        RELEASE_CHANGELOG_HEADER: Final[str] = "# Changelog\n\n"
        RELEASE_VERIFICATION_LINES: Final[tuple[str, ...]] = (
            "- make rel INTERACTIVE=0 CREATE_BRANCHES=0 RELEASE_PHASE=all",
            "- make val VALIDATE_SCOPE=workspace",
            "- make build",
        )


c = TestsFlextInfraConstants
__all__: list[str] = ["TestsFlextInfraConstants", "c"]
