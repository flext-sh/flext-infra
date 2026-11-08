"""Promoted-command framework vocabulary for flext-infra.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import re
from enum import StrEnum, unique
from typing import TYPE_CHECKING, ClassVar

from flext_cli import e
from flext_core import c

from flext_infra._constants import FlextInfraConstantsSharedInfra

if TYPE_CHECKING:
    from flext_core import t


class FlextInfraConstantsPromoted:
    """``scripts/<verb>/<WHAT>`` command framework vocabulary for ``c.Infra``."""

    class PromotedRegistryError(e.ValidationError):
        """Raised when promoted command metadata or invocation is invalid."""

        _default_error_code: ClassVar[str] = "PROMOTED_REGISTRY_ERROR"

    class PromotedMissingHeaderError(PromotedRegistryError):
        """Raised when a file carries no ``[tool.flext.command]`` header at all.

        A file without a header is not a promoted command; a present but invalid
        header is a defect, so the two never share an exception type.
        """

        _default_error_code: ClassVar[str] = "PROMOTED_MISSING_HEADER"

    @unique
    class PromotedHeader(StrEnum):
        """``[tool.flext.command]`` header TOML keys."""

        VERB = "verb"
        WHAT = "what"
        DOMAIN = "domain"
        SUMMARY = c.MetricType.SUMMARY
        DESCRIPTION = "description"
        EXAMPLE = "example"
        MUTATES = "mutates"
        ALIASES = "aliases"
        PARAMS = "params"
        RULES = "rules"
        NAME = "name"
        HELP = "help"
        REQUIRED = "required"
        DEFAULT = "default"
        CHOICES = "choices"
        PARAMS_CHOICES = "params.choices"

    @unique
    class PromotedEnv(StrEnum):
        """Environment variables read or exported by the promoted dispatcher."""

        WHAT = "WHAT"
        HELP = "HELP"
        OPTIONS = "OPTIONS"
        DISPATCHED = "FLEXT_COMMAND_DISPATCHED"
        VERB = "FLEXT_COMMAND_VERB"
        COMMAND_WHAT = "FLEXT_COMMAND_WHAT"
        DOMAIN = "FLEXT_COMMAND_DOMAIN"
        PATH = "FLEXT_COMMAND_PATH"
        SUBMODULE_ROOT = "FLEXT_SUBMODULE_ROOT"
        VIRTUAL_ENV = "VIRTUAL_ENV"
        UV_PROJECT_ENVIRONMENT = "UV_PROJECT_ENVIRONMENT"
        PYTHON = "PYTHON"

    @unique
    class PromotedSelector(StrEnum):
        """Reserved WHAT, argument, and separator tokens of the dispatcher."""

        ALL = "all"
        HELP = "help"
        WHAT = "WHAT"
        VALIDATE = "--validate"
        HELP_PATH = "/"
        ALIAS = "="
        DISPATCHED = "Y"
        DISABLED = "N"
        BASH = "bash"
        PYTHON_SAFE_PATH = "-P"
        VENV_BIN = "bin"
        VENV_PYTHON = "python"
        INCIDENT_DOMAIN = "incident"

    PROMOTED_WHAT_SEPARATOR: ClassVar[str] = "-"
    "Word separator of a public WHAT slug."
    PROMOTED_STEM_SEPARATOR: ClassVar[str] = "_"
    "Word separator a Python module stem uses where a WHAT slug uses ``-``."
    PROMOTED_HEADER_SCAN_LINES: ClassVar[int] = 160
    PROMOTED_HEADER_TABLE: ClassVar[tuple[str, ...]] = ("tool", "flext", "command")
    "Path of the command table inside the PEP 723 ``script`` block."
    PROMOTED_HEADER_INDENT: ClassVar[str] = "    "
    "Indentation of continued strings and one-per-line array elements."
    PROMOTED_HEADER_WORD_RE: ClassVar[t.RegexPattern] = re.compile(r"[^ ]+ *| +")
    "Regex: one word with its trailing spaces, or a leading run of spaces."
    PROMOTED_COMMAND_SUFFIXES: ClassVar[frozenset[str]] = frozenset({
        FlextInfraConstantsSharedInfra.EXT_SHELL,
        FlextInfraConstantsSharedInfra.EXT_PYTHON,
    })
    PROMOTED_NON_COMMAND_NAMES: ClassVar[frozenset[str]] = frozenset({
        FlextInfraConstantsSharedInfra.DUNDER_PYCACHE,
        FlextInfraConstantsSharedInfra.INIT_PY,
    })
    PROMOTED_IGNORED_DIRS: ClassVar[frozenset[str]] = frozenset({
        FlextInfraConstantsSharedInfra.DUNDER_PYCACHE,
        "hooks",
        "legado",
        "lib",
    })
    PROMOTED_INCIDENT_MUTATION_REQUIRED_PARAMS: ClassVar[frozenset[str]] = frozenset({
        "EMERGENCY",
        "BREAKING_GLASS_BEAD",
    })
    PROMOTED_VERB_HELP_SELECTORS: ClassVar[frozenset[str]] = frozenset({
        "",
        PromotedSelector.HELP,
    })
    PROMOTED_GLOBAL_HELP_SELECTORS: ClassVar[frozenset[str]] = frozenset({
        *PROMOTED_VERB_HELP_SELECTORS,
        PromotedSelector.ALL,
    })
    PROMOTED_HELP_ARGS: ClassVar[frozenset[str]] = frozenset({
        PromotedSelector.HELP,
        "--help",
        "-h",
    })
    PROMOTED_ENV_ENABLED_VALUES: ClassVar[frozenset[str]] = frozenset({
        c.ParserBooleanToken.ONE,
        "Y",
        "YES",
        "TRUE",
    })


__all__: list[str] = ["FlextInfraConstantsPromoted"]
