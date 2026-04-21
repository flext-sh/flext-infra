"""Constants namespace for flext_infra.refactor."""

from __future__ import annotations

import re
from collections.abc import (
    Mapping,
    Sequence,
)
from enum import StrEnum, unique
from pathlib import Path
from types import MappingProxyType
from typing import Final

from flext_core import c


class FlextInfraConstantsRefactor:
    """Shared constants for refactor engine modules."""

    RUNTIME_ALIAS_NAMES: Final[frozenset[str]] = c.RUNTIME_ALIAS_NAMES
    NAMESPACE_SOURCE_UNIVERSAL_ALIASES: Final[frozenset[str]] = frozenset(
        c.UNIVERSAL_ALIAS_PARENT_SOURCES
    )

    LEGACY_FIX_ACTIONS: Final[frozenset[str]] = frozenset({
        "remove",
        "inline_and_remove",
        "remove_and_update_refs",
        "keep_try_only",
    })
    IMPORT_FIX_ACTIONS: Final[frozenset[str]] = frozenset({
        "replace_with_alias",
        "hoist_to_module_top",
    })
    CLASS_FIX_ACTIONS: Final[frozenset[str]] = frozenset({"reorder_methods"})
    MRO_FIX_ACTIONS: Final[frozenset[str]] = frozenset({
        "remove_inheritance_keep_class",
        "fix_mro_redeclaration",
        "migrate_to_class_mro",
    })
    PROPAGATION_FIX_ACTIONS: Final[frozenset[str]] = frozenset({
        "propagate_symbol_renames",
        "rename_imported_symbols",
        "propagate_signature_migrations",
    })
    PATTERN_FIX_ACTIONS: Final[frozenset[str]] = frozenset({
        "convert_dict_to_mapping_annotations",
        "remove_redundant_casts",
        "fix_silent_failure_sentinels",
    })
    TYPE_ALIAS_FIX_ACTIONS: Final[frozenset[str]] = frozenset({"unify_typings"})
    TYPING_FIX_ACTIONS: Final[frozenset[str]] = frozenset({
        "replace_object_annotations",
        "remove_unused_models",
    })
    TIER0_FIX_ACTIONS: Final[frozenset[str]] = frozenset({"fix_tier0_imports"})
    FUTURE_FIX_ACTIONS: Final[frozenset[str]] = frozenset({
        "ensure_future_annotations",
    })
    TYPING_DEFINITION_FILES: Final[frozenset[str]] = frozenset({
        "typings.py",
        "_typings",
        "protocols.py",
        "_protocols",
    })
    TYPING_INLINE_UNION_CANONICAL_MAP: Final[Mapping[frozenset[str], str]] = (
        MappingProxyType({
            frozenset({"str", "int", "float", "bool"}): "t.Primitives",
            frozenset({"int", "float"}): "t.Numeric",
            frozenset({"str", "int", "float", "bool", "datetime"}): "t.Scalar",
            frozenset({
                "str",
                "int",
                "float",
                "bool",
                "datetime",
                "Path",
            }): "t.Container",
        })
    )
    FUTURE_CHECKS: Final[frozenset[str]] = frozenset({"missing_future_import"})
    MRO_TARGETS: Final[frozenset[str]] = frozenset({
        "constants",
        "typings",
        "protocols",
        "models",
        "utilities",
        "all",
    })
    "Accepted target arguments for MRO migration runs."
    MRO_SCAN_DIRECTORIES: Final[tuple[str, ...]] = c.SCAN_DIRECTORIES
    "Directories scanned for constants modules in each project."
    MRO_CONSTANTS_FILE_NAMES: Final[frozenset[str]] = frozenset({
        "constants.py",
        "_constants.py",
    })
    "Canonical constants module file names."
    MRO_CONSTANTS_DIRECTORY: Final[str] = "constants"
    "Canonical constants package directory name."
    MRO_TYPINGS_FILE_NAMES: Final[frozenset[str]] = frozenset({
        "typings.py",
        "_typings.py",
    })
    "Canonical typings module file names."
    MRO_TYPINGS_DIRECTORY: Final[str] = "typings"
    "Canonical typings package directory name."
    MRO_PROTOCOLS_FILE_NAMES: Final[frozenset[str]] = frozenset({
        "protocols.py",
        "_protocols.py",
    })
    "Canonical protocols module file names."
    MRO_PROTOCOLS_DIRECTORY: Final[str] = "protocols"
    "Canonical protocols package directory name."
    MRO_MODELS_FILE_NAMES: Final[frozenset[str]] = frozenset({
        "models.py",
        "_models.py",
    })
    "Canonical models module file names."
    MRO_MODELS_DIRECTORY: Final[str] = "models"
    "Canonical models package directory name."
    MRO_UTILITIES_FILE_NAMES: Final[frozenset[str]] = frozenset({
        "utilities.py",
        "_utilities.py",
    })
    "Canonical utilities module file names."
    MRO_UTILITIES_DIRECTORY: Final[str] = "utilities"
    "Canonical utilities package directory name."

    DEFAULT_CONSTANTS_CLASS: Final[str] = "FlextConstants"
    "Fallback constants class name when none exists in module."
    CONSTANTS_CLASS_SUFFIX: Final[str] = "Constants"
    "Class-name suffix used to identify constants facades."
    CONSTANT_PATTERN: Final[re.Pattern[str]] = re.compile(r"^_*[A-Z][A-Z0-9_]*$")
    "Compiled naming pattern for module-level constant candidates."
    FAMILY_SUFFIXES: Final[Mapping[str, str]] = MappingProxyType({
        "c": "Constants",
        "t": "Types",
        "p": "Protocols",
        "m": "Models",
        "u": "Utilities",
    })
    "Facade family letter → class suffix mapping."
    FAMILY_DIRECTORIES: Final[Mapping[str, str]] = MappingProxyType({
        "c": "_constants",
        "t": "_typings",
        "p": "_protocols",
        "m": "_models",
        "u": "_utilities",
    })
    "Facade family letter → subdirectory name mapping."
    FAMILY_FILES: Final[Mapping[str, str]] = MappingProxyType({
        "c": "*constants.py",
        "t": "*typings.py",
        "p": "*protocols.py",
        "m": "*models.py",
        "u": "*utilities.py",
    })
    "Facade family letter → file glob mapping."
    MRO_FAMILIES: Final[frozenset[str]] = frozenset({"c", "t", "p", "m", "u"})
    "All MRO families."
    MRO_FAMILY_PACKAGE_DIRS: Final[Mapping[str, str]] = MappingProxyType({
        "c": "flext_core/constants.py",
        "t": "flext_core/typings.py",
        "p": "flext_core/protocols.py",
        "m": "flext_core/_models",
        "u": "flext_core/_utilities",
    })
    "Family letter → relative package dir/file."
    MRO_FAMILY_FACADE_MODULES: Final[Mapping[str, str]] = MappingProxyType({
        "c": "flext_core/constants.py",
        "t": "flext_core/typings.py",
        "p": "flext_core/protocols.py",
        "m": "flext_core/models.py",
        "u": "flext_core/utilities.py",
    })
    "Family letter → facade module path."
    DOMAIN_PACKAGES: Final[frozenset[str]] = frozenset({
        "flext-ldap",
        "flext-ldif",
        "flext-db-oracle",
        "flext-oracle-wms",
        "flext-oracle-oic",
    })
    "Known domain-layer packages."
    PLATFORM_PACKAGES: Final[frozenset[str]] = frozenset({
        "flext-cli",
        "flext-meltano",
        "flext-api",
        "flext-auth",
        "flext-web",
        "flext-grpc",
    })
    "Known platform-layer packages."
    INTEGRATION_CLASS_PREFIXES: Final[tuple[str, ...]] = (
        "FlextTap",
        "FlextTarget",
        "FlextDbt",
    )
    "Class name prefixes that identify integration projects."
    CONFIDENCE_TO_SCORE: Final[Mapping[str, float]] = MappingProxyType({
        "high": 0.95,
        "medium": 0.75,
        "low": 0.55,
    })
    "Confidence level → numeric score mapping for violations."
    CONFIDENCE_RANKS: Final[Mapping[str, int]] = MappingProxyType({
        "low": 0,
        "medium": 1,
        "high": 2,
    })
    "Confidence level → priority rank mapping."
    REQUIRED_CLASS_TARGETS: Final[Sequence[str]] = (
        "TimeoutEnforcer",
        "CircuitBreakerManager",
    )
    "Class names always required in scanner output."
    CLASS_PATTERN: Final[re.Pattern[str]] = re.compile(r"[^A-Za-z0-9]+")
    "Pattern to split class name fragments."
    MAPPINGS_RELATIVE_PATH: Final[Path] = Path("rules") / "class-nesting-mappings.yml"
    "Relative path from the refactor package to the nesting mappings YAML."
    MODEL_TOKENS: Final[Sequence[str]] = (
        "model",
        "schema",
        "entity",
        "pydantic",
        "dataclass",
    )
    "Tokens indicating model-related code."
    DECORATOR_TOKENS: Final[Sequence[str]] = ("decorator", "inject", "provide")
    "Tokens indicating decorator-related code."
    DISPATCHER_TOKENS: Final[Sequence[str]] = (
        "dispatcher",
        "dispatch",
        "command",
        "query",
        "event",
    )
    "Tokens indicating dispatcher-related code."
    NAMESPACE_PREFIXES: Final[Mapping[str, str]] = MappingProxyType({
        "utility": "FlextUtilities",
        "models": "FlextModels",
        "decorators": "d",
        "dispatcher": "FlextDispatcher",
    })
    "Namespace → class prefix mapping for violation classification."
    CLASSIFICATION_PRIORITY: Final[Sequence[str]] = (
        "dispatcher",
        "decorators",
        "models",
        "utility",
    )
    "Priority order for violation classification."
    MIN_PATH_DEPTH: int = 2
    "Minimum relative path depth for module prefix detection."
    NAMESPACE_CONSTANT_PATTERN: Final[re.Pattern[str]] = re.compile(
        r"^_?[A-Z][A-Z0-9_]+$",
    )
    NAMESPACE_SETTINGS_FILE_NAMES: Final[frozenset[str]] = frozenset({
        "settings.py",
        "_settings.py",
    })
    NAMESPACE_PROTECTED_FILES: Final[frozenset[str]] = frozenset({
        "settings.py",
        "_settings.py",
        "typings.py",
        "_typings.py",
        "__init__.py",
        "__main__.py",
        "__version__.py",
        "conftest.py",
        "py.typed",
    })
    NAMESPACE_CANONICAL_ALIAS_MODULE_STEMS: Final[frozenset[str]] = frozenset({
        "ldif",
        "cli",
        "main",
        "_cli_main",
    })
    "Canonical alias module stems exempt from strict single-class enforcement."
    NAMESPACE_MIN_ALIAS_LENGTH: Final[int] = 2
    NAMESPACE_MAX_RENDERED_LOOSE_OBJECTS: Final[int] = 10
    NAMESPACE_MAX_RENDERED_IMPORT_VIOLATIONS: Final[int] = 5
    NAMESPACE_NO_RENDER_LIMIT: Final[int] = 10_000
    FACADE_ALIAS_RE: Final[re.Pattern[str]] = re.compile(
        r"^(\w)\s*=\s*(\w+)",
        re.MULTILINE,
    )
    "Matches ``m = FlextFooModels`` alias assignments in facade files."

    # --- Detector regex constants ---
    FUNC_DEF_RE: Final[re.Pattern[str]] = re.compile(
        r"^(def\s+(\w+)\s*\()",
        re.MULTILINE,
    )
    "Matches top-level function definitions for loose object detection."
    ASSIGN_RE: Final[re.Pattern[str]] = re.compile(
        r"^([A-Z_]\w*)\s*[:=]",
        re.MULTILINE,
    )
    "Matches top-level UPPER_CASE assignments for loose constant detection."
    LOGGER_ASSIGN_RE: Final[re.Pattern[str]] = re.compile(
        r"^([A-Za-z_]\w*)\s*[:=]\s*(?:(?:\w+\.)*)?"
        r"(?:fetch_logger|create_module_logger|get_logger|logging\.getLogger)\s*\(",
        re.IGNORECASE | re.MULTILINE,
    )
    "Matches top-level logger assignments created outside namespace classes."
    PEP695_RE: Final[re.Pattern[str]] = re.compile(
        r"^type\s+(\w+)\s*=",
        re.MULTILINE,
    )
    "Matches PEP 695 type alias definitions."
    TYPEALIAS_ANNOT_RE: Final[re.Pattern[str]] = re.compile(
        r"^(\w+)\s*:\s*(?:\w+\.)*TypeAlias\s*=",
        re.MULTILINE,
    )
    "Matches TypeAlias annotation syntax for typing alias detection."
    TYPING_FACTORY_ASSIGN_RE: Final[re.Pattern[str]] = re.compile(
        r"^(\w+)\s*=\s*(?:(?:\w+\.)*)?"
        r"(?:TypeVar|ParamSpec|TypeVarTuple|NewType)\s*\(",
        re.MULTILINE,
    )
    "Matches TypeVar/ParamSpec/TypeVarTuple/NewType assignments."
    COMPAT_ALIAS_RE: Final[re.Pattern[str]] = re.compile(
        r"^([A-Z]\w+)\s*=\s*([A-Z]\w+)\s*$",
        re.MULTILINE,
    )
    "Matches compatibility alias assignments (CapitalName = CapitalName)."
    COMPAT_SKIP_NAMES: Final[frozenset[str]] = frozenset({
        "__all__",
        "__version__",
        "__version_info__",
    })
    "Names to skip during compatibility alias detection."
    FUTURE_ANNOTATIONS_RE: Final[re.Pattern[str]] = re.compile(
        r"^from\s+__future__\s+import\s+annotations\b",
        re.MULTILINE,
    )
    "Matches 'from __future__ import annotations' import statement."
    ONLY_DOCSTRING_RE: Final[re.Pattern[str]] = re.compile(
        r'^("""[\s\S]*?"""|\'\'\'[\s\S]*?\'\'\')\s*$',
    )
    "Matches files that contain only a module docstring."
    NAMESPACE_FILE_TO_FAMILY: Final[Mapping[str, str]] = MappingProxyType({
        f"{suffix.lower()}.py": alias for alias, suffix in FAMILY_SUFFIXES.items()
    })
    NAMESPACE_FAMILY_EXPECTED_ALIAS: Final[Mapping[str, tuple[str, str]]] = (
        MappingProxyType({
            f"{suffix.lower()}.py": (alias, suffix)
            for alias, suffix in FAMILY_SUFFIXES.items()
        })
    )

    MIN_METHODS_FOR_REORDER: Final[int] = 2
    "Minimum method count before class method reordering is attempted."

    # --- Class nesting refactor constants (was: class ClassNesting) ---
    NESTING_COERCE_KEYS: Final[tuple[str, ...]] = (
        "loose_name",
        "helper_name",
        "target_namespace",
        "target_name",
        "rewrite_scope",
        "confidence",
    )
    "Keys to coerce from string to typed values in nesting mappings."
    NESTING_SECTION_KEYS: Final[tuple[str, ...]] = (
        "class_nesting",
        "helper_consolidation",
    )
    "Top-level section keys in class nesting YAML configs."

    # --- Method category StrEnum (was: plain class MethodCategory) ---
    @unique
    class MethodCategory(StrEnum):
        """Canonical method category identifiers for MRO reordering."""

        MAGIC = "magic"
        PROPERTY = "property"
        STATIC = "static"
        CLASS = "class"
        PUBLIC = "public"
        PROTECTED = "protected"
        PRIVATE = "private"

    # --- Scan constants (was: class Scan) ---
    SCAN_ALLOWED_TOP_LEVEL: Final[frozenset[str]] = frozenset({
        "__all__",
        "__version__",
        "__version_info__",
    })
    "Top-level names allowed without namespace classification."

    # --- Census mode StrEnum (was: class Census plain strings) ---
    @unique
    class CensusMode(StrEnum):
        """Canonical census usage mode identifiers."""

        ALIAS_FLAT = "alias_flat"
        "Usage via u.method_name (flat alias)."
        ALIAS_NS = "alias_namespaced"
        "Usage via u.ClassName.method_name (namespaced)."
        DIRECT = "direct"
        "Usage via FlextUtilitiesXxx.method_name (direct)."

    CENSUS_DEFAULT_FAMILY: Final[str] = "u"
    "Default census family."


__all__: list[str] = ["FlextInfraConstantsRefactor"]
