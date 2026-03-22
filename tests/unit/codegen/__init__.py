# AUTO-GENERATED FILE — DO NOT EDIT MANUALLY.
# Regenerate with: make codegen
#
"""Codegen package."""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_core.lazy import cleanup_submodule_namespace, lazy_getattr

if TYPE_CHECKING:
    from flext_core.typings import FlextTypes

    from .autofix_tests import (
        fixer,
        test_in_context_typevar_not_flagged,
        test_standalone_final_detected_as_fixable,
        test_standalone_typealias_detected_as_fixable,
        test_standalone_typevar_detected_as_fixable,
        test_syntax_error_files_skipped,
    )
    from .autofix_workspace_tests import (
        test_files_modified_tracks_affected_files,
        test_flexcore_excluded_from_run,
        test_project_without_src_returns_empty,
    )
    from .census_models_tests import (
        TestCensusReportModel,
        TestCensusViolationModel,
        TestExcludedProjects,
        TestViolationPattern,
    )
    from .census_tests import (
        TestFixabilityClassification,
        TestParseViolationInvalid,
        TestParseViolationValid,
        census,
    )
    from .constants_quality_gate_tests import (
        TestConstantsQualityGateCLIDispatch,
        TestConstantsQualityGateVerdict,
    )
    from .init_tests import (
        test_codegen_dir_returns_all_exports,
        test_codegen_getattr_raises_attribute_error,
        test_codegen_lazy_imports_work,
    )
    from .lazy_init_generation_tests import (
        TestGenerateFile,
        TestGenerateTypeChecking,
        TestResolveAliases,
        TestRunRuffFix,
        test_codegen_init_getattr_raises_attribute_error,
    )
    from .lazy_init_helpers_tests import (
        TestBuildSiblingExportIndex,
        TestExtractExports,
        TestInferPackage,
        TestReadExistingDocstring,
    )
    from .lazy_init_process_tests import TestProcessDirectory
    from .lazy_init_service_tests import TestFlextInfraCodegenLazyInit
    from .lazy_init_tests import (
        TestAllDirectoriesScanned,
        TestCheckOnlyMode,
        TestEdgeCases,
        TestExcludedDirectories,
    )
    from .lazy_init_transforms_tests import (
        TestExtractInlineConstants,
        TestExtractVersionExports,
        TestMergeChildExports,
        TestScanAstPublicDefs,
        TestShouldBubbleUp,
    )
    from .main_tests import (
        TestHandleLazyInit,
        TestMainCommandDispatch,
        TestMainEntryPoint,
    )
    from .pipeline_tests import test_codegen_pipeline_end_to_end
    from .scaffolder_naming_tests import (
        TestGeneratedClassNamingConvention,
        TestGeneratedFilesAreValidPython,
    )
    from .scaffolder_tests import (
        TestScaffoldProjectCreatesSrcModules,
        TestScaffoldProjectCreatesTestsModules,
        TestScaffoldProjectIdempotency,
        TestScaffoldProjectNoop,
    )

