"""Centralized constants for the core subpackage."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Final


class FlextInfraConstantsSharedInfra:
    """Shared infrastructure constants consumed by flext_infra.constants."""

    EXEMPT_FILENAMES: Final[frozenset[str]] = frozenset({
        "__init__.py",
        "conftest.py",
        "__main__.py",
    })
    EXEMPT_PREFIXES: Final[frozenset[str]] = frozenset({"test_", "_"})
    ALIAS_NAMES: Final[frozenset[str]] = frozenset({
        "c",
        "t",
        "m",
        "p",
        "u",
        "r",
        "d",
        "e",
        "h",
        "s",
        "x",
        "tc",
    })
    DUNDER_ALLOWED: Final[frozenset[str]] = frozenset({"__all__", "__version__"})
    TYPEVAR_CALLABLES: Final[frozenset[str]] = frozenset({
        "TypeVar",
        "ParamSpec",
        "TypeVarTuple",
    })
    ENUM_BASES: Final[frozenset[str]] = frozenset({"StrEnum", "Enum", "IntEnum"})
    COLLECTION_CALLS: Final[frozenset[str]] = frozenset({
        "frozenset",
        "tuple",
        "dict",
        "list",
    })
    SKILLS_DIR: Final[Path] = Path(".claude/skills")
    REPORT_DEFAULT: Final[str] = ".claude/skills/{skill}/report.json"
    BASELINE_DEFAULT: Final[str] = ".claude/skills/{skill}/baseline.json"
    CACHE_TTL_SECONDS: Final[int] = 300
    MISSING_IMPORT_RE: Final[re.Pattern[str]] = re.compile(
        r"Cannot find module `([^`]+)` \[missing-import\]",
    )
    MYPY_HINT_RE: Final[re.Pattern[str]] = re.compile(
        r"note:\s+(?:hint|note):\s+.*?`(types-\S+)`",
    )
    MYPY_STUB_RE: Final[re.Pattern[str]] = re.compile(
        r"Library stubs not installed for ['\"](\S+?)['\"]",
    )
    INTERNAL_PREFIXES: Final[tuple[str, ...]] = ("flext_", "flext-")

    # --- File names (was: class Files) ---
    PYPROJECT_FILENAME: Final[str] = "pyproject.toml"
    MAKEFILE_FILENAME: Final[str] = "Makefile"
    BASE_MK: Final[str] = "base.mk"
    GO_MOD: Final[str] = "go.mod"
    GITMODULES: Final[str] = ".gitmodules"
    GITIGNORE: Final[str] = ".gitignore"
    INIT_PY: Final[str] = "__init__.py"
    API_PY: Final[str] = "api.py"
    CONSTANTS_PY: Final[str] = "constants.py"
    MODELS_PY: Final[str] = "models.py"
    UTILITIES_PY: Final[str] = "utilities.py"
    TYPINGS_PY: Final[str] = "typings.py"
    PROTOCOLS_PY: Final[str] = "protocols.py"
    CONFTEST_PY: Final[str] = "conftest.py"
    PY_TYPED: Final[str] = "py.typed"

    # --- Git constants (was: class Git) ---
    GIT_DIR: Final[str] = ".git"
    GIT_ORIGIN: Final[str] = "origin"
    GIT_MAIN: Final[str] = "main"
    GIT_HEAD: Final[str] = "HEAD"

    # --- Package name prefixes (was: class Packages) ---
    PKG_CORE: Final[str] = "flext-core"
    PKG_CORE_UNDERSCORE: Final[str] = "flext_core"
    PKG_ROOT: Final[str] = "flext"
    PKG_PREFIX_HYPHEN: Final[str] = "flext-"
    PKG_PREFIX_UNDERSCORE: Final[str] = "flext_"

    # --- Dunder names (was: class Dunders) ---
    DUNDER_ALL: Final[str] = "__all__"
    DUNDER_VERSION: Final[str] = "__version__"
    DUNDER_INIT: Final[str] = "__init__"
    DUNDER_FUTURE: Final[str] = "__future__"
    DUNDER_NAME: Final[str] = "__name__"
    DUNDER_FILE: Final[str] = "__file__"
    DUNDER_PYCACHE: Final[str] = "__pycache__"

    # --- File extensions (was: class Extensions) ---
    EXT_PYTHON: Final[str] = ".py"
    EXT_PYTHON_GLOB: Final[str] = "*.py"
    EXT_STUB: Final[str] = ".pyi"
    EXT_STUB_GLOB: Final[str] = "*.pyi"
    EXT_TOML: Final[str] = ".toml"
    EXT_YAML: Final[str] = ".yml"
    EXT_MARKDOWN: Final[str] = ".md"

    # --- Directory names (was: class Directories) ---
    DIR_TESTS: Final[str] = "tests"
    DIR_EXAMPLES: Final[str] = "examples"
    DIR_SCRIPTS: Final[str] = "scripts"
    DIR_TYPINGS: Final[str] = "typings"
    DIR_DOCS: Final[str] = "docs"
    DIR_BUILD: Final[str] = "build"
    DIR_DIST: Final[str] = "dist"
    DIR_SITE: Final[str] = "site"

    # --- Timeout values in seconds (was: class Timeouts) ---
    TIMEOUT_DEFAULT: Final[int] = 300
    TIMEOUT_SHORT: Final[int] = 60
    TIMEOUT_MEDIUM: Final[int] = 120
    TIMEOUT_LONG: Final[int] = 600
    TIMEOUT_CI: Final[int] = 900

    # --- Path constants (was: class Paths) ---
    WORKSPACE_MARKERS: Final[frozenset[str]] = frozenset({
        ".git",
        "Makefile",
        "pyproject.toml",
    })
    VENV_BIN_REL: Final[str] = ".venv/bin"
    DEFAULT_SRC_DIR: Final[str] = "src"


__all__ = ["FlextInfraConstantsSharedInfra"]
