"""Centralized constants for the deps subpackage."""

from __future__ import annotations

import re
from types import MappingProxyType
from typing import TYPE_CHECKING, Final

if TYPE_CHECKING:
    from flext_cli import t


class FlextInfraConstantsDeps:
    """Deps infrastructure constants."""

    # NOTE: Hardcoded base path constants removed.
    # All tool settings phases now use dynamic discovery via
    # u.Infra.discover_python_dirs() (SSOT in FlextInfraUtilitiesDiscovery).
    SKIP_DIRS: Final[frozenset[str]] = frozenset({
        ".archive",
        ".claude.disabled",
        ".git",
        ".mypy_cache",
        ".pytest_cache",
        ".ruff_cache",
        ".venv",
        "__pycache__",
        "build",
        "dist",
        "htmlcov",
        "node_modules",
        "site",
        "vendor",
    })
    DEP_NAME_RE: Final[t.RegexPattern] = re.compile(r"^\s*([A-Za-z0-9_.-]+)")
    PEP621_NAME_RE: Final[t.RegexPattern] = re.compile(r"^\s*(?P<name>[A-Za-z0-9_.-]+)")
    PEP621_REQUIREMENT_HEAD_RE: Final[t.RegexPattern] = re.compile(
        r"^\s*(?P<head>[A-Za-z0-9_.-]+(?:\[[^\]]+\])?)"
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
    COMMENT_MARKERS: Final[t.StrPairTuple] = (
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
    DEFAULT_MODULE_TO_TYPES_PACKAGE: Final[t.StrMapping] = MappingProxyType({
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
    })
    """Default mapping from module name to ``types-*`` stub package."""


__all__: list[str] = ["FlextInfraConstantsDeps"]
