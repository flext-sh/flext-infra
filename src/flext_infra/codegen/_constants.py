"""Centralized constants for the codegen package.

All constants used across codegen modules are defined here to avoid
duplication and ensure single-source-of-truth for configuration values.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import re
from typing import Final


class FlextInfraCodegenConstants:
    """Namespace for all codegen-related constants."""

    EXCLUDED_PROJECTS: Final[frozenset[str]] = frozenset({"flexcore"})
    "Projects excluded from all codegen operations (Go/Python hybrid)."
    TYPEVAR_CALLABLES: Final[frozenset[str]] = frozenset({
        "TypeVar",
        "ParamSpec",
        "TypeVarTuple",
    })
    "Callable names that create type variables (for standalone detection)."
    SRC_MODULES: Final[tuple[tuple[str, str, str, str], ...]] = (
        ("constants.py", "Constants", "FlextConstants", "Constants"),
        ("typings.py", "Types", "FlextTypes", "Type aliases"),
        ("protocols.py", "Protocols", "FlextProtocols", "Protocol definitions"),
        ("models.py", "Models", "FlextModels", "Domain models"),
        ("utilities.py", "Utilities", "FlextUtilities", "Utility functions"),
    )
    "Base module definitions for src/: (filename, class_suffix, base_class, docstring)."
    TESTS_MODULES: Final[tuple[tuple[str, str, str, str], ...]] = (
        ("constants.py", "Constants", "FlextTestsConstants", "Test constants"),
        ("typings.py", "Types", "FlextTestsTypes", "Test type aliases"),
        ("protocols.py", "Protocols", "FlextTestsProtocols", "Test protocols"),
        ("models.py", "Models", "FlextTestsModels", "Test models"),
        ("utilities.py", "Utilities", "FlextTestsUtilities", "Test utilities"),
    )
    "Base module definitions for tests/: (filename, class_suffix, base_class, docstring)."
    VIOLATION_PATTERN: Final[re.Pattern[str]] = re.compile(
        r"\[(?P<rule>NS-\d{3})-\d{3}\]\s+(?P<module>[^:]+):(?P<line>\d+)\s+\u2014\s+(?P<message>.+)",
    )
    "Regex to parse violation strings: [NS-00X-NNN] path:line — message."
    ALIAS_TO_SUFFIX: Final[dict[str, str]] = {
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
    SKIP_MODULES: Final[frozenset[str]] = frozenset({
        "__future__",
        "typing",
        "collections.abc",
        "abc",
    })
    "Modules to skip when deriving lazy import mappings."
    SKIP_STDLIB: Final[frozenset[str]] = frozenset({
        "sys",
        "importlib",
        "typing",
        "collections",
        "abc",
    })
    "Stdlib modules to skip in lazy-init import derivation."
    MAX_LINE_LENGTH: Final[int] = 88
    "Maximum line length for generated import lines."
    AUTOGEN_HEADER: Final[str] = (
        "# AUTO-GENERATED FILE — DO NOT EDIT MANUALLY.\n"
        "# Regenerate with: make codegen\n"
        "#"
    )
    "Header prepended to every auto-generated ``__init__.py`` file."
    ALL_SCAN_PATTERNS: Final[tuple[str, ...]] = (
        "src/**/__init__.py",
        "tests/**/__init__.py",
        "examples/**/__init__.py",
        "scripts/**/__init__.py",
    )
    "Glob patterns for all directories the lazy-init generator scans."

    class Templates:
        """Generated Python code snippets used by the lazy-init file generator."""

        FUTURE_ANNOTATIONS: Final[str] = "from __future__ import annotations"
        "``from __future__ import annotations`` header line."

        TYPE_CHECKING_IMPORT: Final[str] = "from typing import TYPE_CHECKING"
        "Runtime TYPE_CHECKING guard import."

        TYPE_CHECKING_GUARD: Final[str] = "if TYPE_CHECKING:"
        "Opening line of the TYPE_CHECKING block."

        FLEXT_TYPES_IMPORT: Final[str] = (
            "    from flext_core.typings import FlextTypes"
        )
        "TYPE_CHECKING import for FlextTypes (indented)."

        LAZY_IMPORT: Final[str] = (
            "from flext_core.lazy import cleanup_submodule_namespace, lazy_getattr"
        )
        "Eager import of the lazy-loading helpers from flext_core."

        CLEANUP_CALL: Final[str] = (
            "cleanup_submodule_namespace(__name__, _LAZY_IMPORTS)"
        )
        "Module-level call that strips submodule names from namespace."

        LAZY_IMPORTS_DECL: Final[str] = "_LAZY_IMPORTS: dict[str, tuple[str, str]] = {"
        "Opening line of the ``_LAZY_IMPORTS`` dict literal."

        LAZY_CACHE_DECL: Final[str] = "_LAZY_CACHE: dict[str, object] = {}"
        "Module-level persistent cache for resolved lazy imports."

        ALL_DECL: Final[str] = "__all__ = ["
        "Opening line of the ``__all__`` list literal."

        L0_OVERRIDE_COMMENT: Final[str] = (
            "# L0-OVERRIDE — inline lazy to avoid circular:"
            " _typings -> _utilities.lazy -> typings -> _typings"
        )
        "Comment explaining why the L0 typings package uses a custom __getattr__."

        L0_IMPORT_IMPORTLIB: Final[str] = "import importlib"
        "stdlib importlib import required by the L0 __getattr__ implementation."

        L0_IMPORT_SYS: Final[str] = "import sys"
        "stdlib sys import required by the L0 namespace-cleanup block."

        # --- multi-line generated blocks (used as list[str]) ---

        GETATTR_STANDARD: Final[tuple[str, ...]] = (
            "_LAZY_CACHE: dict[str, object] = {}",
            "",
            "",
            "def __getattr__(name: str) -> FlextTypes.ModuleExport:",
            '    """Lazy-load module attributes on first access (PEP 562).',
            "",
            "    A local cache ``_LAZY_CACHE`` persists resolved objects across repeated",
            "    accesses during process lifetime.",
            "",
            "    Args:",
            "        name: Attribute name requested by dir()/import.",
            "",
            "    Returns:",
            "        Lazy-loaded module export type.",
            "",
            "    Raises:",
            "        AttributeError: If attribute not registered.",
            '    """',
            "    if name in _LAZY_CACHE:",
            "        return _LAZY_CACHE[name]",
            "",
            "    value = lazy_getattr(name, _LAZY_IMPORTS, globals(), __name__)",
            "    _LAZY_CACHE[name] = value",
            "    return value",
            "",
            "",
            "def __dir__() -> list[str]:",
            '    """Return list of available attributes for dir() and autocomplete.',
            "",
            "    Returns:",
            "        List of public names from module exports.",
            '    """',
            "    return sorted(__all__)",
            "",
            "",
            "cleanup_submodule_namespace(__name__, _LAZY_IMPORTS)",
        )
        "Standard PEP 562 __getattr__ + __dir__ block lines (with _LAZY_CACHE)."

        GETATTR_L0: Final[tuple[str, ...]] = (
            "def __getattr__(name: str) -> type:",
            "    if name in _LAZY_IMPORTS:",
            "        module_path, attr_name = _LAZY_IMPORTS[name]",
            "        module = importlib.import_module(module_path)",
            "        value = getattr(module, attr_name)",
            "        globals()[name] = value",
            "        return value",
            '    msg = f"module {__name__!r} has no attribute {name!r}"',
            "    raise AttributeError(msg)",
            "",
            "",
            "def __dir__() -> list[str]:",
            "    return sorted(__all__)",
            "",
            "",
            "_current = sys.modules.get(__name__)",
            "if _current is not None:",
            '    _parts = __name__.split(".")',
            "    for _mod_path, _ in _LAZY_IMPORTS.values():",
            "        if _mod_path:",
            '            _mp = _mod_path.split(".")',
            "            if len(_mp) > len(_parts) and _mp[: len(_parts)] == _parts:",
            "                _sub = getattr(_current, _mp[len(_parts)], None)",
            "                if _sub is not None and isinstance(_sub, type(sys)):",
            "                    delattr(_current, _mp[len(_parts)])",
        )
        "L0-typings __getattr__ + __dir__ + namespace-cleanup block lines."

    class QualityGate:
        """Constants used by constants quality gate analysis/reporting."""

        REPORT_DIR: Final[str] = ".reports/codegen/constants-quality-gate"
        PASS_VERDICTS: Final[tuple[str, ...]] = ("PASS", "CONDITIONAL_PASS")
        RULE_KEYS: Final[tuple[str, ...]] = (
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
        CHECK_BASELINE_LOAD: Final[str] = "baseline_load"
