# AUTO-GENERATED FILE — DO NOT EDIT MANUALLY.
# Regenerate with: make codegen
#
"""Codegen package."""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_core.lazy import cleanup_submodule_namespace, lazy_getattr

if TYPE_CHECKING:
    from flext_core.typings import FlextTypes


if TYPE_CHECKING:
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
        "tests.infra.unit.codegen.lazy_init_tests",
        "TestAllDirectoriesScanned",
    ),
    "TestBuildSiblingExportIndex": (
        "tests.infra.unit.codegen.lazy_init_helpers_tests",
        "TestBuildSiblingExportIndex",
    ),
    "TestCensusReportModel": (
        "tests.infra.unit.codegen.census_models_tests",
        "TestCensusReportModel",
    ),
    "TestCensusViolationModel": (
        "tests.infra.unit.codegen.census_models_tests",
        "TestCensusViolationModel",
    ),
    "TestCheckOnlyMode": (
        "tests.infra.unit.codegen.lazy_init_tests",
        "TestCheckOnlyMode",
    ),
    "TestConstantsQualityGateCLIDispatch": (
        "tests.infra.unit.codegen.constants_quality_gate_tests",
        "TestConstantsQualityGateCLIDispatch",
    ),
    "TestConstantsQualityGateVerdict": (
        "tests.infra.unit.codegen.constants_quality_gate_tests",
        "TestConstantsQualityGateVerdict",
    ),
    "TestEdgeCases": ("tests.infra.unit.codegen.lazy_init_tests", "TestEdgeCases"),
    "TestExcludedDirectories": (
        "tests.infra.unit.codegen.lazy_init_tests",
        "TestExcludedDirectories",
    ),
    "TestExcludedProjects": (
        "tests.infra.unit.codegen.census_models_tests",
        "TestExcludedProjects",
    ),
    "TestExtractExports": (
        "tests.infra.unit.codegen.lazy_init_helpers_tests",
        "TestExtractExports",
    ),
    "TestExtractInlineConstants": (
        "tests.infra.unit.codegen.lazy_init_transforms_tests",
        "TestExtractInlineConstants",
    ),
    "TestExtractVersionExports": (
        "tests.infra.unit.codegen.lazy_init_transforms_tests",
        "TestExtractVersionExports",
    ),
    "TestFixabilityClassification": (
        "tests.infra.unit.codegen.census_tests",
        "TestFixabilityClassification",
    ),
    "TestFlextInfraCodegenLazyInit": (
        "tests.infra.unit.codegen.lazy_init_service_tests",
        "TestFlextInfraCodegenLazyInit",
    ),
    "TestGenerateFile": (
        "tests.infra.unit.codegen.lazy_init_generation_tests",
        "TestGenerateFile",
    ),
    "TestGenerateTypeChecking": (
        "tests.infra.unit.codegen.lazy_init_generation_tests",
        "TestGenerateTypeChecking",
    ),
    "TestGeneratedClassNamingConvention": (
        "tests.infra.unit.codegen.scaffolder_naming_tests",
        "TestGeneratedClassNamingConvention",
    ),
    "TestGeneratedFilesAreValidPython": (
        "tests.infra.unit.codegen.scaffolder_naming_tests",
        "TestGeneratedFilesAreValidPython",
    ),
    "TestHandleLazyInit": ("tests.infra.unit.codegen.main_tests", "TestHandleLazyInit"),
    "TestInferPackage": (
        "tests.infra.unit.codegen.lazy_init_helpers_tests",
        "TestInferPackage",
    ),
    "TestMainCommandDispatch": (
        "tests.infra.unit.codegen.main_tests",
        "TestMainCommandDispatch",
    ),
    "TestMainEntryPoint": ("tests.infra.unit.codegen.main_tests", "TestMainEntryPoint"),
    "TestMergeChildExports": (
        "tests.infra.unit.codegen.lazy_init_transforms_tests",
        "TestMergeChildExports",
    ),
    "TestParseViolationInvalid": (
        "tests.infra.unit.codegen.census_tests",
        "TestParseViolationInvalid",
    ),
    "TestParseViolationValid": (
        "tests.infra.unit.codegen.census_tests",
        "TestParseViolationValid",
    ),
    "TestProcessDirectory": (
        "tests.infra.unit.codegen.lazy_init_process_tests",
        "TestProcessDirectory",
    ),
    "TestReadExistingDocstring": (
        "tests.infra.unit.codegen.lazy_init_helpers_tests",
        "TestReadExistingDocstring",
    ),
    "TestResolveAliases": (
        "tests.infra.unit.codegen.lazy_init_generation_tests",
        "TestResolveAliases",
    ),
    "TestRunRuffFix": (
        "tests.infra.unit.codegen.lazy_init_generation_tests",
        "TestRunRuffFix",
    ),
    "TestScaffoldProjectCreatesSrcModules": (
        "tests.infra.unit.codegen.scaffolder_tests",
        "TestScaffoldProjectCreatesSrcModules",
    ),
    "TestScaffoldProjectCreatesTestsModules": (
        "tests.infra.unit.codegen.scaffolder_tests",
        "TestScaffoldProjectCreatesTestsModules",
    ),
    "TestScaffoldProjectIdempotency": (
        "tests.infra.unit.codegen.scaffolder_tests",
        "TestScaffoldProjectIdempotency",
    ),
    "TestScaffoldProjectNoop": (
        "tests.infra.unit.codegen.scaffolder_tests",
        "TestScaffoldProjectNoop",
    ),
    "TestScanAstPublicDefs": (
        "tests.infra.unit.codegen.lazy_init_transforms_tests",
        "TestScanAstPublicDefs",
    ),
    "TestShouldBubbleUp": (
        "tests.infra.unit.codegen.lazy_init_transforms_tests",
        "TestShouldBubbleUp",
    ),
    "TestViolationPattern": (
        "tests.infra.unit.codegen.census_models_tests",
        "TestViolationPattern",
    ),
    "census": ("tests.infra.unit.codegen.census_tests", "census"),
    "fixer": ("tests.infra.unit.codegen.autofix_tests", "fixer"),
    "test_codegen_dir_returns_all_exports": (
        "tests.infra.unit.codegen.init_tests",
        "test_codegen_dir_returns_all_exports",
    ),
    "test_codegen_getattr_raises_attribute_error": (
        "tests.infra.unit.codegen.init_tests",
        "test_codegen_getattr_raises_attribute_error",
    ),
    "test_codegen_init_getattr_raises_attribute_error": (
        "tests.infra.unit.codegen.lazy_init_generation_tests",
        "test_codegen_init_getattr_raises_attribute_error",
    ),
    "test_codegen_lazy_imports_work": (
        "tests.infra.unit.codegen.init_tests",
        "test_codegen_lazy_imports_work",
    ),
    "test_codegen_pipeline_end_to_end": (
        "tests.infra.unit.codegen.pipeline_tests",
        "test_codegen_pipeline_end_to_end",
    ),
    "test_files_modified_tracks_affected_files": (
        "tests.infra.unit.codegen.autofix_workspace_tests",
        "test_files_modified_tracks_affected_files",
    ),
    "test_flexcore_excluded_from_run": (
        "tests.infra.unit.codegen.autofix_workspace_tests",
        "test_flexcore_excluded_from_run",
    ),
    "test_in_context_typevar_not_flagged": (
        "tests.infra.unit.codegen.autofix_tests",
        "test_in_context_typevar_not_flagged",
    ),
    "test_project_without_src_returns_empty": (
        "tests.infra.unit.codegen.autofix_workspace_tests",
        "test_project_without_src_returns_empty",
    ),
    "test_standalone_final_detected_as_fixable": (
        "tests.infra.unit.codegen.autofix_tests",
        "test_standalone_final_detected_as_fixable",
    ),
    "test_standalone_typealias_detected_as_fixable": (
        "tests.infra.unit.codegen.autofix_tests",
        "test_standalone_typealias_detected_as_fixable",
    ),
    "test_standalone_typevar_detected_as_fixable": (
        "tests.infra.unit.codegen.autofix_tests",
        "test_standalone_typevar_detected_as_fixable",
    ),
    "test_syntax_error_files_skipped": (
        "tests.infra.unit.codegen.autofix_tests",
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
