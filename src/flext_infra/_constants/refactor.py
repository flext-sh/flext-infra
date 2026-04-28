"""Constants namespace for flext_infra.refactor."""

from __future__ import annotations

import re
from collections.abc import (
    Mapping,
)
from enum import StrEnum, unique
from pathlib import Path
from types import MappingProxyType
from typing import Final

from flext_core import c, t
from flext_infra import (
    FlextInfraConstantsBase as cb,
)


class FlextInfraConstantsRefactor:
    """Shared constants for refactor engine modules."""

    RK_REFACTOR_ENGINE: Final[str] = "refactor_engine"
    RK_PROJECT_SCAN_DIRS: Final[str] = "project_scan_dirs"
    RK_IGNORE_PATTERNS: Final[str] = "ignore_patterns"
    RK_FILE_EXTENSIONS: Final[str] = "file_extensions"
    RK_FORBIDDEN_IMPORTS: Final[str] = "forbidden_imports"
    RK_REDUNDANT_TYPE_TARGETS: Final[str] = "redundant_type_targets"
    RK_TARGET_MODULES: Final[str] = "target_modules"
    RK_MODULE_RENAMES: Final[str] = "module_renames"
    RK_IMPORT_SYMBOL_RENAMES: Final[str] = "import_symbol_renames"
    RK_SIGNATURE_MIGRATIONS: Final[str] = "signature_migrations"
    RK_METHOD_ORDER: Final[str] = "method_order"
    RK_ORDER: Final[str] = "order"
    RK_TIER0_MODULES: Final[str] = "tier0_modules"
    RK_CORE_ALIASES: Final[str] = "core_aliases"
    RK_CORE_PACKAGE: Final[str] = "core_package"
    RK_ALIAS_TO_SUBMODULE: Final[str] = "alias_to_submodule"
    RK_QUALITY_GATES: Final[str] = "quality_gates"
    RK_EXPECTED_BASE_CHAIN: Final[str] = "expected_base_chain"
    RK_HELPER_NAME: Final[str] = "helper_name"
    RK_CONFIDENCE_THRESHOLD: Final[str] = "confidence_threshold"
    RK_ALLOW_ALIASES: Final[str] = "allow_aliases"
    RK_ALLOW_TARGET_SUFFIXES: Final[str] = "allow_target_suffixes"
    RK_INCLUDE_RETURN_ANNOTATIONS: Final[str] = "include_return_annotations"
    RK_TARGET_NAME: Final[str] = "target_name"
    RK_IMPORTS_RESOLVE: Final[str] = "imports_resolve"
    RK_MRO_VALID: Final[str] = "mro_valid"
    RK_LSP_DIAGNOSTICS_CLEAN: Final[str] = "lsp_diagnostics_clean"
    CLASS_NESTING_MAPPINGS_FILENAME: Final[str] = "class-nesting-mappings.yml"
    CLASS_NESTING_POLICY_FILENAME: Final[str] = "class-policy-v2.yml"
    ENGINE_CONFIG_KEYS: Final[tuple[str, ...]] = (
        RK_PROJECT_SCAN_DIRS,
        RK_IGNORE_PATTERNS,
        RK_FILE_EXTENSIONS,
    )
    """Allowed keys under the ``refactor_engine`` config scope."""

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
    MRO_MIGRATION_FIX_ACTIONS: Final[frozenset[str]] = frozenset({
        "migrate_to_class_mro",
    })
    MRO_REDUNDANCY_FIX_ACTIONS: Final[frozenset[str]] = frozenset({
        "remove_inheritance_keep_class",
        "fix_mro_redeclaration",
    })
    PATTERN_GENERIC_FIX_ACTIONS: Final[frozenset[str]] = frozenset({
        "convert_dict_to_mapping_annotations",
        "fix_silent_failure_sentinels",
    })
    PATTERN_REDUNDANT_CAST_FIX_ACTIONS: Final[frozenset[str]] = frozenset({
        "remove_redundant_casts",
    })
    SYMBOL_PROPAGATION_FIX_ACTIONS: Final[frozenset[str]] = frozenset({
        "propagate_symbol_renames",
        "rename_imported_symbols",
    })
    SIGNATURE_PROPAGATION_FIX_ACTIONS: Final[frozenset[str]] = frozenset({
        "propagate_signature_migrations",
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
            }): "t.JsonValue",
        })
    )
    FUTURE_CHECKS: Final[frozenset[str]] = frozenset({"missing_future_import"})

    @unique
    class RefactorRuleKind(StrEnum):
        """Canonical executable text-rule kinds."""

        FUTURE_ANNOTATIONS = "future_annotations"
        MRO_CLASS_MIGRATION = "mro_class_migration"
        LEGACY_REMOVAL = "legacy_removal"
        IMPORT_MODERNIZER = "import_modernizer"
        CLASS_RECONSTRUCTOR = "class_reconstructor"
        PATTERN_CORRECTIONS = "pattern_corrections"
        TYPING_UNIFICATION = "typing_unification"
        TYPING_ANNOTATION_FIX = "typing_annotation_fix"
        TIER0_IMPORT_FIX = "tier0_import_fix"
        SYMBOL_PROPAGATION = "symbol_propagation"
        SIGNATURE_PROPAGATION = "signature_propagation"
        MRO_REDUNDANCY = "mro_redundancy"

    @unique
    class RefactorFileRuleKind(StrEnum):
        """Canonical executable Rope-backed file-rule kinds."""

        CLASS_NESTING = "class_nesting"

    RULE_MATCHERS_BY_KIND: Final[
        Mapping[
            RefactorRuleKind,
            tuple[
                tuple[frozenset[str], frozenset[str], frozenset[str], frozenset[str]],
                ...,
            ],
        ]
    ] = MappingProxyType({
        RefactorRuleKind.FUTURE_ANNOTATIONS: (
            (FUTURE_FIX_ACTIONS, FUTURE_CHECKS, frozenset(), frozenset()),
        ),
        RefactorRuleKind.MRO_CLASS_MIGRATION: (
            (MRO_MIGRATION_FIX_ACTIONS, frozenset(), frozenset(), frozenset()),
        ),
        RefactorRuleKind.LEGACY_REMOVAL: (
            (LEGACY_FIX_ACTIONS, frozenset(), frozenset(), frozenset()),
        ),
        RefactorRuleKind.IMPORT_MODERNIZER: (
            (IMPORT_FIX_ACTIONS, frozenset(), frozenset(), frozenset()),
        ),
        RefactorRuleKind.CLASS_RECONSTRUCTOR: (
            (CLASS_FIX_ACTIONS, frozenset(), frozenset(), frozenset()),
        ),
        RefactorRuleKind.PATTERN_CORRECTIONS: (
            (PATTERN_GENERIC_FIX_ACTIONS, frozenset(), frozenset(), frozenset()),
            (
                PATTERN_REDUNDANT_CAST_FIX_ACTIONS,
                frozenset(),
                frozenset(),
                frozenset({RK_REDUNDANT_TYPE_TARGETS}),
            ),
        ),
        RefactorRuleKind.TYPING_UNIFICATION: (
            (TYPE_ALIAS_FIX_ACTIONS, frozenset(), frozenset(), frozenset()),
        ),
        RefactorRuleKind.TYPING_ANNOTATION_FIX: (
            (TYPING_FIX_ACTIONS, frozenset(), frozenset(), frozenset()),
        ),
        RefactorRuleKind.TIER0_IMPORT_FIX: (
            (TIER0_FIX_ACTIONS, frozenset(), frozenset(), frozenset()),
        ),
        RefactorRuleKind.SYMBOL_PROPAGATION: (
            (
                frozenset({"propagate_symbol_renames"}),
                frozenset(),
                frozenset({RK_IMPORT_SYMBOL_RENAMES}),
                frozenset(),
            ),
            (
                frozenset({"rename_imported_symbols"}),
                frozenset(),
                frozenset(),
                frozenset(),
            ),
        ),
        RefactorRuleKind.SIGNATURE_PROPAGATION: (
            (
                SIGNATURE_PROPAGATION_FIX_ACTIONS,
                frozenset(),
                frozenset(),
                frozenset({RK_SIGNATURE_MIGRATIONS}),
            ),
        ),
        RefactorRuleKind.MRO_REDUNDANCY: (
            (MRO_REDUNDANCY_FIX_ACTIONS, frozenset(), frozenset(), frozenset()),
        ),
    })
    FILE_RULE_MATCHERS_BY_KIND: Final[
        Mapping[
            RefactorFileRuleKind,
            tuple[
                tuple[frozenset[str], frozenset[str], frozenset[str], frozenset[str]],
                ...,
            ],
        ]
    ] = MappingProxyType({
        RefactorFileRuleKind.CLASS_NESTING: (
            (frozenset({"nest_classes"}), frozenset(), frozenset(), frozenset()),
        ),
    })
    RULE_TABLE_HEADERS: Final[tuple[str, ...]] = (
        cb.RK_ID,
        cb.NAME,
        cb.RK_DESCRIPTION,
        cb.RK_ENABLED,
        cb.RK_SEVERITY,
    )
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
    FAMILY_SUFFIXES: Final[t.StrMapping] = MappingProxyType({
        "c": "Constants",
        "t": "Types",
        "p": "Protocols",
        "m": "Models",
        "u": "Utilities",
    })
    "Facade family letter → class suffix mapping."
    FAMILY_DIRECTORIES: Final[t.StrMapping] = MappingProxyType({
        "c": "_constants",
        "t": "_typings",
        "p": "_protocols",
        "m": "models",
        "u": "_utilities",
    })
    "Facade family letter → subdirectory name mapping."
    FAMILY_FILES: Final[t.StrMapping] = MappingProxyType({
        "c": "*constants.py",
        "t": "*typings.py",
        "p": "*protocols.py",
        "m": "*models.py",
        "u": "*utilities.py",
    })
    "Facade family letter → file glob mapping."
    MRO_FAMILIES: Final[frozenset[str]] = frozenset({"c", "t", "p", "m", "u"})
    "All MRO families."
    MRO_FAMILY_PACKAGE_DIRS: Final[t.StrMapping] = MappingProxyType({
        "c": "flext_core/constants.py",
        "t": "flext_core/typings.py",
        "p": "flext_core/protocols.py",
        "m": "flext_core/models",
        "u": "flext_core/_utilities",
    })
    "Family letter → relative package dir/file."
    MRO_FAMILY_FACADE_MODULES: Final[t.StrMapping] = MappingProxyType({
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
    CONFIDENCE_RANKS: Final[t.IntMapping] = MappingProxyType({
        "low": 0,
        "medium": 1,
        "high": 2,
    })
    "Confidence level → priority rank mapping."
    REQUIRED_CLASS_TARGETS: Final[t.StrSequence] = (
        "TimeoutEnforcer",
        "CircuitBreakerManager",
    )
    "Class names always required in scanner output."
    CLASS_PATTERN: Final[re.Pattern[str]] = re.compile(r"[^A-Za-z0-9]+")
    "Pattern to split class name fragments."
    MAPPINGS_RELATIVE_PATH: Final[Path] = Path("rules") / "class-nesting-mappings.yml"
    "Relative path from the refactor package to the nesting mappings YAML."
    MODEL_TOKENS: Final[t.StrSequence] = (
        "model",
        "schema",
        "entity",
        "pydantic",
        "dataclass",
    )
    "Tokens indicating model-related code."
    DECORATOR_TOKENS: Final[t.StrSequence] = ("decorator", "inject", "provide")
    "Tokens indicating decorator-related code."
    DISPATCHER_TOKENS: Final[t.StrSequence] = (
        "dispatcher",
        "dispatch",
        "command",
        "query",
        "event",
    )
    "Tokens indicating dispatcher-related code."
    NAMESPACE_PREFIXES: Final[t.StrMapping] = MappingProxyType({
        "utility": "FlextUtilities",
        "models": "FlextModels",
        "decorators": "d",
        "dispatcher": "FlextDispatcher",
    })
    "Namespace → class prefix mapping for violation classification."
    CLASSIFICATION_PRIORITY: Final[t.StrSequence] = (
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
    NAMESPACE_FILE_TO_FAMILY: Final[t.StrMapping] = MappingProxyType({
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
        cb.RK_LOOSE_NAME,
        RK_HELPER_NAME,
        cb.RK_TARGET_NAMESPACE,
        RK_TARGET_NAME,
        cb.RK_REWRITE_SCOPE,
        cb.RK_CONFIDENCE,
    )
    "Keys to coerce from string to typed values in nesting mappings."
    NESTING_SECTION_KEYS: Final[tuple[str, ...]] = (
        cb.RK_CLASS_NESTING,
        cb.RK_HELPER_CONSOLIDATION,
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

    ACCESSOR_WARNING_PREFIXES: Final[frozenset[str]] = frozenset({
        "get_",
        "set_",
        "is_",
    })
    "Public accessor name prefixes that should be renamed (drop the prefix or use a canonical verb)."

    # --- MRO scan patterns ---
    MRO_SCAN_TYPE_PATTERN: Final[re.Pattern[str]] = re.compile(
        r"^_?[A-Za-z][A-Za-z0-9_]*$"
    )
    "Regex: valid Python identifier (used for MRO type/class name validation)."
    MRO_SCAN_PROTOCOL_BASE_PATTERN: Final[re.Pattern[str]] = re.compile(
        r"(^|[\s,(])(?:[A-Za-z_]\w*\.)?Protocol(?:\[[^\]]+\])?(?=$|[\s,)])",
    )
    "Regex: Protocol base in class definition (with optional namespace prefix)."

    # --- Symbol/identifier patterns ---
    IDENTIFIER_PATTERN: Final[re.Pattern[str]] = re.compile(r"\b[A-Za-z_]\w*\b")
    "Regex: Python identifier word boundary match."

    # --- Import bypass pattern (for transformer matching) ---
    IMPORT_BYPASS_RE: Final[re.Pattern[str]] = re.compile(
        r"^try:\n"
        r"(    from .+\n)"
        r"except ImportError:\n"
        r"    from .+\n",
        re.MULTILINE,
    )
    "Regex: try/except ImportError import bypass block (strict form)."

    # --- Deprecated class pattern ---
    CLASS_BLOCK_RE: Final[re.Pattern[str]] = re.compile(
        r"^(class\s+(\w+)\b[^\n]*:\n(?:(?:[ \t]+[^\n]*|[ \t]*)\n)*)",
        re.MULTILINE,
    )
    "Regex: full class block including body lines."
    DEPRECATION_WARN_RE: Final[re.Pattern[str]] = re.compile(r"\.warn\s*\(")
    "Regex: deprecation warning call site (.warn())."

    # --- Lazy import fixer ---
    DEF_ASYNC_CLASS_RE: Final[re.Pattern[str]] = re.compile(
        r"^(?:def |async def |class )", re.MULTILINE
    )
    "Regex: top-level def/async def/class keyword (for lazy import detection)."


__all__: list[str] = ["FlextInfraConstantsRefactor"]
