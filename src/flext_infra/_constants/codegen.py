"""Centralized constants for the codegen package.

All constants used across codegen modules are defined here to avoid
duplication and ensure single-source-of-truth for configuration values.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from typing import ClassVar, Final

from flext_infra import t


class FlextInfraConstantsCodegen:
    """Namespace for all codegen-related constants."""

    EXCLUDED_PROJECTS: Final[frozenset[str]] = frozenset({"flexcore"})
    "Projects excluded from all codegen operations (Go/Python hybrid)."
    SRC_MODULES: Final[t.Infra.VariadicTuple[t.Infra.Quad[str, str, str, str]]] = (
        ("constants.py", "Constants", "FlextConstants", "Constants"),
        ("typings.py", "Types", "FlextTypes", "Type aliases"),
        ("protocols.py", "Protocols", "FlextProtocols", "Protocol definitions"),
        ("models.py", "Models", "FlextModels", "Domain models"),
        ("utilities.py", "Utilities", "FlextUtilities", "Utility functions"),
    )
    "Base module definitions for src/: (filename, class_suffix, base_class, docstring)."
    TESTS_MODULES: Final[t.Infra.VariadicTuple[t.Infra.Quad[str, str, str, str]]] = (
        ("constants.py", "Constants", "FlextTestsConstants", "Test constants"),
        ("typings.py", "Types", "TestsFlextTypes", "Test type aliases"),
        ("protocols.py", "Protocols", "TestsFlextProtocols", "Test protocols"),
        ("models.py", "Models", "TestsFlextModels", "Test models"),
        ("utilities.py", "Utilities", "TestsFlextUtilities", "Test utilities"),
    )
    "Base module definitions for tests/: (filename, class_suffix, base_class, docstring)."
    VIOLATION_PATTERN: Final[re.Pattern[str]] = re.compile(
        r"\[(?P<rule>NS-\d{3})-\d{3}\]\s+(?P<module>[^:]+):(?P<line>\d+)\s+\u2014\s+(?P<message>.+)",
    )
    "Regex to parse violation strings: [NS-00X-NNN] path:line — message."
    ALIAS_TO_SUFFIX: Final[t.StrMapping] = {
        "c": "Constants",
        "d": "Decorators",
        "e": "Exceptions",
        "h": "Handlers",
        "m": "Models",
        "p": "Protocols",
        "r": "Result",
        "s": "Service",
        "t": "Types",
        "u": "Utilities",
        "x": "Mixins",
    }
    "Single-letter alias → class suffix mapping for lazy-init generation."
    MAX_LINE_LENGTH: Final[int] = 88
    "Maximum line length for generated import lines."
    AUTOGEN_HEADER: Final[str] = "# AUTO-GENERATED FILE — Regenerate with: make gen"
    "Header prepended to every auto-generated ``__init__.py`` file."
    ALL_SCAN_PATTERNS: Final[t.StrSequence] = (
        "src/**/__init__.py",
        "tests/**/__init__.py",
        "examples/**/__init__.py",
        "scripts/**/__init__.py",
    )
    "Glob patterns for all directories the lazy-init generator scans."

    BARE_IMPORT_FROM_RE: Final[re.Pattern[str]] = re.compile(
        r"^from\s+import\s",
        re.MULTILINE,
    )
    "Regex: malformed ``from import`` statement (missing module name)."

    LINT_TOOLS: Final[tuple[tuple[str, tuple[str, ...]], ...]] = (
        ("ruff", ("ruff", "check", "{file}", "--no-fix", "--select", "E,F")),
        ("pyright", ("pyright", "{file}")),
        ("mypy", ("mypy", "{file}", "--no-error-summary")),
        ("pyrefly", ("pyrefly", "check", "{file}")),
    )
    "Lint tool names and their CLI command templates for validation."
    DEFAULT_EXCLUDE: Final[frozenset[str]] = frozenset({
        ".mypy_cache",
        "__pycache__",
    })
    "Directories excluded from codegen file scanning."
    INFRA_ONLY_EXPORTS: Final[frozenset[str]] = frozenset({
        "cleanup_submodule_namespace",
        "install_lazy_exports",
        "lazy_getattr",
        "logger",
        "merge_lazy_imports",
        "output",
        "output_reporting",
    })
    "Exports exclusive to flext-infra that should not bubble up."
    ROOT_WRAPPER_SEGMENTS: Final[frozenset[str]] = frozenset({
        "docs",
        "src",
        "tests",
        "examples",
        "scripts",
    })
    "Directory segments recognized as project-root wrapper paths."
    CORE_RUNTIME_ALIAS_TARGETS: Final[Mapping[str, t.Infra.StrPair]] = {
        "d": ("flext_core.decorators", "d"),
        "e": ("flext_core.exceptions", "e"),
        "h": ("flext_core.handlers", "h"),
        "r": ("flext_core.result", "r"),
        "s": ("flext_core.service", "s"),
        "x": ("flext_core.mixins", "x"),
    }
    "Mapping of single-letter aliases to flext-core runtime targets."

    class Detection:
        """Constants for constant detection and analysis."""

        MIN_QUOTED_LITERAL_LEN: Final[int] = 2
        "Minimum length for a quoted string to be considered a literal."
        TYPEVAR_ASSIGN_RE: Final[re.Pattern[str]] = re.compile(
            r"^(\w+)\s*=\s*(?:TypeVar|ParamSpec|TypeVarTuple)\s*\(",
            re.MULTILINE,
        )
        "Regex: TypeVar/ParamSpec/TypeVarTuple assignments."
        MIN_ATTRIBUTE_CHAIN: Final[int] = 2
        "Minimum dotted-chain length for direct constant references."
        MIN_DIRECT_REFERENCE_CHAIN: Final[int] = 2
        "Minimum chain length for FlextXxxConstants.ATTR references."
        TRIVIAL_VALUES: Final[frozenset[str]] = frozenset({
            "True",
            "False",
            "None",
            "0",
            "1",
            "2",
            "3",
            "4",
            "5",
            "-1",
            '""',
            "''",
            "[]",
            "{}",
            "()",
        })
        "Literal values considered trivial for constant detection heuristics."
        FINAL_DECL_RE: Final[re.Pattern[str]] = re.compile(
            r"^(?P<indent>\s*)(?P<name>[A-Z_][A-Z0-9_]*)"
            r"\s*:\s*(?P<ann>Final\[.*?\])\s*=\s*(?P<value>.+?)\s*(?:#.*)?$",
            re.MULTILINE,
        )
        "Regex: NAME: Final[TYPE] = VALUE (with optional inline comment)."
        CLASS_DECL_RE: Final[re.Pattern[str]] = re.compile(
            r"class\s+(\w+)",
        )
        "Regex: class ClassName (captures class name)."
        DIRECT_USAGE_RE: Final[re.Pattern[str]] = re.compile(
            r"\bFlext\w*Constants\.([A-Z_][A-Z0-9_]*)",
        )
        "Regex: FlextXxxConstants.CONSTANT_NAME (captures constant name)."
        ALIAS_USAGE_RE: Final[re.Pattern[str]] = re.compile(
            r"\bc\.\w*\.([A-Z_][A-Z0-9_]*)",
        )
        "Regex: c.Namespace.CONSTANT_NAME (captures constant name)."
        C_ALIAS_RE: Final[re.Pattern[str]] = re.compile(r"\bc\.([A-Za-z_]\w*)")
        "Regex: c.ATTR (captures ATTR after literal ``c.``)."
        DIRECT_REF_RE: Final[re.Pattern[str]] = re.compile(
            r"\b(Flext\w*Constants(?:\.[A-Za-z_]\w*)+)",
        )
        "Regex: FlextXxxConstants.ATTR.SUBATTR... (captures full dotted chain)."
        CANONICAL_ALIASES: Final[frozenset[str]] = frozenset({
            "c",
            "m",
            "p",
            "t",
            "u",
            "r",
            "e",
            "s",
            "d",
            "h",
            "x",
        })
        "Canonical single-letter runtime aliases."

    class Templates:
        """Jinja2 template file names for the lazy-init file generator.

        All templates live in ``flext_infra/templates/`` and are rendered
        via the shared Jinja2 ``Environment`` in
        ``FlextInfraCodegenGeneration``.
        """

        PREAMBLE_STANDARD: Final[str] = "lazy_init_preamble_standard.py.j2"
        "Standard module preamble (future annotations + TYPE_CHECKING + lazy helpers)."

        PREAMBLE_L0: Final[str] = "lazy_init_preamble_l0.py.j2"
        "L0 typings preamble (inline lazy to break circular import chain)."

        BODY: Final[str] = "lazy_init_body.py.j2"
        "Middle section: TYPE_CHECKING block, _LAZY_IMPORTS dict, __all__ list."

        GETATTR_STANDARD: Final[str] = "lazy_init_getattr_standard.py.j2"
        "Standard PEP 562 __getattr__ + __dir__ + cleanup (with _LAZY_CACHE)."

        GETATTR_L0: Final[str] = "lazy_init_getattr_l0.py.j2"
        "L0-typings __getattr__ + __dir__ + namespace-cleanup."

    class Pipeline:
        """Codegen pipeline stage and configuration constants."""

        STAGE_DISCOVER: Final[str] = "discover"
        STAGE_PY_TYPED: Final[str] = "py_typed"
        STAGE_CENSUS_BEFORE: Final[str] = "census_before"
        STAGE_SCAFFOLD: Final[str] = "scaffold"
        STAGE_AUTO_FIX: Final[str] = "auto_fix"
        STAGE_LAZY_INIT: Final[str] = "lazy_init"
        STAGE_CENSUS_AFTER: Final[str] = "census_after"

        STAGE_ORDER: ClassVar[Sequence[str]] = (
            STAGE_DISCOVER,
            STAGE_PY_TYPED,
            STAGE_CENSUS_BEFORE,
            STAGE_SCAFFOLD,
            STAGE_AUTO_FIX,
            STAGE_LAZY_INIT,
            STAGE_CENSUS_AFTER,
        )

        KEY_DRY_RUN: Final[str] = "dry_run"

    class QualityGate:
        """Constants used by constants quality gate analysis/reporting."""

        REPORT_DIR: Final[str] = ".reports/codegen/constants-quality-gate"
        RULE_KEYS: Final[t.StrSequence] = (
            "NS-000",
            "NS-001",
            "NS-002",
            "NS-003",
            "NS-004",
            "NS-005",
        )
        CHECK_NAMESPACE_COMPLIANCE: Final[str] = "namespace_compliance"
        CHECK_MRO_VALIDITY: Final[str] = "mro_validity"
        CHECK_IMPORT_RESOLUTION: Final[str] = "import_resolution"
        CHECK_LAYER_COMPLIANCE: Final[str] = "layer_compliance"
        CHECK_DUPLICATION_REDUCTION: Final[str] = "duplication_reduction"
        CHECK_TYPE_SAFETY: Final[str] = "type_safety"
        CHECK_LINT_CLEAN: Final[str] = "lint_clean"


__all__ = ["FlextInfraConstantsCodegen"]
