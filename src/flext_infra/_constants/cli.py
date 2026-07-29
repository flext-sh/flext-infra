"""CLI-related constants for flext-infra.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Final

from flext_infra.cli_catalog import CliCatalog

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

    SHARED_BOOL_FLAGS: Final[frozenset[str]] = CliCatalog.shared_bool_flags
    SHARED_VALUE_FLAGS: Final[frozenset[str]] = CliCatalog.shared_value_flags
    CLI_GROUP_DESCRIPTIONS: Final[t.StrMapping] = CliCatalog.group_descriptions
    # mro-wkii.17.26 (codex): write routes share one isolated transaction seam.
    WORKTREE_TRANSACTION_ENV: Final[str] = "FLEXT_INFRA_WORKTREE_TRANSACTION"
    WORKTREE_TRANSACTION_NAME_TEMPLATE: Final[str] = (
        "{repository}-transaction-{transaction_id}"
    )
    WORKTREE_TRANSACTION_TIMEOUT_SECONDS: Final[int] = 3600
    WORKTREE_TRANSACTION_APPLY_ROUTES: Final[frozenset[str]] = (
        CliCatalog.transaction_apply_routes
    )
    "CLI routes whose mutations must execute in a complete temporary worktree."
    WORKTREE_TRANSACTION_MODE_ROUTES: Final[frozenset[str]] = (
        CliCatalog.transaction_mode_routes
    )
    "CLI routes that express application through ``--mode apply``."
    WORKTREE_TRANSACTION_LINT_COMMANDS: Final[t.StrSequencePairTuple] = (
        ("ruff", ("ruff", "check", ".", "--preview", "--statistics")),
        ("pyrefly", ("pyrefly", "check")),
    )
    "Lint commands captured before and after each isolated mutation."


__all__: tuple[str, ...] = ("FlextInfraConstantsCli",)
