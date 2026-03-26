"""Constants namespace for flext_infra.refactor."""

from __future__ import annotations

import re
from collections.abc import Mapping
from pathlib import Path
from typing import TYPE_CHECKING, ClassVar

if TYPE_CHECKING:
    from flext_infra import t


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
    TYPING_FIX_ACTIONS: ClassVar[frozenset[str]] = frozenset({
        "replace_object_annotations",
        "remove_unused_models",
    })
    TIER0_FIX_ACTIONS: ClassVar[frozenset[str]] = frozenset({"fix_tier0_imports"})
    DUNDER_OBJECT_ALLOWLIST: ClassVar[frozenset[str]] = frozenset({
        "__eq__",
        "__ne__",
        "__hash__",
        "__lt__",
        "__le__",
        "__gt__",
        "__ge__",
    })
    "Dunder methods where `t.NormalizedValue` parameter type is canonical Python."
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
    MRO_SCAN_DIRECTORIES: ClassVar[t.StrSequence] = (
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

    DEFAULT_CONSTANTS_CLASS: ClassVar[str] = "FlextConstants"
    "Fallback constants class name when none exists in module."
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
    FAMILY_SUFFIXES: ClassVar[t.StrMapping] = {
        "c": "Constants",
        "t": "Types",
        "p": "Protocols",
        "m": "Models",
        "u": "Utilities",
    }
    "Facade family letter → class suffix mapping."
    FAMILY_DIRECTORIES: ClassVar[t.StrMapping] = {
        "c": "_constants",
        "t": "_typings",
        "p": "_protocols",
        "m": "_models",
        "u": "_utilities",
    }
    "Facade family letter → subdirectory name mapping."
    FAMILY_FILES: ClassVar[t.StrMapping] = {
        "c": "*constants.py",
        "t": "*typings.py",
        "p": "*protocols.py",
        "m": "*models.py",
        "u": "*utilities.py",
    }
    "Facade family letter → file glob mapping."
    MRO_FAMILIES: ClassVar[frozenset[str]] = frozenset({"c", "t", "p", "m", "u"})
    "All MRO families."
    MRO_FAMILY_PACKAGE_DIRS: ClassVar[t.StrMapping] = {
        "c": "flext_core/constants.py",
        "t": "flext_core/typings.py",
        "p": "flext_core/protocols.py",
        "m": "flext_core/_models",
        "u": "flext_core/_utilities",
    }
    "Family letter → relative package dir/file."
    MRO_FAMILY_FACADE_MODULES: ClassVar[t.StrMapping] = {
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
    CONFIDENCE_RANKS: ClassVar[Mapping[str, int]] = {"low": 0, "medium": 1, "high": 2}
    "Confidence level → priority rank mapping."
    REQUIRED_CLASS_TARGETS: ClassVar[t.StrSequence] = (
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
    MODEL_TOKENS: ClassVar[t.StrSequence] = (
        "model",
        "schema",
        "entity",
        "pydantic",
        "dataclass",
    )
    "Tokens indicating model-related code."
    DECORATOR_TOKENS: ClassVar[t.StrSequence] = ("decorator", "inject", "provide")
    "Tokens indicating decorator-related code."
    DISPATCHER_TOKENS: ClassVar[t.StrSequence] = (
        "dispatcher",
        "dispatch",
        "command",
        "query",
        "event",
    )
    "Tokens indicating dispatcher-related code."
    NAMESPACE_PREFIXES: ClassVar[t.StrMapping] = {
        "utility": "FlextUtilities",
        "models": "FlextModels",
        "decorators": "FlextDecorators",
        "dispatcher": "FlextDispatcher",
    }
    "Namespace → class prefix mapping for violation classification."
    CLASSIFICATION_PRIORITY: ClassVar[t.StrSequence] = (
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
    NAMESPACE_NO_RENDER_LIMIT: ClassVar[int] = 10_000
    MAX_SCAN_FILES: ClassVar[int] = 10_000
    FACADE_ALIAS_RE: ClassVar[re.Pattern[str]] = re.compile(
        r"^(\w)\s*=\s*(\w+)",
        re.MULTILINE,
    )
    "Matches ``m = FlextFooModels`` alias assignments in facade files."

    # --- Detector regex constants ---
    FUNC_DEF_RE: ClassVar[re.Pattern[str]] = re.compile(
        r"^(def\s+(\w+)\s*\()",
        re.MULTILINE,
    )
    "Matches top-level function definitions for loose object detection."
    ASSIGN_RE: ClassVar[re.Pattern[str]] = re.compile(
        r"^([A-Z_]\w*)\s*[:=]",
        re.MULTILINE,
    )
    "Matches top-level UPPER_CASE assignments for loose constant detection."
    PEP695_RE: ClassVar[re.Pattern[str]] = re.compile(
        r"^type\s+(\w+)\s*=",
        re.MULTILINE,
    )
    "Matches PEP 695 type alias definitions."
    TYPEALIAS_ANNOT_RE: ClassVar[re.Pattern[str]] = re.compile(
        r"^(\w+)\s*:\s*(?:\w+\.)*TypeAlias\s*=",
        re.MULTILINE,
    )
    "Matches TypeAlias annotation syntax for typing alias detection."
    COMPAT_ALIAS_RE: ClassVar[re.Pattern[str]] = re.compile(
        r"^([A-Z]\w+)\s*=\s*([A-Z]\w+)\s*$",
        re.MULTILINE,
    )
    "Matches compatibility alias assignments (CapitalName = CapitalName)."
    COMPAT_SKIP_NAMES: ClassVar[frozenset[str]] = frozenset({
        "__all__",
        "__version__",
        "__version_info__",
    })
    "Names to skip during compatibility alias detection."
    FUTURE_ANNOTATIONS_RE: ClassVar[re.Pattern[str]] = re.compile(
        r"^from\s+__future__\s+import\s+annotations\b",
        re.MULTILINE,
    )
    "Matches 'from __future__ import annotations' import statement."
    ONLY_DOCSTRING_RE: ClassVar[re.Pattern[str]] = re.compile(
        r'^("""[\s\S]*?"""|\'\'\'[\s\S]*?\'\'\')\s*$',
    )
    "Matches files that contain only a module docstring."
    NAMESPACE_FILE_TO_FAMILY: ClassVar[t.StrMapping] = {
        f"{suffix.lower()}.py": alias for alias, suffix in FAMILY_SUFFIXES.items()
    }
    NAMESPACE_FAMILY_EXPECTED_ALIAS: ClassVar[Mapping[str, t.Infra.StrPair]] = {
        f"{suffix.lower()}.py": (alias, suffix)
        for alias, suffix in FAMILY_SUFFIXES.items()
    }

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
        DEFAULT_FAMILY: ClassVar[str] = "u"
        "Default census family."


__all__ = ["FlextInfraRefactorConstants"]
