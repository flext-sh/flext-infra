# AUTO-GENERATED FILE — DO NOT EDIT MANUALLY.
# Regenerate with: make gen
#
"""Codegen package."""

from __future__ import annotations

import typing as _t

from flext_core.lazy import install_lazy_exports

if _t.TYPE_CHECKING:
    import tests.unit.codegen._project_factory as _tests_unit_codegen__project_factory

    _project_factory = _tests_unit_codegen__project_factory
    import tests.unit.codegen.autofix_workspace_tests as _tests_unit_codegen_autofix_workspace_tests
    from tests.unit.codegen._project_factory import FlextInfraCodegenTestProjectFactory

    autofix_workspace_tests = _tests_unit_codegen_autofix_workspace_tests
    import tests.unit.codegen.census_models_tests as _tests_unit_codegen_census_models_tests
    from tests.unit.codegen.autofix_workspace_tests import (
        test_files_modified_tracks_affected_files,
        test_flexcore_excluded_from_run,
        test_project_without_src_returns_empty,
    )

    census_models_tests = _tests_unit_codegen_census_models_tests
    import tests.unit.codegen.census_tests as _tests_unit_codegen_census_tests
    from tests.unit.codegen.census_models_tests import (
        TestCensusReportModel,
        TestCensusViolationModel,
        TestExcludedProjects,
        TestViolationPattern,
    )

    census_tests = _tests_unit_codegen_census_tests
    import tests.unit.codegen.constants_quality_gate_tests as _tests_unit_codegen_constants_quality_gate_tests
    from tests.unit.codegen.census_tests import (
        TestFixabilityClassification,
        TestParseViolationInvalid,
        TestParseViolationValid,
        census,
    )

    constants_quality_gate_tests = _tests_unit_codegen_constants_quality_gate_tests
    import tests.unit.codegen.init_tests as _tests_unit_codegen_init_tests
    from tests.unit.codegen.constants_quality_gate_tests import (
        TestConstantsQualityGateCLIDispatch,
        TestConstantsQualityGateVerdict,
    )

    init_tests = _tests_unit_codegen_init_tests
    import tests.unit.codegen.lazy_init_generation_tests as _tests_unit_codegen_lazy_init_generation_tests
    from tests.unit.codegen.init_tests import (
        test_codegen_dir_returns_all_exports,
        test_codegen_getattr_raises_attribute_error,
        test_codegen_lazy_imports_work,
    )

    lazy_init_generation_tests = _tests_unit_codegen_lazy_init_generation_tests
    import tests.unit.codegen.lazy_init_helpers_tests as _tests_unit_codegen_lazy_init_helpers_tests
    from tests.unit.codegen.lazy_init_generation_tests import (
        TestGenerateFile,
        TestGenerateTypeChecking,
        TestResolveAliases,
        TestRunRuffFix,
        test_codegen_init_getattr_raises_attribute_error,
    )

    lazy_init_helpers_tests = _tests_unit_codegen_lazy_init_helpers_tests
    import tests.unit.codegen.lazy_init_process_tests as _tests_unit_codegen_lazy_init_process_tests
    from tests.unit.codegen.lazy_init_helpers_tests import (
        TestBuildSiblingExportIndex,
        TestExtractExports,
        TestInferPackage,
        TestReadExistingDocstring,
    )

    lazy_init_process_tests = _tests_unit_codegen_lazy_init_process_tests
    import tests.unit.codegen.lazy_init_service_tests as _tests_unit_codegen_lazy_init_service_tests
    from tests.unit.codegen.lazy_init_process_tests import TestProcessDirectory

    lazy_init_service_tests = _tests_unit_codegen_lazy_init_service_tests
    import tests.unit.codegen.lazy_init_tests as _tests_unit_codegen_lazy_init_tests
    from tests.unit.codegen.lazy_init_service_tests import TestFlextInfraCodegenLazyInit

    lazy_init_tests = _tests_unit_codegen_lazy_init_tests
    import tests.unit.codegen.lazy_init_transforms_tests as _tests_unit_codegen_lazy_init_transforms_tests
    from tests.unit.codegen.lazy_init_tests import (
        TestAllDirectoriesScanned,
        TestCheckOnlyMode,
        TestEdgeCases,
        TestExcludedDirectories,
    )

    lazy_init_transforms_tests = _tests_unit_codegen_lazy_init_transforms_tests
    import tests.unit.codegen.main_tests as _tests_unit_codegen_main_tests
    from tests.unit.codegen.lazy_init_transforms_tests import (
        TestExtractVersionExports,
        TestMergeChildExports,
        TestScanPublicDefs,
        TestShouldBubbleUp,
    )

    main_tests = _tests_unit_codegen_main_tests
    import tests.unit.codegen.pipeline_tests as _tests_unit_codegen_pipeline_tests
    from tests.unit.codegen.main_tests import (
        TestHandleLazyInit,
        TestMainCommandDispatch,
        TestMainEntryPoint,
    )

    pipeline_tests = _tests_unit_codegen_pipeline_tests
    import tests.unit.codegen.scaffolder_naming_tests as _tests_unit_codegen_scaffolder_naming_tests
    from tests.unit.codegen.pipeline_tests import test_codegen_pipeline_end_to_end

    scaffolder_naming_tests = _tests_unit_codegen_scaffolder_naming_tests
    import tests.unit.codegen.scaffolder_tests as _tests_unit_codegen_scaffolder_tests
    from tests.unit.codegen.scaffolder_naming_tests import (
        TestGeneratedClassNamingConvention,
        TestGeneratedFilesAreValidPython,
    )

    scaffolder_tests = _tests_unit_codegen_scaffolder_tests
    from tests.unit.codegen.scaffolder_tests import (
        TestScaffoldProjectCreatesSrcModules,
        TestScaffoldProjectCreatesTestsModules,
        TestScaffoldProjectIdempotency,
        TestScaffoldProjectNoop,
    )

    from flext_core.constants import FlextConstants as c
    from flext_core.decorators import FlextDecorators as d
    from flext_core.exceptions import FlextExceptions as e
    from flext_core.handlers import FlextHandlers as h
    from flext_core.mixins import FlextMixins as x
    from flext_core.models import FlextModels as m
    from flext_core.protocols import FlextProtocols as p
    from flext_core.result import FlextResult as r
    from flext_core.service import FlextService as s
    from flext_core.typings import FlextTypes as t
    from flext_core.utilities import FlextUtilities as u
