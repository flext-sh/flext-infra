"""Base constants for flext-infra project.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Mapping
from enum import StrEnum, unique
from types import MappingProxyType
from typing import Final

from flext_infra import (
    FlextInfraConstantsMake,
    FlextInfraConstantsSharedInfra,
    FlextInfraConstantsSourceCode,
)


class FlextInfraConstantsBase(
    FlextInfraConstantsSharedInfra,
    FlextInfraConstantsMake,
    FlextInfraConstantsSourceCode,
):
    """Base constants for flext-infra project."""

    @unique
    class DependencyGroup(StrEnum):
        """Canonical pyproject dependency-group names."""

        DEV = "dev"
        DOCS = "docs"
        SECURITY = "security"
        TEST = "test"
        TYPINGS = "typings"

    @unique
    class ScopeLevel(StrEnum):
        """Scope-resolution granularity enum for refactor selectors."""

        MODULE = "module"
        NAMESPACE = "namespace"
        PROJECT = "project"
        PROJECTS = "projects"
        FILES = "files"
        WORKSPACE = "workspace"

    NAMESPACE_TO_CANONICAL_FILENAME: Final[Mapping[str, str]] = MappingProxyType({
        "c": "constants.py",
        "m": "models.py",
        "p": "protocols.py",
        "t": "typings.py",
        "u": "utilities.py",
    })
    """SSOT mapping from canonical alias (c/m/p/t/u) to its facade filename.

    Used by ``FlextInfraUtilitiesScopeSelector`` (NAMESPACE-level resolution)
    and any future tooling that needs to translate ``--namespace m`` into the
    on-disk ``models.py`` plus ``_models/`` subtree per AGENTS.md §2.2.
    """

    KNOWN_VERBS: Final[frozenset[str]] = frozenset({
        "build",
        "check",
        "dependencies",
        "docs",
        "preflight",
        "release",
        "tests",
        "validate",
        "workspace",
    })

    # TOML section/key names for pyproject.toml parsing

    TOOL: Final[str] = "tool"
    "Top-level [tool] section key."
    POETRY: Final[str] = "poetry"
    "Poetry tool subsection key."
    PROJECT: Final[str] = "project"
    "Top-level [project] section key."
    DEPENDENCIES: Final[str] = "dependencies"
    "Dependencies key within project or poetry sections."
    DEPENDENCY_GROUPS: Final[str] = "dependency-groups"
    "PEP 735 dependency-groups table key."
    OPTIONAL_DEPENDENCIES: Final[str] = "optional-dependencies"
    "Optional dependencies key within [project]."
    GROUP: Final[str] = "group"
    "Poetry group key for dependency groups."
    NAME: Final[str] = "name"
    "Project/package name key."
    VERSION: Final[str] = "version"
    "Version key within project or tool sections."
    PYREFLY: Final[str] = "pyrefly"
    "Pyrefly tool section key."
    MYPY: Final[str] = "mypy"
    "Mypy tool section key."
    PYRIGHT: Final[str] = "pyright"
    "Pyright tool section key."
    PYTEST: Final[str] = "pytest"
    "Pytest tool section key."
    RUFF: Final[str] = "ruff"
    "Ruff tool section key."
    DEPTRY: Final[str] = "deptry"
    "Deptry tool section key."
    ISORT: Final[str] = "isort"
    "Isort tool section key (ruff.lint.isort)."
    INI_OPTIONS: Final[str] = "ini_options"
    "Pytest ini_options subsection key."
    LINT_SECTION: Final[str] = "lint"
    "Ruff lint subsection key."
    SEARCH_PATH: Final[str] = "search-path"
    "Pyrefly search-path settings key."
    PROJECT_EXCLUDES: Final[str] = "project-excludes"
    "Pyrefly project-excludes settings key."
    SUB_CONFIG: Final[str] = "sub-settings"
    "Pyrefly sub-settings key."
    EXECUTION_ENVIRONMENTS: Final[str] = "executionEnvironments"
    "Pyright execution environments settings key."
    EXTRA_PATHS: Final[str] = "extraPaths"
    "Pyright extra paths settings key."
    STUB_PATH: Final[str] = "stubPath"
    "Pyright stub path settings key."
    REPORT_PRIVATE_USAGE: Final[str] = "reportPrivateUsage"
    "Pyright execution-environment private-usage settings key."
    VENV_PATH: Final[str] = "venvPath"
    "Pyright virtualenv base path settings key."
    PYTHON_VERSION_HYPHEN: Final[str] = "python-version"
    "Pyrefly/pyright python-version settings key (hyphenated)."
    PYTHON_VERSION_UNDERSCORE: Final[str] = "python_version"
    "Mypy python_version settings key (underscored)."
    EXTEND: Final[str] = "extend"
    "Ruff extend settings key."
    KNOWN_FIRST_PARTY_HYPHEN: Final[str] = "known-first-party"
    "Ruff isort known-first-party key (hyphenated)."
    KNOWN_FIRST_PARTY_UNDERSCORE: Final[str] = "known_first_party"
    "Ruff isort known_first_party key (underscored)."
    IGNORE_ERRORS_IN_GENERATED: Final[str] = "ignore-errors-in-generated-code"
    "Pyrefly ignore-errors-in-generated-code key."
    MINVERSION: Final[str] = "minversion"
    "Pytest minversion settings key."
    PYTHON_CLASSES: Final[str] = "python_classes"
    "Pytest python_classes settings key."
    PYTHON_FILES: Final[str] = "python_files"
    "Pytest python_files settings key."
    ADDOPTS: Final[str] = "addopts"
    "Pytest addopts settings key."
    MARKERS: Final[str] = "markers"
    "Pytest markers settings key."
    PLUGINS: Final[str] = "plugins"
    "Mypy plugins settings key."
    DISABLE_ERROR_CODE: Final[str] = "disable_error_code"
    "Mypy disable_error_code settings key."
    IGNORE: Final[str] = "ignore"
    "Pyrefly/sub-settings ignore key."
    EXCLUDE: Final[str] = "exclude"
    "Generic exclude key."
    PATH: Final[str] = "path"
    "Path key within dependency entries."
    ERROR: Final[str] = "error"
    "Deptry JSON error field key."
    CODE: Final[str] = "code"
    "Deptry JSON code field key."
    MODULE: Final[str] = "module"
    "Deptry JSON module field key."
    DEV: Final[DependencyGroup] = DependencyGroup.DEV
    "Development dependency group name."
    DOCS: Final[DependencyGroup] = DependencyGroup.DOCS
    "Documentation dependency group name."
    SECURITY: Final[DependencyGroup] = DependencyGroup.SECURITY
    "Security dependency group name."
    TEST: Final[DependencyGroup] = DependencyGroup.TEST
    "Test dependency group name."
    TYPINGS: Final[DependencyGroup] = DependencyGroup.TYPINGS
    "Typing stubs dependency group name."
    TYPING_LIBRARIES: Final[str] = "typing_libraries"
    "Project limits typing_libraries key."
    MODULE_TO_PACKAGE: Final[str] = "module_to_package"
    "Typing libraries module_to_package mapping key."
    PYTHON: Final[str] = "python"
    "Python settings subsection key (in limits)."

    CANONICAL_DEV_DEPENDENCY_GROUPS: Final[tuple[DependencyGroup, ...]] = (
        DEV,
        DOCS,
        SECURITY,
        TEST,
        TYPINGS,
    )
    LEGACY_DEV_DEPENDENCY_GROUPS: Final[tuple[DependencyGroup, ...]] = (
        DOCS,
        SECURITY,
        TEST,
        TYPINGS,
    )

    # ANSI color codes and terminal symbols (SSOT for output styling).

    RESET: Final[str] = "\x1b[0m"
    RED: Final[str] = "\x1b[31m"
    GREEN: Final[str] = "\x1b[32m"
    YELLOW: Final[str] = "\x1b[33m"
    BLUE: Final[str] = "\x1b[34m"
    BOLD: Final[str] = "\x1b[1m"

    # Unicode/ASCII symbols
    OK: Final[str] = "✓"
    FAIL: Final[str] = "✗"
    WARN: Final[str] = "⚠"
    SKIP: Final[str] = "–"

    # CLI tool binary names
    GIT: Final[str] = "git"
    "Git version control binary."
    SG: Final[str] = "sg"
    "ast-grep (sg) binary."
    BANDIT: Final[str] = "bandit"
    "Bandit security linter binary."
    MARKDOWNLINT: Final[str] = "markdownlint"
    "Markdown linter binary."
    GOFMT: Final[str] = "gofmt"
    "Go formatter binary."
    OUTPUT_JSON: Final[str] = "json"
    "Common CLI output format flag value."
    PR: Final[str] = "pr"
    "GitHub pull request subcommand."
    SQUASH: Final[str] = "squash"
    "GitHub squash merge method."
    SCAN: Final[str] = "scan"
    "ast-grep scan subcommand."
    GOVET: Final[str] = "go"
    "Go vet binary (invoked as 'go vet')."
    MAKE: Final[str] = "make"
    "Make build tool binary."

    # Quality gate identifiers.
    CHECK: Final[str] = "check"
    "Generic check command/subcommand identifier."
    LINT: Final[str] = "lint"
    FORMAT: Final[str] = "format"
    MARKDOWN: Final[str] = "markdown"
    GO: Final[str] = "go"
    SILENT_FAILURE: Final[str] = "silent-failure"
    TYPE_ALIAS: Final[str] = "type"
    DEFAULT_CSV: Final[str] = (
        "lint,format,pyrefly,mypy,pyright,silent-failure,security,markdown,go"
    )

    @unique
    class TomlMergeMode(StrEnum):
        """SSOT merge strategies for TOML list synchronization."""

        REPLACE = "replace"
        ADDITIVE = "additive"
        MERGE = "merge"

    @unique
    class ResultStatus(StrEnum):
        """SSOT status values for reports and gate summaries."""

        PASSED = "PASS"
        FAIL = "FAIL"
        OK = "OK"
        WARN = "WARN"

    @unique
    class MatchMode(StrEnum):
        """SSOT scanner match mode values."""

        PRESENT = "present"
        ABSENT = "absent"

    @unique
    class LazyInitAction(StrEnum):
        """SSOT lazy-init action values."""

        WRITE = "write"
        REMOVE = "remove"
        SKIP = "skip"

    @unique
    class PathSyncMode(StrEnum):
        """SSOT dependency path-sync modes."""

        WORKSPACE = "workspace"
        STANDALONE = "standalone"
        AUTO = "auto"

    @unique
    class DependencyConstraintPolicy(StrEnum):
        """SSOT dependency constraint rewrite policies."""

        FLOOR = "floor"
        COMPATIBLE = "compatible"

    @unique
    class TomlOperationKind(StrEnum):
        """SSOT TOML phase operation kinds."""

        SET = "set"
        LIST = "list"
        REMOVE = "remove"

    @unique
    class OperationMode(StrEnum):
        """SSOT operation mode values."""

        BASELINE = "baseline"
        STRICT = "strict"

    @unique
    class SeverityLevel(StrEnum):
        """SSOT severity levels."""

        ERROR = "error"
        WARNING = "warning"
        NOTE = "note"
        LOW = "low"
        SKIP = "skip"

    DEFAULT_UNKNOWN: Final[str] = "unknown"
    DEFAULT_UNNAMED: Final[str] = "unnamed"

    RK_STATUS: Final[str] = "status"
    RK_FILE: Final[str] = "file"
    RK_MESSAGE: Final[str] = "message"
    RK_SUMMARY: Final[str] = "summary"
    RK_TOTAL: Final[str] = "total"
    RK_RULES: Final[str] = "rules"
    RK_RELEASE: Final[str] = "release"
    RK_ACTION: Final[str] = "action"
    RK_SCOPE: Final[str] = "scope"
    RK_VIOLATIONS: Final[str] = "violations"
    RK_VIOLATIONS_COUNT: Final[str] = "violations_count"
    RK_RULE_ID: Final[str] = "rule_id"
    RK_OK: Final[str] = "ok"
    RK_ENABLED: Final[str] = "enabled"
    RK_PROJECTS: Final[str] = "projects"
    RK_WORKSPACE: Final[str] = "workspace"
    RK_ROOT: Final[str] = "root"
    RK_ID: Final[str] = "id"
    RK_URL: Final[str] = "url"
    RK_CLASS_NESTING: Final[str] = "class_nesting"
    RK_TARGET_NAMESPACE: Final[str] = "target_namespace"
    RK_SOURCE_SYMBOL: Final[str] = "source_symbol"
    RK_LOOSE_NAME: Final[str] = "loose_name"
    RK_REWRITE_SCOPE: Final[str] = "rewrite_scope"
    RK_CONFIDENCE: Final[str] = "confidence"
    RK_FIX_ACTION: Final[str] = "fix_action"
    RK_CURRENT_FILE: Final[str] = "current_file"
    RK_DESCRIPTION: Final[str] = "description"
    RK_SEVERITY: Final[str] = "severity"
    RK_VIOLATION_TYPE: Final[str] = "violation_type"
    RK_SUGGESTED_FIX: Final[str] = "suggested_fix"
    RK_HELPER_CONSOLIDATION: Final[str] = "helper_consolidation"
    RK_POST_CHECKS: Final[str] = "post_checks"

    REPORT_KEYS: Final[frozenset[str]] = frozenset({
        RK_STATUS,
        RK_FILE,
        RK_MESSAGE,
        RK_SUMMARY,
        RK_TOTAL,
        RK_RULES,
        RK_RELEASE,
        RK_ACTION,
        RK_SCOPE,
        RK_VIOLATIONS,
        RK_VIOLATIONS_COUNT,
        RK_RULE_ID,
        RK_OK,
        RK_ENABLED,
        RK_PROJECTS,
        RK_WORKSPACE,
        RK_ROOT,
        RK_ID,
        RK_URL,
        RK_CLASS_NESTING,
        RK_TARGET_NAMESPACE,
        RK_SOURCE_SYMBOL,
        RK_LOOSE_NAME,
        RK_REWRITE_SCOPE,
        RK_CONFIDENCE,
        RK_FIX_ACTION,
        RK_CURRENT_FILE,
        RK_DESCRIPTION,
        RK_SEVERITY,
        RK_VIOLATION_TYPE,
        RK_SUGGESTED_FIX,
        RK_HELPER_CONSOLIDATION,
        RK_POST_CHECKS,
    })

    CLI_APPLY_OPTION_DECLS: Final[tuple[str, ...]] = ("--apply/--dry-run",)
    "Typer dual-flag declarations for --apply/--dry-run option."

    @unique
    class FacadeFamily(StrEnum):
        """Facade family enumeration."""

        C = "c"
        T = "t"
        P = "p"
        M = "m"
        U = "u"

    SAFE_EXECUTION_DEFAULT_GATES: Final[str] = "lint,mypy,pyright,pyrefly"
    "Default quality gates for post-transform validation."
    SAFE_EXECUTION_BAK_SUFFIX: Final[str] = ".bak"
    "File backup suffix for copy-on-write safety."

    ENV_VAR_STANDALONE: Final[str] = "FLEXT_STANDALONE"
    ENV_VAR_WORKSPACE_ROOT: Final[str] = "FLEXT_WORKSPACE_ROOT"
    ENV_VAR_USE_HTTPS: Final[str] = "FLEXT_USE_HTTPS"
    ENV_VAR_GITHUB_ACTIONS: Final[str] = "GITHUB_ACTIONS"
    ENV_VAR_GITHUB_HEAD_REF: Final[str] = "GITHUB_HEAD_REF"
    ENV_VAR_GITHUB_REF_NAME: Final[str] = "GITHUB_REF_NAME"
    ENV_DEFAULT_STANDALONE: Final[bool] = False
    ENV_DEFAULT_USE_HTTPS: Final[bool] = False
    ENV_DEFAULT_GITHUB_ACTIONS: Final[bool] = False

    @unique
    class ExecutionMode(StrEnum):
        """Execution mode for commands that modify files."""

        DRY_RUN = "dry-run"
        "Preview changes without writing."
        CHECK_ONLY = "check-only"
        "Detect violations without fixing."
        APPLY_SAFE = "apply-safe"
        "Apply with backup, validate, rollback on failure."
        APPLY_FORCE = "apply-force"
        "Apply without post-validation."


__all__: list[str] = ["FlextInfraConstantsBase"]
