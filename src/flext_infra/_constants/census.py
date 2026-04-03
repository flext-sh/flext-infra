"""Constants for the unified census pipeline — accessed via c.Infra.*."""

from __future__ import annotations

import re
from typing import Final


class FlextInfraConstantsCensus:
    """Census pipeline constants for object detection and classification."""

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
