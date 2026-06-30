# AUTO-GENERATED FILE — Regenerate with: make gen
"""Lazy export map part."""

from __future__ import annotations

from flext_core.lazy import build_lazy_import_map

TESTS_FLEXT_INFRA_UNIT_LAZY_IMPORTS_PART_01 = build_lazy_import_map(
    {
        ".check.extended_config_fixer_errors_tests": ("TestConfigFixerPublicBehavior",),
        ".check.extended_config_fixer_tests": (
            "TestConfigFixerExecute",
            "TestConfigFixerProcessFile",
            "TestConfigFixerRun",
            "TestConfigFixerToArray",
        ),
        ".check.extended_error_reporting_tests": (
            "TestGateErrorReportingPublicBehavior",
        ),
        ".check.extended_models_tests": ("TestCheckIssueFormatted",),
        ".check.extended_runners_extra_tests": ("TestExtendedRunnerExtras",),
        ".check.init_tests": ("TestFlextInfraCheck",),
        ".check.pyrefly_tests": ("TestFlextInfraConfigFixer",),
        ".check.workspace_tests": ("TestFlextInfraWorkspaceChecker",),
        ".codegen.lazy_init_generation_tests": (
            "TestGenerateFile",
            "TestGenerateTypeChecking",
            "TestLazyInitPlannerCollision",
        ),
        ".codegen.lazy_init_tests": (
            "TestAllDirectoriesScanned",
            "TestCheckOnlyMode",
            "TestEdgeCases",
            "TestExcludedDirectories",
        ),
        ".codegen.scaffolder_naming_tests": (
            "TestGeneratedClassNamingConvention",
            "TestGeneratedFilesAreValidPython",
        ),
        ".docs.auditor_links_tests": (
            "TestAuditorBrokenLinks",
            "TestAuditorToMarkdown",
        ),
        ".docs.auditor_scope_tests": (
            "TestAuditorForbiddenTerms",
            "TestAuditorScope",
        ),
        ".docs.auditor_tests": (
            "TestAuditorCore",
            "TestAuditorNormalize",
        ),
        ".docs.builder_tests": ("TestBuilderCore",),
        ".docs.shared_iter_tests": ("TestIterMarkdownFiles",),
        ".refactor.test_infra_refactor_safety": ("EngineSafetyStub",),
        ".refactor.test_infra_refactor_typing_unifier": (
            "FlextInfraRefactorTypingUnificationRule",
        ),
        ".runner_service": ("RealSubprocessRunner",),
        ".validate.namespace_validator_tests": ("TestFlextInfraNamespaceValidator",),
    },
)

__all__: list[str] = ["TESTS_FLEXT_INFRA_UNIT_LAZY_IMPORTS_PART_01"]