_LAZY_IMPORTS: dict[str, tuple[str, str]] = {
    "TestAllDirectoriesScanned": (
        "tests.unit.codegen.lazy_init_tests",
        "TestAllDirectoriesScanned",
    ),
    "TestBuildSiblingExportIndex": (
        "tests.unit.codegen.lazy_init_helpers_tests",
        "TestBuildSiblingExportIndex",
    ),
    "TestCensusReportModel": (
        "tests.unit.codegen.census_models_tests",
        "TestCensusReportModel",
    ),
    "TestCensusViolationModel": (
        "tests.unit.codegen.census_models_tests",
        "TestCensusViolationModel",
    ),
    "TestCheckOnlyMode": ("tests.unit.codegen.lazy_init_tests", "TestCheckOnlyMode"),
    "TestConstantsQualityGateCLIDispatch": (
        "tests.unit.codegen.constants_quality_gate_tests",
        "TestConstantsQualityGateCLIDispatch",
    ),
    "TestConstantsQualityGateVerdict": (
        "tests.unit.codegen.constants_quality_gate_tests",
        "TestConstantsQualityGateVerdict",
    ),
    "TestEdgeCases": ("tests.unit.codegen.lazy_init_tests", "TestEdgeCases"),
    "TestExcludedDirectories": (
        "tests.unit.codegen.lazy_init_tests",
        "TestExcludedDirectories",
    ),
    "TestExcludedProjects": (
        "tests.unit.codegen.census_models_tests",
        "TestExcludedProjects",
    ),
    "TestExtractExports": (
        "tests.unit.codegen.lazy_init_helpers_tests",
        "TestExtractExports",
    ),
    "TestExtractInlineConstants": (
        "tests.unit.codegen.lazy_init_transforms_tests",
        "TestExtractInlineConstants",
    ),
    "TestExtractVersionExports": (
        "tests.unit.codegen.lazy_init_transforms_tests",
        "TestExtractVersionExports",
    ),
    "TestFixabilityClassification": (
        "tests.unit.codegen.census_tests",
        "TestFixabilityClassification",
    ),
    "TestFlextInfraCodegenLazyInit": (
        "tests.unit.codegen.lazy_init_service_tests",
        "TestFlextInfraCodegenLazyInit",
    ),
    "TestGenerateFile": (
        "tests.unit.codegen.lazy_init_generation_tests",
        "TestGenerateFile",
    ),
    "TestGenerateTypeChecking": (
        "tests.unit.codegen.lazy_init_generation_tests",
        "TestGenerateTypeChecking",
    ),
    "TestGeneratedClassNamingConvention": (
        "tests.unit.codegen.scaffolder_naming_tests",
        "TestGeneratedClassNamingConvention",
    ),
    "TestGeneratedFilesAreValidPython": (
        "tests.unit.codegen.scaffolder_naming_tests",
        "TestGeneratedFilesAreValidPython",
    ),
    "TestHandleLazyInit": ("tests.unit.codegen.main_tests", "TestHandleLazyInit"),
    "TestInferPackage": (
        "tests.unit.codegen.lazy_init_helpers_tests",
        "TestInferPackage",
    ),
    "TestMainCommandDispatch": (
        "tests.unit.codegen.main_tests",
        "TestMainCommandDispatch",
    ),
    "TestMainEntryPoint": ("tests.unit.codegen.main_tests", "TestMainEntryPoint"),
    "TestMergeChildExports": (
        "tests.unit.codegen.lazy_init_transforms_tests",
        "TestMergeChildExports",
    ),
    "TestParseViolationInvalid": (
        "tests.unit.codegen.census_tests",
        "TestParseViolationInvalid",
    ),
    "TestParseViolationValid": (
        "tests.unit.codegen.census_tests",
        "TestParseViolationValid",
    ),
    "TestProcessDirectory": (
        "tests.unit.codegen.lazy_init_process_tests",
        "TestProcessDirectory",
    ),
    "TestReadExistingDocstring": (
        "tests.unit.codegen.lazy_init_helpers_tests",
        "TestReadExistingDocstring",
    ),
    "TestResolveAliases": (
        "tests.unit.codegen.lazy_init_generation_tests",
        "TestResolveAliases",
    ),
    "TestRunRuffFix": (
        "tests.unit.codegen.lazy_init_generation_tests",
        "TestRunRuffFix",
    ),
    "TestScaffoldProjectCreatesSrcModules": (
        "tests.unit.codegen.scaffolder_tests",
        "TestScaffoldProjectCreatesSrcModules",
    ),
    "TestScaffoldProjectCreatesTestsModules": (
        "tests.unit.codegen.scaffolder_tests",
        "TestScaffoldProjectCreatesTestsModules",
    ),
    "TestScaffoldProjectIdempotency": (
        "tests.unit.codegen.scaffolder_tests",
        "TestScaffoldProjectIdempotency",
    ),
    "TestScaffoldProjectNoop": (
        "tests.unit.codegen.scaffolder_tests",
        "TestScaffoldProjectNoop",
    ),
    "TestScanAstPublicDefs": (
        "tests.unit.codegen.lazy_init_transforms_tests",
        "TestScanAstPublicDefs",
    ),
    "TestShouldBubbleUp": (
        "tests.unit.codegen.lazy_init_transforms_tests",
        "TestShouldBubbleUp",
    ),
    "TestViolationPattern": (
        "tests.unit.codegen.census_models_tests",
        "TestViolationPattern",
    ),
    "census": ("tests.unit.codegen.census_tests", "census"),
    "fixer": ("tests.unit.codegen.autofix_tests", "fixer"),
    "test_codegen_dir_returns_all_exports": (
        "tests.unit.codegen.init_tests",
        "test_codegen_dir_returns_all_exports",
    ),
    "test_codegen_getattr_raises_attribute_error": (
        "tests.unit.codegen.init_tests",
        "test_codegen_getattr_raises_attribute_error",
    ),
    "test_codegen_init_getattr_raises_attribute_error": (
        "tests.unit.codegen.lazy_init_generation_tests",
        "test_codegen_init_getattr_raises_attribute_error",
    ),
    "test_codegen_lazy_imports_work": (
        "tests.unit.codegen.init_tests",
        "test_codegen_lazy_imports_work",
    ),
    "test_codegen_pipeline_end_to_end": (
        "tests.unit.codegen.pipeline_tests",
        "test_codegen_pipeline_end_to_end",
    ),
    "test_files_modified_tracks_affected_files": (
        "tests.unit.codegen.autofix_workspace_tests",
        "test_files_modified_tracks_affected_files",
    ),
    "test_flexcore_excluded_from_run": (
        "tests.unit.codegen.autofix_workspace_tests",
        "test_flexcore_excluded_from_run",
    ),
    "test_in_context_typevar_not_flagged": (
        "tests.unit.codegen.autofix_tests",
        "test_in_context_typevar_not_flagged",
    ),
    "test_project_without_src_returns_empty": (
        "tests.unit.codegen.autofix_workspace_tests",
        "test_project_without_src_returns_empty",
    ),
    "test_standalone_final_detected_as_fixable": (
        "tests.unit.codegen.autofix_tests",
        "test_standalone_final_detected_as_fixable",
    ),
    "test_standalone_typealias_detected_as_fixable": (
        "tests.unit.codegen.autofix_tests",
        "test_standalone_typealias_detected_as_fixable",
    ),
    "test_standalone_typevar_detected_as_fixable": (
        "tests.unit.codegen.autofix_tests",
        "test_standalone_typevar_detected_as_fixable",
    ),
    "test_syntax_error_files_skipped": (
        "tests.unit.codegen.autofix_tests",
        "test_syntax_error_files_skipped",
    ),
}

__all__ = [
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
    "census",
    "fixer",
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


_LAZY_CACHE: dict[str, FlextTypes.ModuleExport] = {}


def __getattr__(name: str) -> FlextTypes.ModuleExport:
    """Lazy-load module attributes on first access (PEP 562).

    A local cache ``_LAZY_CACHE`` persists resolved objects across repeated
    accesses during process lifetime.

    Args:
        name: Attribute name requested by dir()/import.

    Returns:
        Lazy-loaded module export type.

    Raises:
        AttributeError: If attribute not registered.

    """
    if name in _LAZY_CACHE:
        return _LAZY_CACHE[name]

    value = lazy_getattr(name, _LAZY_IMPORTS, globals(), __name__)
    _LAZY_CACHE[name] = value
    return value


def __dir__() -> list[str]:
    """Return list of available attributes for dir() and autocomplete.

    Returns:
        List of public names from module exports.

    """
    return sorted(__all__)


cleanup_submodule_namespace(__name__, _LAZY_IMPORTS)
