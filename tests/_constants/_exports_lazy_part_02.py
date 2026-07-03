# AUTO-GENERATED FILE — Regenerate with: make gen
"""Lazy export map part."""

from __future__ import annotations

from flext_core.lazy import build_lazy_import_map

TESTS_FLEXT_INFRA_LAZY_IMPORTS_PART_02 = build_lazy_import_map(
    {
        ".unit.check.extended_cli_entry_tests": ("TestWorkspaceCheckCLI",),
        ".unit.check.extended_config_fixer_errors_tests": (
            "TestConfigFixerPublicBehavior",
        ),
        ".unit.check.extended_config_fixer_tests": (
            "TestConfigFixerExecute",
            "TestConfigFixerProcessFile",
            "TestConfigFixerRun",
            "TestConfigFixerToArray",
        ),
        ".unit.check.extended_error_reporting_tests": (
            "TestGateErrorReportingPublicBehavior",
        ),
        ".unit.check.extended_models_tests": (
            "TestProjectResultProperties",
            "TestRunCommandGateParsing",
            "TestWorkspaceCheckerErrorSummary",
        ),
        ".unit.check.extended_project_runners_tests": ("TestsExtendedProjectRunners",),
        ".unit.check.extended_resolve_gates_tests": (
            "TestWorkspaceCheckerResolveGates",
        ),
        ".unit.check.extended_run_projects_tests": ("TestRunProjectsPublicBehavior",),
        ".unit.check.extended_runners_extra_tests": ("TestExtendedRunnerExtras",),
        ".unit.check.extended_runners_tests": ("TestRunnerPublicBehavior",),
        ".unit.check.init_tests": ("TestFlextInfraCheck",),
        ".unit.check.pyrefly_tests": ("TestFlextInfraConfigFixer",),
        ".unit.check.tests_cli": ("TestWorkspaceCheckCli",),
        ".unit.check.workspace_tests": ("TestFlextInfraWorkspaceChecker",),
        ".unit.codegen.lazy_init_generation_tests": (
            "TestGenerateFile",
            "TestGenerateTypeChecking",
            "TestLazyInitPlannerCollision",
            "TestRunRuffFix",
        ),
        ".unit.codegen.lazy_init_tests": (
            "TestEdgeCases",
            "TestExcludedDirectories",
        ),
        ".unit.codegen.scaffolder_naming_tests": (
            "TestGeneratedClassNamingConvention",
            "TestGeneratedFilesAreValidPython",
        ),
        ".unit.docs.auditor_budgets_tests": ("TestLoadAuditBudgets",),
        ".unit.docs.shared_iter_tests": (
            "TestIterMarkdownFiles",
            "TestSelectedProjectNames",
        ),
        ".unit.validate.main_cli_tests": ("TestValidateCli",),
        ".unit.validate.namespace_validator_tests": (
            "TestFlextInfraNamespaceValidator",
        ),
    },
)

__all__: list[str] = ["TESTS_FLEXT_INFRA_LAZY_IMPORTS_PART_02"]
