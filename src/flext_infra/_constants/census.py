"""Constants for the unified census pipeline — accessed via c.Infra.*."""

from __future__ import annotations

import re
from typing import ClassVar, Final

from flext_infra import t


class FlextInfraConstantsCensus:
    """Census pipeline constants for object detection and classification."""

    class CensusObjectKind:
        """Object kind identifiers for census classification."""

        CONSTANT: Final[str] = "constant"
        TYPE: Final[str] = "type"
        PROTOCOL: Final[str] = "protocol"
        MODEL: Final[str] = "model"
        UTILITY: Final[str] = "utility"
        ALL: ClassVar[frozenset[str]] = frozenset({
            CONSTANT,
            TYPE,
            PROTOCOL,
            MODEL,
            UTILITY,
        })

    class CensusViolationKind:
        """Violation kind identifiers for census analysis."""

        MISPLACED: Final[str] = "misplaced"
        DUPLICATE: Final[str] = "duplicate"
        UNUSED: Final[str] = "unused"
        MISSING_MRO_BASE: Final[str] = "missing_mro_base"
        FLAT_ALIAS: Final[str] = "flat_alias"
        WRONG_TIER: Final[str] = "wrong_tier"
        ALL: ClassVar[frozenset[str]] = frozenset({
            MISPLACED,
            DUPLICATE,
            UNUSED,
            MISSING_MRO_BASE,
            FLAT_ALIAS,
            WRONG_TIER,
        })

    class CensusFixAction:
        """Fix action identifiers for census auto-fix."""

        MOVE_TO_TIER: Final[str] = "move_to_tier"
        DEDUPLICATE: Final[str] = "deduplicate"
        REMOVE_UNUSED: Final[str] = "remove_unused"
        ADD_MRO_BASE: Final[str] = "add_mro_base"
        REMOVE_FLAT_ALIAS: Final[str] = "remove_flat_alias"
        ALL: ClassVar[frozenset[str]] = frozenset({
            MOVE_TO_TIER,
            DEDUPLICATE,
            REMOVE_UNUSED,
            ADD_MRO_BASE,
            REMOVE_FLAT_ALIAS,
        })

    CENSUS_TIER_MAP: ClassVar[t.StrMapping] = {
        "constants.py": "constant",
        "_constants.py": "constant",
        "_constants": "constant",
        "typings.py": "type",
        "_typings.py": "type",
        "_typings": "type",
        "protocols.py": "protocol",
        "_protocols.py": "protocol",
        "_protocols": "protocol",
        "models.py": "model",
        "_models.py": "model",
        "_models": "model",
        "utilities.py": "utility",
        "_utilities.py": "utility",
        "_utilities": "utility",
    }
    """Filename/dirname → object kind mapping for tier resolution."""

    CENSUS_TIER_FILES: ClassVar[t.StrMapping] = {
        "constant": "constants.py",
        "type": "typings.py",
        "protocol": "protocols.py",
        "model": "models.py",
        "utility": "utilities.py",
    }
    """Object kind → canonical facade filename (reverse of TIER_MAP)."""

    CENSUS_TIER_SUBDIRS: ClassVar[t.StrMapping] = {
        "constant": "_constants",
        "type": "_typings",
        "protocol": "_protocols",
        "model": "_models",
        "utility": "_utilities",
    }
    """Object kind → canonical subpackage directory."""

    CENSUS_OBJECT_MARKERS: ClassVar[t.StrMapping] = {
        "Final": "constant",
        "ClassVar": "constant",
        "Protocol": "protocol",
        "BaseModel": "model",
        "TypedDict": "model",
        "FrozenStrictModel": "model",
        "ArbitraryTypesModel": "model",
        "TypeAlias": "type",
    }
    """Base class / annotation name → object kind for classification."""

    CENSUS_CONSTANT_NAME_RE: ClassVar[str] = r"^_?[A-Z][A-Z0-9_]+$"
    """Regex for UPPER_CASE constant name detection."""

    CENSUS_FACADE_SUFFIXES: ClassVar[frozenset[str]] = frozenset({
        "Constants",
        "Types",
        "Protocols",
        "Models",
        "Utilities",
    })
    """Facade class name suffixes identifying namespace classes."""

    class CensusPatterns:
        """Regex patterns for violation census detection."""

        CAST_RE: Final[re.Pattern[str]] = re.compile(r"\bcast\s*\(")
        "Detect ``cast(...)`` calls."
        LITERAL_RE: Final[re.Pattern[str]] = re.compile(r"\bLiteral\s*\[")
        "Detect ``Literal[...]`` annotations."
        DICT_INVARIANCE_RE: Final[re.Pattern[str]] = re.compile(
            r"\bdict\s*\[\s*str\s*,\s*(?:t\.Container|t\.NormalizedValue|object)",
        )
        "Detect invariant dict[str, ...] patterns."
        DIRECT_SUBMODULE_RE: Final[re.Pattern[str]] = re.compile(
            r"^from\s+flext_core\.\S+\s+import\s+",
            re.MULTILINE,
        )
        "Detect direct flext_core submodule imports."
        LEGACY_MAPPING_RE: Final[re.Pattern[str]] = re.compile(
            r"^from\s+typing\s+import\s+.*\bMapping\b",
            re.MULTILINE,
        )
        "Detect legacy ``from typing import Mapping``."
        FLEXT_CORE_IMPORT_RE: Final[re.Pattern[str]] = re.compile(
            r"^from\s+flext_core\s+import\s+(.+?)$",
            re.MULTILINE,
        )
        "Detect ``from flext_core import ...``."
        STRENUM_RE: Final[re.Pattern[str]] = re.compile(
            r"class\s+(\w+)\s*\([^)]*\bStrEnum\b",
        )
        "Detect StrEnum class definitions."
        COMPAT_ALIAS_RE: Final[re.Pattern[str]] = re.compile(
            r"^([A-Z]\w+)\s*=\s*([A-Z]\w+)\s*$",
            re.MULTILINE,
        )
        "Detect compatibility alias assignments (X = Y)."
        CONSTANT_DICT_RE: Final[re.Pattern[str]] = re.compile(
            r"^([A-Z_]+)\s*=\s*\{",
            re.MULTILINE,
        )
        "Detect constant dict assignments."
        TYPE_ALIAS_OLD_RE: Final[re.Pattern[str]] = re.compile(
            r":\s*TypeAlias\s*=",
        )
        "Detect old-style TypeAlias annotations."
        TYPE_ALIAS_PEP695_RE: Final[re.Pattern[str]] = re.compile(
            r"^type\s+(\w+)\s*=",
            re.MULTILINE,
        )
        "Detect PEP 695 type alias statements."


__all__ = ["FlextInfraConstantsCensus"]
