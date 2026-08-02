"""Make-related constants for flext-infra project.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Final

if TYPE_CHECKING:
    from flext_infra import t


class FlextInfraConstantsMake:
    """Make-related constants for Makefile generation and CLI routing."""

    VERB_CHECK: Final[str] = "check"
    VERB_VALIDATE: Final[str] = "validate"
    VERB_PUBLISH: Final[str] = "publish"
    VERB_RUN: Final[str] = "run"
    VERB_CHECKS: Final[str] = "checks"

    # --- Canonical make contract constants (was: class Make) ---

    CLI_GROUP_CHECK: Final[str] = "check"
    CLI_GROUP_CODEGEN: Final[str] = "codegen"
    CLI_GROUP_DEPS: Final[str] = "deps"
    CLI_GROUP_DOCS: Final[str] = "docs"
    CLI_GROUP_GITHUB: Final[str] = "github"
    CLI_GROUP_MAINTENANCE: Final[str] = "maintenance"
    CLI_GROUP_REFACTOR: Final[str] = "refactor"
    CLI_GROUP_RELEASE: Final[str] = "release"
    CLI_ROUTE_RELEASE: Final[str] = "release run"
    CLI_GROUP_VALIDATE: Final[str] = "validate"
    CLI_ROUTE_MAINTENANCE: Final[str] = "maintenance run"
    CLI_GROUP_WORKSPACE: Final[str] = "workspace"
    MYPY_MEMORY_LIMIT_MB_ENV: Final[str] = "MYPY_MEMORY_LIMIT_MB"
    MYPY_MEMORY_LIMIT_MB_DEFAULT: Final[int] = 6144
    MYPY_TIMEOUT_SECONDS_ENV: Final[str] = "MYPY_TIMEOUT_SECONDS"
    MYPY_TIMEOUT_SECONDS_DEFAULT: Final[int] = 600
    MYPY_TIMEOUT_GRACE_SECONDS: Final[int] = 10
    PRLIMIT_COMMAND: Final[str] = "prlimit"
    PRLIMIT_ADDRESS_SPACE_OPTION: Final[str] = "--as"
    TIMEOUT_COMMAND: Final[str] = "timeout"
    TIMEOUT_KILL_AFTER_SECONDS: Final[int] = 5
    ORCHESTRATOR_REMOVE_ENV_KEYS: Final[t.StrSequence] = (
        "GNUMAKEFLAGS",
        "MAKEFLAGS",
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
        "PYTHONPATH",
        "UV_PROJECT",
        "UV_PROJECT_ENVIRONMENT",
        "VIRTUAL_ENV",
    )
    "Environment keys removed before project-level make orchestration."
    ORCHESTRATOR_ENV_PATH: Final[str] = "PATH"
    ORCHESTRATOR_ENV_PYTHONPATH: Final[str] = "PYTHONPATH"
    ORCHESTRATOR_ENV_PYTHONDONTWRITEBYTECODE: Final[str] = "PYTHONDONTWRITEBYTECODE"
    ORCHESTRATOR_ENV_PATH_SEPARATOR: Final[str] = ":"
    PYTEST_ENV_ARGS: Final[str] = "FLEXT_PYTEST_ARGS_RAW"
    PYTEST_ENV_DIAG: Final[str] = "FLEXT_PYTEST_DIAG_RAW"
    PYTEST_ENV_FAIL_FAST: Final[str] = "FLEXT_PYTEST_FAIL_FAST_RAW"
    PYTEST_ENV_FILE: Final[str] = "FLEXT_PYTEST_FILE_RAW"
    PYTEST_ENV_FILES: Final[str] = "FLEXT_PYTEST_FILES_RAW"
    PYTEST_ENV_MATCH: Final[str] = "FLEXT_PYTEST_MATCH_RAW"
    PYTEST_ENV_REPORTS: Final[str] = "FLEXT_PYTEST_REPORTS_RAW"
    PYTEST_ENV_TARGET: Final[str] = "FLEXT_PYTEST_TARGET_RAW"
    PYTEST_ENV_VERBOSE: Final[str] = "FLEXT_PYTEST_VERBOSE_RAW"
    PYTEST_ENV_WHAT: Final[str] = "FLEXT_PYTEST_WHAT_RAW"
    PYTEST_INHERITED_ENV_REMOVE_KEYS: Final[t.StrSequence] = (
        "PYTEST_ADDOPTS",
        "PYTHONPATH",
    )


__all__: list[str] = ["FlextInfraConstantsMake"]
