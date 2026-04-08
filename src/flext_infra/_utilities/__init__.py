# AUTO-GENERATED FILE — DO NOT EDIT MANUALLY.
# Regenerate with: make gen
#
"""Utilities package."""

from __future__ import annotations

import typing as _t

from flext_core.lazy import install_lazy_exports

if _t.TYPE_CHECKING:
    import flext_infra._utilities._utilities as _flext_infra__utilities__utilities

    _utilities = _flext_infra__utilities__utilities
    import flext_infra._utilities._utilities_census as _flext_infra__utilities__utilities_census
    from flext_infra._utilities._utilities import FlextInfraUtilitiesRefactor

    _utilities_census = _flext_infra__utilities__utilities_census
    import flext_infra._utilities._utilities_cli as _flext_infra__utilities__utilities_cli
    from flext_infra._utilities._utilities_census import (
        FlextInfraUtilitiesRefactorCensus,
    )

    _utilities_cli = _flext_infra__utilities__utilities_cli
    import flext_infra._utilities._utilities_engine as _flext_infra__utilities__utilities_engine
    from flext_infra._utilities._utilities_cli import FlextInfraUtilitiesRefactorCli

    _utilities_engine = _flext_infra__utilities__utilities_engine
    import flext_infra._utilities._utilities_mro_scan as _flext_infra__utilities__utilities_mro_scan
    from flext_infra._utilities._utilities_engine import (
        FlextInfraUtilitiesRefactorEngine,
    )

    _utilities_mro_scan = _flext_infra__utilities__utilities_mro_scan
    import flext_infra._utilities._utilities_mro_transform as _flext_infra__utilities__utilities_mro_transform
    from flext_infra._utilities._utilities_mro_scan import (
        FlextInfraUtilitiesRefactorMroScan,
    )

    _utilities_mro_transform = _flext_infra__utilities__utilities_mro_transform
    import flext_infra._utilities._utilities_namespace as _flext_infra__utilities__utilities_namespace
    from flext_infra._utilities._utilities_mro_transform import (
        FlextInfraUtilitiesRefactorMroTransform,
    )

    _utilities_namespace = _flext_infra__utilities__utilities_namespace
    import flext_infra._utilities._utilities_namespace_analysis as _flext_infra__utilities__utilities_namespace_analysis
    from flext_infra._utilities._utilities_namespace import (
        FlextInfraUtilitiesRefactorNamespace,
    )

    _utilities_namespace_analysis = (
        _flext_infra__utilities__utilities_namespace_analysis
    )
    import flext_infra._utilities._utilities_namespace_facades as _flext_infra__utilities__utilities_namespace_facades
    from flext_infra._utilities._utilities_namespace_analysis import (
        FlextInfraUtilitiesRefactorNamespaceCommon,
        FlextInfraUtilitiesRefactorNamespaceMro,
    )

    _utilities_namespace_facades = _flext_infra__utilities__utilities_namespace_facades
    import flext_infra._utilities._utilities_namespace_moves as _flext_infra__utilities__utilities_namespace_moves
    from flext_infra._utilities._utilities_namespace_facades import (
        FlextInfraUtilitiesRefactorNamespaceFacades,
    )

    _utilities_namespace_moves = _flext_infra__utilities__utilities_namespace_moves
    import flext_infra._utilities._utilities_namespace_runtime as _flext_infra__utilities__utilities_namespace_runtime
    from flext_infra._utilities._utilities_namespace_moves import (
        FlextInfraUtilitiesRefactorNamespaceMoves,
    )

    _utilities_namespace_runtime = _flext_infra__utilities__utilities_namespace_runtime
    import flext_infra._utilities._utilities_policy as _flext_infra__utilities__utilities_policy
    from flext_infra._utilities._utilities_namespace_runtime import (
        FlextInfraUtilitiesRefactorNamespaceRuntime,
    )

    _utilities_policy = _flext_infra__utilities__utilities_policy
    import flext_infra._utilities._utilities_pydantic as _flext_infra__utilities__utilities_pydantic
    from flext_infra._utilities._utilities_policy import (
        FlextInfraUtilitiesRefactorPolicy,
    )

    _utilities_pydantic = _flext_infra__utilities__utilities_pydantic
    import flext_infra._utilities._utilities_pydantic_analysis as _flext_infra__utilities__utilities_pydantic_analysis
    from flext_infra._utilities._utilities_pydantic import (
        FlextInfraUtilitiesRefactorPydantic,
    )

    _utilities_pydantic_analysis = _flext_infra__utilities__utilities_pydantic_analysis
    import flext_infra._utilities.base as _flext_infra__utilities_base
    from flext_infra._utilities._utilities_pydantic_analysis import (
        FlextInfraUtilitiesRefactorPydanticAnalysis,
    )

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
    import flext_infra._utilities.codegen as _flext_infra__utilities_codegen
    from flext_infra._utilities.cli_subcommand import FlextInfraUtilitiesCliSubcommand

    codegen = _flext_infra__utilities_codegen
    import flext_infra._utilities.codegen_constants as _flext_infra__utilities_codegen_constants
    from flext_infra._utilities.codegen import FlextInfraUtilitiesCodegen

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
    from flext_infra._utilities.codegen_generation import (
        FlextInfraUtilitiesCodegenGeneration,
    )

    codegen_import_cycles = _flext_infra__utilities_codegen_import_cycles
    import flext_infra._utilities.codegen_lazy as _flext_infra__utilities_codegen_lazy
    from flext_infra._utilities.codegen_import_cycles import (
        FlextInfraUtilitiesCodegenImportCycles,
    )

    codegen_lazy = _flext_infra__utilities_codegen_lazy
    import flext_infra._utilities.codegen_namespace as _flext_infra__utilities_codegen_namespace
    from flext_infra._utilities.codegen_lazy import (
        FlextInfraUtilitiesCodegenLazyAliases,
        FlextInfraUtilitiesCodegenLazyMerging,
        FlextInfraUtilitiesCodegenLazyScanning,
    )

    codegen_namespace = _flext_infra__utilities_codegen_namespace
    import flext_infra._utilities.deps_paths as _flext_infra__utilities_deps_paths
    from flext_infra._utilities.codegen_namespace import (
        FlextInfraUtilitiesCodegenNamespace,
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
    import flext_infra._utilities.docs_api as _flext_infra__utilities_docs_api
    from flext_infra._utilities.docs import FlextInfraUtilitiesDocs

    docs_api = _flext_infra__utilities_docs_api
    import flext_infra._utilities.docs_audit as _flext_infra__utilities_docs_audit
    from flext_infra._utilities.docs_api import FlextInfraUtilitiesDocsApi

    docs_audit = _flext_infra__utilities_docs_audit
    import flext_infra._utilities.docs_build as _flext_infra__utilities_docs_build
    from flext_infra._utilities.docs_audit import FlextInfraUtilitiesDocsAudit

    docs_build = _flext_infra__utilities_docs_build
    import flext_infra._utilities.docs_contract as _flext_infra__utilities_docs_contract
    from flext_infra._utilities.docs_build import FlextInfraUtilitiesDocsBuild

    docs_contract = _flext_infra__utilities_docs_contract
    import flext_infra._utilities.docs_fix as _flext_infra__utilities_docs_fix
    from flext_infra._utilities.docs_contract import FlextInfraUtilitiesDocsContract

    docs_fix = _flext_infra__utilities_docs_fix
    import flext_infra._utilities.docs_generate as _flext_infra__utilities_docs_generate
    from flext_infra._utilities.docs_fix import FlextInfraUtilitiesDocsFix

    docs_generate = _flext_infra__utilities_docs_generate
    import flext_infra._utilities.docs_render as _flext_infra__utilities_docs_render
    from flext_infra._utilities.docs_generate import FlextInfraUtilitiesDocsGenerate

    docs_render = _flext_infra__utilities_docs_render
    import flext_infra._utilities.docs_scope as _flext_infra__utilities_docs_scope
    from flext_infra._utilities.docs_render import FlextInfraUtilitiesDocsRender

    docs_scope = _flext_infra__utilities_docs_scope
    import flext_infra._utilities.docs_validate as _flext_infra__utilities_docs_validate
    from flext_infra._utilities.docs_scope import FlextInfraUtilitiesDocsScope

    docs_validate = _flext_infra__utilities_docs_validate
    import flext_infra._utilities.formatting as _flext_infra__utilities_formatting
    from flext_infra._utilities.docs_validate import FlextInfraUtilitiesDocsValidate

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
    import flext_infra._utilities.import_normalizer as _flext_infra__utilities_import_normalizer
    from flext_infra._utilities.github_pr import FlextInfraUtilitiesGithubPr

    import_normalizer = _flext_infra__utilities_import_normalizer
    import flext_infra._utilities.iteration as _flext_infra__utilities_iteration
    from flext_infra._utilities.import_normalizer import (
        FlextInfraNormalizerContext,
        FlextInfraUtilitiesImportNormalizer,
    )

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
    import flext_infra._utilities.protected_edit as _flext_infra__utilities_protected_edit
    from flext_infra._utilities.patterns import FlextInfraUtilitiesPatterns

    protected_edit = _flext_infra__utilities_protected_edit
    import flext_infra._utilities.release as _flext_infra__utilities_release
    from flext_infra._utilities.protected_edit import FlextInfraUtilitiesProtectedEdit

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
    import flext_infra._utilities.terminal as _flext_infra__utilities_terminal
    from flext_infra._utilities.selection import FlextInfraUtilitiesSelection

    terminal = _flext_infra__utilities_terminal
    import flext_infra._utilities.toml as _flext_infra__utilities_toml
    from flext_infra._utilities.terminal import FlextInfraUtilitiesTerminal

    toml = _flext_infra__utilities_toml
    import flext_infra._utilities.toml_parse as _flext_infra__utilities_toml_parse
    from flext_infra._utilities.toml import FlextInfraUtilitiesToml

    toml_parse = _flext_infra__utilities_toml_parse
    import flext_infra._utilities.transformer_policy as _flext_infra__utilities_transformer_policy
    from flext_infra._utilities.toml_parse import FlextInfraUtilitiesTomlParse

    transformer_policy = _flext_infra__utilities_transformer_policy
    import flext_infra._utilities.versioning as _flext_infra__utilities_versioning
    from flext_infra._utilities.transformer_policy import (
        FlextInfraUtilitiesRefactorTransformerPolicy,
    )

    versioning = _flext_infra__utilities_versioning
    import flext_infra._utilities.yaml as _flext_infra__utilities_yaml
    from flext_infra._utilities.versioning import FlextInfraUtilitiesVersioning

    yaml = _flext_infra__utilities_yaml
    from flext_infra._utilities.yaml import FlextInfraUtilitiesYaml
_LAZY_IMPORTS = {
    "FlextInfraExtraPathsResolutionMixin": (
        "flext_infra._utilities.deps_paths",
        "FlextInfraExtraPathsResolutionMixin",
    ),
    "FlextInfraInternalSyncRepoMixin": (
        "flext_infra._utilities.deps_repos",
        "FlextInfraInternalSyncRepoMixin",
    ),
    "FlextInfraNormalizerContext": (
        "flext_infra._utilities.import_normalizer",
        "FlextInfraNormalizerContext",
    ),
    "FlextInfraUtilitiesBase": (
        "flext_infra._utilities.base",
        "FlextInfraUtilitiesBase",
    ),
    "FlextInfraUtilitiesCli": ("flext_infra._utilities.cli", "FlextInfraUtilitiesCli"),
    "FlextInfraUtilitiesCliShared": (
        "flext_infra._utilities.cli_shared",
        "FlextInfraUtilitiesCliShared",
    ),
    "FlextInfraUtilitiesCliSubcommand": (
        "flext_infra._utilities.cli_subcommand",
        "FlextInfraUtilitiesCliSubcommand",
    ),
    "FlextInfraUtilitiesCodegen": (
        "flext_infra._utilities.codegen",
        "FlextInfraUtilitiesCodegen",
    ),
    "FlextInfraUtilitiesCodegenConstantAnalysis": (
        "flext_infra._utilities.codegen_constants",
        "FlextInfraUtilitiesCodegenConstantAnalysis",
    ),
    "FlextInfraUtilitiesCodegenConstantDetection": (
        "flext_infra._utilities.codegen_constants",
        "FlextInfraUtilitiesCodegenConstantDetection",
    ),
    "FlextInfraUtilitiesCodegenConstantTransformation": (
        "flext_infra._utilities.codegen_constants",
        "FlextInfraUtilitiesCodegenConstantTransformation",
    ),
    "FlextInfraUtilitiesCodegenExecution": (
        "flext_infra._utilities.codegen_execution",
        "FlextInfraUtilitiesCodegenExecution",
    ),
    "FlextInfraUtilitiesCodegenGeneration": (
        "flext_infra._utilities.codegen_generation",
        "FlextInfraUtilitiesCodegenGeneration",
    ),
    "FlextInfraUtilitiesCodegenGovernance": (
        "flext_infra._utilities.codegen_constants",
        "FlextInfraUtilitiesCodegenGovernance",
    ),
    "FlextInfraUtilitiesCodegenImportCycles": (
        "flext_infra._utilities.codegen_import_cycles",
        "FlextInfraUtilitiesCodegenImportCycles",
    ),
    "FlextInfraUtilitiesCodegenLazyAliases": (
        "flext_infra._utilities.codegen_lazy",
        "FlextInfraUtilitiesCodegenLazyAliases",
    ),
    "FlextInfraUtilitiesCodegenLazyMerging": (
        "flext_infra._utilities.codegen_lazy",
        "FlextInfraUtilitiesCodegenLazyMerging",
    ),
    "FlextInfraUtilitiesCodegenLazyScanning": (
        "flext_infra._utilities.codegen_lazy",
        "FlextInfraUtilitiesCodegenLazyScanning",
    ),
    "FlextInfraUtilitiesCodegenNamespace": (
        "flext_infra._utilities.codegen_namespace",
        "FlextInfraUtilitiesCodegenNamespace",
    ),
    "FlextInfraUtilitiesDiscovery": (
        "flext_infra._utilities.discovery",
        "FlextInfraUtilitiesDiscovery",
    ),
    "FlextInfraUtilitiesDiscoveryScanning": (
        "flext_infra._utilities.discovery_scanning",
        "FlextInfraUtilitiesDiscoveryScanning",
    ),
    "FlextInfraUtilitiesDocs": (
        "flext_infra._utilities.docs",
        "FlextInfraUtilitiesDocs",
    ),
    "FlextInfraUtilitiesDocsApi": (
        "flext_infra._utilities.docs_api",
        "FlextInfraUtilitiesDocsApi",
    ),
    "FlextInfraUtilitiesDocsAudit": (
        "flext_infra._utilities.docs_audit",
        "FlextInfraUtilitiesDocsAudit",
    ),
    "FlextInfraUtilitiesDocsBuild": (
        "flext_infra._utilities.docs_build",
        "FlextInfraUtilitiesDocsBuild",
    ),
    "FlextInfraUtilitiesDocsContract": (
        "flext_infra._utilities.docs_contract",
        "FlextInfraUtilitiesDocsContract",
    ),
    "FlextInfraUtilitiesDocsFix": (
        "flext_infra._utilities.docs_fix",
        "FlextInfraUtilitiesDocsFix",
    ),
    "FlextInfraUtilitiesDocsGenerate": (
        "flext_infra._utilities.docs_generate",
        "FlextInfraUtilitiesDocsGenerate",
    ),
    "FlextInfraUtilitiesDocsRender": (
        "flext_infra._utilities.docs_render",
        "FlextInfraUtilitiesDocsRender",
    ),
    "FlextInfraUtilitiesDocsScope": (
        "flext_infra._utilities.docs_scope",
        "FlextInfraUtilitiesDocsScope",
    ),
    "FlextInfraUtilitiesDocsValidate": (
        "flext_infra._utilities.docs_validate",
        "FlextInfraUtilitiesDocsValidate",
    ),
    "FlextInfraUtilitiesFormatting": (
        "flext_infra._utilities.formatting",
        "FlextInfraUtilitiesFormatting",
    ),
    "FlextInfraUtilitiesGit": ("flext_infra._utilities.git", "FlextInfraUtilitiesGit"),
    "FlextInfraUtilitiesGithub": (
        "flext_infra._utilities.github",
        "FlextInfraUtilitiesGithub",
    ),
    "FlextInfraUtilitiesGithubPr": (
        "flext_infra._utilities.github_pr",
        "FlextInfraUtilitiesGithubPr",
    ),
    "FlextInfraUtilitiesImportNormalizer": (
        "flext_infra._utilities.import_normalizer",
        "FlextInfraUtilitiesImportNormalizer",
    ),
    "FlextInfraUtilitiesIteration": (
        "flext_infra._utilities.iteration",
        "FlextInfraUtilitiesIteration",
    ),
    "FlextInfraUtilitiesLogParser": (
        "flext_infra._utilities.log_parser",
        "FlextInfraUtilitiesLogParser",
    ),
    "FlextInfraUtilitiesOutput": (
        "flext_infra._utilities.output",
        "FlextInfraUtilitiesOutput",
    ),
    "FlextInfraUtilitiesOutputReporting": (
        "flext_infra._utilities.output_reporting",
        "FlextInfraUtilitiesOutputReporting",
    ),
    "FlextInfraUtilitiesParsing": (
        "flext_infra._utilities.parsing",
        "FlextInfraUtilitiesParsing",
    ),
    "FlextInfraUtilitiesPaths": (
        "flext_infra._utilities.paths",
        "FlextInfraUtilitiesPaths",
    ),
    "FlextInfraUtilitiesPatterns": (
        "flext_infra._utilities.patterns",
        "FlextInfraUtilitiesPatterns",
    ),
    "FlextInfraUtilitiesProtectedEdit": (
        "flext_infra._utilities.protected_edit",
        "FlextInfraUtilitiesProtectedEdit",
    ),
    "FlextInfraUtilitiesRefactor": (
        "flext_infra._utilities._utilities",
        "FlextInfraUtilitiesRefactor",
    ),
    "FlextInfraUtilitiesRefactorCensus": (
        "flext_infra._utilities._utilities_census",
        "FlextInfraUtilitiesRefactorCensus",
    ),
    "FlextInfraUtilitiesRefactorCli": (
        "flext_infra._utilities._utilities_cli",
        "FlextInfraUtilitiesRefactorCli",
    ),
    "FlextInfraUtilitiesRefactorEngine": (
        "flext_infra._utilities._utilities_engine",
        "FlextInfraUtilitiesRefactorEngine",
    ),
    "FlextInfraUtilitiesRefactorMroScan": (
        "flext_infra._utilities._utilities_mro_scan",
        "FlextInfraUtilitiesRefactorMroScan",
    ),
    "FlextInfraUtilitiesRefactorMroTransform": (
        "flext_infra._utilities._utilities_mro_transform",
        "FlextInfraUtilitiesRefactorMroTransform",
    ),
    "FlextInfraUtilitiesRefactorNamespace": (
        "flext_infra._utilities._utilities_namespace",
        "FlextInfraUtilitiesRefactorNamespace",
    ),
    "FlextInfraUtilitiesRefactorNamespaceCommon": (
        "flext_infra._utilities._utilities_namespace_analysis",
        "FlextInfraUtilitiesRefactorNamespaceCommon",
    ),
    "FlextInfraUtilitiesRefactorNamespaceFacades": (
        "flext_infra._utilities._utilities_namespace_facades",
        "FlextInfraUtilitiesRefactorNamespaceFacades",
    ),
    "FlextInfraUtilitiesRefactorNamespaceMoves": (
        "flext_infra._utilities._utilities_namespace_moves",
        "FlextInfraUtilitiesRefactorNamespaceMoves",
    ),
    "FlextInfraUtilitiesRefactorNamespaceMro": (
        "flext_infra._utilities._utilities_namespace_analysis",
        "FlextInfraUtilitiesRefactorNamespaceMro",
    ),
    "FlextInfraUtilitiesRefactorNamespaceRuntime": (
        "flext_infra._utilities._utilities_namespace_runtime",
        "FlextInfraUtilitiesRefactorNamespaceRuntime",
    ),
    "FlextInfraUtilitiesRefactorPolicy": (
        "flext_infra._utilities._utilities_policy",
        "FlextInfraUtilitiesRefactorPolicy",
    ),
    "FlextInfraUtilitiesRefactorPydantic": (
        "flext_infra._utilities._utilities_pydantic",
        "FlextInfraUtilitiesRefactorPydantic",
    ),
    "FlextInfraUtilitiesRefactorPydanticAnalysis": (
        "flext_infra._utilities._utilities_pydantic_analysis",
        "FlextInfraUtilitiesRefactorPydanticAnalysis",
    ),
    "FlextInfraUtilitiesRefactorTransformerPolicy": (
        "flext_infra._utilities.transformer_policy",
        "FlextInfraUtilitiesRefactorTransformerPolicy",
    ),
    "FlextInfraUtilitiesRelease": (
        "flext_infra._utilities.release",
        "FlextInfraUtilitiesRelease",
    ),
    "FlextInfraUtilitiesReporting": (
        "flext_infra._utilities.reporting",
        "FlextInfraUtilitiesReporting",
    ),
    "FlextInfraUtilitiesRope": (
        "flext_infra._utilities.rope",
        "FlextInfraUtilitiesRope",
    ),
    "FlextInfraUtilitiesRopeAnalysis": (
        "flext_infra._utilities.rope_analysis",
        "FlextInfraUtilitiesRopeAnalysis",
    ),
    "FlextInfraUtilitiesRopeAnalysisIntrospection": (
        "flext_infra._utilities.rope_analysis_introspection",
        "FlextInfraUtilitiesRopeAnalysisIntrospection",
    ),
    "FlextInfraUtilitiesRopeCore": (
        "flext_infra._utilities.rope_core",
        "FlextInfraUtilitiesRopeCore",
    ),
    "FlextInfraUtilitiesRopeHelpers": (
        "flext_infra._utilities.rope_helpers",
        "FlextInfraUtilitiesRopeHelpers",
    ),
    "FlextInfraUtilitiesRopeImports": (
        "flext_infra._utilities.rope_imports",
        "FlextInfraUtilitiesRopeImports",
    ),
    "FlextInfraUtilitiesRopeSource": (
        "flext_infra._utilities.rope_source",
        "FlextInfraUtilitiesRopeSource",
    ),
    "FlextInfraUtilitiesSafety": (
        "flext_infra._utilities.safety",
        "FlextInfraUtilitiesSafety",
    ),
    "FlextInfraUtilitiesSelection": (
        "flext_infra._utilities.selection",
        "FlextInfraUtilitiesSelection",
    ),
    "FlextInfraUtilitiesTerminal": (
        "flext_infra._utilities.terminal",
        "FlextInfraUtilitiesTerminal",
    ),
    "FlextInfraUtilitiesToml": (
        "flext_infra._utilities.toml",
        "FlextInfraUtilitiesToml",
    ),
    "FlextInfraUtilitiesTomlParse": (
        "flext_infra._utilities.toml_parse",
        "FlextInfraUtilitiesTomlParse",
    ),
    "FlextInfraUtilitiesVersioning": (
        "flext_infra._utilities.versioning",
        "FlextInfraUtilitiesVersioning",
    ),
    "FlextInfraUtilitiesYaml": (
        "flext_infra._utilities.yaml",
        "FlextInfraUtilitiesYaml",
    ),
    "_utilities": "flext_infra._utilities._utilities",
    "_utilities_census": "flext_infra._utilities._utilities_census",
    "_utilities_cli": "flext_infra._utilities._utilities_cli",
    "_utilities_engine": "flext_infra._utilities._utilities_engine",
    "_utilities_mro_scan": "flext_infra._utilities._utilities_mro_scan",
    "_utilities_mro_transform": "flext_infra._utilities._utilities_mro_transform",
    "_utilities_namespace": "flext_infra._utilities._utilities_namespace",
    "_utilities_namespace_analysis": "flext_infra._utilities._utilities_namespace_analysis",
    "_utilities_namespace_facades": "flext_infra._utilities._utilities_namespace_facades",
    "_utilities_namespace_moves": "flext_infra._utilities._utilities_namespace_moves",
    "_utilities_namespace_runtime": "flext_infra._utilities._utilities_namespace_runtime",
    "_utilities_policy": "flext_infra._utilities._utilities_policy",
    "_utilities_pydantic": "flext_infra._utilities._utilities_pydantic",
    "_utilities_pydantic_analysis": "flext_infra._utilities._utilities_pydantic_analysis",
    "base": "flext_infra._utilities.base",
    "cli": "flext_infra._utilities.cli",
    "cli_shared": "flext_infra._utilities.cli_shared",
    "cli_subcommand": "flext_infra._utilities.cli_subcommand",
    "codegen": "flext_infra._utilities.codegen",
    "codegen_constants": "flext_infra._utilities.codegen_constants",
    "codegen_execution": "flext_infra._utilities.codegen_execution",
    "codegen_generation": "flext_infra._utilities.codegen_generation",
    "codegen_import_cycles": "flext_infra._utilities.codegen_import_cycles",
    "codegen_lazy": "flext_infra._utilities.codegen_lazy",
    "codegen_namespace": "flext_infra._utilities.codegen_namespace",
    "deps_paths": "flext_infra._utilities.deps_paths",
    "deps_repos": "flext_infra._utilities.deps_repos",
    "discovery": "flext_infra._utilities.discovery",
    "discovery_scanning": "flext_infra._utilities.discovery_scanning",
    "docs": "flext_infra._utilities.docs",
    "docs_api": "flext_infra._utilities.docs_api",
    "docs_audit": "flext_infra._utilities.docs_audit",
    "docs_build": "flext_infra._utilities.docs_build",
    "docs_contract": "flext_infra._utilities.docs_contract",
    "docs_fix": "flext_infra._utilities.docs_fix",
    "docs_generate": "flext_infra._utilities.docs_generate",
    "docs_render": "flext_infra._utilities.docs_render",
    "docs_scope": "flext_infra._utilities.docs_scope",
    "docs_validate": "flext_infra._utilities.docs_validate",
    "formatting": "flext_infra._utilities.formatting",
    "git": "flext_infra._utilities.git",
    "github": "flext_infra._utilities.github",
    "github_pr": "flext_infra._utilities.github_pr",
    "import_normalizer": "flext_infra._utilities.import_normalizer",
    "iteration": "flext_infra._utilities.iteration",
    "log_parser": "flext_infra._utilities.log_parser",
    "output": "flext_infra._utilities.output",
    "output_reporting": "flext_infra._utilities.output_reporting",
    "parsing": "flext_infra._utilities.parsing",
    "paths": "flext_infra._utilities.paths",
    "patterns": "flext_infra._utilities.patterns",
    "protected_edit": "flext_infra._utilities.protected_edit",
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
    "terminal": "flext_infra._utilities.terminal",
    "toml": "flext_infra._utilities.toml",
    "toml_parse": "flext_infra._utilities.toml_parse",
    "transformer_policy": "flext_infra._utilities.transformer_policy",
    "versioning": "flext_infra._utilities.versioning",
    "yaml": "flext_infra._utilities.yaml",
}

__all__ = [
    "FlextInfraExtraPathsResolutionMixin",
    "FlextInfraInternalSyncRepoMixin",
    "FlextInfraNormalizerContext",
    "FlextInfraUtilitiesBase",
    "FlextInfraUtilitiesCli",
    "FlextInfraUtilitiesCliShared",
    "FlextInfraUtilitiesCliSubcommand",
    "FlextInfraUtilitiesCodegen",
    "FlextInfraUtilitiesCodegenConstantAnalysis",
    "FlextInfraUtilitiesCodegenConstantDetection",
    "FlextInfraUtilitiesCodegenConstantTransformation",
    "FlextInfraUtilitiesCodegenExecution",
    "FlextInfraUtilitiesCodegenGeneration",
    "FlextInfraUtilitiesCodegenGovernance",
    "FlextInfraUtilitiesCodegenImportCycles",
    "FlextInfraUtilitiesCodegenLazyAliases",
    "FlextInfraUtilitiesCodegenLazyMerging",
    "FlextInfraUtilitiesCodegenLazyScanning",
    "FlextInfraUtilitiesCodegenNamespace",
    "FlextInfraUtilitiesDiscovery",
    "FlextInfraUtilitiesDiscoveryScanning",
    "FlextInfraUtilitiesDocs",
    "FlextInfraUtilitiesDocsApi",
    "FlextInfraUtilitiesDocsAudit",
    "FlextInfraUtilitiesDocsBuild",
    "FlextInfraUtilitiesDocsContract",
    "FlextInfraUtilitiesDocsFix",
    "FlextInfraUtilitiesDocsGenerate",
    "FlextInfraUtilitiesDocsRender",
    "FlextInfraUtilitiesDocsScope",
    "FlextInfraUtilitiesDocsValidate",
    "FlextInfraUtilitiesFormatting",
    "FlextInfraUtilitiesGit",
    "FlextInfraUtilitiesGithub",
    "FlextInfraUtilitiesGithubPr",
    "FlextInfraUtilitiesImportNormalizer",
    "FlextInfraUtilitiesIteration",
    "FlextInfraUtilitiesLogParser",
    "FlextInfraUtilitiesOutput",
    "FlextInfraUtilitiesOutputReporting",
    "FlextInfraUtilitiesParsing",
    "FlextInfraUtilitiesPaths",
    "FlextInfraUtilitiesPatterns",
    "FlextInfraUtilitiesProtectedEdit",
    "FlextInfraUtilitiesRefactor",
    "FlextInfraUtilitiesRefactorCensus",
    "FlextInfraUtilitiesRefactorCli",
    "FlextInfraUtilitiesRefactorEngine",
    "FlextInfraUtilitiesRefactorMroScan",
    "FlextInfraUtilitiesRefactorMroTransform",
    "FlextInfraUtilitiesRefactorNamespace",
    "FlextInfraUtilitiesRefactorNamespaceCommon",
    "FlextInfraUtilitiesRefactorNamespaceFacades",
    "FlextInfraUtilitiesRefactorNamespaceMoves",
    "FlextInfraUtilitiesRefactorNamespaceMro",
    "FlextInfraUtilitiesRefactorNamespaceRuntime",
    "FlextInfraUtilitiesRefactorPolicy",
    "FlextInfraUtilitiesRefactorPydantic",
    "FlextInfraUtilitiesRefactorPydanticAnalysis",
    "FlextInfraUtilitiesRefactorTransformerPolicy",
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
    "FlextInfraUtilitiesTerminal",
    "FlextInfraUtilitiesToml",
    "FlextInfraUtilitiesTomlParse",
    "FlextInfraUtilitiesVersioning",
    "FlextInfraUtilitiesYaml",
    "_utilities",
    "_utilities_census",
    "_utilities_cli",
    "_utilities_engine",
    "_utilities_mro_scan",
    "_utilities_mro_transform",
    "_utilities_namespace",
    "_utilities_namespace_analysis",
    "_utilities_namespace_facades",
    "_utilities_namespace_moves",
    "_utilities_namespace_runtime",
    "_utilities_policy",
    "_utilities_pydantic",
    "_utilities_pydantic_analysis",
    "base",
    "cli",
    "cli_shared",
    "cli_subcommand",
    "codegen",
    "codegen_constants",
    "codegen_execution",
    "codegen_generation",
    "codegen_import_cycles",
    "codegen_lazy",
    "codegen_namespace",
    "deps_paths",
    "deps_repos",
    "discovery",
    "discovery_scanning",
    "docs",
    "docs_api",
    "docs_audit",
    "docs_build",
    "docs_contract",
    "docs_fix",
    "docs_generate",
    "docs_render",
    "docs_scope",
    "docs_validate",
    "formatting",
    "git",
    "github",
    "github_pr",
    "import_normalizer",
    "iteration",
    "log_parser",
    "output",
    "output_reporting",
    "parsing",
    "paths",
    "patterns",
    "protected_edit",
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
    "terminal",
    "toml",
    "toml_parse",
    "transformer_policy",
    "versioning",
    "yaml",
]


install_lazy_exports(__name__, globals(), _LAZY_IMPORTS)
