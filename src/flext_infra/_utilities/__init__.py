# AUTO-GENERATED FILE — Regenerate with: make gen
"""Utilities package."""

from __future__ import annotations

from flext_core.lazy import build_lazy_import_map, install_lazy_exports

_LAZY_IMPORTS = build_lazy_import_map(
    {
        ".base": ("FlextInfraUtilitiesBase",),
        ".census": ("FlextInfraUtilitiesRefactorCensus",),
        ".cli": ("FlextInfraUtilitiesCli",),
        ".cli_dispatch": ("FlextInfraUtilitiesCliDispatch",),
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
        ".deps_repos": ("FlextInfraInternalSyncRepoMixin",),
        ".discovery": ("FlextInfraUtilitiesDiscovery",),
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
        ".mro_transform": ("FlextInfraUtilitiesRefactorMroTransform",),
        ".namespace": ("FlextInfraUtilitiesCodegenNamespace",),
        ".namespace_analysis": (
            "FlextInfraUtilitiesRefactorNamespaceCommon",
            "FlextInfraUtilitiesRefactorNamespaceMro",
        ),
        ".namespace_facades": ("FlextInfraUtilitiesRefactorNamespaceFacades",),
        ".namespace_moves": ("FlextInfraUtilitiesRefactorNamespaceMoves",),
        ".namespaces": ("FlextInfraUtilitiesRefactorNamespace",),
        ".normalizer": (
            "FlextInfraNormalizerContext",
            "FlextInfraUtilitiesImportNormalizer",
        ),
        ".output_failure_summary": ("FlextInfraUtilitiesOutputFailureSummary",),
        ".output_reporting": ("FlextInfraUtilitiesOutputReporting",),
        ".parsing": ("FlextInfraUtilitiesParsing",),
        ".paths": ("FlextInfraUtilitiesPaths",),
        ".patterns": ("FlextInfraUtilitiesPatterns",),
        ".policy": ("FlextInfraUtilitiesRefactorPolicy",),
        ".protected_edit": ("FlextInfraUtilitiesProtectedEdit",),
        ".refactor": ("FlextInfraUtilitiesRefactor",),
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
        ".toml": ("FlextInfraUtilitiesToml",),
        ".toml_parse": ("FlextInfraUtilitiesTomlParse",),
        ".utilities_cli": ("FlextInfraUtilitiesRefactorCli",),
        ".versioning": ("FlextInfraUtilitiesVersioning",),
    },
)


install_lazy_exports(__name__, globals(), _LAZY_IMPORTS, publish_all=False)
