"""Centralized constants for the core subpackage.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import re
from enum import IntEnum, StrEnum, unique
from pathlib import Path
from typing import TYPE_CHECKING, ClassVar

from flext_core import c

if TYPE_CHECKING:
    from flext_infra import t


class FlextInfraConstantsSharedInfra:
    """Shared infrastructure constants consumed by flext_infra.constants."""

    @unique
    class PytestConnectivityProperty(StrEnum):
        """Wire properties proving a connectivity prerequisite skip."""

        REASON = "flext_connectivity_prerequisite"
        PHASE = "flext_connectivity_prerequisite_phase"
        CAPABILITY = "flext_connectivity_prerequisite_capability"
        NODE = "flext_connectivity_prerequisite_node"

    @unique
    class PytestExitCode(IntEnum):
        """Pytest's documented process exit codes (external protocol)."""

        OK = 0
        TESTS_FAILED = 1
        INTERRUPTED = 2
        INTERNAL_ERROR = 3
        USAGE_ERROR = 4
        NO_TESTS_COLLECTED = 5

    @unique
    class ScriptExitCode(IntEnum):
        """Canonical exit codes for infra-owned validation scripts."""

        PASS = 0
        FAIL = 1
        USAGE = 2
        INFRA = 3

    FACADE_MODULE_DEPTH: ClassVar[int] = 3
    "Relative path part count for root facade modules (src/<pkg>/<file>.py)."
    FACADE_MINIMUM_BASES: ClassVar[int] = 2
    "Minimum explicit bases required by a canonical nested project facade."
    ALIAS_NAMES: ClassVar[frozenset[str]] = frozenset({
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
    CLASSVAR_ANNOTATION_NAMES: ClassVar[frozenset[str]] = frozenset({"ClassVar"})
    "Names treated as class-variable constant annotations."
    SKILLS_DIR: ClassVar[Path] = Path(".agents/skills")
    BASELINE_DEFAULT: ClassVar[str] = ".agents/skills/{skill}/baseline.json"
    CPROFILE_RECEIPT_ARGUMENT_COUNT: ClassVar[int] = 3
    "``argv`` length when an explicit run receipt accompanies the profile path."
    PYTHON_IMPORT_NAME_RE: ClassVar[t.RegexPattern] = re.compile(
        r"^[A-Za-z_][A-Za-z0-9_]*(\.[A-Za-z_][A-Za-z0-9_]*)*$",
    )
    MISSING_IMPORT_RE: ClassVar[t.RegexPattern] = re.compile(
        r"Cannot find module `([^`]+)` \[missing-import\]",
    )
    MYPY_HINT_RE: ClassVar[t.RegexPattern] = re.compile(
        r'note:\s+(?:hint|note):\s+(?:["`].*?\bpip\s+install\s+|install\s+stub\s+package\s+["`]?)'
        r'([A-Za-z0-9][A-Za-z0-9_.-]*)["`]?',
        re.IGNORECASE,
    )
    MYPY_BUILD_SOURCE_MARKER: ClassVar[str] = "Found source:"
    "Mypy verbose trace marker of one selected build source."
    MYPY_BUILD_SOURCE_RE: ClassVar[t.RegexPattern] = re.compile(
        r"Found source:\s+BuildSource\(path=(.+?), module=",
    )
    "Mypy verbose build source entry, capturing the path's Python literal."
    MYPY_BUILD_FINISHED_MARKER: ClassVar[str] = "Build finished in "
    "Mypy verbose trace marker proving the build completed."
    INTERNAL_PREFIXES: ClassVar[t.VariadicTuple[str]] = ("flext_", "flext-")

    # --- File names (was: class Files) ---
    PYPROJECT_FILENAME: ClassVar[str] = c.PYPROJECT_FILENAME
    MAKEFILE_FILENAME: ClassVar[str] = "Makefile"
    GITMODULES: ClassVar[str] = ".gitmodules"
    GITMODULE_MANAGED_KEY: ClassVar[str] = "flext-managed"
    GITMODULE_LAYER_KEY: ClassVar[str] = "flext-layer"
    "``.gitmodules`` key whose non-``true`` value opts a member out of governance."
    GITMODULE_SECTION_PREFIX: ClassVar[str] = "submodule."
    GITMODULE_PATH_KEY: ClassVar[str] = "path"
    GITMODULE_URL_KEY: ClassVar[str] = "url"
    GITMODULE_BRANCH_KEY: ClassVar[str] = "branch"
    FOLLOW_SUPERPROJECT_BRANCH: ClassVar[str] = "."
    GITIGNORE: ClassVar[str] = ".gitignore"
    PRE_COMMIT_CONFIG_FILENAME: ClassVar[str] = ".pre-commit-config.yaml"
    MARKDOWNLINT_CONFIG_FILENAME: ClassVar[str] = ".markdownlint.json"
    MARKDOWN_CONFIG_FILENAME: ClassVar[str] = ".rumdl.toml"
    MARKDOWNLINT_IGNORE_FILENAME: ClassVar[str] = ".markdownlintignore"
    "Generated markdown lint/format projections (SSOT: tooling.tools.markdown)."
    "Hook-config projection whose presence decides whether a checkout runs hooks."
    SONARCLOUD_PROPERTIES_FILENAME: ClassVar[str] = ".sonarcloud.properties"
    "Generated SonarCloud automatic-analysis scope (SSOT: codegen.sonarcloud)."
    SONARCLOUD_ISSUE_IGNORE_KEY: ClassVar[str] = "sonar.issue.ignore.multicriteria"
    "Server-side PROPERTY_SET that automatic analysis honors for issue exclusions."
    SONARCLOUD_API_AUTH_VALIDATE_PATH: ClassVar[str] = "/api/authentication/validate"
    SONARCLOUD_API_ISSUES_SEARCH_PATH: ClassVar[str] = "/api/issues/search"
    SONARCLOUD_ISSUES_SEARCH_LIMIT: ClassVar[int] = 10000
    "Maximum result window documented by SonarSource for issue search."
    SONARCLOUD_API_SETTINGS_VALUES_PATH: ClassVar[str] = "/api/settings/values"
    SONARCLOUD_API_SETTINGS_SET_PATH: ClassVar[str] = "/api/settings/set"
    SONARCLOUD_API_SETTINGS_RESET_PATH: ClassVar[str] = "/api/settings/reset"
    "SonarCloud web API routes of the proven settings-sync contract."
    SONARCLOUD_PROJECT_KEY_SEPARATOR: ClassVar[str] = "_"
    "Joins organization and repository into the SonarCloud project key."
    BEADS_CONFIG_RELPATH: ClassVar[str] = ".beads/config.yaml"
    BEADS_METADATA_RELPATH: ClassVar[str] = ".beads/metadata.json"
    "Generated project-owned Beads configuration paths."
    GITIGNORE_DERIVED_SECTION_NAME: ClassVar[str] = "Derived build and tool artifacts"
    "Heading of the trailing .gitignore section holding derived artifacts."
    GITIGNORE_MANAGED_SECTION_NAME: ClassVar[str] = "Tracked managed artifacts"
    "Heading of the trailing .gitignore section that re-allows managed files."
    GITIGNORE_LAYOUT_SECTION_NAME: ClassVar[str] = "Project layout exceptions"
    GITIGNORE_PROJECT_SECTION_NAME: ClassVar[str] = (
        "Project ignore patterns (config/*.yaml ManagedArtifacts.Gitignore)"
    )
    "Heading of the trailing .gitignore section holding layout-SSOT additions."
    MANAGED_FILE_POLICY_FULL: ClassVar[str] = "full"
    INIT_PY: ClassVar[str] = "__init__.py"
    API_PY: ClassVar[str] = "api.py"
    CONSTANTS_PY: ClassVar[str] = "constants.py"
    MODELS_PY: ClassVar[str] = "models.py"
    RESULT_PY: ClassVar[str] = "result.py"
    UTILITIES_PY: ClassVar[str] = "utilities.py"
    TYPINGS_PY: ClassVar[str] = "typings.py"
    PROTOCOLS_PY: ClassVar[str] = "protocols.py"
    PY_TYPED: ClassVar[str] = "py.typed"

    # --- Git constants (was: class Git) ---
    GIT_DIR: ClassVar[str] = c.GIT_DIR_NAME
    GIT_ORIGIN: ClassVar[str] = "origin"
    GIT_MAIN: ClassVar[str] = "main"
    GIT_HEAD: ClassVar[str] = "HEAD"

    # --- Package name prefixes (was: class Packages) ---
    PKG_CORE: ClassVar[str] = "flext-core"
    PKG_CORE_UNDERSCORE: ClassVar[str] = "flext_core"
    PKG_TESTS_UNDERSCORE: ClassVar[str] = "flext_tests"
    PKG_INFRA_UNDERSCORE: ClassVar[str] = "flext_infra"
    PKG_ROOT: ClassVar[str] = "flext"
    PKG_PREFIX_HYPHEN: ClassVar[str] = "flext-"
    PKG_PREFIX_UNDERSCORE: ClassVar[str] = "flext_"

    # --- Dunder names (was: class Dunders) ---
    DUNDER_ALL: ClassVar[str] = "__all__"
    DUNDER_VERSION: ClassVar[str] = "__version__"
    DUNDER_INIT: ClassVar[str] = "__init__"
    DUNDER_PYCACHE: ClassVar[str] = "__pycache__"

    # --- File extensions (was: class Extensions) ---
    EXT_PYTHON: ClassVar[str] = ".py"
    EXT_PYTHON_GLOB: ClassVar[str] = "*.py"
    EXT_PYTHON_STUB: ClassVar[str] = ".pyi"
    PYTHON_SOURCE_SUFFIXES: ClassVar[t.VariadicTuple[str]] = (
        EXT_PYTHON,
        EXT_PYTHON_STUB,
    )
    "Suffixes of Python source the rule engine scans: modules and stubs."

    # --- Directory names (was: class Directories) ---
    DIR_TESTS: ClassVar[str] = "tests"
    DIR_EXAMPLES: ClassVar[str] = "examples"
    DIR_SCRIPTS: ClassVar[str] = "scripts"
    "imports directly as the bottom of the c/t/p/m/u chain."
    DIR_DOCS: ClassVar[str] = "docs"
    DIR_BUILD: ClassVar[str] = "build"
    DIR_SITE: ClassVar[str] = "site"

    # --- Timeout values in seconds (was: class Timeouts) ---
    TIMEOUT_DEFAULT: ClassVar[int] = 300
    TIMEOUT_SHORT: ClassVar[int] = 60
    TIMEOUT_SHORT_POLL: ClassVar[int] = 2
    "Bounded wait proving a child is still blocked on a held owner lock."
    TIMEOUT_MEDIUM: ClassVar[int] = 120
    TIMEOUT_LONG: ClassVar[int] = 600
    TIMEOUT_CI: ClassVar[int] = 900

    # --- Path constants (was: class Paths) ---
    DEFAULT_SRC_DIR: ClassVar[str] = "src"

    # --- Fresh-process import probe templates ---
    FRESH_IMPORT_PRELUDE: ClassVar[str] = (
        "import importlib, sys\n"
        "from importlib.metadata import EntryPoint\n"
        "from pathlib import Path\n"
    )
    FRESH_IMPORT_EXPORT_IMPORT_CODE: ClassVar[str] = (
        "module = importlib.import_module({package!r})\n"
    )
    # The origin gate runs between the import and the name resolution: a
    # module loaded from outside this checkout must fail with the origin
    # error naming the foreign path, never with a phantom-attribute error
    # raised while resolving a stale export name.
    # After the exports resolve, every pydantic class reachable from them must
    # be complete at import: a deferred annotation would need the banned
    # ``model_rebuild`` or fail at first use.
    FRESH_IMPORT_EXPORT_RESOLVE_CODE: ClassVar[str] = (
        "for name in (*{exports!r}, *getattr(module, '__all__', ())):\n"
        "    getattr(module, name)\n"
        "from flext_infra.validate.fresh_import import "
        "FlextInfraValidateFreshImport as fresh_import_owner\n"
        "fresh_import_owner.require_complete_models(module)\n"
    )
    # Synthetic concat keeps the placeholder out of one plain literal: the
    # marker is template text substituted at render time, never an f-string.
    FRESH_IMPORT_ORIGINS_PLACEHOLDER: ClassVar[str] = "{" + "origins!r}"
    # The origin gate runs inside the same probe namespace as the export
    # resolution, so its loop names must never rebind the probed ``module``.
    FRESH_IMPORT_ORIGIN_CODE: ClassVar[str] = (
        "from flext_infra.workspace.environment_provenance import "
        "FlextInfraWorkspaceEnvironmentProvenance as native_origins\n"
        "for loaded_name in tuple(sys.modules):\n"
        "    for package, directory in {origins!r}:\n"
        "        if loaded_name == package or loaded_name.startswith(package + '.'):\n"
        "            origin = native_origins.module_source(loaded_name).unwrap()\n"
        "            if not origin.resolve().is_relative_to(Path(directory)):\n"
        "                raise ImportError(\n"
        "                    f'{loaded_name}: origin {origin!r} '\n"
        "                    f'is outside {directory}'\n"
        "                )\n"
    )


__all__: list[str] = ["FlextInfraConstantsSharedInfra"]
