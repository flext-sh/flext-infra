# AUTO-GENERATED FILE — DO NOT EDIT MANUALLY.
# Regenerate with: make gen
#
"""Infrastructure utility modules for flext-infra.

Organizes helper functions into domain-specific namespaces, following the
same pattern as flext_core._utilities.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Mapping, MutableMapping, Sequence
from typing import TYPE_CHECKING

from flext_core.lazy import cleanup_submodule_namespace, lazy_getattr

if TYPE_CHECKING:
    from flext_core import FlextTypes

    from flext_infra._utilities import (
        base,
        cli,
        cst,
        discovery,
        docs,
        formatting,
        git,
        github,
        io,
        iteration,
        log_parser,
        output,
        parsing,
        paths,
        patterns,
        release,
        reporting,
        rope,
        safety,
        selection,
        subprocess,
        templates,
        terminal,
        toml,
        toml_parse,
        versioning,
        yaml,
    )
    from flext_infra._utilities.base import FlextInfraUtilitiesBase
    from flext_infra._utilities.cli import FlextInfraUtilitiesCli
    from flext_infra._utilities.cst import FlextInfraUtilitiesCst
    from flext_infra._utilities.discovery import FlextInfraUtilitiesDiscovery
    from flext_infra._utilities.docs import FlextInfraUtilitiesDocs
    from flext_infra._utilities.formatting import FlextInfraUtilitiesFormatting
    from flext_infra._utilities.git import FlextInfraUtilitiesGit
    from flext_infra._utilities.github import FlextInfraUtilitiesGithub
    from flext_infra._utilities.io import FlextInfraUtilitiesIo
    from flext_infra._utilities.iteration import FlextInfraUtilitiesIteration
    from flext_infra._utilities.log_parser import FlextInfraUtilitiesLogParser
    from flext_infra._utilities.output import FlextInfraUtilitiesOutput
    from flext_infra._utilities.parsing import FlextInfraUtilitiesParsing
    from flext_infra._utilities.paths import FlextInfraUtilitiesPaths
    from flext_infra._utilities.patterns import FlextInfraUtilitiesPatterns
    from flext_infra._utilities.release import FlextInfraUtilitiesRelease
    from flext_infra._utilities.reporting import FlextInfraUtilitiesReporting
    from flext_infra._utilities.rope import FlextInfraUtilitiesRope
    from flext_infra._utilities.safety import FlextInfraUtilitiesSafety
    from flext_infra._utilities.selection import FlextInfraUtilitiesSelection
    from flext_infra._utilities.subprocess import FlextInfraUtilitiesSubprocess
    from flext_infra._utilities.templates import FlextInfraUtilitiesTemplates
    from flext_infra._utilities.terminal import FlextInfraUtilitiesTerminal
    from flext_infra._utilities.toml import FlextInfraUtilitiesToml
    from flext_infra._utilities.toml_parse import FlextInfraUtilitiesTomlParse
    from flext_infra._utilities.versioning import FlextInfraUtilitiesVersioning
    from flext_infra._utilities.yaml import FlextInfraUtilitiesYaml

_LAZY_IMPORTS: Mapping[str, Sequence[str]] = {
    "FlextInfraUtilitiesBase": [
        "flext_infra._utilities.base",
        "FlextInfraUtilitiesBase",
    ],
    "FlextInfraUtilitiesCli": ["flext_infra._utilities.cli", "FlextInfraUtilitiesCli"],
    "FlextInfraUtilitiesCst": ["flext_infra._utilities.cst", "FlextInfraUtilitiesCst"],
    "FlextInfraUtilitiesDiscovery": [
        "flext_infra._utilities.discovery",
        "FlextInfraUtilitiesDiscovery",
    ],
    "FlextInfraUtilitiesDocs": [
        "flext_infra._utilities.docs",
        "FlextInfraUtilitiesDocs",
    ],
    "FlextInfraUtilitiesFormatting": [
        "flext_infra._utilities.formatting",
        "FlextInfraUtilitiesFormatting",
    ],
    "FlextInfraUtilitiesGit": ["flext_infra._utilities.git", "FlextInfraUtilitiesGit"],
    "FlextInfraUtilitiesGithub": [
        "flext_infra._utilities.github",
        "FlextInfraUtilitiesGithub",
    ],
    "FlextInfraUtilitiesIo": ["flext_infra._utilities.io", "FlextInfraUtilitiesIo"],
    "FlextInfraUtilitiesIteration": [
        "flext_infra._utilities.iteration",
        "FlextInfraUtilitiesIteration",
    ],
    "FlextInfraUtilitiesLogParser": [
        "flext_infra._utilities.log_parser",
        "FlextInfraUtilitiesLogParser",
    ],
    "FlextInfraUtilitiesOutput": [
        "flext_infra._utilities.output",
        "FlextInfraUtilitiesOutput",
    ],
    "FlextInfraUtilitiesParsing": [
        "flext_infra._utilities.parsing",
        "FlextInfraUtilitiesParsing",
    ],
    "FlextInfraUtilitiesPaths": [
        "flext_infra._utilities.paths",
        "FlextInfraUtilitiesPaths",
    ],
    "FlextInfraUtilitiesPatterns": [
        "flext_infra._utilities.patterns",
        "FlextInfraUtilitiesPatterns",
    ],
    "FlextInfraUtilitiesRelease": [
        "flext_infra._utilities.release",
        "FlextInfraUtilitiesRelease",
    ],
    "FlextInfraUtilitiesReporting": [
        "flext_infra._utilities.reporting",
        "FlextInfraUtilitiesReporting",
    ],
    "FlextInfraUtilitiesRope": [
        "flext_infra._utilities.rope",
        "FlextInfraUtilitiesRope",
    ],
    "FlextInfraUtilitiesSafety": [
        "flext_infra._utilities.safety",
        "FlextInfraUtilitiesSafety",
    ],
    "FlextInfraUtilitiesSelection": [
        "flext_infra._utilities.selection",
        "FlextInfraUtilitiesSelection",
    ],
    "FlextInfraUtilitiesSubprocess": [
        "flext_infra._utilities.subprocess",
        "FlextInfraUtilitiesSubprocess",
    ],
    "FlextInfraUtilitiesTemplates": [
        "flext_infra._utilities.templates",
        "FlextInfraUtilitiesTemplates",
    ],
    "FlextInfraUtilitiesTerminal": [
        "flext_infra._utilities.terminal",
        "FlextInfraUtilitiesTerminal",
    ],
    "FlextInfraUtilitiesToml": [
        "flext_infra._utilities.toml",
        "FlextInfraUtilitiesToml",
    ],
    "FlextInfraUtilitiesTomlParse": [
        "flext_infra._utilities.toml_parse",
        "FlextInfraUtilitiesTomlParse",
    ],
    "FlextInfraUtilitiesVersioning": [
        "flext_infra._utilities.versioning",
        "FlextInfraUtilitiesVersioning",
    ],
    "FlextInfraUtilitiesYaml": [
        "flext_infra._utilities.yaml",
        "FlextInfraUtilitiesYaml",
    ],
    "base": ["flext_infra._utilities.base", ""],
    "cli": ["flext_infra._utilities.cli", ""],
    "cst": ["flext_infra._utilities.cst", ""],
    "discovery": ["flext_infra._utilities.discovery", ""],
    "docs": ["flext_infra._utilities.docs", ""],
    "formatting": ["flext_infra._utilities.formatting", ""],
    "git": ["flext_infra._utilities.git", ""],
    "github": ["flext_infra._utilities.github", ""],
    "io": ["flext_infra._utilities.io", ""],
    "iteration": ["flext_infra._utilities.iteration", ""],
    "log_parser": ["flext_infra._utilities.log_parser", ""],
    "output": ["flext_infra._utilities.output", ""],
    "parsing": ["flext_infra._utilities.parsing", ""],
    "paths": ["flext_infra._utilities.paths", ""],
    "patterns": ["flext_infra._utilities.patterns", ""],
    "release": ["flext_infra._utilities.release", ""],
    "reporting": ["flext_infra._utilities.reporting", ""],
    "rope": ["flext_infra._utilities.rope", ""],
    "safety": ["flext_infra._utilities.safety", ""],
    "selection": ["flext_infra._utilities.selection", ""],
    "subprocess": ["flext_infra._utilities.subprocess", ""],
    "templates": ["flext_infra._utilities.templates", ""],
    "terminal": ["flext_infra._utilities.terminal", ""],
    "toml": ["flext_infra._utilities.toml", ""],
    "toml_parse": ["flext_infra._utilities.toml_parse", ""],
    "versioning": ["flext_infra._utilities.versioning", ""],
    "yaml": ["flext_infra._utilities.yaml", ""],
}

__all__ = [
    "FlextInfraUtilitiesBase",
    "FlextInfraUtilitiesCli",
    "FlextInfraUtilitiesCst",
    "FlextInfraUtilitiesDiscovery",
    "FlextInfraUtilitiesDocs",
    "FlextInfraUtilitiesFormatting",
    "FlextInfraUtilitiesGit",
    "FlextInfraUtilitiesGithub",
    "FlextInfraUtilitiesIo",
    "FlextInfraUtilitiesIteration",
    "FlextInfraUtilitiesLogParser",
    "FlextInfraUtilitiesOutput",
    "FlextInfraUtilitiesParsing",
    "FlextInfraUtilitiesPaths",
    "FlextInfraUtilitiesPatterns",
    "FlextInfraUtilitiesRelease",
    "FlextInfraUtilitiesReporting",
    "FlextInfraUtilitiesRope",
    "FlextInfraUtilitiesSafety",
    "FlextInfraUtilitiesSelection",
    "FlextInfraUtilitiesSubprocess",
    "FlextInfraUtilitiesTemplates",
    "FlextInfraUtilitiesTerminal",
    "FlextInfraUtilitiesToml",
    "FlextInfraUtilitiesTomlParse",
    "FlextInfraUtilitiesVersioning",
    "FlextInfraUtilitiesYaml",
    "base",
    "cli",
    "cst",
    "discovery",
    "docs",
    "formatting",
    "git",
    "github",
    "io",
    "iteration",
    "log_parser",
    "output",
    "parsing",
    "paths",
    "patterns",
    "release",
    "reporting",
    "rope",
    "safety",
    "selection",
    "subprocess",
    "templates",
    "terminal",
    "toml",
    "toml_parse",
    "versioning",
    "yaml",
]


_LAZY_CACHE: MutableMapping[str, FlextTypes.ModuleExport] = {}


def __getattr__(name: str) -> FlextTypes.ModuleExport:
    """Lazy-load module attributes on first access (PEP 562).

    A local cache ``_LAZY_CACHE`` persists resolved objects across repeated
    accesses during process lifetime.

    Args:
        name: Attribute name requested by dir()/import.

    Returns:
        Lazy-loaded module export type.

    Raises:
        AttributeError: If attribute not registered.

    """
    if name in _LAZY_CACHE:
        return _LAZY_CACHE[name]

    value = lazy_getattr(name, _LAZY_IMPORTS, globals(), __name__)
    _LAZY_CACHE[name] = value
    return value


def __dir__() -> Sequence[str]:
    """Return list of available attributes for dir() and autocomplete.

    Returns:
        List of public names from module exports.

    """
    return sorted(__all__)


cleanup_submodule_namespace(__name__, _LAZY_IMPORTS)
