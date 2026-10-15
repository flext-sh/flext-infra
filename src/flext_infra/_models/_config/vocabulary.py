"""Layer-zero vocabulary shared by workspace declarations and constants.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import re
from enum import StrEnum, unique
from types import MappingProxyType
from typing import ClassVar

from flext_cli import t


class FlextInfraConfigVocabulary:
    """Canonical closed contracts required before project facades initialize."""

    @unique
    class RepositoryState(StrEnum):
        """Lifecycle state used by repository selection."""

        ACTIVE = "active"
        EXCLUDED = "excluded"

    @unique
    class CodegenKind(StrEnum):
        """Code-generation policy applied to one repository."""

        CONFORM = "conform"
        PYTHON = "python"
        NONE = "none"

    @unique
    class ProjectKind(StrEnum):
        """Own governance profile; external forks retain upstream contracts."""

        INTERNAL_FLEXT = "internal_flext"
        INTERNAL = "internal"
        THIRD_PARTY_FORK = "third_party_fork"

    @unique
    class MakeProfile(StrEnum):
        """Generated Make profile proven by the repository checkout topology."""

        WORKSPACE = "workspace"
        STANDALONE = "standalone"

    class PytestCacheEnvironment(StrEnum):
        """OS and pytest-testmon keys consumed by the Make cache contract."""

        DATA_HOME = "XDG_CACHE_HOME"
        USER_HOME = "HOME"
        DATABASE_FILE = "TESTMON_DATAFILE"

    class MypyCacheEnvironment(StrEnum):
        """Mypy cache and XDG keys consumed by the Make cache contract."""

        CACHE_DIR = "MYPY_CACHE_DIR"
        DATA_HOME = "XDG_CACHE_HOME"
        USER_HOME = "HOME"

    @unique
    class GateKind(StrEnum):
        """Owner of a gate's rule catalog, independent of its execution engine."""

        EXTERNAL = "external"
        TYPE_CHECKER = "type-checker"
        INFRA = "infra"

    RUFF_UNSAFE_FIXES_FLAG: ClassVar[str] = "--unsafe-fixes"
    VERB_CHECK: ClassVar[str] = "check"
    VERB_TEST: ClassVar[str] = "test"
    CUSTOM_MAKE_FILENAME: ClassVar[str] = "custom.mk"
    AST_GREP_DOCS_URL: ClassVar[str] = "https://ast-grep.github.io/"
    LINT: ClassVar[str] = "lint"
    FORMAT: ClassVar[str] = "format"
    MARKDOWN: ClassVar[str] = "markdown"
    MARKDOWN_FORMAT: ClassVar[str] = "markdown-format"
    MARKDOWN_CODE: ClassVar[str] = "markdown-code"
    SMELLS: ClassVar[str] = "smells"
    RUNTIME_CENSUS: ClassVar[str] = "runtime-census"
    FRESH_IMPORT: ClassVar[str] = "fresh-import"
    CONFLICT_MARKERS: ClassVar[str] = "conflict-markers"
    DEPS: ClassVar[str] = "deps"

    GATE_TOOLS_BY_KIND: ClassVar[t.MappingKV[GateKind, t.MappingKV[str, t.StrPair]]] = (
        MappingProxyType({
            GateKind.EXTERNAL: MappingProxyType({
                "lint": ("Ruff Linter", "https://docs.astral.sh/ruff/"),
                "format": ("Ruff Formatter", "https://docs.astral.sh/ruff/formatter/"),
                "security": ("Bandit", "https://bandit.readthedocs.io/"),
                "markdown": ("rumdl", "https://rumdl.dev/"),
                "markdown-format": ("rumdl", "https://rumdl.dev/"),
                "markdown-code": ("Ruff", "https://docs.astral.sh/ruff/"),
                "duplication": ("jscpd", "https://github.com/kucherenko/jscpd"),
            }),
            GateKind.TYPE_CHECKER: MappingProxyType({
                "pyrefly": ("Pyrefly", "https://github.com/facebook/pyrefly"),
                "mypy": ("Mypy", "https://mypy.readthedocs.io/"),
                "pyright": ("Pyright", "https://github.com/microsoft/pyright"),
            }),
            GateKind.INFRA: MappingProxyType({
                CONFLICT_MARKERS: (
                    "Git Conflict Markers",
                    "internal://flext-infra/conflict-markers",
                ),
                "loc-cap": ("scc", "https://github.com/boyter/scc"),
                "runtime-census": (
                    "Flext Runtime Enforcement Census",
                    "internal://flext-infra/runtime-census",
                ),
                FRESH_IMPORT: (
                    "Flext Fresh-Process Import Gate",
                    "internal://flext-infra/fresh-import",
                ),
                DEPS: (
                    "Flext Dependency Declaration Gate",
                    "internal://flext-infra/deps",
                ),
                "index-declarations": (
                    "Flext Index Declarations Gate",
                    "internal://flext-infra/index-declarations",
                ),
                SMELLS: ("Flext Code Smell Detector", "internal://flext-infra/smells"),
                "codemod": ("ast-grep", AST_GREP_DOCS_URL),
                "layout": (
                    "Flext Project Layout Gate",
                    "internal://flext-infra/layout",
                ),
                "direnv": (
                    "Flext Direnv Environment Contract Gate",
                    "internal://flext-infra/direnv",
                ),
            }),
        })
    )
    """Sole gate registry; each gate is declared once under its catalog owner."""
    GATE_KINDS: ClassVar[t.MappingKV[str, GateKind]] = MappingProxyType({
        gate: kind for kind, tools in GATE_TOOLS_BY_KIND.items() for gate in tools
    })
    TYPE_CHECKER_GATES: ClassVar[frozenset[str]] = frozenset(
        GATE_TOOLS_BY_KIND[GateKind.TYPE_CHECKER],
    )
    SARIF_TOOL_INFO: ClassVar[t.MappingKV[str, t.StrPair]] = MappingProxyType({
        gate: tool
        for tools in GATE_TOOLS_BY_KIND.values()
        for gate, tool in tools.items()
    })
    ALLOWED_GATES: ClassVar[frozenset[str]] = frozenset(SARIF_TOOL_INFO)
    CANONICAL_GATE_IDS: ClassVar[t.VariadicTuple[str]] = tuple(SARIF_TOOL_INFO)
    CANONICAL_FIXABLE_GATE_IDS: ClassVar[t.VariadicTuple[str]] = (
        "lint",
        "markdown",
        "markdown-code",
    )
    """Independent repair policy; formatting remains owned by Make fmt."""

    @unique
    class RepositoryState(StrEnum):
        """Lifecycle state used by repository selection."""

        ACTIVE = "active"
        EXCLUDED = "excluded"

    @unique
    class CodegenKind(StrEnum):
        """Code-generation policy applied to one repository."""

        CONFORM = "conform"
        PYTHON = "python"
        NONE = "none"

    @unique
    class ProjectKind(StrEnum):
        """Own governance profile; external forks retain upstream contracts."""

        INTERNAL_FLEXT = "internal_flext"
        INTERNAL = "internal"
        THIRD_PARTY_FORK = "third_party_fork"

    @unique
    class GateAcceptancePolicy(StrEnum):
        """Whether evidence claims clean quality or complete diagnostic execution."""

        CLEAN = "clean"
        COMPLETE_EXECUTION = "complete_execution"

    RUFF_CACHE_ENVIRONMENT_VARIABLE: ClassVar[str] = "RUFF_CACHE_DIR"
    """Ruff's immutable external cache-directory environment contract."""

    DEPENDENCY_GROUPS: ClassVar[str] = "dependency-groups"
    """PEP 735 dependency-groups table key."""

    WORKSPACE_MANIFEST_VERSION: ClassVar[int] = 3

    CODEGEN_CONFIG_DIR: ClassVar[str] = "config"
    """Directory name for flext-infra config files relative to the package root."""

    CODEGEN_LOCAL_OVERRIDES_FILENAME: ClassVar[str] = "codegen-overrides.local.yaml"
    """Local operator override file name, excluded from the tracked baseline."""

    CODEGEN_ORG_OVERRIDES_FILENAME: ClassVar[str] = "codegen-org.yaml"
    """Governed repository org overrides file name."""

    GIT_COMMIT_OID_RE: ClassVar[t.RegexPattern] = re.compile(
        r"^(?:[0-9a-f]{40}|[0-9a-f]{64})$",
    )

    @unique
    class CodegenConformSurface(StrEnum):
        """Managed file selection accepted by canonical conform declarations."""

        ALL = "all"
        DEPENDENCIES = "dependencies"
        DOCS_CONFIG = "docs-config"
        ENVRC = "envrc"
        FACADES = "facades"
        LAZY_INIT = "lazy-init"
        MAKEFILE = "makefile"
        MISE_CONFIG = "mise-config"
        PYPROJECT = "pyproject"
        RUNTIME_BINDINGS = "runtime-bindings"
