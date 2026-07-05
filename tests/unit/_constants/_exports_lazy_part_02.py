# AUTO-GENERATED FILE — Regenerate with: make gen
"""Lazy export map part."""

from __future__ import annotations

from flext_core.lazy import build_lazy_import_map

TESTS_FLEXT_INFRA_UNIT_LAZY_IMPORTS_PART_02 = build_lazy_import_map(
    {
        ".basemk.test_generator": ("TestsFlextInfraBasemkGenerator",),
        ".basemk.test_generator_edge_cases": (
            "TestsFlextInfraBasemkGeneratorEdgeCases",
        ),
        ".basemk.test_init": ("TestsFlextInfraBasemkInit",),
        ".basemk.test_main": ("TestsFlextInfraBasemkMain",),
        ".basemk.test_make_contract": ("TestsFlextInfraBasemkMakeContract",),
        ".basemk.test_renderer": ("TestsFlextInfraBasemkRenderer",),
        ".check.enforcement_fixer_orchestrator_tests": (
            "TestsEnforcementFixerOrchestrator",
        ),
        ".check.extended_cli_entry_tests": ("TestWorkspaceCheckCLI",),
        ".check.extended_error_reporting_tests": (
            "TestGateErrorReportingPublicBehavior",
        ),
        ".check.extended_models_tests": (
            "TestProjectResultProperties",
            "TestRunCommandGateParsing",
            "TestWorkspaceCheckerErrorSummary",
        ),
        ".check.extended_project_runners_tests": ("TestsExtendedProjectRunners",),
        ".check.extended_resolve_gates_tests": ("TestWorkspaceCheckerResolveGates",),
        ".check.extended_run_projects_tests": ("TestRunProjectsPublicBehavior",),
        ".check.extended_runners_tests": ("TestRunnerPublicBehavior",),
        ".check.pyrefly_tests": ("TestFlextInfraConfigFixer",),
        ".check.tests_cli": ("TestWorkspaceCheckCli",),
        ".check.workspace_tests": ("TestFlextInfraWorkspaceChecker",),
        ".cli_what_selector_tests": ("TestsFlextInfraCliWhatSelector",),
        ".codegen.lazy_init_generation_tests": (
            "TestGenerateFile",
            "TestGenerateTypeChecking",
            "TestLazyInitPlannerCollision",
            "TestRunRuffFix",
        ),
        ".codegen.scaffolder_naming_tests": (
            "TestGeneratedClassNamingConvention",
            "TestGeneratedFilesAreValidPython",
        ),
        ".container.test_infra_container": ("TestsFlextInfraContainerInfraContainer",),
        ".docs.auditor_budgets_tests": ("TestLoadAuditBudgets",),
        ".docs.shared_iter_tests": (
            "TestIterMarkdownFiles",
            "TestSelectedProjectNames",
        ),
        ".validate.main_cli_tests": ("TestValidateCli",),
        ".validate.namespace_validator_tests": ("TestFlextInfraNamespaceValidator",),
    },
)

__all__: list[str] = ["TESTS_FLEXT_INFRA_UNIT_LAZY_IMPORTS_PART_02"]
