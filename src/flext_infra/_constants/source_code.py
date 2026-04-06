"""Source code and detection constants for flext-infra project.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import re
from typing import Final

from flext_infra import t


class FlextInfraConstantsSourceCode:
    """Source code patterns, exclusion sets, and detection constants."""

    class Excluded:
        """Directory exclusion sets for analysis."""

        COMMON_EXCLUDED_DIRS: Final[frozenset[str]] = frozenset({
            ".git",
            ".venv",
            "node_modules",
            "__pycache__",
            "dist",
            "build",
            ".reports",
            ".mypy_cache",
            ".pytest_cache",
            ".ruff_cache",
        })
        "Common directories to exclude from analysis across all scripts."
        DOC_EXCLUDED_DIRS: Final[frozenset[str]] = COMMON_EXCLUDED_DIRS | {"site"}
        "Directories to exclude when analyzing documentation."
        PYPROJECT_SKIP_DIRS: Final[frozenset[str]] = COMMON_EXCLUDED_DIRS | {
            ".claude.disabled",
            ".flext-deps",
            ".sisyphus",
        }
        "Directories to skip when scanning pyproject.toml files."
        CHECK_EXCLUDED_DIRS: Final[frozenset[str]] = COMMON_EXCLUDED_DIRS | {
            ".flext-deps",
            "reports",
        }
        "Directories to exclude during quality checks."
        ITERATION_EXCLUDED_PARTS: Final[frozenset[str]] = COMMON_EXCLUDED_DIRS | {
            "dist-packages",
            "site-packages",
            "vendor",
            "venv",
        }
        "Path parts to skip during file iteration (superset of COMMON_EXCLUDED_DIRS)."

    class Encoding:
        """Encoding constants."""

        DEFAULT: Final[str] = "utf-8"
        "Default text encoding for file operations."

    class SourceCode:
        """Source code template constants and parsing patterns."""

        FUTURE_ANNOTATIONS: Final[str] = "from __future__ import annotations"
        "Standard future annotations import line."
        IMPORT_FROM_STRICT_RE: Final[re.Pattern[str]] = re.compile(
            r"^from\s+([\w.]+)\s+import\s+(.+)",
            re.MULTILINE,
        )
        "Regex: ``from <module> import <names>`` — anchored at col 0, no comment strip."
        IMPORT_RE: Final[re.Pattern[str]] = re.compile(
            r"^import\s+(.+)",
            re.MULTILINE,
        )
        "Regex: ``import <module>``."
        DEF_CLASS_RE: Final[re.Pattern[str]] = re.compile(
            r"^(?:def|async\s+def|class)\s+(\w+)",
            re.MULTILINE,
        )
        "Regex: ``def/async def/class <name>``."
        CLASS_NAME_RE: Final[re.Pattern[str]] = re.compile(
            r"^class\s+(\w+)",
            re.MULTILINE,
        )
        "Regex: any class definition — captures name only."
        CLASS_WITH_BASES_RE: Final[re.Pattern[str]] = re.compile(
            r"^class\s+(\w+)\s*\(([^)]*)\)\s*:",
            re.MULTILINE,
        )
        "Regex: ``class <name>(<bases>):`` — requires parentheses, captures bases."
        ASSIGN_RE: Final[re.Pattern[str]] = re.compile(
            r"^(\w+)\s*(?::.*)?=",
            re.MULTILINE,
        )
        "Regex: ``<name> [: ...] = ...`` assignment."
        FUNC_PARAM_RE: Final[re.Pattern[str]] = re.compile(
            r"^(?:def|async\s+def)\s+\w+\s*\(([^)]*)\)",
            re.MULTILINE | re.DOTALL,
        )
        "Regex: function parameter list."
        BARE_IMPORT_FROM_RE: Final[re.Pattern[str]] = re.compile(
            r"^\s*from\s+import\s",
            re.MULTILINE,
        )
        "Regex: malformed ``from import ...`` (missing module)."
        IMPORT_LINE_RE: Final[re.Pattern[str]] = re.compile(
            r"^\s*(?:from\s+\S+\s+import\s|import\s)",
            re.MULTILINE,
        )
        "Regex: any import line (from or import)."
        FUTURE_IMPORT_RE: Final[re.Pattern[str]] = re.compile(
            r"^\s*from\s+__future__\s+import\s",
        )
        "Regex: future import line."
        FROM_IMPORT_RE: Final[re.Pattern[str]] = re.compile(
            r"^\s*from\s+([\w.]+)\s+import\s+(.+?)(?:\s*#.*)?$",
            re.MULTILINE,
        )
        "Regex: from-import with optional trailing comment."
        FROM_IMPORT_BLOCK_RE: Final[re.Pattern[str]] = re.compile(
            r"^\s*from\s+([\w.]+)\s+import\s*\((.*?)\)",
            re.MULTILINE | re.DOTALL,
        )
        "Regex: multiline from-import block."
        DOCSTRING_RE: Final[re.Pattern[str]] = re.compile(
            r"""^\s*(?:'''|\"\"\"|\"|')""",
        )
        "Regex: docstring opening (single/triple quote)."
        CONSTANT_NAME_RE: Final[re.Pattern[str]] = re.compile(
            r"^_?[A-Z][A-Z0-9_]*$",
        )
        "Regex: constant name pattern (UPPER_CASE with optional leading underscore)."
        FINAL_ASSIGN_RE: Final[re.Pattern[str]] = re.compile(
            r"^(_?[A-Z][A-Z0-9_]*)\s*:\s*(?:Final|typing\.Final)(?:\[.*?\])?\s*=",
            re.MULTILINE,
        )
        "Regex: Final-annotated assignment (captures constant name)."
        DEPRECATED_RE: Final[re.Pattern[str]] = re.compile(
            r"^@deprecated.*\n(?:class|def)\s+(\w+).*?(?=\n(?:class |def |@|\Z))",
            re.MULTILINE | re.DOTALL,
        )
        "Regex: @deprecated decorated class/function block."
        WRAPPER_RE: Final[re.Pattern[str]] = re.compile(
            r"^def\s+(\w+)\s*\([^)]*\)[^:]*:\s*\n"
            r"\s+return\s+(\w+)\s*\([^)]*\)\s*$",
            re.MULTILINE,
        )
        "Regex: thin wrapper function (def f(): return g())."
        BYPASS_RE: Final[re.Pattern[str]] = re.compile(
            r"^try:\s*\n\s+from\s+\S+\s+import\s+\S+.*?\n"
            r"except\s+ImportError.*?(?=\n(?:class |def |@|try:|\Z))",
            re.MULTILINE | re.DOTALL,
        )
        "Regex: try/except ImportError bypass pattern."

    DEFAULT_CHECK_DIRS: Final[t.StrSequence] = (
        "src",
        "tests",
        "examples",
        "scripts",
    )
    "Default directories to check in a project (root only uses scripts)."
    CHECK_DIRS_SUBPROJECT: Final[t.StrSequence] = ("src", "tests", "examples")
    "Subprojects: type-check src/tests/examples only (scripts are workspace copies, run from root)."

    GITHUB_REPO_URL: Final[str] = "https://github.com/flext-sh/flext"
    "Official GitHub repository URL for the FLEXT project."
    GITHUB_REPO_NAME: Final[str] = "flext-sh/flext"
    "GitHub repository name in owner/repo format."

    class LogParser:
        """Log parsing and output constants."""

        TAIL_LINES: Final[int] = 50
        "Number of tail lines to extract from log output."
        ERROR_PATTERNS: Final[tuple[re.Pattern[str], ...]] = (
            re.compile(r"^\s*\S+\.py:\d+"),
            re.compile(r"^ERROR:", re.IGNORECASE),
            re.compile(r"^\s+\[B\d+\]"),
            re.compile(r"^FAIL:", re.IGNORECASE),
            re.compile(r"^error:", re.IGNORECASE),
            re.compile(r"^E\s+\w"),
            re.compile(r"^FAILED\s"),
        )
        "Regex patterns for identifying error lines in logs."
        NOISE_PATTERNS: Final[tuple[re.Pattern[str], ...]] = (
            re.compile(r"^make\["),
            re.compile(r"warning:\s+(overriding|ignoring)"),
            re.compile(r"^(Total|Success|Failed|Skipped):"),
            re.compile(r"^──\s"),
            re.compile(r"^INFO:"),
        )
        "Regex patterns for identifying noise lines in logs."

    class Tier:
        """Module tier classification constants."""

        UNKNOWN: Final[int] = 99
        "Tier value for unclassifiable modules."
        DEFAULT_SUBDIR: Final[int] = 4
        "Default tier for subpackage/subdirectory modules."

    class ClassPlacement:
        """Class placement detection constants."""

        PYDANTIC_BASE_NAMES: Final[frozenset[str]] = frozenset({
            "BaseModel",
            "FrozenModel",
            "ArbitraryTypesModel",
            "ContractModel",
            "FrozenValueModel",
            "TimestampedModel",
        })
        "Pydantic model base class names for placement detection."
        CANONICAL_MODEL_FILES: Final[frozenset[str]] = frozenset({
            "models.py",
            "_models.py",
        })
        "Canonical file names where Pydantic models should live."

    class Thresholds:
        """Shared threshold constants for analysis and transformations."""

        MIN_UNION_MEMBERS: Final[int] = 2
        "Minimum members for a union type to be normalizable."
        DICT_KEY_VALUE_ARITY: Final[int] = 2
        "Expected arity for dict key-value subscript."
        MIN_DUPLICATE_PROJECT_COUNT: Final[int] = 2
        "Minimum number of projects with same constant to flag as duplicate."
        SINGLE_LINE_DOCSTRING_QUOTE_COUNT: Final[int] = 2
        "Minimum quote count to detect single-line docstring."

    class Versioning:
        """Semantic versioning constants for version management."""

        PROJECT_SECTION: Final[str] = "[project]"
        "TOML section header for project metadata."
        SEMVER_RE: Final[re.Pattern[str]] = re.compile(
            r"^(\d+)\.(\d+)\.(\d+)(?:-dev)?$",
        )
        "Regex pattern for parsing semantic version strings."
        VALID_BUMP_TYPES: Final[frozenset[str]] = frozenset({
            "major",
            "minor",
            "patch",
        })
        "Allowed version bump type identifiers."

    class Reporting:
        """Reporting service constants for .reports/ path management."""

        REPORTS_DIR_NAME: Final[str] = ".reports"
        "Standard directory name for report output."


__all__ = ["FlextInfraConstantsSourceCode"]
