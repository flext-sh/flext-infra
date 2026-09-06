"""Selector-free Make and project-tool constants."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Final

if TYPE_CHECKING:
    from flext_infra import t


class FlextInfraConstantsMake:
    """One canonical vocabulary shared by generated Make and its services."""

    MAKE_ASSIGNMENT_RE: Final[t.RegexPattern] = re.compile(
        r"^[A-Za-z_][A-Za-z0-9_]*\s*(?::?:|\?|\+)?="
    )
    MAKE_DIRECTIVE_RE: Final[t.RegexPattern] = re.compile(
        r"^(?:export|unexport|override|include|-include|sinclude|vpath)\b"
    )
    MAKE_CONDITIONAL_RE: Final[t.RegexPattern] = re.compile(
        r"^(?:else\b|endif\b|ifeq\b|ifneq\b|ifdef\b|ifndef\b)"
    )

    VERB_CHECK: Final[str] = "check"
    VERB_DEPS: Final[str] = "deps"
    VERB_TEST: Final[str] = "test"
    VERB_CLEAN: Final[str] = "clean"
    VERB_VALIDATE: Final[str] = "validate"
    VERB_PUBLISH: Final[str] = "publish"
    VERB_RUN: Final[str] = "run"
    VERB_CHECKS: Final[str] = "checks"

    CLI_GROUP_CHECK: Final[str] = "check"
    CLI_GROUP_CODEGEN: Final[str] = "codegen"
    CLI_GROUP_DEPS: Final[str] = "deps"
    CLI_GROUP_DOCS: Final[str] = "docs"
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

    # loc-cap is deliberately absent from the canonical cycle: the fleet's
    # integrated reality carries 145+ over-ceiling modules, so enforcing now
    # would block every landing (operator authorization 2026-09-06). The gate
    # stays registered and its ceiling is config-owned
    # (codegen.loc_cap.max_lines); re-entry into this tuple is owned by the
    # module-split epic.
    CANONICAL_GATE_IDS: Final[tuple[str, ...]] = (
        "lint",
        "pyrefly",
        "mypy",
        "pyright",
        "silent-failure",
        "deferred-self-reference",
        "security",
        "markdown",
        "boundary",
        "canonical-alias",
        "runtime-census",
        "namespace",
        "layout",
        "tier-whitelist",
        "smells",
        "codemod",
        "direnv",
        "duplication",
    )
    CANONICAL_DEFAULT_GATE_IDS: Final[tuple[str, ...]] = CANONICAL_GATE_IDS
    CANONICAL_FIXABLE_GATE_IDS: Final[tuple[str, ...]] = (
        "lint",
        "markdown",
        "canonical-alias",
        "smells",
    )
    ORCHESTRATED_VERBS: Final[t.StrSequence] = (
        "build",
        "check",
        "clean",
        "docs",
        "fmt",
        "fix",
        "test",
    )
    ORCHESTRATOR_REMOVE_ENV_KEYS: Final[t.StrSequence] = (
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
        "UV_PROJECT",
        "UV_PROJECT_ENVIRONMENT",
        "VIRTUAL_ENV",
    )
    ORCHESTRATOR_ENV_NO_COLOR: Final[str] = "NO_COLOR"
    ORCHESTRATOR_ENV_PATH: Final[str] = "PATH"
    ORCHESTRATOR_ENV_PYTHONPATH: Final[str] = "PYTHONPATH"
    ORCHESTRATOR_ENV_PATH_SEPARATOR: Final[str] = ":"
    ORCHESTRATOR_ENV_MISE_SHIMS: Final[str] = "MISE_SHIMS"
    ORCHESTRATOR_ENV_WORKSPACE_MISE_SHIMS: Final[str] = "WORKSPACE_MISE_SHIMS"

    PYTEST_ENV_REPORTS: Final[str] = "FLEXT_PYTEST_REPORTS_RAW"
    PYTEST_ENV_TARGET: Final[str] = "FLEXT_PYTEST_TARGET_RAW"
    PYTEST_ENV_CI: Final[str] = "CI"
    PYTEST_ENV_TESTMON_DATAFILE: Final[str] = "TESTMON_DATAFILE"
    PYTEST_DESELECTED_RE: Final[t.RegexPattern] = re.compile(
        r"(?P<count>[0-9]+)\s+deselected\b"
    )
    PYTEST_COVERAGE_FAILURE_RE: Final[t.RegexPattern] = re.compile(
        r"(?:Coverage failure:|required test coverage .* not reached)", re.IGNORECASE
    )
    PYTEST_INHERITED_ENV_REMOVE_KEYS: Final[t.StrSequence] = (
        "PYTEST_ADDOPTS",
        "PYTHONPATH",
    )


__all__: list[str] = ["FlextInfraConstantsMake"]
