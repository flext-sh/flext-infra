"""Base constants for flext-infra project.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from enum import StrEnum, unique
from typing import Final

from flext_infra._constants.make import FlextInfraConstantsMake
from flext_infra._constants.source_code import FlextInfraConstantsSourceCode


class FlextInfraConstantsBase(
    FlextInfraConstantsMake,
    FlextInfraConstantsSourceCode,
):
    """Base constants for flext-infra project."""

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
    "Pyrefly search-path config key."
    PROJECT_EXCLUDES: Final[str] = "project-excludes"
    "Pyrefly project-excludes config key."
    SUB_CONFIG: Final[str] = "sub-config"
    "Pyrefly sub-config key."
    PYTHON_VERSION_HYPHEN: Final[str] = "python-version"
    "Pyrefly/pyright python-version config key (hyphenated)."
    PYTHON_VERSION_UNDERSCORE: Final[str] = "python_version"
    "Mypy python_version config key (underscored)."
    EXTEND: Final[str] = "extend"
    "Ruff extend config key."
    KNOWN_FIRST_PARTY_HYPHEN: Final[str] = "known-first-party"
    "Ruff isort known-first-party key (hyphenated)."
    KNOWN_FIRST_PARTY_UNDERSCORE: Final[str] = "known_first_party"
    "Ruff isort known_first_party key (underscored)."
    IGNORE_ERRORS_IN_GENERATED: Final[str] = "ignore-errors-in-generated-code"
    "Pyrefly ignore-errors-in-generated-code key."
    MINVERSION: Final[str] = "minversion"
    "Pytest minversion config key."
    PYTHON_CLASSES: Final[str] = "python_classes"
    "Pytest python_classes config key."
    PYTHON_FILES: Final[str] = "python_files"
    "Pytest python_files config key."
    ADDOPTS: Final[str] = "addopts"
    "Pytest addopts config key."
    MARKERS: Final[str] = "markers"
    "Pytest markers config key."
    PLUGINS: Final[str] = "plugins"
    "Mypy plugins config key."
    DISABLE_ERROR_CODE: Final[str] = "disable_error_code"
    "Mypy disable_error_code config key."
    IGNORE: Final[str] = "ignore"
    "Pyrefly/sub-config ignore key."
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
    DEV: Final[str] = "dev"
    "Development dependency group name."
    DOCS: Final[str] = "docs"
    "Documentation dependency group name."
    SECURITY: Final[str] = "security"
    "Security dependency group name."
    TEST: Final[str] = "test"
    "Test dependency group name."
    TYPING_LIBRARIES: Final[str] = "typing_libraries"
    "Project limits typing_libraries key."
    MODULE_TO_PACKAGE: Final[str] = "module_to_package"
    "Typing libraries module_to_package mapping key."
    PYTHON: Final[str] = "python"
    "Python config subsection key (in limits)."

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
    TYPE_ALIAS: Final[str] = "type"
    DEFAULT_CSV: Final[str] = "lint,format,pyrefly,mypy,pyright,security,markdown,go"

    class Status:
        """Status strings for check results."""

        PASSED: Final[str] = "PASS"
        FAIL: Final[str] = "FAIL"
        OK: Final[str] = "OK"
        WARN: Final[str] = "WARN"

    class Defaults:
        """Default fallback values."""

        UNKNOWN: Final[str] = "unknown"
        UNNAMED: Final[str] = "unnamed"

    class MatchModes:
        """Scanner match mode constants."""

        PRESENT: Final[str] = "present"
        ABSENT: Final[str] = "absent"

    class Modes:
        """Operation mode constants."""

        BASELINE: Final[str] = "baseline"
        STRICT: Final[str] = "strict"

    class Severity:
        """Severity level constants for check/report results."""

        ERROR: Final[str] = "error"
        WARNING: Final[str] = "warning"
        LOW: Final[str] = "low"
        SKIP: Final[str] = "skip"

    class ReportKeys:
        """Common dictionary key names for reports and results."""

        STATUS: Final[str] = "status"
        FILE: Final[str] = "file"
        MESSAGE: Final[str] = "message"
        SUMMARY: Final[str] = "summary"
        TOTAL: Final[str] = "total"
        RULES: Final[str] = "rules"
        RELEASE: Final[str] = "release"
        ACTION: Final[str] = "action"
        SCOPE: Final[str] = "scope"
        VIOLATIONS: Final[str] = "violations"
        VIOLATIONS_COUNT: Final[str] = "violations_count"
        RULE_ID: Final[str] = "rule_id"
        OK: Final[str] = "ok"
        ENABLED: Final[str] = "enabled"
        PROJECTS: Final[str] = "projects"
        WORKSPACE: Final[str] = "workspace"
        ROOT: Final[str] = "root"
        ID: Final[str] = "id"
        URL: Final[str] = "url"
        CLASS_NESTING: Final[str] = "class_nesting"
        TARGET_NAMESPACE: Final[str] = "target_namespace"
        SOURCE_SYMBOL: Final[str] = "source_symbol"
        LOOSE_NAME: Final[str] = "loose_name"
        REWRITE_SCOPE: Final[str] = "rewrite_scope"
        CONFIDENCE: Final[str] = "confidence"
        FIX_ACTION: Final[str] = "fix_action"
        CURRENT_FILE: Final[str] = "current_file"
        VIOLATION_TYPE: Final[str] = "violation_type"
        SUGGESTED_FIX: Final[str] = "suggested_fix"
        HELPER_CONSOLIDATION: Final[str] = "helper_consolidation"
        POST_CHECKS: Final[str] = "post_checks"

    @unique
    class FacadeFamily(StrEnum):
        """Facade family enumeration."""

        C = "c"
        T = "t"
        P = "p"
        M = "m"
        U = "u"


__all__ = ["FlextInfraConstantsBase"]
