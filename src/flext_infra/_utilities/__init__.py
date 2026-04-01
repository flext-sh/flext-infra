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

from collections.abc import Mapping, Sequence
from typing import TYPE_CHECKING as _TYPE_CHECKING

from flext_core.lazy import install_lazy_exports

if _TYPE_CHECKING:
    from flext_core import FlextTypes

    from flext_infra._utilities import (
        base,
        cli,
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

_LAZY_IMPORTS: Mapping[str, str | Sequence[str]] = {
    "FlextInfraUtilitiesBase": "flext_infra._utilities.base",
    "FlextInfraUtilitiesCli": "flext_infra._utilities.cli",
    "FlextInfraUtilitiesDiscovery": "flext_infra._utilities.discovery",
    "FlextInfraUtilitiesDocs": "flext_infra._utilities.docs",
    "FlextInfraUtilitiesFormatting": "flext_infra._utilities.formatting",
    "FlextInfraUtilitiesGit": "flext_infra._utilities.git",
    "FlextInfraUtilitiesGithub": "flext_infra._utilities.github",
    "FlextInfraUtilitiesIo": "flext_infra._utilities.io",
    "FlextInfraUtilitiesIteration": "flext_infra._utilities.iteration",
    "FlextInfraUtilitiesLogParser": "flext_infra._utilities.log_parser",
    "FlextInfraUtilitiesOutput": "flext_infra._utilities.output",
    "FlextInfraUtilitiesParsing": "flext_infra._utilities.parsing",
    "FlextInfraUtilitiesPaths": "flext_infra._utilities.paths",
    "FlextInfraUtilitiesPatterns": "flext_infra._utilities.patterns",
    "FlextInfraUtilitiesRelease": "flext_infra._utilities.release",
    "FlextInfraUtilitiesReporting": "flext_infra._utilities.reporting",
    "FlextInfraUtilitiesRope": "flext_infra._utilities.rope",
    "FlextInfraUtilitiesSafety": "flext_infra._utilities.safety",
    "FlextInfraUtilitiesSelection": "flext_infra._utilities.selection",
    "FlextInfraUtilitiesSubprocess": "flext_infra._utilities.subprocess",
    "FlextInfraUtilitiesTemplates": "flext_infra._utilities.templates",
    "FlextInfraUtilitiesTerminal": "flext_infra._utilities.terminal",
    "FlextInfraUtilitiesToml": "flext_infra._utilities.toml",
    "FlextInfraUtilitiesTomlParse": "flext_infra._utilities.toml_parse",
    "FlextInfraUtilitiesVersioning": "flext_infra._utilities.versioning",
    "FlextInfraUtilitiesYaml": "flext_infra._utilities.yaml",
    "base": "flext_infra._utilities.base",
    "cli": "flext_infra._utilities.cli",
    "discovery": "flext_infra._utilities.discovery",
    "docs": "flext_infra._utilities.docs",
    "formatting": "flext_infra._utilities.formatting",
    "git": "flext_infra._utilities.git",
    "github": "flext_infra._utilities.github",
    "io": "flext_infra._utilities.io",
    "iteration": "flext_infra._utilities.iteration",
    "log_parser": "flext_infra._utilities.log_parser",
    "output": "flext_infra._utilities.output",
    "parsing": "flext_infra._utilities.parsing",
    "paths": "flext_infra._utilities.paths",
    "patterns": "flext_infra._utilities.patterns",
    "release": "flext_infra._utilities.release",
    "reporting": "flext_infra._utilities.reporting",
    "rope": "flext_infra._utilities.rope",
    "safety": "flext_infra._utilities.safety",
    "selection": "flext_infra._utilities.selection",
    "subprocess": "flext_infra._utilities.subprocess",
    "templates": "flext_infra._utilities.templates",
    "terminal": "flext_infra._utilities.terminal",
    "toml": "flext_infra._utilities.toml",
    "toml_parse": "flext_infra._utilities.toml_parse",
    "versioning": "flext_infra._utilities.versioning",
    "yaml": "flext_infra._utilities.yaml",
}


install_lazy_exports(__name__, globals(), _LAZY_IMPORTS)
