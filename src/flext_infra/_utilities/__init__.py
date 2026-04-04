# AUTO-GENERATED FILE — DO NOT EDIT MANUALLY.
# Regenerate with: make gen
#
"""Utilities package."""

from __future__ import annotations

import typing as _t

from flext_core.lazy import install_lazy_exports

if _t.TYPE_CHECKING:
    import flext_infra._utilities.base as _flext_infra__utilities_base

    base = _flext_infra__utilities_base
    import flext_infra._utilities.cli as _flext_infra__utilities_cli
    from flext_infra._utilities.base import FlextInfraUtilitiesBase

    cli = _flext_infra__utilities_cli
    import flext_infra._utilities.cli_shared as _flext_infra__utilities_cli_shared
    from flext_infra._utilities.cli import FlextInfraUtilitiesCli

    cli_shared = _flext_infra__utilities_cli_shared
    import flext_infra._utilities.cli_subcommand as _flext_infra__utilities_cli_subcommand
    from flext_infra._utilities.cli_shared import FlextInfraUtilitiesCliShared

    cli_subcommand = _flext_infra__utilities_cli_subcommand
    import flext_infra._utilities.codegen_constants as _flext_infra__utilities_codegen_constants
    from flext_infra._utilities.cli_subcommand import FlextInfraUtilitiesCliSubcommand

    codegen_constants = _flext_infra__utilities_codegen_constants
    import flext_infra._utilities.codegen_execution as _flext_infra__utilities_codegen_execution
    from flext_infra._utilities.codegen_constants import (
        FlextInfraUtilitiesCodegenConstantAnalysis,
        FlextInfraUtilitiesCodegenConstantDetection,
        FlextInfraUtilitiesCodegenConstantTransformation,
        FlextInfraUtilitiesCodegenGovernance,
    )

    codegen_execution = _flext_infra__utilities_codegen_execution
    import flext_infra._utilities.codegen_generation as _flext_infra__utilities_codegen_generation
    from flext_infra._utilities.codegen_execution import (
        FlextInfraUtilitiesCodegenExecution,
    )

    codegen_generation = _flext_infra__utilities_codegen_generation
    import flext_infra._utilities.codegen_import_cycles as _flext_infra__utilities_codegen_import_cycles

    codegen_import_cycles = _flext_infra__utilities_codegen_import_cycles
    import flext_infra._utilities.codegen_lazy as _flext_infra__utilities_codegen_lazy
    from flext_infra._utilities.codegen_import_cycles import (
        FlextInfraUtilitiesCodegenImportCycles,
    )

    codegen_lazy = _flext_infra__utilities_codegen_lazy
    import flext_infra._utilities.deps_paths as _flext_infra__utilities_deps_paths
    from flext_infra._utilities.codegen_lazy import (
        FlextInfraUtilitiesCodegenLazyAliases,
        FlextInfraUtilitiesCodegenLazyMerging,
        FlextInfraUtilitiesCodegenLazyScanning,
    )

    deps_paths = _flext_infra__utilities_deps_paths
    import flext_infra._utilities.deps_repos as _flext_infra__utilities_deps_repos
    from flext_infra._utilities.deps_paths import FlextInfraExtraPathsResolutionMixin

    deps_repos = _flext_infra__utilities_deps_repos
    import flext_infra._utilities.discovery as _flext_infra__utilities_discovery
    from flext_infra._utilities.deps_repos import FlextInfraInternalSyncRepoMixin

    discovery = _flext_infra__utilities_discovery
    import flext_infra._utilities.discovery_scanning as _flext_infra__utilities_discovery_scanning
    from flext_infra._utilities.discovery import FlextInfraUtilitiesDiscovery

    discovery_scanning = _flext_infra__utilities_discovery_scanning
    import flext_infra._utilities.docs as _flext_infra__utilities_docs
    from flext_infra._utilities.discovery_scanning import (
        FlextInfraUtilitiesDiscoveryScanning,
    )

    docs = _flext_infra__utilities_docs
    import flext_infra._utilities.formatting as _flext_infra__utilities_formatting
    from flext_infra._utilities.docs import FlextInfraUtilitiesDocs

    formatting = _flext_infra__utilities_formatting
    import flext_infra._utilities.git as _flext_infra__utilities_git
    from flext_infra._utilities.formatting import FlextInfraUtilitiesFormatting

    git = _flext_infra__utilities_git
    import flext_infra._utilities.github as _flext_infra__utilities_github
    from flext_infra._utilities.git import FlextInfraUtilitiesGit

    github = _flext_infra__utilities_github
    import flext_infra._utilities.github_pr as _flext_infra__utilities_github_pr
    from flext_infra._utilities.github import FlextInfraUtilitiesGithub

    github_pr = _flext_infra__utilities_github_pr
    import flext_infra._utilities.io as _flext_infra__utilities_io
    from flext_infra._utilities.github_pr import FlextInfraUtilitiesGithubPr

    io = _flext_infra__utilities_io
    import flext_infra._utilities.iteration as _flext_infra__utilities_iteration
    from flext_infra._utilities.io import FlextInfraUtilitiesIo

    iteration = _flext_infra__utilities_iteration
    import flext_infra._utilities.log_parser as _flext_infra__utilities_log_parser
    from flext_infra._utilities.iteration import FlextInfraUtilitiesIteration

    log_parser = _flext_infra__utilities_log_parser
    import flext_infra._utilities.output as _flext_infra__utilities_output
    from flext_infra._utilities.log_parser import FlextInfraUtilitiesLogParser

    output = _flext_infra__utilities_output
    import flext_infra._utilities.output_reporting as _flext_infra__utilities_output_reporting
    from flext_infra._utilities.output import FlextInfraUtilitiesOutput

    output_reporting = _flext_infra__utilities_output_reporting
    import flext_infra._utilities.parsing as _flext_infra__utilities_parsing
    from flext_infra._utilities.output_reporting import (
        FlextInfraUtilitiesOutputReporting,
    )

    parsing = _flext_infra__utilities_parsing
    import flext_infra._utilities.paths as _flext_infra__utilities_paths
    from flext_infra._utilities.parsing import FlextInfraUtilitiesParsing

    paths = _flext_infra__utilities_paths
    import flext_infra._utilities.patterns as _flext_infra__utilities_patterns
    from flext_infra._utilities.paths import FlextInfraUtilitiesPaths

    patterns = _flext_infra__utilities_patterns
    import flext_infra._utilities.release as _flext_infra__utilities_release
    from flext_infra._utilities.patterns import FlextInfraUtilitiesPatterns

    release = _flext_infra__utilities_release
    import flext_infra._utilities.reporting as _flext_infra__utilities_reporting
    from flext_infra._utilities.release import FlextInfraUtilitiesRelease

    reporting = _flext_infra__utilities_reporting
    import flext_infra._utilities.rope as _flext_infra__utilities_rope
    from flext_infra._utilities.reporting import FlextInfraUtilitiesReporting

    rope = _flext_infra__utilities_rope
    import flext_infra._utilities.rope_analysis as _flext_infra__utilities_rope_analysis
    from flext_infra._utilities.rope import FlextInfraUtilitiesRope

    rope_analysis = _flext_infra__utilities_rope_analysis
    import flext_infra._utilities.rope_analysis_introspection as _flext_infra__utilities_rope_analysis_introspection
    from flext_infra._utilities.rope_analysis import FlextInfraUtilitiesRopeAnalysis

    rope_analysis_introspection = _flext_infra__utilities_rope_analysis_introspection
    import flext_infra._utilities.rope_core as _flext_infra__utilities_rope_core
    from flext_infra._utilities.rope_analysis_introspection import (
        FlextInfraUtilitiesRopeAnalysisIntrospection,
    )

    rope_core = _flext_infra__utilities_rope_core
    import flext_infra._utilities.rope_helpers as _flext_infra__utilities_rope_helpers
    from flext_infra._utilities.rope_core import FlextInfraUtilitiesRopeCore

    rope_helpers = _flext_infra__utilities_rope_helpers
    import flext_infra._utilities.rope_imports as _flext_infra__utilities_rope_imports
    from flext_infra._utilities.rope_helpers import FlextInfraUtilitiesRopeHelpers

    rope_imports = _flext_infra__utilities_rope_imports
    import flext_infra._utilities.rope_source as _flext_infra__utilities_rope_source
    from flext_infra._utilities.rope_imports import FlextInfraUtilitiesRopeImports

    rope_source = _flext_infra__utilities_rope_source
    import flext_infra._utilities.safety as _flext_infra__utilities_safety
    from flext_infra._utilities.rope_source import FlextInfraUtilitiesRopeSource

    safety = _flext_infra__utilities_safety
    import flext_infra._utilities.selection as _flext_infra__utilities_selection
    from flext_infra._utilities.safety import FlextInfraUtilitiesSafety

    selection = _flext_infra__utilities_selection
    import flext_infra._utilities.subprocess as _flext_infra__utilities_subprocess
    from flext_infra._utilities.selection import FlextInfraUtilitiesSelection

    subprocess = _flext_infra__utilities_subprocess
    import flext_infra._utilities.templates as _flext_infra__utilities_templates
    from flext_infra._utilities.subprocess import FlextInfraUtilitiesSubprocess

    templates = _flext_infra__utilities_templates
    import flext_infra._utilities.terminal as _flext_infra__utilities_terminal
    from flext_infra._utilities.templates import FlextInfraUtilitiesTemplates

    terminal = _flext_infra__utilities_terminal
    import flext_infra._utilities.toml as _flext_infra__utilities_toml
    from flext_infra._utilities.terminal import FlextInfraUtilitiesTerminal

    toml = _flext_infra__utilities_toml
    import flext_infra._utilities.toml_parse as _flext_infra__utilities_toml_parse
    from flext_infra._utilities.toml import FlextInfraUtilitiesToml

    toml_parse = _flext_infra__utilities_toml_parse
    import flext_infra._utilities.versioning as _flext_infra__utilities_versioning
    from flext_infra._utilities.toml_parse import FlextInfraUtilitiesTomlParse

    versioning = _flext_infra__utilities_versioning
    import flext_infra._utilities.yaml as _flext_infra__utilities_yaml
    from flext_infra._utilities.versioning import FlextInfraUtilitiesVersioning

    yaml = _flext_infra__utilities_yaml
    from flext_infra._utilities.yaml import FlextInfraUtilitiesYaml
