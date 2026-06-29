"""Shared CLI flag vocabularies for the flext-infra command surface."""

from __future__ import annotations

SHARED_BOOL_FLAGS: frozenset[str] = frozenset(
    {
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
    }
)
SHARED_VALUE_FLAGS: frozenset[str] = frozenset(
    {
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
    }
)
CHECK_RUN_SCOPE_VALUE_FLAGS: frozenset[str] = frozenset(
    {
        "--workspace",
        "--projects",
        "--project",
    }
)

__all__: list[str] = [
    "CHECK_RUN_SCOPE_VALUE_FLAGS",
    "SHARED_BOOL_FLAGS",
    "SHARED_VALUE_FLAGS",
]
