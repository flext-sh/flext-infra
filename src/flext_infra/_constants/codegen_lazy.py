"""Lazy-init constants for the codegen package."""

from __future__ import annotations

import re
from types import MappingProxyType
from typing import TYPE_CHECKING, Final

if TYPE_CHECKING:
    from flext_infra import t


class FlextInfraConstantsCodegenLazy:
    """Lazy-init and export-policy constants for codegen."""

    MAX_LINE_LENGTH: Final[int] = 88
    "Maximum line length for generated import lines."
    AUTOGEN_HEADER: Final[str] = "# AUTO-GENERATED FILE — Regenerate with: make gen"
    "Header prepended to every auto-generated ``__init__.py`` file."
    ROOT_EXPORTS_FILENAME: Final[str] = "_exports.py"
    "Root public ABI contract module consumed by lazy-init planning."
    ROOT_EXPORTS_DIR: Final[str] = "_constants"
    "Directory under each package where lazy-init registries must live."
    INIT_PY: Final[str] = "__init__.py"
    "Standard Python package initializer filename."
    INIT_PYI: Final[str] = "__init__.pyi"
    "Typing stub paired with generated thin package initializers."
    STUB_STRING_LITERAL_LIMIT: Final[int] = 50
    "Maximum string-literal length accepted by Ruff for ``.pyi`` files."
    ROOT_PUBLIC_EXPORTS_SUFFIX: Final[str] = "_PUBLIC_EXPORTS"
    "Suffix for tuple constants that declare frozen public root exports."
    LAZY_REGISTRY_PART_SIZE: Final[int] = 32
    "Maximum lazy import entry groups emitted per generated registry part."
    ALL_SCAN_PATTERNS: Final[t.StrSequence] = (
        "src/**/__init__.py",
        "tests/**/__init__.py",
        "examples/**/__init__.py",
        "scripts/**/__init__.py",
    )
    "Glob patterns for all directories the lazy-init generator scans."
    NON_PUBLIC_LAZY_ROOTS: Final[frozenset[str]] = frozenset({
        "examples",
        "scripts",
        "tests",
    })
    "Root import surfaces generated as private lazy plumbing, not public ABI."

    BARE_IMPORT_FROM_RE: Final[t.RegexPattern] = re.compile(
        r"^from\s+import\s",
        re.MULTILINE,
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
    PUBLIC_ROOT_INTERNAL_CHILD_PACKAGES: Final[frozenset[str]] = frozenset({
        "_constants",
        "_models",
        "_protocols",
        "_typings",
        "_utilities",
        "basemk",
        "check",
        "codegen",
        "deps",
        "detectors",
        "docs",
        "gates",
        "maintenance",
        "refactor",
        "release",
        "transformers",
        "validate",
        "workspace",
    })
    "Child packages whose implementation exports do not bubble into root APIs."
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
    "Public-module symbols withheld from generated root-facade __all__."
    PUBLIC_ROOT_ALIAS_ORDER: Final[t.StrSequence] = (
        "c",
        "d",
        "e",
        "h",
        "infra",
        "m",
        "main",
        "p",
        "r",
        "s",
        "t",
        "u",
        "x",
    )
    "Canonical order for public root aliases and operational entry points."
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
