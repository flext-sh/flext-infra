"""CLI-related constants for flext-infra.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import Final


class FlextInfraConstantsCli:
    """Shared CLI flag vocabularies and route tables."""

    _SHARED_BOOL_FLAG_VALUES: Final[tuple[str, ...]] = (
        "--apply",
        "--check",
        "--check-only",
        "--dry-run",
        "--diff",
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
        "--rollback",
    )
    _SHARED_VALUE_FLAG_VALUES: Final[tuple[str, ...]] = (
        "--constraint-policy",
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


__all__: tuple[str, ...] = ("FlextInfraConstantsCli",)
