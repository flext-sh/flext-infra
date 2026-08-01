"""CLI-related constants for flext-infra.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from types import MappingProxyType
from typing import TYPE_CHECKING, Final

if TYPE_CHECKING:
    from flext_infra import t


class FlextInfraConstantsCli:
    """Shared CLI flag vocabularies and route tables."""

    PROCESS_TIMEOUT_EXIT_CODE: Final[int] = 124
    "Exit code emitted by the canonical wall-time limiter."
    PROCESS_SIGNAL_EXIT_OFFSET: Final[int] = 128
    "POSIX shell offset used to encode a terminating signal."
    PROCESS_EXIT_ERROR_CODE: Final[str] = "EXTERNAL_PROCESS_EXIT"
    "Stable result error code for non-zero external process exits."

    _SHARED_BOOL_FLAG_VALUES: Final[tuple[str, ...]] = (
        "--apply",
        "--check",
        "--check-only",
        "--dry-run",
        "--fail-fast",
        "--verbose",
        "--quiet",
        "--no-fail",
        "--typings",
        "--apply-typings",
        "--no-pip-check",
        "--skip-check",
        "--skip-comments",
        "--audit",
        "--rewrite-constraints",
    )
    _SHARED_VALUE_FLAG_VALUES: Final[tuple[str, ...]] = (
        "--checks",
        "--docstring-min",
        "--workspace",
        "--projects",
        "--project",
        "--module",
        "--namespace",
        "--gates",
        "--what",
        "--format",
        "--output",
        "--report",
        "--output-dir",
        "--json-output",
        "--reports-dir",
        "--ruff-args",
        "--pyright-args",
        "--operation",
        "--branch",
        "--base",
    )
    SHARED_BOOL_FLAGS: Final[frozenset[str]] = frozenset(_SHARED_BOOL_FLAG_VALUES)
    SHARED_VALUE_FLAGS: Final[frozenset[str]] = frozenset(_SHARED_VALUE_FLAG_VALUES)
    CLI_GROUP_DESCRIPTIONS: Final[t.StrMapping] = MappingProxyType({
        "basemk": "Base.mk template generation",
        "check": "Lint gates and pyrefly settings management",
        "codegen": "Code generation and workspace standardization",
        "validate": "Infrastructure validators and diagnostics",
        "deps": "Dependency detection and modernization",
        "docs": "Documentation audit, fix, build, generate, validate",
        "github": "GitHub workflows, linting, and PR automation",
        "maintenance": "Python version enforcement",
        "refactor": "Declarative refactoring and modernization",
        "release": "Release orchestration",
        "workspace": "Workspace detection and orchestration",
    })
    # mro-wkii.17.26 (codex): write routes share one isolated transaction seam.
    WORKTREE_TRANSACTION_ENV: Final[str] = "FLEXT_INFRA_WORKTREE_TRANSACTION"
    WORKTREE_TRANSACTION_NAME_TEMPLATE: Final[str] = (
        "{repository}-transaction-{transaction_id}"
    )
    WORKTREE_TRANSACTION_TIMEOUT_SECONDS: Final[int] = 3600
    WORKTREE_TRANSACTION_APPLY_ROUTES: Final[frozenset[str]] = frozenset({
        "check:fix-enforcement",
        "check:fix-pyrefly-settings",
        "codegen:auto-fix",
        "codegen:consolidate",
        "codegen:init",
        "codegen:new",
        "codegen:pipeline",
        "codegen:py-typed",
        "codegen:scaffold",
        "codegen:version-file",
        "deps:extra-paths",
        "deps:modernize",
        "refactor:accessor-migrate",
        "refactor:apply-renames",
        "refactor:migrate-mro",
        "refactor:modernize-cli",
        "refactor:modernize-logging",
        "refactor:modernize-patterns",
        "refactor:modernize-pydantic",
        "refactor:modernize-result-di",
        "refactor:namespace-enforce",
        "refactor:wrapper-root-namespace",
    })
    "CLI routes whose mutations must execute in a complete temporary worktree."
    WORKTREE_TRANSACTION_MODE_ROUTES: Final[frozenset[str]] = frozenset({
        "codegen:conform"
    })
    "CLI routes that express application through ``--mode apply``."
    WORKTREE_TRANSACTION_LINT_COMMANDS: Final[t.StrSequencePairTuple] = ()
    """Empty by contract: one tool runs once, in the verb that owns it.

    Why (ai-hub-qwoc): this ran `ruff check . --preview` inside the isolated
    transaction worktree, which has neither the project's pyproject nor its
    path scoping. Measured on ai-hub: `ruff check src/ tests/` reports zero
    errors while the transaction reported 548 (189 SLF001, 70 PLC2701, 52
    S108 ...), so a clean repository could not be conformed at all --
    `make gen APPLY=Y` aborted before writing a single managed file.

    Linting belongs to its own verb and runs exactly once: `ruff check` in
    `make check`, `ruff format` in `make fmt`, `ruff check --fix` in
    `make fix`. Conform owns structural conformance, never a second lint pass.
    """


__all__: tuple[str, ...] = ("FlextInfraConstantsCli",)
