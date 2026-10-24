"""Lazy-init constants for the codegen package.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import re
from enum import IntEnum, StrEnum, unique
from types import MappingProxyType
from typing import TYPE_CHECKING, ClassVar

if TYPE_CHECKING:
    from flext_infra import t


class FlextInfraConstantsCodegenLazy:
    """Lazy-init and export-policy constants for codegen."""

    MAX_ALIAS_LENGTH: ClassVar[int] = 2
    "Maximum length of a public facade alias."
    AUTOGEN_HEADER: ClassVar[str] = "# AUTO-GENERATED FILE — Regenerate with: make gen"
    "Header prepended to every auto-generated ``__init__.py`` file."
    AUTOGEN_HEADERS: ClassVar[t.Pair[str, str]] = (
        AUTOGEN_HEADER,
        "# @generated AUTO-GENERATED FILE — Regenerate with: make gen",
    )
    "Current and former generated initializer headers accepted during migration."
    GENERATED_EXPORT_SIDECAR_RE: ClassVar[t.RegexPattern] = re.compile(
        r"^(?:_exports(?:_lazy(?:_part_[0-9]+)?)?|_lazy_exports)\.py$",
    )
    "Regex matching every generated lazy-export sidecar filename "
    "(``_exports.py``, ``_exports_lazy.py``, ``_exports_lazy_part_N.py``, "
    "``_lazy_exports.py``); legacy variants are excluded from discovery and cleanup."
    OBSOLETE_ROOT_SUPPORT_NAMES: ClassVar[frozenset[str]] = frozenset({
        "_root_exports",
        "_root_exports_parts",
        "_root_typing",
        "_root_typing_parts",
    })
    "Closed set of retired root registry module and package names."
    LAZY_BOOTSTRAP_HELPERS: ClassVar[t.VariadicTuple[str]] = (
        "build_lazy_import_map",
        "install_lazy_exports",
    )
    "Existing SDK helpers eagerly bound and published by the bootstrap root."
    TEST_ONLY_SOURCE_MODULE_RE: ClassVar[t.RegexPattern] = re.compile(
        r"^(?:_?test(?:_[A-Za-z0-9_]+)?|[A-Za-z0-9_]+_tests?)\.py$",
    )
    "Test-module filenames forbidden from installable package export maps."
    INIT_PYI: ClassVar[str] = "__init__.pyi"
    "Typing stub paired with generated thin package initializers."
    ALL_SCAN_PATTERNS: ClassVar[t.StrSequence] = (
        "src/**/__init__.py",
        "tests/**/__init__.py",
        "examples/**/__init__.py",
    )
    """Glob patterns for all directories the lazy-init generator scans.

    ``scripts/`` is deliberately absent: its modules are entry points, each
    owning its own ``main``, not a package whose names a generated initializer
    should re-export.
    """
    NON_PUBLIC_LAZY_ROOTS: ClassVar[frozenset[str]] = frozenset({
        "examples",
        "scripts",
        "tests",
    })
    "Root import surfaces generated as private lazy plumbing, not public ABI."
    WRAPPER_NAMESPACE_DEPTH: ClassVar[int] = 2
    "Dotted depth of a namespace package under a governed wrapper surface."
    LAZY_BOOTSTRAP_ROOT_PACKAGE: ClassVar[str] = "flext_core"
    LAZY_BOOTSTRAP_MODULE: ClassVar[str] = "flext_core.lazy"
    "Defining module imported directly only by the bootstrap root initializer."

    LINT_TOOLS: ClassVar[t.StrSequencePairTuple] = (
        # Ruff runs with NO --select override: the project's pyproject.toml
        # (select=ALL + narrow whitelist + preview) is the ONLY rule policy.
        ("ruff", ("ruff", "check", "{file}", "--no-fix")),
        ("pyright", ("pyright", "{file}")),
        ("mypy", ("mypy", "{file}", "--no-error-summary")),
        ("pyrefly", ("pyrefly", "check", "{file}")),
    )
    "Lint tool names and their CLI command templates for validation."
    LOCAL_INFERRED_SEGMENTS: ClassVar[frozenset[str]] = frozenset({
        "_constants",
        "_exceptions",
        "_models",
        "_protocols",
        "_typings",
        "_utilities",
        "constants",
        "exceptions",
        "models",
        "protocols",
        "typings",
        "utilities",
        "services",
        "docs",
        "tools",
    })
    "Module segments recognized as local inferred imports in lazy-load chain."
    PUBLIC_ROOT_ALIAS_ORDER: ClassVar[t.StrSequence] = (
        "c",
        "t",
        "p",
        "m",
        "u",
        "d",
        "e",
        "h",
        "r",
        "s",
        "x",
        "infra",
        "main",
    )
    "Canonical dependency order for public aliases and operational entry points."
    TEST_RUNTIME_ALIAS_TARGETS: ClassVar[t.MappingKV[str, t.StrPair]] = (
        MappingProxyType({
            "c": ("flext_tests", "c"),
            "d": ("flext_tests", "d"),
            "e": ("flext_tests", "e"),
            "h": ("flext_tests", "h"),
            "m": ("flext_tests", "m"),
            "p": ("flext_tests", "p"),
            "r": ("flext_tests", "r"),
            "s": ("flext_tests", "s"),
            "t": ("flext_tests", "t"),
            "td": ("flext_tests", "td"),
            "tf": ("flext_tests", "tf"),
            "tk": ("flext_tests", "tk"),
            "tm": ("flext_tests", "tm"),
            "u": ("flext_tests", "u"),
            "x": ("flext_tests", "x"),
        })
    )
    "Mapping of test-only aliases to flext-tests runtime targets."
    LAZY_INIT_HIDDEN_CHILD_EXPORTS: ClassVar[frozenset[str]] = frozenset({
        "__init__",
        "pytestmark",
    })
    "Child-package exports never re-published by a parent initializer."
    LAZY_INIT_FIXTURES_DIR: ClassVar[str] = "_fixtures"
    "Package name whose modules are governed fixture publication owners."
    LAZY_INIT_CONSTANTS_MARKER: ClassVar[str] = "Constants"
    "Class-name marker of the facade class whose bases declare facade parents."

    @unique
    class LazyInitScore(IntEnum):
        """Publication score weights electing between two export routes."""

        FACADE_ALIAS = 100
        FAMILY_SUFFIX = 25
        FOREIGN_ALIAS = -40
        FOREIGN_FAMILY = -20
        PUBLISHED = 20
        DECLARED = 15
        SELF_NAMED = 3
        GOVERNED = 10
        BARE_ALIAS = -80

    @unique
    class LazyInitMessage(StrEnum):
        """Lazy-init planning diagnostics, rendered with ``str.format``."""

        WORKSPACE_NOT_DIR = "lazy-init workspace is not a directory: {workspace}"
        SCOPE_OUTSIDE = (
            "lazy-init repository scope is missing or outside {workspace}: {root}"
        )
        TARGET_AMBIGUOUS = "lazy-init target module is ambiguous: {module}"
        TARGET_NOT_FOUND = "lazy-init target module not found: {module}"
        CONFLICTING_PLANS = "conflicting lazy-init plans for {path}"
        PLAN_SUMMARY = "Lazy-init plan: {effects} effects"
        PUBLICATION_OWNED_BY_CONFORM = (
            "lazy-init publication is owned by codegen conform; "
            "conform must publish plan_files()"
        )
        DRIFT = "init drift detected in {count} generated artifacts: {paths}"
        VIEW_OUTSIDE = "lazy-init consumer is outside its injected source view"


__all__: list[str] = ["FlextInfraConstantsCodegenLazy"]
