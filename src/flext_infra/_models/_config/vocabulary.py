"""Layer-zero vocabulary shared by workspace declarations and constants.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from enum import StrEnum, unique


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

    @unique
    class GateAcceptancePolicy(StrEnum):
        """Whether evidence claims clean quality or complete diagnostic execution."""

        CLEAN = "clean"
        COMPLETE_EXECUTION = "complete_execution"

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
        WORKFLOWS = "workflows"


__all__: list[str] = ["FlextInfraConfigVocabulary"]
