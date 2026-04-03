# AUTO-GENERATED FILE — DO NOT EDIT MANUALLY.
# Regenerate with: make gen
#
"""Utilities package."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import TYPE_CHECKING as _TYPE_CHECKING

from flext_core.lazy import install_lazy_exports

if _TYPE_CHECKING:
    from flext_core import FlextTypes
    from flext_infra._utilities import (
        base,
        cli,
        cli_subcommand,
        codegen_constant_analysis,
        codegen_constant_detection,
        codegen_constant_transformation,
        codegen_execution,
        codegen_governance,
        codegen_import_cycles,
        codegen_lazy_aliases,
        codegen_lazy_scanning,
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
        rope_analysis,
        rope_core,
        rope_helpers,
        rope_imports,
        rope_source,
        rule_helpers,
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
    from flext_infra._utilities.cli_subcommand import FlextInfraUtilitiesCliSubcommand
    from flext_infra._utilities.codegen_constant_analysis import (
        FlextInfraUtilitiesCodegenConstantAnalysis,
    )
    from flext_infra._utilities.codegen_constant_detection import (
        FlextInfraUtilitiesCodegenConstantDetection,
    )
    from flext_infra._utilities.codegen_constant_transformation import (
        FlextInfraUtilitiesCodegenConstantTransformation,
    )
    from flext_infra._utilities.codegen_execution import (
        FlextInfraUtilitiesCodegenExecution,
    )
    from flext_infra._utilities.codegen_governance import (
        FlextInfraUtilitiesCodegenGovernance,
    )
    from flext_infra._utilities.codegen_import_cycles import (
        FlextInfraUtilitiesCodegenImportCycles,
    )
    from flext_infra._utilities.codegen_lazy_aliases import (
        FlextInfraUtilitiesCodegenLazyAliases,
    )
    from flext_infra._utilities.codegen_lazy_scanning import (
        FlextInfraUtilitiesCodegenLazyScanning,
    )
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
    from flext_infra._utilities.rope_analysis import FlextInfraUtilitiesRopeAnalysis
    from flext_infra._utilities.rope_core import FlextInfraUtilitiesRopeCore
    from flext_infra._utilities.rope_helpers import FlextInfraUtilitiesRopeHelpers
    from flext_infra._utilities.rope_imports import FlextInfraUtilitiesRopeImports
    from flext_infra._utilities.rope_source import FlextInfraUtilitiesRopeSource
    from flext_infra._utilities.rule_helpers import FlextInfraUtilitiesRuleHelpers
    from flext_infra._utilities.safety import FlextInfraUtilitiesSafety
    from flext_infra._utilities.selection import FlextInfraUtilitiesSelection
    from flext_infra._utilities.subprocess import FlextInfraUtilitiesSubprocess
    from flext_infra._utilities.templates import FlextInfraUtilitiesTemplates
    from flext_infra._utilities.terminal import FlextInfraUtilitiesTerminal
    from flext_infra._utilities.toml import FlextInfraUtilitiesToml
    from flext_infra._utilities.toml_parse import FlextInfraUtilitiesTomlParse
    from flext_infra._utilities.versioning import FlextInfraUtilitiesVersioning
    from flext_infra._utilities.yaml import FlextInfraUtilitiesYaml

_LAZY_IMPORTS: FlextTypes.LazyImportIndex = {
    "FlextInfraUtilitiesBase": "flext_infra._utilities.base",
    "FlextInfraUtilitiesCli": "flext_infra._utilities.cli",
    "FlextInfraUtilitiesCliSubcommand": "flext_infra._utilities.cli_subcommand",
    "FlextInfraUtilitiesCodegenConstantAnalysis": "flext_infra._utilities.codegen_constant_analysis",
    "FlextInfraUtilitiesCodegenConstantDetection": "flext_infra._utilities.codegen_constant_detection",
    "FlextInfraUtilitiesCodegenConstantTransformation": "flext_infra._utilities.codegen_constant_transformation",
    "FlextInfraUtilitiesCodegenExecution": "flext_infra._utilities.codegen_execution",
    "FlextInfraUtilitiesCodegenGovernance": "flext_infra._utilities.codegen_governance",
    "FlextInfraUtilitiesCodegenImportCycles": "flext_infra._utilities.codegen_import_cycles",
    "FlextInfraUtilitiesCodegenLazyAliases": "flext_infra._utilities.codegen_lazy_aliases",
    "FlextInfraUtilitiesCodegenLazyScanning": "flext_infra._utilities.codegen_lazy_scanning",
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
    "FlextInfraUtilitiesRopeAnalysis": "flext_infra._utilities.rope_analysis",
    "FlextInfraUtilitiesRopeCore": "flext_infra._utilities.rope_core",
    "FlextInfraUtilitiesRopeHelpers": "flext_infra._utilities.rope_helpers",
    "FlextInfraUtilitiesRopeImports": "flext_infra._utilities.rope_imports",
    "FlextInfraUtilitiesRopeSource": "flext_infra._utilities.rope_source",
    "FlextInfraUtilitiesRuleHelpers": "flext_infra._utilities.rule_helpers",
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
    "cli_subcommand": "flext_infra._utilities.cli_subcommand",
    "codegen_constant_analysis": "flext_infra._utilities.codegen_constant_analysis",
    "codegen_constant_detection": "flext_infra._utilities.codegen_constant_detection",
    "codegen_constant_transformation": "flext_infra._utilities.codegen_constant_transformation",
    "codegen_execution": "flext_infra._utilities.codegen_execution",
    "codegen_governance": "flext_infra._utilities.codegen_governance",
    "codegen_import_cycles": "flext_infra._utilities.codegen_import_cycles",
    "codegen_lazy_aliases": "flext_infra._utilities.codegen_lazy_aliases",
    "codegen_lazy_scanning": "flext_infra._utilities.codegen_lazy_scanning",
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
    "rope_analysis": "flext_infra._utilities.rope_analysis",
    "rope_core": "flext_infra._utilities.rope_core",
    "rope_helpers": "flext_infra._utilities.rope_helpers",
    "rope_imports": "flext_infra._utilities.rope_imports",
    "rope_source": "flext_infra._utilities.rope_source",
    "rule_helpers": "flext_infra._utilities.rule_helpers",
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
