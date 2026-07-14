"""CLI-related constants for flext-infra.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from types import MappingProxyType
from typing import Final

from flext_infra import t


class FlextInfraConstantsCli:
    """Shared CLI flag vocabularies and route tables."""

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
        "--constraint-policy",
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
    )
    SHARED_BOOL_FLAGS: Final[frozenset[str]] = frozenset(_SHARED_BOOL_FLAG_VALUES)
    SHARED_VALUE_FLAGS: Final[frozenset[str]] = frozenset(_SHARED_VALUE_FLAG_VALUES)
    CLI_GROUP_DESCRIPTIONS: Final[t.StrMapping] = MappingProxyType({
        "basemk": "Base.mk template generation",
        "check": "Lint gates and pyrefly settings management",
        "codegen": "Code generation and workspace standardization",
        "validate": "Infrastructure validators and diagnostics",
        "deps": "Dependency detection, sync, and modernization",
        "docs": "Documentation audit, fix, build, generate, validate",
        "github": "GitHub workflows, linting, and PR automation",
        "maintenance": "Python version enforcement",
        "refactor": "Declarative refactoring and modernization",
        "release": "Release orchestration",
        "workspace": "Workspace detection, sync, orchestration, migration",
    })
    # mro-wkii.17.26 (codex): write routes share one isolated transaction seam.
    WORKTREE_TRANSACTION_ENV: Final[str] = "FLEXT_INFRA_WORKTREE_TRANSACTION"
    WORKTREE_TRANSACTION_ROOT: Final[str] = ".worktrees"
    WORKTREE_TRANSACTION_TIMEOUT_SECONDS: Final[int] = 3600
    WORKTREE_TRANSACTION_APPLY_ROUTES: Final[frozenset[str]] = frozenset({
        "basemk:generate",
        "check:fix-enforcement",
        "check:fix-pyrefly-settings",
        "codegen:auto-fix",
        "codegen:consolidate",
        "codegen:grpc",
        "codegen:init",
        "codegen:new",
        "codegen:pipeline",
        "codegen:py-typed",
        "codegen:scaffold",
        "codegen:version-file",
        "deps:extra-paths",
        "deps:internal-sync",
        "deps:modernize",
        "refactor:accessor-migrate",
        "refactor:migrate-mro",
        "refactor:modernize-cli",
        "refactor:modernize-logging",
        "refactor:modernize-patterns",
        "refactor:modernize-pydantic",
        "refactor:modernize-result-di",
        "refactor:namespace-enforce",
        "refactor:wrapper-root-namespace",
        "workspace:migrate",
        "workspace:sync",
    })
    "CLI routes whose mutations must execute in a complete temporary worktree."
    WORKTREE_TRANSACTION_MODE_ROUTES: Final[frozenset[str]] = frozenset({
        "codegen:conform"
    })
    "CLI routes that express application through ``--mode apply``."
    WORKTREE_TRANSACTION_LINT_COMMANDS: Final[t.StrSequencePairTuple] = (
        ("ruff", ("ruff", "check", ".", "--preview", "--statistics")),
        ("pyrefly", ("pyrefly", "check")),
    )
    "Lint commands captured before and after each isolated mutation."


__all__: tuple[str, ...] = ("FlextInfraConstantsCli",)
