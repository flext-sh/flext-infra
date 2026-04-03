# AUTO-GENERATED FILE — DO NOT EDIT MANUALLY.
# Regenerate with: make gen
#
"""Codegen package."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import TYPE_CHECKING as _TYPE_CHECKING

from flext_core.lazy import install_lazy_exports

if _TYPE_CHECKING:
    from flext_core import FlextTypes
    from tests.unit.codegen import (
        _project_factory,
        autofix_workspace_tests,
        census_models_tests,
        census_tests,
        constants_quality_gate_tests,
        init_tests,
        lazy_init_generation_tests,
        lazy_init_helpers_tests,
        lazy_init_process_tests,
        lazy_init_service_tests,
        lazy_init_tests,
        lazy_init_transforms_tests,
        main_tests,
        pipeline_tests,
        scaffolder_naming_tests,
        scaffolder_tests,
    )
    from tests.unit.codegen._project_factory import FlextInfraCodegenTestProjectFactory
    from tests.unit.codegen.autofix_workspace_tests import (
        test_files_modified_tracks_affected_files,
        test_flexcore_excluded_from_run,
        test_project_without_src_returns_empty,
    )
    from tests.unit.codegen.census_models_tests import (
        TestCensusReportModel,
        TestCensusViolationModel,
        TestExcludedProjects,
        TestViolationPattern,
    )
    from tests.unit.codegen.census_tests import (
        TestFixabilityClassification,
        TestParseViolationInvalid,
        TestParseViolationValid,
        census,
    )
    from tests.unit.codegen.constants_quality_gate_tests import (
        TestConstantsQualityGateCLIDispatch,
        TestConstantsQualityGateVerdict,
    )
    from tests.unit.codegen.init_tests import (
        test_codegen_dir_returns_all_exports,
        test_codegen_getattr_raises_attribute_error,
        test_codegen_lazy_imports_work,
    )
    from tests.unit.codegen.lazy_init_generation_tests import (
        TestGenerateFile,
        TestGenerateTypeChecking,
        TestResolveAliases,
        TestRunRuffFix,
        test_codegen_init_getattr_raises_attribute_error,
    )
    from tests.unit.codegen.lazy_init_helpers_tests import (
        TestBuildSiblingExportIndex,
        TestExtractExports,
        TestInferPackage,
        TestReadExistingDocstring,
    )
    from tests.unit.codegen.lazy_init_process_tests import TestProcessDirectory
    from tests.unit.codegen.lazy_init_service_tests import TestFlextInfraCodegenLazyInit
    from tests.unit.codegen.lazy_init_tests import (
        TestAllDirectoriesScanned,
        TestCheckOnlyMode,
        TestEdgeCases,
        TestExcludedDirectories,
    )
    from tests.unit.codegen.lazy_init_transforms_tests import (
        TestExtractInlineConstants,
        TestExtractVersionExports,
        TestMergeChildExports,
        TestScanAstPublicDefs,
        TestShouldBubbleUp,
    )
    from tests.unit.codegen.main_tests import (
        TestHandleLazyInit,
        TestMainCommandDispatch,
        TestMainEntryPoint,
    )
    from tests.unit.codegen.pipeline_tests import test_codegen_pipeline_end_to_end
    from tests.unit.codegen.scaffolder_naming_tests import (
        TestGeneratedClassNamingConvention,
        TestGeneratedFilesAreValidPython,
    )
    from tests.unit.codegen.scaffolder_tests import (
        TestScaffoldProjectCreatesSrcModules,
        TestScaffoldProjectCreatesTestsModules,
        TestScaffoldProjectIdempotency,
        TestScaffoldProjectNoop,
    )

_LAZY_IMPORTS: FlextTypes.LazyImportIndex = {
    "FlextInfraCodegenTestProjectFactory": "tests.unit.codegen._project_factory",
    "TestAllDirectoriesScanned": "tests.unit.codegen.lazy_init_tests",
    "TestBuildSiblingExportIndex": "tests.unit.codegen.lazy_init_helpers_tests",
    "TestCensusReportModel": "tests.unit.codegen.census_models_tests",
    "TestCensusViolationModel": "tests.unit.codegen.census_models_tests",
    "TestCheckOnlyMode": "tests.unit.codegen.lazy_init_tests",
    "TestConstantsQualityGateCLIDispatch": "tests.unit.codegen.constants_quality_gate_tests",
    "TestConstantsQualityGateVerdict": "tests.unit.codegen.constants_quality_gate_tests",
    "TestEdgeCases": "tests.unit.codegen.lazy_init_tests",
    "TestExcludedDirectories": "tests.unit.codegen.lazy_init_tests",
    "TestExcludedProjects": "tests.unit.codegen.census_models_tests",
    "TestExtractExports": "tests.unit.codegen.lazy_init_helpers_tests",
    "TestExtractInlineConstants": "tests.unit.codegen.lazy_init_transforms_tests",
    "TestExtractVersionExports": "tests.unit.codegen.lazy_init_transforms_tests",
    "TestFixabilityClassification": "tests.unit.codegen.census_tests",
    "TestFlextInfraCodegenLazyInit": "tests.unit.codegen.lazy_init_service_tests",
    "TestGenerateFile": "tests.unit.codegen.lazy_init_generation_tests",
    "TestGenerateTypeChecking": "tests.unit.codegen.lazy_init_generation_tests",
    "TestGeneratedClassNamingConvention": "tests.unit.codegen.scaffolder_naming_tests",
    "TestGeneratedFilesAreValidPython": "tests.unit.codegen.scaffolder_naming_tests",
    "TestHandleLazyInit": "tests.unit.codegen.main_tests",
    "TestInferPackage": "tests.unit.codegen.lazy_init_helpers_tests",
    "TestMainCommandDispatch": "tests.unit.codegen.main_tests",
    "TestMainEntryPoint": "tests.unit.codegen.main_tests",
    "TestMergeChildExports": "tests.unit.codegen.lazy_init_transforms_tests",
    "TestParseViolationInvalid": "tests.unit.codegen.census_tests",
    "TestParseViolationValid": "tests.unit.codegen.census_tests",
    "TestProcessDirectory": "tests.unit.codegen.lazy_init_process_tests",
    "TestReadExistingDocstring": "tests.unit.codegen.lazy_init_helpers_tests",
    "TestResolveAliases": "tests.unit.codegen.lazy_init_generation_tests",
    "TestRunRuffFix": "tests.unit.codegen.lazy_init_generation_tests",
    "TestScaffoldProjectCreatesSrcModules": "tests.unit.codegen.scaffolder_tests",
    "TestScaffoldProjectCreatesTestsModules": "tests.unit.codegen.scaffolder_tests",
    "TestScaffoldProjectIdempotency": "tests.unit.codegen.scaffolder_tests",
    "TestScaffoldProjectNoop": "tests.unit.codegen.scaffolder_tests",
    "TestScanAstPublicDefs": "tests.unit.codegen.lazy_init_transforms_tests",
    "TestShouldBubbleUp": "tests.unit.codegen.lazy_init_transforms_tests",
    "TestViolationPattern": "tests.unit.codegen.census_models_tests",
    "_project_factory": "tests.unit.codegen._project_factory",
    "autofix_workspace_tests": "tests.unit.codegen.autofix_workspace_tests",
    "census": "tests.unit.codegen.census_tests",
    "census_models_tests": "tests.unit.codegen.census_models_tests",
    "census_tests": "tests.unit.codegen.census_tests",
    "constants_quality_gate_tests": "tests.unit.codegen.constants_quality_gate_tests",
    "init_tests": "tests.unit.codegen.init_tests",
    "lazy_init_generation_tests": "tests.unit.codegen.lazy_init_generation_tests",
    "lazy_init_helpers_tests": "tests.unit.codegen.lazy_init_helpers_tests",
    "lazy_init_process_tests": "tests.unit.codegen.lazy_init_process_tests",
    "lazy_init_service_tests": "tests.unit.codegen.lazy_init_service_tests",
    "lazy_init_tests": "tests.unit.codegen.lazy_init_tests",
    "lazy_init_transforms_tests": "tests.unit.codegen.lazy_init_transforms_tests",
    "main_tests": "tests.unit.codegen.main_tests",
    "pipeline_tests": "tests.unit.codegen.pipeline_tests",
    "scaffolder_naming_tests": "tests.unit.codegen.scaffolder_naming_tests",
    "scaffolder_tests": "tests.unit.codegen.scaffolder_tests",
    "test_codegen_dir_returns_all_exports": "tests.unit.codegen.init_tests",
    "test_codegen_getattr_raises_attribute_error": "tests.unit.codegen.init_tests",
    "test_codegen_init_getattr_raises_attribute_error": "tests.unit.codegen.lazy_init_generation_tests",
    "test_codegen_lazy_imports_work": "tests.unit.codegen.init_tests",
    "test_codegen_pipeline_end_to_end": "tests.unit.codegen.pipeline_tests",
    "test_files_modified_tracks_affected_files": "tests.unit.codegen.autofix_workspace_tests",
    "test_flexcore_excluded_from_run": "tests.unit.codegen.autofix_workspace_tests",
    "test_project_without_src_returns_empty": "tests.unit.codegen.autofix_workspace_tests",
}


install_lazy_exports(__name__, globals(), _LAZY_IMPORTS)
