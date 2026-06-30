# AUTO-GENERATED FILE — Regenerate with: make gen
"""Lazy export map part."""

from __future__ import annotations

from flext_core.lazy import build_lazy_import_map

TESTS_FLEXT_INFRA_LAZY_IMPORTS_PART_01 = build_lazy_import_map(
    {
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
        ".unit.check.extended_models_tests": ("TestCheckIssueFormatted",),
        ".unit.check.extended_runners_extra_tests": ("TestExtendedRunnerExtras",),
        ".unit.check.init_tests": ("TestFlextInfraCheck",),
        ".unit.check.pyrefly_tests": ("TestFlextInfraConfigFixer",),
        ".unit.check.workspace_tests": ("TestFlextInfraWorkspaceChecker",),
        ".unit.codegen.lazy_init_generation_tests": (
            "TestGenerateFile",
            "TestGenerateTypeChecking",
            "TestLazyInitPlannerCollision",
        ),
        ".unit.codegen.lazy_init_tests": (
            "TestAllDirectoriesScanned",
            "TestCheckOnlyMode",
            "TestEdgeCases",
            "TestExcludedDirectories",
        ),
        ".unit.codegen.scaffolder_naming_tests": (
            "TestGeneratedClassNamingConvention",
            "TestGeneratedFilesAreValidPython",
        ),
        ".unit.docs.auditor_links_tests": (
            "TestAuditorBrokenLinks",
            "TestAuditorToMarkdown",
        ),
        ".unit.docs.auditor_scope_tests": (
            "TestAuditorForbiddenTerms",
            "TestAuditorScope",
        ),
        ".unit.docs.auditor_tests": (
            "TestAuditorCore",
            "TestAuditorNormalize",
        ),
        ".unit.docs.builder_tests": ("TestBuilderCore",),
        ".unit.docs.shared_iter_tests": ("TestIterMarkdownFiles",),
        ".unit.refactor.test_infra_refactor_safety": ("RefactorSafetyStub",),
        ".unit.refactor.test_infra_refactor_typing_unifier": (
            "FlextInfraRefactorTypingUnificationRule",
        ),
        ".unit.runner_service": ("RealSubprocessRunner",),
        ".unit.validate.namespace_validator_tests": (
            "TestFlextInfraNamespaceValidator",
        ),
    },
)

__all__: list[str] = ["TESTS_FLEXT_INFRA_LAZY_IMPORTS_PART_01"]
