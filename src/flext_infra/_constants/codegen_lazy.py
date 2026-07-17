"""Lazy-init constants for the codegen package.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import re
from types import MappingProxyType
from typing import TYPE_CHECKING, Final

if TYPE_CHECKING:
    from flext_infra import t


class FlextInfraConstantsCodegenLazy:
    """Lazy-init and export-policy constants for codegen."""

    # NOTE (multi-agent, mro-wkii.17.26.2 / agent: codex): generated width is
    # runtime tooling policy, owned only by config.Infra.tooling.tools.ruff.
    AUTOGEN_HEADER: Final[str] = "# AUTO-GENERATED FILE — Regenerate with: make gen"
    "Header prepended to every auto-generated ``__init__.py`` file."
    ROOT_EXPORTS_FILENAME: Final[str] = "_exports.py"
    "Root public ABI contract module consumed by lazy-init planning."
    ROOT_EXPORTS_DIR: Final[str] = "_constants"
    "Directory under each package where lazy-init registries must live."
    GENERATED_EXPORT_SIDECAR_RE: Final[t.RegexPattern] = re.compile(
        r"^(?:_exports(?:_lazy(?:_part_[0-9]+)?)?|_lazy_exports)\.py$"
    )
    "Regex matching every generated lazy-export sidecar filename "
    "(``_exports.py``, ``_exports_lazy.py``, ``_exports_lazy_part_N.py``, "
    "``_lazy_exports.py``); these reserved names are superseded by the inline "
    "``__init__.py`` lazy map — excluded from lazy-init discovery and swept by cleanup."
    # mro-pulj (codex): these parallel root registries are superseded atomically
    # by the inline map and must never participate in source discovery.
    OBSOLETE_ROOT_SUPPORT_NAMES: Final[frozenset[str]] = frozenset({
        "_root_exports",
        "_root_exports_parts",
        "_root_typing",
        "_root_typing_parts",
    })
    "Closed set of retired root registry module and package names."
    INIT_PY: Final[str] = "__init__.py"
    "Standard Python package initializer filename."
    # mro-wkii.17.26 (codex): cleanup owns every retired generated init artifact.
    OBSOLETE_GENERATED_INIT_FILES: Final[t.StrSequence] = (
        "__init__.pyi",
        "__unit__.py",
    )
    "Generated initializer artifacts removed during every codegen pass."
    INIT_PYI: Final[str] = "__init__.pyi"
    "Forbidden legacy initializer stub name retained only for violation detection."
    PYTEST_PLUGINS_ASSIGNMENT: Final[str] = "pytest_plugins"
    "Declarative Pytest plugin registry consumed by generated initializers."
    ROOT_PUBLIC_EXPORTS_SUFFIX: Final[str] = "_PUBLIC_EXPORTS"
    "Suffix for tuple constants that declare frozen public root exports."
    ALL_SCAN_PATTERNS: Final[t.StrSequence] = (
        "src/**/__init__.py",
        "tests/**/__init__.py",
        "examples/**/__init__.py",
        "scripts/**/__init__.py",
    )
    "Glob patterns for all directories the lazy-init generator scans."
    BARE_IMPORT_FROM_RE: Final[t.RegexPattern] = re.compile(
        r"^from\s+import\s", re.MULTILINE
    )
    "Regex: malformed ``from import`` statement (missing module name)."

    LINT_TOOLS: Final[t.StrSequencePairTuple] = (
        ("ruff", ("ruff", "check", "{file}", "--no-fix", "--select", "E,F")),
        ("pyright", ("pyright", "{file}")),
        ("mypy", ("mypy", "{file}", "--no-error-summary")),
        ("pyrefly", ("pyrefly", "check", "{file}")),
    )
    "Lint tool names and their CLI command templates for validation."
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
    PUBLIC_ROOT_MODULE_EXPORTS: Final[frozenset[str]] = frozenset({"basemk"})
    "Internal child packages exported at the root as module objects only."
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
    "Exports excluded from package __init__.py auto-export."
    PUBLISHED_ALL_EXCLUDE: Final[frozenset[str]] = frozenset({
        "build_lazy_import_map",
        "lazy",
        "normalize_lazy_imports",
    })
    # mro-pulj (codex): these remain direct inline lazy imports without
    # widening the explicit wildcard contract or requiring root sidecars.
    "Public-module symbols withheld from generated root-facade __all__."
    PUBLIC_ROOT_ALIAS_ORDER: Final[t.StrSequence] = (
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
    # mro-wkii.17 (Codex): static analyzers bind local facade classes, not rebinds.
    PUBLIC_ROOT_TYPING_FACADE_SUFFIXES: Final[t.MappingKV[str, str]] = (
        MappingProxyType({
            "c": "Constants",
            "t": "Types",
            "p": "Protocols",
            "m": "Models",
            "u": "Utilities",
            "s": "ServiceBase",
        })
    )
    "Named local facade suffixes used by generated TYPE_CHECKING aliases."
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
    TEST_RUNTIME_ALIAS_TARGETS: Final[t.MappingKV[str, t.StrPair]] = MappingProxyType({
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
        "tv": ("flext_tests", "tv"),
        "u": ("flext_tests", "u"),
        "x": ("flext_tests", "x"),
    })
    "Mapping of test-only aliases to flext-tests runtime targets."


__all__: list[str] = ["FlextInfraConstantsCodegenLazy"]
