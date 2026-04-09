# AUTO-GENERATED FILE — Regenerate with: make gen
"""Utilities package."""

from __future__ import annotations

from flext_core.lazy import build_lazy_import_map, install_lazy_exports

_LAZY_IMPORTS = build_lazy_import_map(
    {
        "._utilities": ("FlextInfraUtilitiesRefactor",),
        "._utilities_cli": ("FlextInfraUtilitiesRefactorCli",),
        "._utilities_mro_transform": ("FlextInfraUtilitiesRefactorMroTransform",),
        "._utilities_namespace": ("FlextInfraUtilitiesRefactorNamespace",),
        "._utilities_namespace_analysis": (
            "FlextInfraUtilitiesRefactorNamespaceCommon",
            "FlextInfraUtilitiesRefactorNamespaceMro",
        ),
        "._utilities_namespace_facades": (
            "FlextInfraUtilitiesRefactorNamespaceFacades",
        ),
        "._utilities_namespace_moves": ("FlextInfraUtilitiesRefactorNamespaceMoves",),
        "._utilities_namespace_runtime": (
            "FlextInfraUtilitiesRefactorNamespaceRuntime",
        ),
        "._utilities_policy": ("FlextInfraUtilitiesRefactorPolicy",),
        "._utilities_pydantic": ("FlextInfraUtilitiesRefactorPydantic",),
        "._utilities_pydantic_analysis": (
            "FlextInfraUtilitiesRefactorPydanticAnalysis",
        ),
        ".base": ("FlextInfraUtilitiesBase",),
        ".census": ("FlextInfraUtilitiesRefactorCensus",),
        ".cli": ("FlextInfraUtilitiesCli",),
        ".cli_shared": ("FlextInfraUtilitiesCliShared",),
        ".cli_subcommand": ("FlextInfraUtilitiesCliSubcommand",),
        ".codegen": ("FlextInfraUtilitiesCodegen",),
        ".codegen_constants": (
            "FlextInfraUtilitiesCodegenConstantAnalysis",
            "FlextInfraUtilitiesCodegenConstantDetection",
            "FlextInfraUtilitiesCodegenConstantTransformation",
            "FlextInfraUtilitiesCodegenGovernance",
        ),
        ".codegen_execution": ("FlextInfraUtilitiesCodegenExecution",),
        ".codegen_generation": ("FlextInfraUtilitiesCodegenGeneration",),
        ".codegen_import_cycles": ("FlextInfraUtilitiesCodegenImportCycles",),
        ".deps_path_sync": ("FlextInfraUtilitiesDependencyPathSync",),
        ".deps_paths": ("FlextInfraExtraPathsResolutionMixin",),
        ".deps_repos": ("FlextInfraInternalSyncRepoMixin",),
        ".discovery": ("FlextInfraUtilitiesDiscovery",),
        ".discovery_scanning": ("FlextInfraUtilitiesDiscoveryScanning",),
        ".docs": ("FlextInfraUtilitiesDocs",),
        ".docs_api": ("FlextInfraUtilitiesDocsApi",),
        ".docs_audit": ("FlextInfraUtilitiesDocsAudit",),
        ".docs_build": ("FlextInfraUtilitiesDocsBuild",),
        ".docs_contract": ("FlextInfraUtilitiesDocsContract",),
        ".docs_fix": ("FlextInfraUtilitiesDocsFix",),
        ".docs_generate": ("FlextInfraUtilitiesDocsGenerate",),
        ".docs_render": ("FlextInfraUtilitiesDocsRender",),
        ".docs_scope": ("FlextInfraUtilitiesDocsScope",),
        ".docs_validate": ("FlextInfraUtilitiesDocsValidate",),
        ".engine": ("FlextInfraUtilitiesRefactorEngine",),
        ".formatting": ("FlextInfraUtilitiesFormatting",),
        ".git": ("FlextInfraUtilitiesGit",),
        ".github": ("FlextInfraUtilitiesGithub",),
        ".github_pr": ("FlextInfraUtilitiesGithubPr",),
        ".iteration": ("FlextInfraUtilitiesIteration",),
        ".lazy": (
            "FlextInfraUtilitiesCodegenLazyAliases",
            "FlextInfraUtilitiesCodegenLazyMerging",
            "FlextInfraUtilitiesCodegenLazyScanning",
        ),
        ".log_parser": ("FlextInfraUtilitiesLogParser",),
        ".mro_scan": ("FlextInfraUtilitiesRefactorMroScan",),
        ".namespace": ("FlextInfraUtilitiesCodegenNamespace",),
        ".normalizer": (
            "FlextInfraNormalizerContext",
            "FlextInfraUtilitiesImportNormalizer",
        ),
        ".output": ("FlextInfraUtilitiesOutput",),
        ".output_failure_summary": ("FlextInfraUtilitiesOutputFailureSummary",),
        ".output_reporting": ("FlextInfraUtilitiesOutputReporting",),
        ".parsing": ("FlextInfraUtilitiesParsing",),
        ".paths": ("FlextInfraUtilitiesPaths",),
        ".patterns": ("FlextInfraUtilitiesPatterns",),
        ".protected_edit": ("FlextInfraUtilitiesProtectedEdit",),
        ".release": ("FlextInfraUtilitiesRelease",),
        ".reporting": ("FlextInfraUtilitiesReporting",),
        ".rope": ("FlextInfraUtilitiesRope",),
        ".rope_analysis": ("FlextInfraUtilitiesRopeAnalysis",),
        ".rope_analysis_introspection": (
            "FlextInfraUtilitiesRopeAnalysisIntrospection",
        ),
        ".rope_core": ("FlextInfraUtilitiesRopeCore",),
        ".rope_helpers": ("FlextInfraUtilitiesRopeHelpers",),
        ".rope_imports": ("FlextInfraUtilitiesRopeImports",),
        ".rope_source": ("FlextInfraUtilitiesRopeSource",),
        ".safety": ("FlextInfraUtilitiesSafety",),
        ".selection": ("FlextInfraUtilitiesSelection",),
        ".terminal": ("FlextInfraUtilitiesTerminal",),
        ".toml": ("FlextInfraUtilitiesToml",),
        ".toml_parse": ("FlextInfraUtilitiesTomlParse",),
        ".transformer_policy": ("FlextInfraUtilitiesRefactorTransformerPolicy",),
        ".versioning": ("FlextInfraUtilitiesVersioning",),
        ".yaml": ("FlextInfraUtilitiesYaml",),
    },
)


install_lazy_exports(__name__, globals(), _LAZY_IMPORTS, publish_all=False)
