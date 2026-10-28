"""Selector-free Make and project-tool constants.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import (
    Iterable,
    Iterator,
    Mapping,
    MutableMapping,
    MutableSequence,
    Sequence,
)

import re
from collections.abc import Sequence
from enum import StrEnum
from typing import TYPE_CHECKING, ClassVar

from flext_infra._constants.config import FlextInfraConstantsConfig

if TYPE_CHECKING:
    from flext_infra import t


class FlextInfraConstantsMake(FlextInfraConstantsConfig):
    """One canonical vocabulary shared by generated Make and its services."""

    class PytestExecutionMode(StrEnum):
        """Keep test inventory scope distinct from dependency selection.

        GLOBAL_INCREMENTAL shares FULL's marker scope, but uses Testmon to
        select impacted cases. INCREMENTAL retains the local/slow partition.
        FULL executes the complete inventory once without Testmon.
        """

        INCREMENTAL = "incremental"
        GLOBAL_INCREMENTAL = "global-incremental"
        FULL = "full"
        COVERAGE = "coverage"

        @property
        def is_global(self) -> bool:
            """Whether the inventory retains FULL's external and CI marker scope."""
            return self in {self.GLOBAL_INCREMENTAL, self.FULL}

        @property
        def is_incremental(self) -> bool:
            """Whether testmon selects impacted cases before suite execution."""
            return self in {self.INCREMENTAL, self.GLOBAL_INCREMENTAL}

    MAKE_ASSIGNMENT_RE: ClassVar[t.RegexPattern] = re.compile(
        r"^[A-Za-z_][A-Za-z0-9_]*\s*(?::?:|\?|\+)?=",
    )
    MAKE_DIRECTIVE_RE: ClassVar[t.RegexPattern] = re.compile(
        r"^(?:export|unexport|override|include|-include|sinclude|vpath)\b",
    )
    MAKE_CONDITIONAL_RE: ClassVar[t.RegexPattern] = re.compile(
        r"^(?:else\b|endif\b|ifeq\b|ifneq\b|ifdef\b|ifndef\b)",
    )
    MAKE_REPOSITORY_ROOT: ClassVar[str] = "REPOSITORY_ROOT"
    "Make variable the workspace orchestrator passes to attached members."
    VERB_CLEAN: ClassVar[str] = "clean"
    VERB_VALIDATE: ClassVar[str] = "validate"
    VERB_PUBLISH: ClassVar[str] = "publish"
    VERB_RUN: ClassVar[str] = "run"
    VERB_CHECKS: ClassVar[str] = "checks"
    VERB_SONARCLOUD_SYNC: ClassVar[str] = "sonarcloud-sync"
    VERB_SONARCLOUD_ISSUES: ClassVar[str] = "sonarcloud-issues"
    VERB_CHECK: ClassVar[str] = "check"
    VERB_TEST: ClassVar[str] = "tests"
    VERB_TEST_FULL: ClassVar[str] = "tests-full"
    RUFF_UNSAFE_FIXES_FLAG: ClassVar[str] = "--unsafe-fixes"
    RUFF_CACHE_ENVIRONMENT_VARIABLE: ClassVar[str] = "RUFF_CACHE_DIR"
    """Ruff's immutable external cache-directory environment contract."""
    PYTEST_BASETEMP_ARGUMENT: ClassVar[str] = "--basetemp"
    """Native pytest option electing its owned temporary tree."""
    PYTEST_TEMP_ENVIRONMENT_VARIABLES: ClassVar[t.StrTuple] = ("TMPDIR", "TMP", "TEMP")
    """Native Python and platform temporary-directory environment names."""
    TEST_SELECTION_DISABLE_PLUGIN_ARGS: ClassVar[t.StrTuple] = (
        "-p",
        "no:pytest-testmon",
        "-p",
        "no:testmon.pytest_testmon",
    )
    """Block the selection plugin's installed entrypoint and module forms."""

    CLI_GROUP_CHECK: ClassVar[str] = "check"
    CLI_GROUP_CODEGEN: ClassVar[str] = "codegen"
    CLI_GROUP_DEPS: ClassVar[str] = "deps"
    CLI_GROUP_DOCS: ClassVar[str] = "docs"
    CLI_GROUP_MAINTENANCE: ClassVar[str] = "maintenance"
    CLI_GROUP_REFACTOR: ClassVar[str] = "refactor"
    CLI_GROUP_RELEASE: ClassVar[str] = "release"
    CLI_ROUTE_RELEASE: ClassVar[str] = "release run"
    CLI_GROUP_VALIDATE: ClassVar[str] = "validate"
    CLI_ROUTE_MAINTENANCE: ClassVar[str] = "maintenance run"
    CLI_GROUP_WORKSPACE: ClassVar[str] = "workspace"

    MYPY_MEMORY_LIMIT_MB_ENV: ClassVar[str] = "MYPY_MEMORY_LIMIT_MB"
    MYPY_MEMORY_LIMIT_MB_DEFAULT: ClassVar[int] = 6144
    MYPY_PROFILE_OUTPUT_ENV: ClassVar[str] = "FLEXT_MYPY_PROFILE_OUTPUT"
    MYPY_TIMEOUT_GRACE_SECONDS: ClassVar[int] = 10
    MYPY_SUPERVISOR_PS_TIMEOUT: ClassVar[int] = 1
    MYPY_SUPERVISOR_POLL_SECONDS: ClassVar[float] = 0.1
    MYPY_SUPERVISOR_SHUTDOWN_POLL_SECONDS: ClassVar[float] = 0.05
    PRLIMIT_COMMAND: ClassVar[str] = "prlimit"
    PRLIMIT_ADDRESS_SPACE_OPTION: ClassVar[str] = "--as"
    TIMEOUT_COMMAND: ClassVar[str] = "timeout"
    TIMEOUT_KILL_AFTER_SECONDS: ClassVar[int] = 5

    ORCHESTRATOR_REMOVE_ENV_KEYS: ClassVar[Sequence[str]] = (
        "GNUMAKEFLAGS",
        "MAKEFLAGS",
        "MAKEFILES",
        "MAKELEVEL",
        "MAKEOVERRIDES",
        "MISE_DIR",
        "MISE_EXE",
        "MISE_ORIG_PATH",
        "MISE_SESSION",
        "MISE_SHELL",
        "MISE_SHIMS",
        "MISE_VERBOSE",
        "MFLAGS",
        "MYPYPATH",
        "PYTHONDONTWRITEBYTECODE",
        "PYTHONPATH",
        "RUNTIME_ROOT",
        "UV_PROJECT",
        "UV_PROJECT_ENVIRONMENT",
        "VIRTUAL_ENV",
    )
    ORCHESTRATOR_ENV_NO_COLOR: ClassVar[str] = "NO_COLOR"
    ORCHESTRATOR_ENV_PATH: ClassVar[str] = "PATH"
    ORCHESTRATOR_ENV_PYTHONPATH: ClassVar[str] = "PYTHONPATH"
    ORCHESTRATOR_ENV_PATH_SEPARATOR: ClassVar[str] = ":"

    PYTEST_ENV_REPORTS: ClassVar[str] = "FLEXT_PYTEST_REPORTS_RAW"
    PYTEST_ENV_REPOSITORY_ROOT: ClassVar[str] = "PROJECT_ROOT"
    PYTEST_ENV_TARGET: ClassVar[str] = "FLEXT_PYTEST_TARGET_RAW"
    PYTEST_ENV_TARGET_FILE: ClassVar[str] = "FLEXT_PYTEST_TARGET_FILE"
    PYTEST_ENV_CI: ClassVar[str] = "CI"
    PYTEST_ENV_TESTMON_DATAFILE: ClassVar[str] = "TESTMON_DATAFILE"
    PYTEST_WARNING_EVENTS_SUFFIX: ClassVar[str] = ".warnings.jsonl"
    PYTEST_INHERITED_ENV_REMOVE_KEYS: ClassVar[Sequence[str]] = (
        "PYTEST_ADDOPTS",
        "PYTHONPATH",
    )


__all__: list[str] = ["FlextInfraConstantsMake"]
