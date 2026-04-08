# AUTO-GENERATED FILE — DO NOT EDIT MANUALLY.
# Regenerate with: make gen
#
"""Utilities package."""

from __future__ import annotations

from flext_core.lazy import install_lazy_exports

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
        "flext_infra._utilities.normalizer",
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
        "flext_infra._utilities.lazy",
        "FlextInfraUtilitiesCodegenLazyAliases",
    ),
    "FlextInfraUtilitiesCodegenLazyMerging": (
        "flext_infra._utilities.lazy",
        "FlextInfraUtilitiesCodegenLazyMerging",
    ),
    "FlextInfraUtilitiesCodegenLazyScanning": (
        "flext_infra._utilities.lazy",
        "FlextInfraUtilitiesCodegenLazyScanning",
    ),
    "FlextInfraUtilitiesCodegenNamespace": (
        "flext_infra._utilities.namespace",
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
        "flext_infra._utilities.normalizer",
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
        "flext_infra._utilities.census",
        "FlextInfraUtilitiesRefactorCensus",
    ),
    "FlextInfraUtilitiesRefactorCli": (
        "flext_infra._utilities._utilities_cli",
        "FlextInfraUtilitiesRefactorCli",
    ),
    "FlextInfraUtilitiesRefactorEngine": (
        "flext_infra._utilities.engine",
        "FlextInfraUtilitiesRefactorEngine",
    ),
    "FlextInfraUtilitiesRefactorMroScan": (
        "flext_infra._utilities.mro_scan",
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
    "base": "flext_infra._utilities.base",
    "census": "flext_infra._utilities.census",
    "cli": "flext_infra._utilities.cli",
    "cli_shared": "flext_infra._utilities.cli_shared",
    "cli_subcommand": "flext_infra._utilities.cli_subcommand",
    "codegen": "flext_infra._utilities.codegen",
    "codegen_constants": "flext_infra._utilities.codegen_constants",
    "codegen_execution": "flext_infra._utilities.codegen_execution",
    "codegen_generation": "flext_infra._utilities.codegen_generation",
    "codegen_import_cycles": "flext_infra._utilities.codegen_import_cycles",
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
    "engine": "flext_infra._utilities.engine",
    "formatting": "flext_infra._utilities.formatting",
    "git": "flext_infra._utilities.git",
    "github": "flext_infra._utilities.github",
    "github_pr": "flext_infra._utilities.github_pr",
    "iteration": "flext_infra._utilities.iteration",
    "lazy": "flext_infra._utilities.lazy",
    "log_parser": "flext_infra._utilities.log_parser",
    "mro_scan": "flext_infra._utilities.mro_scan",
    "namespace": "flext_infra._utilities.namespace",
    "normalizer": "flext_infra._utilities.normalizer",
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


install_lazy_exports(__name__, globals(), _LAZY_IMPORTS, publish_all=False)
