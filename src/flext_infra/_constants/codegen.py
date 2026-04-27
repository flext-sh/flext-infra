"""Centralized constants for the codegen package.

All constants used across codegen modules are defined here to avoid
duplication and ensure single-source-of-truth for configuration values.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import re
from collections.abc import (
    Mapping,
)
from enum import StrEnum, unique
from types import MappingProxyType
from typing import TYPE_CHECKING, Final

if TYPE_CHECKING:
    from flext_infra import t


class FlextInfraConstantsCodegen:
    """Namespace for all codegen-related constants."""

    EXCLUDED_PROJECTS: Final[frozenset[str]] = frozenset({"flexcore"})
    "Projects excluded from all codegen operations (Go/Python hybrid)."
    SRC_MODULES: Final[t.VariadicTuple[t.Quad[str, str, str, str]]] = (
        ("constants.py", "Constants", "FlextConstants", "Constants"),
        ("typings.py", "Types", "FlextTypes", "Type aliases"),
        ("protocols.py", "Protocols", "FlextProtocols", "Protocol definitions"),
        ("models.py", "Models", "FlextModels", "Domain models"),
        ("utilities.py", "Utilities", "FlextUtilities", "Utility functions"),
    )
    "Base module definitions for src/: (filename, class_suffix, base_class, docstring)."
    TESTS_MODULES: Final[t.VariadicTuple[t.Quad[str, str, str, str]]] = (
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
    LOCAL_INFERRED_SEGMENTS: Final[frozenset[str]] = frozenset({
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
    INFRA_ONLY_EXPORTS: Final[frozenset[str]] = frozenset({
        "cleanup_submodule_namespace",
        "install_lazy_exports",
        "lazy_getattr",
        "logger",
        "merge_lazy_imports",
        "output",
        "output_reporting",
        "pytest_addoption",
        "pytest_collect_file",
        "pytest_collection_modifyitems",
        "pytest_configure",
        "pytest_runtest_setup",
        "pytest_runtest_teardown",
        "pytest_sessionfinish",
        "pytest_sessionstart",
        "pytest_terminal_summary",
        "pytest_warning_recorded",
    })
    "Exports excluded from package __init__.py auto-export — pytest hooks live per-module via pytest plugin entry-points and infra-only utilities never bubble up."
    ROOT_WRAPPER_SEGMENTS: Final[frozenset[str]] = frozenset({
        "docs",
        "src",
        "tests",
        "examples",
        "scripts",
    })
    "Directory segments recognized as project-root wrapper paths."
    DUPLICATE_CLASS_MIN_LEN: Final[int] = 8
    "Minimum class-name length for workspace-wide duplicate detection."
    CORE_RUNTIME_ALIAS_TARGETS: Final[Mapping[str, t.Infra.StrPair]] = (
        MappingProxyType({
            "d": ("flext_core", "d"),
            "e": ("flext_core", "e"),
            "h": ("flext_core", "h"),
            "r": ("flext_core", "r"),
            "s": ("flext_core", "s"),
            "x": ("flext_core", "x"),
        })
    )
    "Mapping of single-letter aliases to flext-core runtime targets."

    # --- Constant detection constants (was: class Detection) ---
    DETECTION_MIN_QUOTED_LITERAL_LEN: Final[int] = 2
    "Minimum length for a quoted string to be considered a literal."
    DETECTION_TYPEVAR_ASSIGN_RE: Final[re.Pattern[str]] = re.compile(
        r"^(\w+)\s*=\s*(?:TypeVar|ParamSpec|TypeVarTuple)\s*\(",
        re.MULTILINE,
    )
    "Regex: TypeVar/ParamSpec/TypeVarTuple assignments."
    DETECTION_MIN_ATTRIBUTE_CHAIN: Final[int] = 2
    "Minimum dotted-chain length for direct constant references."
    DETECTION_MIN_DIRECT_REFERENCE_CHAIN: Final[int] = 2
    "Minimum chain length for FlextXxxConstants.ATTR references."
    DETECTION_TRIVIAL_VALUES: Final[frozenset[str]] = frozenset({
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
    DETECTION_FINAL_DECL_RE: Final[re.Pattern[str]] = re.compile(
        r"^(?P<indent>\s*)(?P<name>[A-Z_][A-Z0-9_]*)"
        r"\s*:\s*(?P<ann>Final\[.*?\])\s*=\s*(?P<value>.+?)\s*(?:#.*)?$",
        re.MULTILINE,
    )
    "Regex: NAME: Final[TYPE] = VALUE (with optional inline comment)."
    DETECTION_CLASS_DECL_RE: Final[re.Pattern[str]] = re.compile(
        r"class\s+(\w+)",
    )
    "Regex: class ClassName (captures class name)."
    DETECTION_DIRECT_USAGE_RE: Final[re.Pattern[str]] = re.compile(
        r"\bFlext\w*Constants\.([A-Z_][A-Z0-9_]*)",
    )
    "Regex: FlextXxxConstants.CONSTANT_NAME (captures constant name)."
    DETECTION_ALIAS_USAGE_RE: Final[re.Pattern[str]] = re.compile(
        r"\bc\.\w*\.([A-Z_][A-Z0-9_]*)",
    )
    "Regex: c.Namespace.CONSTANT_NAME (captures constant name)."
    DETECTION_C_ALIAS_RE: Final[re.Pattern[str]] = re.compile(r"\bc\.([A-Za-z_]\w*)")
    "Regex: c.ATTR (captures ATTR after literal ``c.``)."
    DETECTION_DIRECT_REF_RE: Final[re.Pattern[str]] = re.compile(
        r"\b(Flext\w*Constants(?:\.[A-Za-z_]\w*)+)",
    )
    "Regex: FlextXxxConstants.ATTR.SUBATTR... (captures full dotted chain)."
    DETECTION_CANONICAL_ALIASES: Final[frozenset[str]] = frozenset({
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

    # --- Template file names (was: class Templates) ---
    TEMPLATE_PREAMBLE_STANDARD: Final[str] = "lazy_init_preamble_standard.py.j2"
    "Standard module preamble (future annotations + TYPE_CHECKING + lazy helpers)."
    TEMPLATE_PREAMBLE_L0: Final[str] = "lazy_init_preamble_l0.py.j2"
    "L0 typings preamble (inline lazy to break circular import chain)."
    TEMPLATE_BODY: Final[str] = "lazy_init_body.py.j2"
    "Middle section: TYPE_CHECKING block, _LAZY_IMPORTS dict, __all__ list."
    TEMPLATE_GETATTR_STANDARD: Final[str] = "lazy_init_getattr_standard.py.j2"
    "Standard PEP 562 __getattr__ + __dir__ + cleanup (with _LAZY_CACHE)."
    TEMPLATE_GETATTR_L0: Final[str] = "lazy_init_getattr_l0.py.j2"
    "L0-typings __getattr__ + __dir__ + namespace-cleanup."
    TEMPLATE_VERSION_FILE: Final[str] = "version_file.py.j2"
    "Per-project ``__version__.py`` (inherits ``FlextVersion``)."
    TEMPLATE_MKDOCS_PROJECT: Final[str] = "mkdocs_project.yml.j2"
    "Per-project ``mkdocs.yml`` (Material theme + mkdocstrings + validation)."
    TEMPLATE_MKDOCS_ROOT: Final[str] = "mkdocs_root.yml.j2"
    "Workspace-root ``mkdocs.yml`` (Material theme + nav)."

    # --- Pipeline stage StrEnum (was: class Pipeline plain strings) ---
    @unique
    class PipelineStage(StrEnum):
        """Canonical codegen pipeline stage identifiers."""

        DISCOVER = "discover"
        PY_TYPED = "py_typed"
        CENSUS_BEFORE = "census_before"
        SCAFFOLD = "scaffold"
        AUTO_FIX = "auto_fix"
        LAZY_INIT = "lazy_init"
        CENSUS_AFTER = "census_after"

    PIPELINE_STAGE_ORDER: Final[tuple[PipelineStage, ...]] = (
        PipelineStage.DISCOVER,
        PipelineStage.PY_TYPED,
        PipelineStage.CENSUS_BEFORE,
        PipelineStage.SCAFFOLD,
        PipelineStage.AUTO_FIX,
        PipelineStage.LAZY_INIT,
        PipelineStage.CENSUS_AFTER,
    )
    "Ordered sequence of pipeline stage identifiers."
    PIPELINE_KEY_DRY_RUN: Final[str] = "dry_run"
    "Config key for pipeline dry-run mode."

    # --- Quality gate constants (was: class QualityGate) ---
    QG_REPORT_DIR: Final[str] = ".reports/codegen/constants-quality-gate"
    "Report directory for constants quality gate."
    QG_RULE_KEYS: Final[tuple[str, ...]] = (
        "NS-000",
        "NS-001",
        "NS-002",
        "NS-003",
        "NS-004",
        "NS-005",
    )
    "Canonical rule key identifiers for quality gate reporting."
    QG_CHECK_NAMESPACE_COMPLIANCE: Final[str] = "namespace_compliance"
    QG_CHECK_MRO_VALIDITY: Final[str] = "mro_validity"
    QG_CHECK_IMPORT_RESOLUTION: Final[str] = "import_resolution"
    QG_CHECK_LAYER_COMPLIANCE: Final[str] = "layer_compliance"
    QG_CHECK_DUPLICATION_REDUCTION: Final[str] = "duplication_reduction"
    QG_CHECK_TYPE_SAFETY: Final[str] = "type_safety"
    QG_CHECK_LINT_CLEAN: Final[str] = "lint_clean"


__all__: list[str] = ["FlextInfraConstantsCodegen"]
