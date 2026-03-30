# AUTO-GENERATED FILE — DO NOT EDIT MANUALLY.
# Regenerate with: make gen
#
"""Codegen package."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import TYPE_CHECKING

from flext_core.lazy import install_lazy_exports

if TYPE_CHECKING:
    from tests.unit.codegen import (
        autofix_tests as autofix_tests,
        autofix_workspace_tests as autofix_workspace_tests,
        census_models_tests as census_models_tests,
        census_tests as census_tests,
        constants_quality_gate_tests as constants_quality_gate_tests,
        init_tests as init_tests,
        lazy_init_generation_tests as lazy_init_generation_tests,
        lazy_init_helpers_tests as lazy_init_helpers_tests,
        lazy_init_process_tests as lazy_init_process_tests,
        lazy_init_service_tests as lazy_init_service_tests,
        lazy_init_tests as lazy_init_tests,
        lazy_init_transforms_tests as lazy_init_transforms_tests,
        main_tests as main_tests,
        pipeline_tests as pipeline_tests,
        scaffolder_naming_tests as scaffolder_naming_tests,
        scaffolder_tests as scaffolder_tests,
    )
    from tests.unit.codegen.autofix_tests import (
        fixer as fixer,
        test_in_context_typevar_not_flagged as test_in_context_typevar_not_flagged,
        test_standalone_final_detected_as_fixable as test_standalone_final_detected_as_fixable,
        test_standalone_typealias_detected_as_fixable as test_standalone_typealias_detected_as_fixable,
        test_standalone_typevar_detected_as_fixable as test_standalone_typevar_detected_as_fixable,
        test_syntax_error_files_skipped as test_syntax_error_files_skipped,
    )
    from tests.unit.codegen.autofix_workspace_tests import (
        test_files_modified_tracks_affected_files as test_files_modified_tracks_affected_files,
        test_flexcore_excluded_from_run as test_flexcore_excluded_from_run,
        test_project_without_src_returns_empty as test_project_without_src_returns_empty,
    )
    from tests.unit.codegen.census_models_tests import (
        TestCensusReportModel as TestCensusReportModel,
        TestCensusViolationModel as TestCensusViolationModel,
        TestExcludedProjects as TestExcludedProjects,
        TestViolationPattern as TestViolationPattern,
    )
    from tests.unit.codegen.census_tests import (
        TestFixabilityClassification as TestFixabilityClassification,
        TestParseViolationInvalid as TestParseViolationInvalid,
        TestParseViolationValid as TestParseViolationValid,
        census as census,
    )
    from tests.unit.codegen.constants_quality_gate_tests import (
        TestConstantsQualityGateCLIDispatch as TestConstantsQualityGateCLIDispatch,
        TestConstantsQualityGateVerdict as TestConstantsQualityGateVerdict,
    )
    from tests.unit.codegen.init_tests import (
        test_codegen_dir_returns_all_exports as test_codegen_dir_returns_all_exports,
        test_codegen_getattr_raises_attribute_error as test_codegen_getattr_raises_attribute_error,
        test_codegen_lazy_imports_work as test_codegen_lazy_imports_work,
    )
    from tests.unit.codegen.lazy_init_generation_tests import (
        TestGenerateFile as TestGenerateFile,
        TestGenerateTypeChecking as TestGenerateTypeChecking,
        TestResolveAliases as TestResolveAliases,
        TestRunRuffFix as TestRunRuffFix,
        test_codegen_init_getattr_raises_attribute_error as test_codegen_init_getattr_raises_attribute_error,
    )
    from tests.unit.codegen.lazy_init_helpers_tests import (
        TestBuildSiblingExportIndex as TestBuildSiblingExportIndex,
        TestExtractExports as TestExtractExports,
        TestInferPackage as TestInferPackage,
        TestReadExistingDocstring as TestReadExistingDocstring,
    )
    from tests.unit.codegen.lazy_init_process_tests import (
        TestProcessDirectory as TestProcessDirectory,
    )
    from tests.unit.codegen.lazy_init_service_tests import (
        TestFlextInfraCodegenLazyInit as TestFlextInfraCodegenLazyInit,
    )
    from tests.unit.codegen.lazy_init_tests import (
        TestAllDirectoriesScanned as TestAllDirectoriesScanned,
        TestCheckOnlyMode as TestCheckOnlyMode,
        TestEdgeCases as TestEdgeCases,
        TestExcludedDirectories as TestExcludedDirectories,
    )
    from tests.unit.codegen.lazy_init_transforms_tests import (
        TestExtractInlineConstants as TestExtractInlineConstants,
        TestExtractVersionExports as TestExtractVersionExports,
        TestMergeChildExports as TestMergeChildExports,
        TestScanAstPublicDefs as TestScanAstPublicDefs,
        TestShouldBubbleUp as TestShouldBubbleUp,
    )
    from tests.unit.codegen.main_tests import (
        TestHandleLazyInit as TestHandleLazyInit,
        TestMainCommandDispatch as TestMainCommandDispatch,
        TestMainEntryPoint as TestMainEntryPoint,
    )
    from tests.unit.codegen.pipeline_tests import (
        test_codegen_pipeline_end_to_end as test_codegen_pipeline_end_to_end,
    )
    from tests.unit.codegen.scaffolder_naming_tests import (
        TestGeneratedClassNamingConvention as TestGeneratedClassNamingConvention,
        TestGeneratedFilesAreValidPython as TestGeneratedFilesAreValidPython,
    )
    from tests.unit.codegen.scaffolder_tests import (
        TestScaffoldProjectCreatesSrcModules as TestScaffoldProjectCreatesSrcModules,
        TestScaffoldProjectCreatesTestsModules as TestScaffoldProjectCreatesTestsModules,
        TestScaffoldProjectIdempotency as TestScaffoldProjectIdempotency,
        TestScaffoldProjectNoop as TestScaffoldProjectNoop,
    )

_LAZY_IMPORTS: Mapping[str, Sequence[str]] = {
    "TestAllDirectoriesScanned": [
        "tests.unit.codegen.lazy_init_tests",
        "TestAllDirectoriesScanned",
    ],
    "TestBuildSiblingExportIndex": [
        "tests.unit.codegen.lazy_init_helpers_tests",
        "TestBuildSiblingExportIndex",
    ],
    "TestCensusReportModel": [
        "tests.unit.codegen.census_models_tests",
        "TestCensusReportModel",
    ],
    "TestCensusViolationModel": [
        "tests.unit.codegen.census_models_tests",
        "TestCensusViolationModel",
    ],
    "TestCheckOnlyMode": ["tests.unit.codegen.lazy_init_tests", "TestCheckOnlyMode"],
    "TestConstantsQualityGateCLIDispatch": [
        "tests.unit.codegen.constants_quality_gate_tests",
        "TestConstantsQualityGateCLIDispatch",
    ],
    "TestConstantsQualityGateVerdict": [
        "tests.unit.codegen.constants_quality_gate_tests",
        "TestConstantsQualityGateVerdict",
    ],
    "TestEdgeCases": ["tests.unit.codegen.lazy_init_tests", "TestEdgeCases"],
    "TestExcludedDirectories": [
        "tests.unit.codegen.lazy_init_tests",
        "TestExcludedDirectories",
    ],
    "TestExcludedProjects": [
        "tests.unit.codegen.census_models_tests",
        "TestExcludedProjects",
    ],
    "TestExtractExports": [
        "tests.unit.codegen.lazy_init_helpers_tests",
        "TestExtractExports",
    ],
    "TestExtractInlineConstants": [
        "tests.unit.codegen.lazy_init_transforms_tests",
        "TestExtractInlineConstants",
    ],
    "TestExtractVersionExports": [
        "tests.unit.codegen.lazy_init_transforms_tests",
        "TestExtractVersionExports",
    ],
    "TestFixabilityClassification": [
        "tests.unit.codegen.census_tests",
        "TestFixabilityClassification",
    ],
    "TestFlextInfraCodegenLazyInit": [
        "tests.unit.codegen.lazy_init_service_tests",
        "TestFlextInfraCodegenLazyInit",
    ],
    "TestGenerateFile": [
        "tests.unit.codegen.lazy_init_generation_tests",
        "TestGenerateFile",
    ],
    "TestGenerateTypeChecking": [
        "tests.unit.codegen.lazy_init_generation_tests",
        "TestGenerateTypeChecking",
    ],
    "TestGeneratedClassNamingConvention": [
        "tests.unit.codegen.scaffolder_naming_tests",
        "TestGeneratedClassNamingConvention",
    ],
    "TestGeneratedFilesAreValidPython": [
        "tests.unit.codegen.scaffolder_naming_tests",
        "TestGeneratedFilesAreValidPython",
    ],
    "TestHandleLazyInit": ["tests.unit.codegen.main_tests", "TestHandleLazyInit"],
    "TestInferPackage": [
        "tests.unit.codegen.lazy_init_helpers_tests",
        "TestInferPackage",
    ],
    "TestMainCommandDispatch": [
        "tests.unit.codegen.main_tests",
        "TestMainCommandDispatch",
    ],
    "TestMainEntryPoint": ["tests.unit.codegen.main_tests", "TestMainEntryPoint"],
    "TestMergeChildExports": [
        "tests.unit.codegen.lazy_init_transforms_tests",
        "TestMergeChildExports",
    ],
    "TestParseViolationInvalid": [
        "tests.unit.codegen.census_tests",
        "TestParseViolationInvalid",
    ],
    "TestParseViolationValid": [
        "tests.unit.codegen.census_tests",
        "TestParseViolationValid",
    ],
    "TestProcessDirectory": [
        "tests.unit.codegen.lazy_init_process_tests",
        "TestProcessDirectory",
    ],
    "TestReadExistingDocstring": [
        "tests.unit.codegen.lazy_init_helpers_tests",
        "TestReadExistingDocstring",
    ],
    "TestResolveAliases": [
        "tests.unit.codegen.lazy_init_generation_tests",
        "TestResolveAliases",
    ],
    "TestRunRuffFix": [
        "tests.unit.codegen.lazy_init_generation_tests",
        "TestRunRuffFix",
    ],
    "TestScaffoldProjectCreatesSrcModules": [
        "tests.unit.codegen.scaffolder_tests",
        "TestScaffoldProjectCreatesSrcModules",
    ],
    "TestScaffoldProjectCreatesTestsModules": [
        "tests.unit.codegen.scaffolder_tests",
        "TestScaffoldProjectCreatesTestsModules",
    ],
    "TestScaffoldProjectIdempotency": [
        "tests.unit.codegen.scaffolder_tests",
        "TestScaffoldProjectIdempotency",
    ],
    "TestScaffoldProjectNoop": [
        "tests.unit.codegen.scaffolder_tests",
        "TestScaffoldProjectNoop",
    ],
    "TestScanAstPublicDefs": [
        "tests.unit.codegen.lazy_init_transforms_tests",
        "TestScanAstPublicDefs",
    ],
    "TestShouldBubbleUp": [
        "tests.unit.codegen.lazy_init_transforms_tests",
        "TestShouldBubbleUp",
    ],
    "TestViolationPattern": [
        "tests.unit.codegen.census_models_tests",
        "TestViolationPattern",
    ],
    "autofix_tests": ["tests.unit.codegen.autofix_tests", ""],
    "autofix_workspace_tests": ["tests.unit.codegen.autofix_workspace_tests", ""],
    "census": ["tests.unit.codegen.census_tests", "census"],
    "census_models_tests": ["tests.unit.codegen.census_models_tests", ""],
    "census_tests": ["tests.unit.codegen.census_tests", ""],
    "constants_quality_gate_tests": [
        "tests.unit.codegen.constants_quality_gate_tests",
        "",
    ],
    "fixer": ["tests.unit.codegen.autofix_tests", "fixer"],
    "init_tests": ["tests.unit.codegen.init_tests", ""],
    "lazy_init_generation_tests": ["tests.unit.codegen.lazy_init_generation_tests", ""],
    "lazy_init_helpers_tests": ["tests.unit.codegen.lazy_init_helpers_tests", ""],
    "lazy_init_process_tests": ["tests.unit.codegen.lazy_init_process_tests", ""],
    "lazy_init_service_tests": ["tests.unit.codegen.lazy_init_service_tests", ""],
    "lazy_init_tests": ["tests.unit.codegen.lazy_init_tests", ""],
    "lazy_init_transforms_tests": ["tests.unit.codegen.lazy_init_transforms_tests", ""],
    "main_tests": ["tests.unit.codegen.main_tests", ""],
    "pipeline_tests": ["tests.unit.codegen.pipeline_tests", ""],
    "scaffolder_naming_tests": ["tests.unit.codegen.scaffolder_naming_tests", ""],
    "scaffolder_tests": ["tests.unit.codegen.scaffolder_tests", ""],
    "test_codegen_dir_returns_all_exports": [
        "tests.unit.codegen.init_tests",
        "test_codegen_dir_returns_all_exports",
    ],
    "test_codegen_getattr_raises_attribute_error": [
        "tests.unit.codegen.init_tests",
        "test_codegen_getattr_raises_attribute_error",
    ],
    "test_codegen_init_getattr_raises_attribute_error": [
        "tests.unit.codegen.lazy_init_generation_tests",
        "test_codegen_init_getattr_raises_attribute_error",
    ],
    "test_codegen_lazy_imports_work": [
        "tests.unit.codegen.init_tests",
        "test_codegen_lazy_imports_work",
    ],
    "test_codegen_pipeline_end_to_end": [
        "tests.unit.codegen.pipeline_tests",
        "test_codegen_pipeline_end_to_end",
    ],
    "test_files_modified_tracks_affected_files": [
        "tests.unit.codegen.autofix_workspace_tests",
        "test_files_modified_tracks_affected_files",
    ],
    "test_flexcore_excluded_from_run": [
        "tests.unit.codegen.autofix_workspace_tests",
        "test_flexcore_excluded_from_run",
    ],
    "test_in_context_typevar_not_flagged": [
        "tests.unit.codegen.autofix_tests",
        "test_in_context_typevar_not_flagged",
    ],
    "test_project_without_src_returns_empty": [
        "tests.unit.codegen.autofix_workspace_tests",
        "test_project_without_src_returns_empty",
    ],
    "test_standalone_final_detected_as_fixable": [
        "tests.unit.codegen.autofix_tests",
        "test_standalone_final_detected_as_fixable",
    ],
    "test_standalone_typealias_detected_as_fixable": [
        "tests.unit.codegen.autofix_tests",
        "test_standalone_typealias_detected_as_fixable",
    ],
    "test_standalone_typevar_detected_as_fixable": [
        "tests.unit.codegen.autofix_tests",
        "test_standalone_typevar_detected_as_fixable",
    ],
    "test_syntax_error_files_skipped": [
        "tests.unit.codegen.autofix_tests",
        "test_syntax_error_files_skipped",
    ],
}

_EXPORTS: Sequence[str] = [
    "TestAllDirectoriesScanned",
    "TestBuildSiblingExportIndex",
    "TestCensusReportModel",
    "TestCensusViolationModel",
    "TestCheckOnlyMode",
    "TestConstantsQualityGateCLIDispatch",
    "TestConstantsQualityGateVerdict",
    "TestEdgeCases",
    "TestExcludedDirectories",
    "TestExcludedProjects",
    "TestExtractExports",
    "TestExtractInlineConstants",
    "TestExtractVersionExports",
    "TestFixabilityClassification",
    "TestFlextInfraCodegenLazyInit",
    "TestGenerateFile",
    "TestGenerateTypeChecking",
    "TestGeneratedClassNamingConvention",
    "TestGeneratedFilesAreValidPython",
    "TestHandleLazyInit",
    "TestInferPackage",
    "TestMainCommandDispatch",
    "TestMainEntryPoint",
    "TestMergeChildExports",
    "TestParseViolationInvalid",
    "TestParseViolationValid",
    "TestProcessDirectory",
    "TestReadExistingDocstring",
    "TestResolveAliases",
    "TestRunRuffFix",
    "TestScaffoldProjectCreatesSrcModules",
    "TestScaffoldProjectCreatesTestsModules",
    "TestScaffoldProjectIdempotency",
    "TestScaffoldProjectNoop",
    "TestScanAstPublicDefs",
    "TestShouldBubbleUp",
    "TestViolationPattern",
    "autofix_tests",
    "autofix_workspace_tests",
    "census",
    "census_models_tests",
    "census_tests",
    "constants_quality_gate_tests",
    "fixer",
    "init_tests",
    "lazy_init_generation_tests",
    "lazy_init_helpers_tests",
    "lazy_init_process_tests",
    "lazy_init_service_tests",
    "lazy_init_tests",
    "lazy_init_transforms_tests",
    "main_tests",
    "pipeline_tests",
    "scaffolder_naming_tests",
    "scaffolder_tests",
    "test_codegen_dir_returns_all_exports",
    "test_codegen_getattr_raises_attribute_error",
    "test_codegen_init_getattr_raises_attribute_error",
    "test_codegen_lazy_imports_work",
    "test_codegen_pipeline_end_to_end",
    "test_files_modified_tracks_affected_files",
    "test_flexcore_excluded_from_run",
    "test_in_context_typevar_not_flagged",
    "test_project_without_src_returns_empty",
    "test_standalone_final_detected_as_fixable",
    "test_standalone_typealias_detected_as_fixable",
    "test_standalone_typevar_detected_as_fixable",
    "test_syntax_error_files_skipped",
]


install_lazy_exports(__name__, globals(), _LAZY_IMPORTS, _EXPORTS)
