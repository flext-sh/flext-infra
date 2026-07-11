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


__all__: tuple[str, ...] = ("FlextInfraConstantsCli",)