_LAZY_IMPORTS = {
    "FlextInfraExtraPathsResolutionMixin": "flext_infra._utilities.deps_paths",
    "FlextInfraInternalSyncRepoMixin": "flext_infra._utilities.deps_repos",
    "FlextInfraUtilitiesBase": "flext_infra._utilities.base",
    "FlextInfraUtilitiesCli": "flext_infra._utilities.cli",
    "FlextInfraUtilitiesCliShared": "flext_infra._utilities.cli_shared",
    "FlextInfraUtilitiesCliSubcommand": "flext_infra._utilities.cli_subcommand",
    "FlextInfraUtilitiesCodegenConstantAnalysis": "flext_infra._utilities.codegen_constants",
    "FlextInfraUtilitiesCodegenConstantDetection": "flext_infra._utilities.codegen_constants",
    "FlextInfraUtilitiesCodegenConstantTransformation": "flext_infra._utilities.codegen_constants",
    "FlextInfraUtilitiesCodegenExecution": "flext_infra._utilities.codegen_execution",
    "FlextInfraUtilitiesCodegenGovernance": "flext_infra._utilities.codegen_constants",
    "FlextInfraUtilitiesCodegenImportCycles": "flext_infra._utilities.codegen_import_cycles",
    "FlextInfraUtilitiesCodegenLazyAliases": "flext_infra._utilities.codegen_lazy",
    "FlextInfraUtilitiesCodegenLazyMerging": "flext_infra._utilities.codegen_lazy",
    "FlextInfraUtilitiesCodegenLazyScanning": "flext_infra._utilities.codegen_lazy",
    "FlextInfraUtilitiesDiscovery": "flext_infra._utilities.discovery",
    "FlextInfraUtilitiesDiscoveryScanning": "flext_infra._utilities.discovery_scanning",
    "FlextInfraUtilitiesDocs": "flext_infra._utilities.docs",
    "FlextInfraUtilitiesFormatting": "flext_infra._utilities.formatting",
    "FlextInfraUtilitiesGit": "flext_infra._utilities.git",
    "FlextInfraUtilitiesGithub": "flext_infra._utilities.github",
    "FlextInfraUtilitiesGithubPr": "flext_infra._utilities.github_pr",
    "FlextInfraUtilitiesIo": "flext_infra._utilities.io",
    "FlextInfraUtilitiesIteration": "flext_infra._utilities.iteration",
    "FlextInfraUtilitiesLogParser": "flext_infra._utilities.log_parser",
    "FlextInfraUtilitiesOutput": "flext_infra._utilities.output",
    "FlextInfraUtilitiesOutputReporting": "flext_infra._utilities.output_reporting",
    "FlextInfraUtilitiesParsing": "flext_infra._utilities.parsing",
    "FlextInfraUtilitiesPaths": "flext_infra._utilities.paths",
    "FlextInfraUtilitiesPatterns": "flext_infra._utilities.patterns",
    "FlextInfraUtilitiesRelease": "flext_infra._utilities.release",
    "FlextInfraUtilitiesReporting": "flext_infra._utilities.reporting",
    "FlextInfraUtilitiesRope": "flext_infra._utilities.rope",
    "FlextInfraUtilitiesRopeAnalysis": "flext_infra._utilities.rope_analysis",
    "FlextInfraUtilitiesRopeAnalysisIntrospection": "flext_infra._utilities.rope_analysis_introspection",
    "FlextInfraUtilitiesRopeCore": "flext_infra._utilities.rope_core",
    "FlextInfraUtilitiesRopeHelpers": "flext_infra._utilities.rope_helpers",
    "FlextInfraUtilitiesRopeImports": "flext_infra._utilities.rope_imports",
    "FlextInfraUtilitiesRopeSource": "flext_infra._utilities.rope_source",
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
    "cli_shared": "flext_infra._utilities.cli_shared",
    "cli_subcommand": "flext_infra._utilities.cli_subcommand",
    "codegen_constants": "flext_infra._utilities.codegen_constants",
    "codegen_execution": "flext_infra._utilities.codegen_execution",
    "codegen_generation": "flext_infra._utilities.codegen_generation",
    "codegen_import_cycles": "flext_infra._utilities.codegen_import_cycles",
    "codegen_lazy": "flext_infra._utilities.codegen_lazy",
    "deps_paths": "flext_infra._utilities.deps_paths",
    "deps_repos": "flext_infra._utilities.deps_repos",
    "discovery": "flext_infra._utilities.discovery",
    "discovery_scanning": "flext_infra._utilities.discovery_scanning",
    "docs": "flext_infra._utilities.docs",
    "formatting": "flext_infra._utilities.formatting",
    "git": "flext_infra._utilities.git",
    "github": "flext_infra._utilities.github",
    "github_pr": "flext_infra._utilities.github_pr",
    "io": "flext_infra._utilities.io",
    "iteration": "flext_infra._utilities.iteration",
    "log_parser": "flext_infra._utilities.log_parser",
    "output": "flext_infra._utilities.output",
    "output_reporting": "flext_infra._utilities.output_reporting",
    "parsing": "flext_infra._utilities.parsing",
    "paths": "flext_infra._utilities.paths",
    "patterns": "flext_infra._utilities.patterns",
    "release": "flext_infra._utilities.release",
    "reporting": "flext_infra._utilities.reporting",
    "rope": "flext_infra._utilities.rope",
    "rope_analysis": "flext_infra._utilities.rope_analysis",
    "rope_analysis_introspection": "flext_infra._utilities.rope_analysis_introspection",
    "rope_core": "flext_infra._utilities.rope_core",
    "rope_helpers": "flext_infra._utilities.rope_helpers",
    "rope_imports": "flext_infra._utilities.rope_imports",
    "rope_source": "flext_infra._utilities.rope_source",
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

__all__ = [
    "FlextInfraExtraPathsResolutionMixin",
    "FlextInfraInternalSyncRepoMixin",
    "FlextInfraUtilitiesBase",
    "FlextInfraUtilitiesCli",
    "FlextInfraUtilitiesCliShared",
    "FlextInfraUtilitiesCliSubcommand",
    "FlextInfraUtilitiesCodegenConstantAnalysis",
    "FlextInfraUtilitiesCodegenConstantDetection",
    "FlextInfraUtilitiesCodegenConstantTransformation",
    "FlextInfraUtilitiesCodegenExecution",
    "FlextInfraUtilitiesCodegenGovernance",
    "FlextInfraUtilitiesCodegenImportCycles",
    "FlextInfraUtilitiesCodegenLazyAliases",
    "FlextInfraUtilitiesCodegenLazyMerging",
    "FlextInfraUtilitiesCodegenLazyScanning",
    "FlextInfraUtilitiesDiscovery",
    "FlextInfraUtilitiesDiscoveryScanning",
    "FlextInfraUtilitiesDocs",
    "FlextInfraUtilitiesFormatting",
    "FlextInfraUtilitiesGit",
    "FlextInfraUtilitiesGithub",
    "FlextInfraUtilitiesGithubPr",
    "FlextInfraUtilitiesIo",
    "FlextInfraUtilitiesIteration",
    "FlextInfraUtilitiesLogParser",
    "FlextInfraUtilitiesOutput",
    "FlextInfraUtilitiesOutputReporting",
    "FlextInfraUtilitiesParsing",
    "FlextInfraUtilitiesPaths",
    "FlextInfraUtilitiesPatterns",
    "FlextInfraUtilitiesRelease",
    "FlextInfraUtilitiesReporting",
    "FlextInfraUtilitiesRope",
    "FlextInfraUtilitiesRopeAnalysis",
    "FlextInfraUtilitiesRopeAnalysisIntrospection",
    "FlextInfraUtilitiesRopeCore",
    "FlextInfraUtilitiesRopeHelpers",
    "FlextInfraUtilitiesRopeImports",
    "FlextInfraUtilitiesRopeSource",
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
    "cli_shared",
    "cli_subcommand",
    "codegen_constants",
    "codegen_execution",
    "codegen_generation",
    "codegen_import_cycles",
    "codegen_lazy",
    "deps_paths",
    "deps_repos",
    "discovery",
    "discovery_scanning",
    "docs",
    "formatting",
    "git",
    "github",
    "github_pr",
    "io",
    "iteration",
    "log_parser",
    "output",
    "output_reporting",
    "parsing",
    "paths",
    "patterns",
    "release",
    "reporting",
    "rope",
    "rope_analysis",
    "rope_analysis_introspection",
    "rope_core",
    "rope_helpers",
    "rope_imports",
    "rope_source",
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


install_lazy_exports(__name__, globals(), _LAZY_IMPORTS)
