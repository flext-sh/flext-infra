"""Constants namespace for flext_infra.refactor."""

from __future__ import annotations

import re
from collections.abc import Mapping
from pathlib import Path
from typing import ClassVar


class FlextInfraRefactorConstants:
    """Shared constants for refactor engine modules."""

    RUNTIME_ALIAS_NAMES: ClassVar[frozenset[str]] = frozenset({
        "c",
        "m",
        "r",
        "t",
        "u",
        "p",
        "d",
        "e",
        "h",
        "s",
        "x",
    })
    NAMESPACE_SOURCE_UNIVERSAL_ALIASES: ClassVar[frozenset[str]] = frozenset({"r"})

    RUNTIME_ALIAS_NAMES_BY_PACKAGE: ClassVar[dict[str, tuple[str, ...]]] = {
        "flext_core": ("c", "d", "e", "h", "m", "p", "r", "s", "t", "u", "x"),
        "flext_infra": ("c", "m", "p", "r", "s", "t", "u"),
        "flext_api": ("c", "m", "p", "t", "u"),
        "flext_auth": ("c", "m", "p", "s", "t", "u", "x"),
        "flext_cli": ("c", "m", "p", "s", "t", "u", "x"),
        "flext_db_oracle": ("c", "e", "m", "p", "s", "t", "u"),
        "flext_dbt_ldap": ("c", "m", "p", "s", "t", "u"),
        "flext_dbt_ldif": ("c", "m", "p", "s", "t", "u"),
        "flext_dbt_oracle": ("c", "m", "p", "t", "u"),
        "flext_dbt_oracle_wms": ("c", "m", "p", "s", "t", "u"),
        "flext_grpc": ("c", "m", "p", "t", "u"),
        "flext_ldap": ("c", "m", "p", "s", "t", "u"),
        "flext_ldif": ("c", "d", "m", "p", "r", "s", "t", "u"),
        "flext_meltano": ("c", "m", "p", "r", "s", "t", "u"),
        "flext_observability": ("c", "m", "p", "t", "u"),
        "flext_oracle_oic": ("c", "m", "p", "s", "t", "u"),
        "flext_oracle_wms": ("c", "e", "m", "p", "t", "u"),
        "flext_plugin": ("c", "h", "m", "p", "s", "t", "u"),
        "flext_quality": ("c", "m", "p", "r", "s", "t", "u"),
        "flext_tap_ldap": ("c", "m", "p", "t", "u"),
        "flext_tap_ldif": ("c", "m", "p", "t", "u"),
        "flext_tap_oracle": ("c", "m", "p", "s", "t", "u"),
        "flext_tap_oracle_oic": ("c", "m", "p", "t", "u"),
        "flext_tap_oracle_wms": ("c", "m", "p", "t", "u"),
        "flext_target_ldap": ("c", "m", "p", "r", "s", "t", "u"),
        "flext_target_ldif": ("c", "m", "p", "t", "u"),
        "flext_target_oracle": ("c", "e", "m", "p", "s", "t", "u"),
        "flext_target_oracle_oic": ("c", "m", "p", "t", "u"),
        "flext_target_oracle_wms": ("c", "m", "p", "t", "u"),
        "flext_tests": ("c", "m", "p", "s", "t", "u"),
        "flext_web": ("c", "h", "m", "p", "t", "u"),
        "gruponos_meltano_native": ("c", "m", "p", "r", "t", "u"),
        "algar_oud_mig": ("c", "m", "p", "r", "s", "t", "u"),
    }
    "Package → exported single-letter aliases for import normalization."

    FACADE_FILE_DECLARES_ALIAS: ClassVar[dict[str, str]] = {
        "constants.py": "c",
        "typings.py": "t",
        "models.py": "m",
        "protocols.py": "p",
        "utilities.py": "u",
        "exceptions.py": "e",
        "decorators.py": "d",
        "handlers.py": "h",
        "service.py": "s",
        "services.py": "s",
        "mixins.py": "x",
        "result.py": "r",
    }
    "Facade file → single-letter alias it declares (self-import is circular)."

    LEGACY_FIX_ACTIONS: ClassVar[frozenset[str]] = frozenset({
        "remove",
        "inline_and_remove",
        "remove_and_update_refs",
        "keep_try_only",
    })
    IMPORT_FIX_ACTIONS: ClassVar[frozenset[str]] = frozenset({
        "replace_with_alias",
        "hoist_to_module_top",
    })
    CLASS_FIX_ACTIONS: ClassVar[frozenset[str]] = frozenset({"reorder_methods"})
    MRO_FIX_ACTIONS: ClassVar[frozenset[str]] = frozenset({
        "remove_inheritance_keep_class",
        "fix_mro_redeclaration",
        "migrate_to_class_mro",
    })
    PROPAGATION_FIX_ACTIONS: ClassVar[frozenset[str]] = frozenset({
        "propagate_symbol_renames",
        "rename_imported_symbols",
        "propagate_signature_migrations",
    })
    PATTERN_FIX_ACTIONS: ClassVar[frozenset[str]] = frozenset({
        "convert_dict_to_mapping_annotations",
        "remove_redundant_casts",
    })
    TYPE_ALIAS_FIX_ACTIONS: ClassVar[frozenset[str]] = frozenset({"unify_typings"})
    FUTURE_FIX_ACTIONS: ClassVar[frozenset[str]] = frozenset({
        "ensure_future_annotations",
    })
    TYPING_DEFINITION_FILES: ClassVar[frozenset[str]] = frozenset({
        "typings.py",
        "_typings",
        "protocols.py",
        "_protocols",
    })
    TYPING_INLINE_UNION_CANONICAL_MAP: ClassVar[Mapping[frozenset[str], str]] = {
        frozenset({"str", "int", "float", "bool"}): "t.Primitives",
        frozenset({"int", "float"}): "t.Numeric",
        frozenset({"str", "int", "float", "bool", "datetime"}): "t.Scalar",
        frozenset({"str", "int", "float", "bool", "datetime", "Path"}): ("t.Container"),
    }
    FUTURE_CHECKS: ClassVar[frozenset[str]] = frozenset({"missing_future_import"})
    MRO_TARGETS: ClassVar[frozenset[str]] = frozenset({
        "constants",
        "typings",
        "protocols",
        "models",
        "utilities",
        "all",
    })
    "Accepted target arguments for MRO migration runs."
    MRO_SCAN_DIRECTORIES: ClassVar[tuple[str, ...]] = (
        "src",
        "examples",
        "scripts",
        "tests",
    )
    "Directories scanned for constants modules in each project."
    MRO_CONSTANTS_FILE_NAMES: ClassVar[frozenset[str]] = frozenset({
        "constants.py",
        "_constants.py",
    })
    "Canonical constants module file names."
    MRO_CONSTANTS_DIRECTORY: ClassVar[str] = "constants"
    "Canonical constants package directory name."
    MRO_TYPINGS_FILE_NAMES: ClassVar[frozenset[str]] = frozenset({
        "typings.py",
        "_typings.py",
    })
    "Canonical typings module file names."
    MRO_TYPINGS_DIRECTORY: ClassVar[str] = "typings"
    "Canonical typings package directory name."
    MRO_PROTOCOLS_FILE_NAMES: ClassVar[frozenset[str]] = frozenset({
        "protocols.py",
        "_protocols.py",
    })
    "Canonical protocols module file names."
    MRO_PROTOCOLS_DIRECTORY: ClassVar[str] = "protocols"
    "Canonical protocols package directory name."
    MRO_MODELS_FILE_NAMES: ClassVar[frozenset[str]] = frozenset({
        "models.py",
        "_models.py",
    })
    "Canonical models module file names."
    MRO_MODELS_DIRECTORY: ClassVar[str] = "models"
    "Canonical models package directory name."
    MRO_UTILITIES_FILE_NAMES: ClassVar[frozenset[str]] = frozenset({
        "utilities.py",
        "_utilities.py",
    })
    "Canonical utilities module file names."
    MRO_UTILITIES_DIRECTORY: ClassVar[str] = "utilities"
    "Canonical utilities package directory name."

    CONSTANTS_DIRECTORY = "constants"
    TYPINGS_DIRECTORY = "typings"
    DEFAULT_CONSTANTS_CLASS: ClassVar[str] = "FlextConstants"
    "Fallback constants class name when none exists in module."
    DEFAULT_TYPES_CLASS: ClassVar[str] = "FlextTypes"
    "Fallback types class name when none exists in module."
    CONSTANTS_FILE_GLOB: ClassVar[str] = "constants.py"
    "Constants module glob scanned by the migration scanner."
    CONSTANTS_CLASS_SUFFIX: ClassVar[str] = "Constants"
    "Class-name suffix used to identify constants facades."
    FINAL_ANNOTATION_NAME: ClassVar[str] = "Final"
    "Annotation marker used to detect module-level constants."
    CONSTANT_PATTERN_REGEX: ClassVar[str] = "^_*[A-Z][A-Z0-9_]*$"
    "Naming pattern for module-level constant candidates."
    CONSTANT_PATTERN: ClassVar[re.Pattern[str]] = re.compile(CONSTANT_PATTERN_REGEX)
    "Compiled naming pattern for module-level constant candidates."
    DEFAULT_FACADE_ALIAS: ClassVar[str] = "c"
    "Default facade alias inserted during import rewrite."
    MRO_CLASS_TEMPLATE: ClassVar[str] = "class {class_name}:\n    pass\n"
    "Template used to create a new constants facade class."
    FAMILY_SUFFIXES: ClassVar[Mapping[str, str]] = {
        "c": "Constants",
        "t": "Types",
        "p": "Protocols",
        "m": "Models",
        "u": "Utilities",
    }
    "Facade family letter → class suffix mapping."
    FAMILY_FILES: ClassVar[dict[str, str]] = {
        "c": "*constants.py",
        "t": "*typings.py",
        "p": "*protocols.py",
        "m": "*models.py",
        "u": "*utilities.py",
    }
    "Facade family letter → file glob mapping."
    MRO_FAMILIES: ClassVar[frozenset[str]] = frozenset({"c", "t", "p", "m", "u"})
    "All MRO families."
    MRO_FAMILY_PACKAGE_DIRS: ClassVar[Mapping[str, str]] = {
        "c": "flext_core/constants.py",
        "t": "flext_core/typings.py",
        "p": "flext_core/protocols.py",
        "m": "flext_core/_models",
        "u": "flext_core/_utilities",
    }
    "Family letter → relative package dir/file."
    MRO_FAMILY_FACADE_MODULES: ClassVar[Mapping[str, str]] = {
        "c": "flext_core/constants.py",
        "t": "flext_core/typings.py",
        "p": "flext_core/protocols.py",
        "m": "flext_core/models.py",
        "u": "flext_core/utilities.py",
    }
    "Family letter → facade module path."
    DOMAIN_PACKAGES: ClassVar[frozenset[str]] = frozenset({
        "flext-ldap",
        "flext-ldif",
        "flext-db-oracle",
        "flext-oracle-wms",
        "flext-oracle-oic",
    })
    "Known domain-layer packages."
    PLATFORM_PACKAGES: ClassVar[frozenset[str]] = frozenset({
        "flext-cli",
        "flext-meltano",
        "flext-api",
        "flext-auth",
        "flext-web",
        "flext-grpc",
    })
    "Known platform-layer packages."
    INTEGRATION_CLASS_PREFIXES: ClassVar[tuple[str, ...]] = (
        "FlextTap",
        "FlextTarget",
        "FlextDbt",
    )
    "Class name prefixes that identify integration projects."
    CONFIDENCE_TO_SCORE: ClassVar[Mapping[str, float]] = {
        "high": 0.95,
        "medium": 0.75,
        "low": 0.55,
    }
    "Confidence level → numeric score mapping for violations."
    CONFIDENCE_RANKS: ClassVar[dict[str, int]] = {"low": 0, "medium": 1, "high": 2}
    "Confidence level → priority rank mapping."
    REQUIRED_CLASS_TARGETS: ClassVar[tuple[str, ...]] = (
        "TimeoutEnforcer",
        "CircuitBreakerManager",
    )
    "Class names always required in scanner output."
    CLASS_PATTERN: ClassVar[re.Pattern[str]] = re.compile(r"[^A-Za-z0-9]+")
    "Pattern to split class name fragments."
    MAPPINGS_RELATIVE_PATH: ClassVar[Path] = (
        Path("rules") / "class-nesting-mappings.yml"
    )
    "Relative path from the refactor package to the nesting mappings YAML."
    VIOLATION_PATTERNS: ClassVar[Mapping[str, re.Pattern[str]]] = {
        "container_invariance": re.compile(
            r"\bdict\s*\[\s*str\s*,\s*t\.(?:Container|object)\s*\]",
        ),
        "redundant_cast": re.compile(r"\bcast\s*\(\s*[\"'][^\"']+[\"']\s*,"),
        "direct_submodule_import": re.compile(
            r"\bfrom\s+flext_core\.[\w\.]+\s+import\b",
        ),
        "legacy_typing_mapping": re.compile(
            r"\bfrom\s+typing\s+import\s+.*\bMapping\b",
        ),
        "runtime_alias_violation": re.compile(
            r"\bfrom\s+flext_core\s+import\s+(?!.*\b(?:c|m|r|t|u|p|d|e|h|s|x)\b).*",
        ),
        "strenum_usage": re.compile(
            r"\bclass\s+[A-Za-z_][A-Za-z0-9_]*\s*\(\s*(?:\w+\.)?StrEnum\s*\)",
        ),
        "literal_usage": re.compile(r"\bLiteral\s*\["),
        "manual_mapping_constant": re.compile(
            r"^\s*[A-Z][A-Z0-9_]*\s*(?::\s*[^=]+)?=\s*\{",
            re.MULTILINE,
        ),
        "manual_typing_alias": re.compile(
            r"(?m)^\s*(?:type\s+[A-Za-z_][A-Za-z0-9_]*\s*=|[A-Za-z_][A-Za-z0-9_]*\s*:\s*TypeAlias\s*=)",
        ),
        "compatibility_alias": re.compile(
            r"(?m)^\s*[A-Za-z_][A-Za-z0-9_]*\s*=\s*[A-Za-z_][A-Za-z0-9_]*\s*$",
        ),
    }
    "Regex patterns for violation analysis."
    MODEL_TOKENS: ClassVar[tuple[str, ...]] = (
        "model",
        "schema",
        "entity",
        "pydantic",
        "dataclass",
    )
    "Tokens indicating model-related code."
    DECORATOR_TOKENS: ClassVar[tuple[str, ...]] = ("decorator", "inject", "provide")
    "Tokens indicating decorator-related code."
    DISPATCHER_TOKENS: ClassVar[tuple[str, ...]] = (
        "dispatcher",
        "dispatch",
        "command",
        "query",
        "event",
    )
    "Tokens indicating dispatcher-related code."
    NAMESPACE_PREFIXES: ClassVar[Mapping[str, str]] = {
        "utility": "FlextUtilities",
        "models": "FlextModels",
        "decorators": "FlextDecorators",
        "dispatcher": "FlextDispatcher",
    }
    "Namespace → class prefix mapping for violation classification."
    CLASSIFICATION_PRIORITY: ClassVar[tuple[str, ...]] = (
        "dispatcher",
        "decorators",
        "models",
        "utility",
    )
    "Priority order for violation classification."
    CAST_ARITY: int = 2
    "Expected number of arguments for typing.cast calls."
    MIN_PATH_DEPTH: int = 2
    "Minimum relative path depth for module prefix detection."
    TYPED_DICT_MIN_ARGS: int = 2
    "Minimum positional args expected in TypedDict(name, fields, ...)."

    NAMESPACE_CONSTANT_PATTERN: ClassVar[re.Pattern[str]] = re.compile(
        r"^_?[A-Z][A-Z0-9_]+$",
    )
    NAMESPACE_SETTINGS_FILE_NAMES: ClassVar[frozenset[str]] = frozenset({
        "settings.py",
        "_settings.py",
    })
    NAMESPACE_PROTECTED_FILES: ClassVar[frozenset[str]] = frozenset({
        "settings.py",
        "_settings.py",
        "__init__.py",
        "__main__.py",
        "__version__.py",
        "conftest.py",
        "py.typed",
    })
    NAMESPACE_MIN_ALIAS_LENGTH: ClassVar[int] = 2
    NAMESPACE_MAX_RENDERED_LOOSE_OBJECTS: ClassVar[int] = 10
    NAMESPACE_MAX_RENDERED_IMPORT_VIOLATIONS: ClassVar[int] = 5
    NAMESPACE_FILE_TO_FAMILY: ClassVar[dict[str, str]] = {
        f"{suffix.lower()}.py": alias for alias, suffix in FAMILY_SUFFIXES.items()
    }
    NAMESPACE_FAMILY_EXPECTED_ALIAS: ClassVar[dict[str, tuple[str, str]]] = {
        f"{suffix.lower()}.py": (alias, suffix)
        for alias, suffix in FAMILY_SUFFIXES.items()
    }
    NAMESPACE_CANONICAL_PROTOCOL_FILES: ClassVar[frozenset[str]] = (
        MRO_PROTOCOLS_FILE_NAMES
    )
    NAMESPACE_CANONICAL_PROTOCOL_DIR: ClassVar[str] = MRO_PROTOCOLS_DIRECTORY
    NAMESPACE_CANONICAL_TYPINGS_FILES: ClassVar[frozenset[str]] = MRO_TYPINGS_FILE_NAMES
    NAMESPACE_CANONICAL_TYPINGS_DIR: ClassVar[str] = MRO_TYPINGS_DIRECTORY

    class MethodCategory:
        MAGIC: ClassVar[str] = "magic"
        PROPERTY: ClassVar[str] = "property"
        STATIC: ClassVar[str] = "static"
        CLASS: ClassVar[str] = "class"
        PUBLIC: ClassVar[str] = "public"
        PROTECTED: ClassVar[str] = "protected"
        PRIVATE: ClassVar[str] = "private"

    class Census:
        """Constants for the usage census module."""

        MODE_ALIAS_FLAT: ClassVar[str] = "alias_flat"
        "Usage via u.method_name (flat alias)."
        MODE_ALIAS_NS: ClassVar[str] = "alias_namespaced"
        "Usage via u.ClassName.method_name (namespaced)."
        MODE_DIRECT: ClassVar[str] = "direct"
        "Usage via FlextUtilitiesXxx.method_name (direct)."
        CORE_PROJECT: ClassVar[str] = "flext-core"
        "Core project directory name."
        UTILITIES_PACKAGE: ClassVar[str] = "flext_core/_utilities"
        "Relative package path for _utilities."
        FACADE_MODULE: ClassVar[str] = "flext_core/utilities.py"
        "Relative path to the FlextUtilities facade."
        DEFAULT_FAMILY: ClassVar[str] = "u"
        "Default census family."

    PROJECT_KIND_VALUES: ClassVar[frozenset[str]] = frozenset({
        "core",
        "domain",
        "platform",
        "integration",
        "app",
    })
    type ProjectKind = str


__all__ = ["FlextInfraRefactorConstants"]
