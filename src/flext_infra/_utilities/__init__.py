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
    from flext_infra._utilities.base import *
    from flext_infra._utilities.cli import *
    from flext_infra._utilities.cst import *
    from flext_infra._utilities.discovery import *
    from flext_infra._utilities.docs import *
    from flext_infra._utilities.formatting import *
    from flext_infra._utilities.git import *
    from flext_infra._utilities.github import *
    from flext_infra._utilities.io import *
    from flext_infra._utilities.iteration import *
    from flext_infra._utilities.log_parser import *
    from flext_infra._utilities.output import *
    from flext_infra._utilities.parsing import *
    from flext_infra._utilities.paths import *
    from flext_infra._utilities.patterns import *
    from flext_infra._utilities.release import *
    from flext_infra._utilities.reporting import *
    from flext_infra._utilities.rope import *
    from flext_infra._utilities.safety import *
    from flext_infra._utilities.selection import *
    from flext_infra._utilities.subprocess import *
    from flext_infra._utilities.templates import *
    from flext_infra._utilities.terminal import *
    from flext_infra._utilities.toml import *
    from flext_infra._utilities.toml_parse import *
    from flext_infra._utilities.versioning import *
    from flext_infra._utilities.yaml import *

_LAZY_IMPORTS: Mapping[str, str | Sequence[str]] = {
    "FlextInfraUtilitiesBase": "flext_infra._utilities.base",
    "FlextInfraUtilitiesCli": "flext_infra._utilities.cli",
    "FlextInfraUtilitiesCst": "flext_infra._utilities.cst",
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
    "cst": "flext_infra._utilities.cst",
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