_LAZY_IMPORTS = {
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
    "TestScanPublicDefs": "tests.unit.codegen.lazy_init_transforms_tests",
    "TestShouldBubbleUp": "tests.unit.codegen.lazy_init_transforms_tests",
    "TestViolationPattern": "tests.unit.codegen.census_models_tests",
    "_project_factory": "tests.unit.codegen._project_factory",
    "autofix_workspace_tests": "tests.unit.codegen.autofix_workspace_tests",
    "c": ("flext_core.constants", "FlextConstants"),
    "census": "tests.unit.codegen.census_tests",
    "census_models_tests": "tests.unit.codegen.census_models_tests",
    "census_tests": "tests.unit.codegen.census_tests",
    "constants_quality_gate_tests": "tests.unit.codegen.constants_quality_gate_tests",
    "d": ("flext_core.decorators", "FlextDecorators"),
    "e": ("flext_core.exceptions", "FlextExceptions"),
    "h": ("flext_core.handlers", "FlextHandlers"),
    "init_tests": "tests.unit.codegen.init_tests",
    "lazy_init_generation_tests": "tests.unit.codegen.lazy_init_generation_tests",
    "lazy_init_helpers_tests": "tests.unit.codegen.lazy_init_helpers_tests",
    "lazy_init_process_tests": "tests.unit.codegen.lazy_init_process_tests",
    "lazy_init_service_tests": "tests.unit.codegen.lazy_init_service_tests",
    "lazy_init_tests": "tests.unit.codegen.lazy_init_tests",
    "lazy_init_transforms_tests": "tests.unit.codegen.lazy_init_transforms_tests",
    "m": ("flext_core.models", "FlextModels"),
    "main_tests": "tests.unit.codegen.main_tests",
    "p": ("flext_core.protocols", "FlextProtocols"),
    "pipeline_tests": "tests.unit.codegen.pipeline_tests",
    "r": ("flext_core.result", "FlextResult"),
    "s": ("flext_core.service", "FlextService"),
    "scaffolder_naming_tests": "tests.unit.codegen.scaffolder_naming_tests",
    "scaffolder_tests": "tests.unit.codegen.scaffolder_tests",
    "t": ("flext_core.typings", "FlextTypes"),
    "test_codegen_dir_returns_all_exports": "tests.unit.codegen.init_tests",
    "test_codegen_getattr_raises_attribute_error": "tests.unit.codegen.init_tests",
    "test_codegen_init_getattr_raises_attribute_error": "tests.unit.codegen.lazy_init_generation_tests",
    "test_codegen_lazy_imports_work": "tests.unit.codegen.init_tests",
    "test_codegen_pipeline_end_to_end": "tests.unit.codegen.pipeline_tests",
    "test_files_modified_tracks_affected_files": "tests.unit.codegen.autofix_workspace_tests",
    "test_flexcore_excluded_from_run": "tests.unit.codegen.autofix_workspace_tests",
    "test_project_without_src_returns_empty": "tests.unit.codegen.autofix_workspace_tests",
    "u": ("flext_core.utilities", "FlextUtilities"),
    "x": ("flext_core.mixins", "FlextMixins"),
}

__all__ = [
    "FlextInfraCodegenTestProjectFactory",
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
    "TestScanPublicDefs",
    "TestShouldBubbleUp",
    "TestViolationPattern",
    "_project_factory",
    "autofix_workspace_tests",
    "c",
    "census",
    "census_models_tests",
    "census_tests",
    "constants_quality_gate_tests",
    "d",
    "e",
    "h",
    "init_tests",
    "lazy_init_generation_tests",
    "lazy_init_helpers_tests",
    "lazy_init_process_tests",
    "lazy_init_service_tests",
    "lazy_init_tests",
    "lazy_init_transforms_tests",
    "m",
    "main_tests",
    "p",
    "pipeline_tests",
    "r",
    "s",
    "scaffolder_naming_tests",
    "scaffolder_tests",
    "t",
    "test_codegen_dir_returns_all_exports",
    "test_codegen_getattr_raises_attribute_error",
    "test_codegen_init_getattr_raises_attribute_error",
    "test_codegen_lazy_imports_work",
    "test_codegen_pipeline_end_to_end",
    "test_files_modified_tracks_affected_files",
    "test_flexcore_excluded_from_run",
    "test_project_without_src_returns_empty",
    "u",
    "x",
]


install_lazy_exports(__name__, globals(), _LAZY_IMPORTS)
