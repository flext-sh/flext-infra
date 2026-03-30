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
from typing import TYPE_CHECKING

from flext_core.lazy import install_lazy_exports

if TYPE_CHECKING:
    from flext_infra._utilities import (
        base as base,
        cli as cli,
        cst as cst,
        discovery as discovery,
        docs as docs,
        formatting as formatting,
        git as git,
        github as github,
        io as io,
        iteration as iteration,
        log_parser as log_parser,
        output as output,
        parsing as parsing,
        paths as paths,
        patterns as patterns,
        release as release,
        reporting as reporting,
        rope as rope,
        safety as safety,
        selection as selection,
        subprocess as subprocess,
        templates as templates,
        terminal as terminal,
        toml as toml,
        toml_parse as toml_parse,
        versioning as versioning,
        yaml as yaml,
    )
    from flext_infra._utilities.base import (
        FlextInfraUtilitiesBase as FlextInfraUtilitiesBase,
    )
    from flext_infra._utilities.cli import (
        FlextInfraUtilitiesCli as FlextInfraUtilitiesCli,
    )
    from flext_infra._utilities.cst import (
        FlextInfraUtilitiesCst as FlextInfraUtilitiesCst,
    )
    from flext_infra._utilities.discovery import (
        FlextInfraUtilitiesDiscovery as FlextInfraUtilitiesDiscovery,
    )
    from flext_infra._utilities.docs import (
        FlextInfraUtilitiesDocs as FlextInfraUtilitiesDocs,
    )
    from flext_infra._utilities.formatting import (
        FlextInfraUtilitiesFormatting as FlextInfraUtilitiesFormatting,
    )
    from flext_infra._utilities.git import (
        FlextInfraUtilitiesGit as FlextInfraUtilitiesGit,
    )
    from flext_infra._utilities.github import (
        FlextInfraUtilitiesGithub as FlextInfraUtilitiesGithub,
    )
    from flext_infra._utilities.io import FlextInfraUtilitiesIo as FlextInfraUtilitiesIo
    from flext_infra._utilities.iteration import (
        FlextInfraUtilitiesIteration as FlextInfraUtilitiesIteration,
    )
    from flext_infra._utilities.log_parser import (
        FlextInfraUtilitiesLogParser as FlextInfraUtilitiesLogParser,
    )
    from flext_infra._utilities.output import (
        FlextInfraUtilitiesOutput as FlextInfraUtilitiesOutput,
    )
    from flext_infra._utilities.parsing import (
        FlextInfraUtilitiesParsing as FlextInfraUtilitiesParsing,
    )
    from flext_infra._utilities.paths import (
        FlextInfraUtilitiesPaths as FlextInfraUtilitiesPaths,
    )
    from flext_infra._utilities.patterns import (
        FlextInfraUtilitiesPatterns as FlextInfraUtilitiesPatterns,
    )
    from flext_infra._utilities.release import (
        FlextInfraUtilitiesRelease as FlextInfraUtilitiesRelease,
    )
    from flext_infra._utilities.reporting import (
        FlextInfraUtilitiesReporting as FlextInfraUtilitiesReporting,
    )
    from flext_infra._utilities.rope import (
        FlextInfraUtilitiesRope as FlextInfraUtilitiesRope,
    )
    from flext_infra._utilities.safety import (
        FlextInfraUtilitiesSafety as FlextInfraUtilitiesSafety,
    )
    from flext_infra._utilities.selection import (
        FlextInfraUtilitiesSelection as FlextInfraUtilitiesSelection,
    )
    from flext_infra._utilities.subprocess import (
        FlextInfraUtilitiesSubprocess as FlextInfraUtilitiesSubprocess,
    )
    from flext_infra._utilities.templates import (
        FlextInfraUtilitiesTemplates as FlextInfraUtilitiesTemplates,
    )
    from flext_infra._utilities.terminal import (
        FlextInfraUtilitiesTerminal as FlextInfraUtilitiesTerminal,
    )
    from flext_infra._utilities.toml import (
        FlextInfraUtilitiesToml as FlextInfraUtilitiesToml,
    )
    from flext_infra._utilities.toml_parse import (
        FlextInfraUtilitiesTomlParse as FlextInfraUtilitiesTomlParse,
    )
    from flext_infra._utilities.versioning import (
        FlextInfraUtilitiesVersioning as FlextInfraUtilitiesVersioning,
    )
    from flext_infra._utilities.yaml import (
        FlextInfraUtilitiesYaml as FlextInfraUtilitiesYaml,
    )

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

_EXPORTS: Sequence[str] = [
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


install_lazy_exports(__name__, globals(), _LAZY_IMPORTS, _EXPORTS)
