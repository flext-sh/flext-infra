"""Centralized constants for the deps subpackage."""

from __future__ import annotations

import re
from typing import Final

from flext_infra import t


class FlextInfraConstantsDeps:
    """Deps infrastructure constants."""

    # NOTE: Hardcoded base path constants removed.
    # All tool config phases now use dynamic discovery via
    # u.Infra.discover_python_dirs() (SSOT in FlextInfraUtilitiesDiscovery).
    GIT_REF_RE: Final[re.Pattern[str]] = re.compile(
        r"^[A-Za-z0-9][A-Za-z0-9._/-]{0,127}$",
    )
    GITHUB_REPO_URL_RE: Final[re.Pattern[str]] = re.compile(
        r"^(?:git@github\.com:[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+(?:\.git)?|https://github\.com/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+(?:\.git)?)$",
    )
    PEP621_PATH_RE: Final[re.Pattern[str]] = re.compile(r"@\s*(?:file:)?(?P<path>.+)$")
    SKIP_DIRS: Final[frozenset[str]] = frozenset({
        ".archive",
        ".claude.disabled",
        ".flext-deps",
        ".git",
        ".mypy_cache",
        ".pytest_cache",
        ".ruff_cache",
        ".sisyphus",
        ".venv",
        "__pycache__",
        "build",
        "dist",
        "htmlcov",
        "node_modules",
        "site",
        "vendor",
    })
    DEP_NAME_RE: Final[re.Pattern[str]] = re.compile(r"^\s*([A-Za-z0-9_.-]+)")
    FLEXT_DEPS_DIR: Final[str] = ".flext-deps"
    PEP621_PATH_DEP_RE: Final[re.Pattern[str]] = re.compile(
        r"^(?P<name>[A-Za-z0-9_.-]+)\s*@\s*(?:file:(?://)?)?(?P<path>.+)$",
    )
    PEP621_NAME_RE: Final[re.Pattern[str]] = re.compile(
        r"^\s*(?P<name>[A-Za-z0-9_.-]+)",
    )
    BANNER: Final[str] = (
        "# [MANAGED] FLEXT pyproject standardization\n# Sections with [MANAGED] are enforced by flext_infra.deps.modernizer.\n# Run `make mod` to regenerate all managed pyproject sections.\n# Sections with [CUSTOM] are project-specific extension points.\n"
    )
    DEV_OPTIONAL_DEPS_MARKER: Final[str] = (
        "# [MANAGED] consolidated development dependencies"
    )
    LEGACY_AUTO_MARKER: Final[str] = (
        "# [AUTO] merged from dev/docs/security/test/typings"
    )
    LEGACY_AUTO_BANNER_LINE: Final[str] = (
        "# Sections with [AUTO] are derived from workspace layout and dependencies."
    )
    COMMENT_MARKERS: Final[t.Infra.VariadicTuple[t.Infra.StrPair]] = (
        ("[build-system]", "# [MANAGED] build system"),
        ("[project]", "# [CUSTOM] project metadata"),
        ("[tool.poetry.group.dev.dependencies]", "# [CUSTOM] poetry dev extensions"),
        ("[tool.deptry]", "# [MANAGED] deptry"),
        ("[tool.ruff]", "# [MANAGED] ruff"),
        ("[tool.codespell]", "# [MANAGED] codespell"),
        ("[tool.tomlsort]", "# [MANAGED] tomlsort"),
        ("[tool.yamlfix]", "# [MANAGED] yamlfix"),
        ("[tool.pytest", "# [MANAGED] pytest"),
        ("[tool.coverage", "# [MANAGED] coverage"),
        ("[tool.mypy]", "# [MANAGED] mypy"),
        ("[tool.pydantic-mypy]", "# [MANAGED] pydantic-mypy"),
        ("[tool.pyrefly]", "# [MANAGED] pyrefly"),
        ("[tool.pyright]", "# [MANAGED] pyright"),
    )
    DEFAULT_MODULE_TO_TYPES_PACKAGE: Final[t.StrMapping] = {
        "yaml": "types-pyyaml",
        "ldap3": "types-ldap3",
        "redis": "types-redis",
        "requests": "types-requests",
        "setuptools": "types-setuptools",
        "toml": "types-toml",
        "dateutil": "types-python-dateutil",
        "psutil": "types-psutil",
        "psycopg2": "types-psycopg2",
        "protobuf": "types-protobuf",
        "pyyaml": "types-pyyaml",
        "decorator": "types-decorator",
        "jsonschema": "types-jsonschema",
        "openpyxl": "types-openpyxl",
        "xlrd": "types-xlrd",
    }
    """Default mapping from module name to ``types-*`` stub package."""


__all__ = ["FlextInfraConstantsDeps"]
