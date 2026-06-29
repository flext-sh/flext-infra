"""Shared CLI flag vocabularies for the flext-infra command surface."""

from __future__ import annotations

from typing import Final

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
SHARED_BOOL_FLAGS: frozenset[str] = frozenset(_SHARED_BOOL_FLAG_VALUES)
SHARED_VALUE_FLAGS: frozenset[str] = frozenset(_SHARED_VALUE_FLAG_VALUES)

__all__: list[str] = [
    "SHARED_BOOL_FLAGS",
    "SHARED_VALUE_FLAGS",
]
