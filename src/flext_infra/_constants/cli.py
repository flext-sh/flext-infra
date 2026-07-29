"""CLI-related constants for flext-infra.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

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
