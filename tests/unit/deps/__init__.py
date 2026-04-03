# AUTO-GENERATED FILE — DO NOT EDIT MANUALLY.
# Regenerate with: make gen
#
"""Deps package."""

from __future__ import annotations

import typing as _t

from flext_core.lazy import install_lazy_exports

if _t.TYPE_CHECKING:
    import tests.unit.deps.test_detection_classify as _tests_unit_deps_test_detection_classify

    test_detection_classify = _tests_unit_deps_test_detection_classify
    import tests.unit.deps.test_detection_deptry as _tests_unit_deps_test_detection_deptry
    from tests.unit.deps.test_detection_classify import (
        TestBuildProjectReport,
        TestClassifyIssues,
    )

    test_detection_deptry = _tests_unit_deps_test_detection_deptry
    import tests.unit.deps.test_detection_discover as _tests_unit_deps_test_detection_discover
    from tests.unit.deps.test_detection_deptry import TestRunDeptry

    test_detection_discover = _tests_unit_deps_test_detection_discover
    import tests.unit.deps.test_detection_models as _tests_unit_deps_test_detection_models
    from tests.unit.deps.test_detection_discover import TestDiscoverProjects

    test_detection_models = _tests_unit_deps_test_detection_models
    import tests.unit.deps.test_detection_pip_check as _tests_unit_deps_test_detection_pip_check
    from tests.unit.deps.test_detection_models import (
        TestFlextInfraDependencyDetectionModels,
        TestFlextInfraDependencyDetectionService,
        TestToInfraValue,
    )

    test_detection_pip_check = _tests_unit_deps_test_detection_pip_check
    import tests.unit.deps.test_detection_typings as _tests_unit_deps_test_detection_typings
    from tests.unit.deps.test_detection_pip_check import TestRunPipCheck

    test_detection_typings = _tests_unit_deps_test_detection_typings
    import tests.unit.deps.test_detection_typings_flow as _tests_unit_deps_test_detection_typings_flow
    from tests.unit.deps.test_detection_typings import (
        TestLoadDependencyLimits,
        TestRunMypyStubHints,
    )

    test_detection_typings_flow = _tests_unit_deps_test_detection_typings_flow
    import tests.unit.deps.test_detection_uncovered as _tests_unit_deps_test_detection_uncovered
    from tests.unit.deps.test_detection_typings_flow import TestModuleAndTypingsFlow

    test_detection_uncovered = _tests_unit_deps_test_detection_uncovered
    import tests.unit.deps.test_detector_detect as _tests_unit_deps_test_detector_detect
    from tests.unit.deps.test_detection_uncovered import TestDetectionUncoveredLines

    test_detector_detect = _tests_unit_deps_test_detector_detect
    import tests.unit.deps.test_detector_detect_failures as _tests_unit_deps_test_detector_detect_failures
    from tests.unit.deps.test_detector_detect import (
        TestFlextInfraRuntimeDevDependencyDetectorRunDetect,
    )

    test_detector_detect_failures = _tests_unit_deps_test_detector_detect_failures
    import tests.unit.deps.test_detector_init as _tests_unit_deps_test_detector_init
    from tests.unit.deps.test_detector_detect_failures import TestDetectorRunFailures

    test_detector_init = _tests_unit_deps_test_detector_init
    import tests.unit.deps.test_detector_main as _tests_unit_deps_test_detector_main
    from tests.unit.deps.test_detector_init import (
        TestFlextInfraRuntimeDevDependencyDetectorInit,
    )

    test_detector_main = _tests_unit_deps_test_detector_main
    import tests.unit.deps.test_detector_models as _tests_unit_deps_test_detector_models
    from tests.unit.deps.test_detector_main import (
        TestFlextInfraRuntimeDevDependencyDetectorRunTypings,
        TestMainFunction,
    )

    test_detector_models = _tests_unit_deps_test_detector_models
    import tests.unit.deps.test_detector_report as _tests_unit_deps_test_detector_report
    from tests.unit.deps.test_detector_models import (
        TestFlextInfraDependencyDetectorModels,
    )

    test_detector_report = _tests_unit_deps_test_detector_report
    import tests.unit.deps.test_detector_report_flags as _tests_unit_deps_test_detector_report_flags
    from tests.unit.deps.test_detector_report import (
        TestFlextInfraRuntimeDevDependencyDetectorRunReport,
    )

    test_detector_report_flags = _tests_unit_deps_test_detector_report_flags
    import tests.unit.deps.test_extra_paths_manager as _tests_unit_deps_test_extra_paths_manager
    from tests.unit.deps.test_detector_report_flags import TestDetectorReportFlags

    test_extra_paths_manager = _tests_unit_deps_test_extra_paths_manager
    import tests.unit.deps.test_extra_paths_pep621 as _tests_unit_deps_test_extra_paths_pep621
    from tests.unit.deps.test_extra_paths_manager import (
        TestConstants,
        TestFlextInfraExtraPathsManager,
        TestGetDepPaths,
        TestSyncOne,
        test_pyrefly_search_paths_include_workspace_declared_dev_dependencies,
    )

    test_extra_paths_pep621 = _tests_unit_deps_test_extra_paths_pep621
    import tests.unit.deps.test_extra_paths_sync as _tests_unit_deps_test_extra_paths_sync
    from tests.unit.deps.test_extra_paths_pep621 import (
        TestPathDepPathsPep621,
        TestPathDepPathsPoetry,
    )

    test_extra_paths_sync = _tests_unit_deps_test_extra_paths_sync
    import tests.unit.deps.test_init as _tests_unit_deps_test_init
    from tests.unit.deps.test_extra_paths_sync import (
        pyright_content,
        test_main_success_modes,
        test_main_sync_failure,
        test_sync_extra_paths_missing_root_pyproject,
        test_sync_extra_paths_success_modes,
        test_sync_extra_paths_sync_failure,
        test_sync_one_edge_cases,
    )

    test_init = _tests_unit_deps_test_init
    import tests.unit.deps.test_internal_sync_discovery as _tests_unit_deps_test_internal_sync_discovery
    from tests.unit.deps.test_init import TestFlextInfraDeps

    test_internal_sync_discovery = _tests_unit_deps_test_internal_sync_discovery
    import tests.unit.deps.test_internal_sync_discovery_edge as _tests_unit_deps_test_internal_sync_discovery_edge
    from tests.unit.deps.test_internal_sync_discovery import (
        TestCollectInternalDeps,
        TestParseGitmodules,
        TestParseRepoMap,
    )

    test_internal_sync_discovery_edge = (
        _tests_unit_deps_test_internal_sync_discovery_edge
    )
    import tests.unit.deps.test_internal_sync_main as _tests_unit_deps_test_internal_sync_main
    from tests.unit.deps.test_internal_sync_discovery_edge import (
        TestCollectInternalDepsEdgeCases,
    )

    test_internal_sync_main = _tests_unit_deps_test_internal_sync_main
    import tests.unit.deps.test_internal_sync_resolve as _tests_unit_deps_test_internal_sync_resolve

    test_internal_sync_resolve = _tests_unit_deps_test_internal_sync_resolve
    import tests.unit.deps.test_internal_sync_sync as _tests_unit_deps_test_internal_sync_sync
    from tests.unit.deps.test_internal_sync_resolve import (
        TestInferOwnerFromOrigin,
        TestResolveRef,
        TestSynthesizedRepoMap,
    )

    test_internal_sync_sync = _tests_unit_deps_test_internal_sync_sync
    import tests.unit.deps.test_internal_sync_sync_edge as _tests_unit_deps_test_internal_sync_sync_edge
    from tests.unit.deps.test_internal_sync_sync import TestSync

    test_internal_sync_sync_edge = _tests_unit_deps_test_internal_sync_sync_edge
    import tests.unit.deps.test_internal_sync_sync_edge_more as _tests_unit_deps_test_internal_sync_sync_edge_more
    from tests.unit.deps.test_internal_sync_sync_edge import TestSyncMethodEdgeCases

    test_internal_sync_sync_edge_more = (
        _tests_unit_deps_test_internal_sync_sync_edge_more
    )
    import tests.unit.deps.test_internal_sync_update as _tests_unit_deps_test_internal_sync_update
    from tests.unit.deps.test_internal_sync_sync_edge_more import (
        TestSyncMethodEdgeCasesMore,
    )

    test_internal_sync_update = _tests_unit_deps_test_internal_sync_update
    import tests.unit.deps.test_internal_sync_update_checkout_edge as _tests_unit_deps_test_internal_sync_update_checkout_edge
    from tests.unit.deps.test_internal_sync_update import (
        TestEnsureCheckout,
        TestEnsureSymlink,
        TestEnsureSymlinkEdgeCases,
    )

    test_internal_sync_update_checkout_edge = (
        _tests_unit_deps_test_internal_sync_update_checkout_edge
    )
    import tests.unit.deps.test_internal_sync_validation as _tests_unit_deps_test_internal_sync_validation
    from tests.unit.deps.test_internal_sync_update_checkout_edge import (
        TestEnsureCheckoutEdgeCases,
    )

    test_internal_sync_validation = _tests_unit_deps_test_internal_sync_validation
    import tests.unit.deps.test_internal_sync_workspace as _tests_unit_deps_test_internal_sync_workspace
    from tests.unit.deps.test_internal_sync_validation import (
        TestFlextInfraInternalDependencySyncService,
        TestIsInternalPathDep,
        TestIsRelativeTo,
        TestOwnerFromRemoteUrl,
        TestValidateGitRefEdgeCases,
    )

    test_internal_sync_workspace = _tests_unit_deps_test_internal_sync_workspace
    import tests.unit.deps.test_main as _tests_unit_deps_test_main
    from tests.unit.deps.test_internal_sync_workspace import (
        TestIsWorkspaceMode,
        TestWorkspaceRootFromEnv,
        TestWorkspaceRootFromParents,
    )

    test_main = _tests_unit_deps_test_main
    import tests.unit.deps.test_main_dispatch as _tests_unit_deps_test_main_dispatch
    from tests.unit.deps.test_main import (
        TestMainHelpAndErrors,
        TestMainReturnValues,
        TestSubcommandMapping,
    )

    test_main_dispatch = _tests_unit_deps_test_main_dispatch
    import tests.unit.deps.test_modernizer_comments as _tests_unit_deps_test_modernizer_comments
    from tests.unit.deps.test_main_dispatch import (
        TestMainDelegation,
        TestMainExceptionHandling,
        TestMainModuleImport,
        TestMainSubcommandDispatch,
        TestMainSysArgvModification,
        main,
        test_string_zero_return_value,
    )

    test_modernizer_comments = _tests_unit_deps_test_modernizer_comments
    import tests.unit.deps.test_modernizer_consolidate as _tests_unit_deps_test_modernizer_consolidate
    from tests.unit.deps.test_modernizer_comments import (
        TestInjectCommentsPhase,
        test_inject_comments_phase_apply_banner,
        test_inject_comments_phase_apply_broken_group_section,
        test_inject_comments_phase_apply_markers,
        test_inject_comments_phase_apply_with_optional_dependencies_dev,
        test_inject_comments_phase_deduplicates_family_markers,
        test_inject_comments_phase_marks_pytest_and_coverage_subtables,
        test_inject_comments_phase_removes_auto_banner_and_auto_marker,
        test_inject_comments_phase_repositions_marker_before_section,
    )

    test_modernizer_consolidate = _tests_unit_deps_test_modernizer_consolidate
    import tests.unit.deps.test_modernizer_coverage as _tests_unit_deps_test_modernizer_coverage
    from tests.unit.deps.test_modernizer_consolidate import (
        TestConsolidateGroupsPhase,
        test_consolidate_groups_phase_apply_removes_old_groups,
        test_consolidate_groups_phase_apply_with_empty_poetry_group,
    )

    test_modernizer_coverage = _tests_unit_deps_test_modernizer_coverage
    import tests.unit.deps.test_modernizer_helpers as _tests_unit_deps_test_modernizer_helpers
    from tests.unit.deps.test_modernizer_coverage import TestEnsureCoverageConfigPhase

    test_modernizer_helpers = _tests_unit_deps_test_modernizer_helpers
    import tests.unit.deps.test_modernizer_main as _tests_unit_deps_test_modernizer_main
    from tests.unit.deps.test_modernizer_helpers import (
        doc,
        test_array,
        test_as_string_list,
        test_as_string_list_toml_item,
        test_canonical_dev_dependencies,
        test_declared_dependency_names_collects_all_supported_groups,
        test_dedupe_specs,
        test_dep_name,
        test_ensure_table,
        test_project_dev_groups,
        test_project_dev_groups_missing_sections,
        test_unwrap_item,
        test_unwrap_item_toml_item,
    )

    test_modernizer_main = _tests_unit_deps_test_modernizer_main
    import tests.unit.deps.test_modernizer_main_extra as _tests_unit_deps_test_modernizer_main_extra
    from tests.unit.deps.test_modernizer_main import (
        TestFlextInfraPyprojectModernizer,
        TestModernizerRunAndMain,
    )

    test_modernizer_main_extra = _tests_unit_deps_test_modernizer_main_extra
    import tests.unit.deps.test_modernizer_pyrefly as _tests_unit_deps_test_modernizer_pyrefly
    from tests.unit.deps.test_modernizer_main_extra import (
        TestModernizerEdgeCases,
        TestModernizerUncoveredLines,
        test_flext_infra_pyproject_modernizer_find_pyproject_files,
        test_flext_infra_pyproject_modernizer_process_file_invalid_toml,
    )

    test_modernizer_pyrefly = _tests_unit_deps_test_modernizer_pyrefly
    import tests.unit.deps.test_modernizer_pyright as _tests_unit_deps_test_modernizer_pyright
    from tests.unit.deps.test_modernizer_pyrefly import (
        TestEnsurePyreflyConfigPhase,
        test_ensure_pyrefly_config_phase_apply_errors,
        test_ensure_pyrefly_config_phase_apply_ignore_errors,
        test_ensure_pyrefly_config_phase_apply_python_version,
        test_ensure_pyrefly_config_phase_apply_search_path,
    )

    test_modernizer_pyright = _tests_unit_deps_test_modernizer_pyright
    import tests.unit.deps.test_modernizer_pytest as _tests_unit_deps_test_modernizer_pytest
    from tests.unit.deps.test_modernizer_pyright import TestEnsurePyrightConfigPhase

    test_modernizer_pytest = _tests_unit_deps_test_modernizer_pytest
    import tests.unit.deps.test_modernizer_workspace as _tests_unit_deps_test_modernizer_workspace
    from tests.unit.deps.test_modernizer_pytest import (
        TestEnsurePytestConfigPhase,
        test_ensure_pytest_config_phase_apply_markers,
        test_ensure_pytest_config_phase_apply_minversion,
        test_ensure_pytest_config_phase_apply_python_classes,
    )

    test_modernizer_workspace = _tests_unit_deps_test_modernizer_workspace
    import tests.unit.deps.test_path_sync_helpers as _tests_unit_deps_test_path_sync_helpers
    from tests.unit.deps.test_modernizer_workspace import (
        TestParser,
        TestReadDoc,
        TestWorkspaceRoot,
        test_workspace_root_doc_construction,
    )

    test_path_sync_helpers = _tests_unit_deps_test_path_sync_helpers
    import tests.unit.deps.test_path_sync_init as _tests_unit_deps_test_path_sync_init
    from tests.unit.deps.test_path_sync_helpers import (
        extract_dep_name,
        test_extract_dep_name,
        test_extract_requirement_name,
        test_helpers_alias_is_reachable_helpers,
        test_target_path,
    )

    test_path_sync_init = _tests_unit_deps_test_path_sync_init
    import tests.unit.deps.test_path_sync_main as _tests_unit_deps_test_path_sync_main
    from tests.unit.deps.test_path_sync_init import (
        TestDetectMode,
        TestFlextInfraDependencyPathSync,
        TestPathSyncEdgeCases,
        test_detect_mode_with_nonexistent_path,
        test_detect_mode_with_path_object,
    )

    test_path_sync_main = _tests_unit_deps_test_path_sync_main
    import tests.unit.deps.test_path_sync_main_edges as _tests_unit_deps_test_path_sync_main_edges
    from tests.unit.deps.test_path_sync_main import TestMain

    test_path_sync_main_edges = _tests_unit_deps_test_path_sync_main_edges
    import tests.unit.deps.test_path_sync_main_more as _tests_unit_deps_test_path_sync_main_more
    from tests.unit.deps.test_path_sync_main_edges import TestMainEdgeCases

    test_path_sync_main_more = _tests_unit_deps_test_path_sync_main_more
    import tests.unit.deps.test_path_sync_main_project_obj as _tests_unit_deps_test_path_sync_main_project_obj
    from tests.unit.deps.test_path_sync_main_more import (
        test_main_discovery_failure,
        test_main_no_changes_needed,
        test_main_project_invalid_toml,
        test_main_project_no_name,
        test_main_project_non_string_name,
        test_main_with_changes_and_dry_run,
        test_main_with_changes_no_dry_run,
        test_workspace_root_fallback,
    )

    test_path_sync_main_project_obj = _tests_unit_deps_test_path_sync_main_project_obj
    import tests.unit.deps.test_path_sync_rewrite_deps as _tests_unit_deps_test_path_sync_rewrite_deps
    from tests.unit.deps.test_path_sync_main_project_obj import (
        test_helpers_alias_is_reachable_project_obj,
        test_main_project_obj_not_dict_first_loop,
        test_main_project_obj_not_dict_second_loop,
    )

    test_path_sync_rewrite_deps = _tests_unit_deps_test_path_sync_rewrite_deps
    import tests.unit.deps.test_path_sync_rewrite_pep621 as _tests_unit_deps_test_path_sync_rewrite_pep621
    from tests.unit.deps.test_path_sync_rewrite_deps import (
        TestRewriteDepPaths,
        rewrite_dep_paths,
        test_rewrite_dep_paths_dry_run,
        test_rewrite_dep_paths_read_failure,
        test_rewrite_dep_paths_with_internal_names,
        test_rewrite_dep_paths_with_no_deps,
    )

    test_path_sync_rewrite_pep621 = _tests_unit_deps_test_path_sync_rewrite_pep621
    import tests.unit.deps.test_path_sync_rewrite_poetry as _tests_unit_deps_test_path_sync_rewrite_poetry
    from tests.unit.deps.test_path_sync_rewrite_pep621 import (
        TestRewritePep621,
        test_rewrite_pep621_invalid_path_dep_regex,
        test_rewrite_pep621_no_project_table,
        test_rewrite_pep621_non_string_item,
    )

    test_path_sync_rewrite_poetry = _tests_unit_deps_test_path_sync_rewrite_poetry
    from tests.unit.deps.test_path_sync_rewrite_poetry import (
        TestRewritePoetry,
        test_rewrite_poetry_no_poetry_table,
        test_rewrite_poetry_no_tool_table,
        test_rewrite_poetry_with_non_dict_value,
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
    "TestBuildProjectReport": "tests.unit.deps.test_detection_classify",
    "TestClassifyIssues": "tests.unit.deps.test_detection_classify",
    "TestCollectInternalDeps": "tests.unit.deps.test_internal_sync_discovery",
    "TestCollectInternalDepsEdgeCases": "tests.unit.deps.test_internal_sync_discovery_edge",
    "TestConsolidateGroupsPhase": "tests.unit.deps.test_modernizer_consolidate",
    "TestConstants": "tests.unit.deps.test_extra_paths_manager",
    "TestDetectMode": "tests.unit.deps.test_path_sync_init",
    "TestDetectionUncoveredLines": "tests.unit.deps.test_detection_uncovered",
    "TestDetectorReportFlags": "tests.unit.deps.test_detector_report_flags",
    "TestDetectorRunFailures": "tests.unit.deps.test_detector_detect_failures",
    "TestDiscoverProjects": "tests.unit.deps.test_detection_discover",
    "TestEnsureCheckout": "tests.unit.deps.test_internal_sync_update",
    "TestEnsureCheckoutEdgeCases": "tests.unit.deps.test_internal_sync_update_checkout_edge",
    "TestEnsureCoverageConfigPhase": "tests.unit.deps.test_modernizer_coverage",
    "TestEnsurePyreflyConfigPhase": "tests.unit.deps.test_modernizer_pyrefly",
    "TestEnsurePyrightConfigPhase": "tests.unit.deps.test_modernizer_pyright",
    "TestEnsurePytestConfigPhase": "tests.unit.deps.test_modernizer_pytest",
    "TestEnsureSymlink": "tests.unit.deps.test_internal_sync_update",
    "TestEnsureSymlinkEdgeCases": "tests.unit.deps.test_internal_sync_update",
    "TestFlextInfraDependencyDetectionModels": "tests.unit.deps.test_detection_models",
    "TestFlextInfraDependencyDetectionService": "tests.unit.deps.test_detection_models",
    "TestFlextInfraDependencyDetectorModels": "tests.unit.deps.test_detector_models",
    "TestFlextInfraDependencyPathSync": "tests.unit.deps.test_path_sync_init",
    "TestFlextInfraDeps": "tests.unit.deps.test_init",
    "TestFlextInfraExtraPathsManager": "tests.unit.deps.test_extra_paths_manager",
    "TestFlextInfraInternalDependencySyncService": "tests.unit.deps.test_internal_sync_validation",
    "TestFlextInfraPyprojectModernizer": "tests.unit.deps.test_modernizer_main",
    "TestFlextInfraRuntimeDevDependencyDetectorInit": "tests.unit.deps.test_detector_init",
    "TestFlextInfraRuntimeDevDependencyDetectorRunDetect": "tests.unit.deps.test_detector_detect",
    "TestFlextInfraRuntimeDevDependencyDetectorRunReport": "tests.unit.deps.test_detector_report",
    "TestFlextInfraRuntimeDevDependencyDetectorRunTypings": "tests.unit.deps.test_detector_main",
    "TestGetDepPaths": "tests.unit.deps.test_extra_paths_manager",
    "TestInferOwnerFromOrigin": "tests.unit.deps.test_internal_sync_resolve",
    "TestInjectCommentsPhase": "tests.unit.deps.test_modernizer_comments",
    "TestIsInternalPathDep": "tests.unit.deps.test_internal_sync_validation",
    "TestIsRelativeTo": "tests.unit.deps.test_internal_sync_validation",
    "TestIsWorkspaceMode": "tests.unit.deps.test_internal_sync_workspace",
    "TestLoadDependencyLimits": "tests.unit.deps.test_detection_typings",
    "TestMain": "tests.unit.deps.test_path_sync_main",
    "TestMainDelegation": "tests.unit.deps.test_main_dispatch",
    "TestMainEdgeCases": "tests.unit.deps.test_path_sync_main_edges",
    "TestMainExceptionHandling": "tests.unit.deps.test_main_dispatch",
    "TestMainFunction": "tests.unit.deps.test_detector_main",
    "TestMainHelpAndErrors": "tests.unit.deps.test_main",
    "TestMainModuleImport": "tests.unit.deps.test_main_dispatch",
    "TestMainReturnValues": "tests.unit.deps.test_main",
    "TestMainSubcommandDispatch": "tests.unit.deps.test_main_dispatch",
    "TestMainSysArgvModification": "tests.unit.deps.test_main_dispatch",
    "TestModernizerEdgeCases": "tests.unit.deps.test_modernizer_main_extra",
    "TestModernizerRunAndMain": "tests.unit.deps.test_modernizer_main",
    "TestModernizerUncoveredLines": "tests.unit.deps.test_modernizer_main_extra",
    "TestModuleAndTypingsFlow": "tests.unit.deps.test_detection_typings_flow",
    "TestOwnerFromRemoteUrl": "tests.unit.deps.test_internal_sync_validation",
    "TestParseGitmodules": "tests.unit.deps.test_internal_sync_discovery",
    "TestParseRepoMap": "tests.unit.deps.test_internal_sync_discovery",
    "TestParser": "tests.unit.deps.test_modernizer_workspace",
    "TestPathDepPathsPep621": "tests.unit.deps.test_extra_paths_pep621",
    "TestPathDepPathsPoetry": "tests.unit.deps.test_extra_paths_pep621",
    "TestPathSyncEdgeCases": "tests.unit.deps.test_path_sync_init",
    "TestReadDoc": "tests.unit.deps.test_modernizer_workspace",
    "TestResolveRef": "tests.unit.deps.test_internal_sync_resolve",
    "TestRewriteDepPaths": "tests.unit.deps.test_path_sync_rewrite_deps",
    "TestRewritePep621": "tests.unit.deps.test_path_sync_rewrite_pep621",
    "TestRewritePoetry": "tests.unit.deps.test_path_sync_rewrite_poetry",
    "TestRunDeptry": "tests.unit.deps.test_detection_deptry",
    "TestRunMypyStubHints": "tests.unit.deps.test_detection_typings",
    "TestRunPipCheck": "tests.unit.deps.test_detection_pip_check",
    "TestSubcommandMapping": "tests.unit.deps.test_main",
    "TestSync": "tests.unit.deps.test_internal_sync_sync",
    "TestSyncMethodEdgeCases": "tests.unit.deps.test_internal_sync_sync_edge",
    "TestSyncMethodEdgeCasesMore": "tests.unit.deps.test_internal_sync_sync_edge_more",
    "TestSyncOne": "tests.unit.deps.test_extra_paths_manager",
    "TestSynthesizedRepoMap": "tests.unit.deps.test_internal_sync_resolve",
    "TestToInfraValue": "tests.unit.deps.test_detection_models",
    "TestValidateGitRefEdgeCases": "tests.unit.deps.test_internal_sync_validation",
    "TestWorkspaceRoot": "tests.unit.deps.test_modernizer_workspace",
    "TestWorkspaceRootFromEnv": "tests.unit.deps.test_internal_sync_workspace",
    "TestWorkspaceRootFromParents": "tests.unit.deps.test_internal_sync_workspace",
    "c": ("flext_core.constants", "FlextConstants"),
    "d": ("flext_core.decorators", "FlextDecorators"),
    "doc": "tests.unit.deps.test_modernizer_helpers",
    "e": ("flext_core.exceptions", "FlextExceptions"),
    "extract_dep_name": "tests.unit.deps.test_path_sync_helpers",
    "h": ("flext_core.handlers", "FlextHandlers"),
    "m": ("flext_core.models", "FlextModels"),
    "main": "tests.unit.deps.test_main_dispatch",
    "p": ("flext_core.protocols", "FlextProtocols"),
    "pyright_content": "tests.unit.deps.test_extra_paths_sync",
    "r": ("flext_core.result", "FlextResult"),
    "rewrite_dep_paths": "tests.unit.deps.test_path_sync_rewrite_deps",
    "s": ("flext_core.service", "FlextService"),
    "t": ("flext_core.typings", "FlextTypes"),
    "test_array": "tests.unit.deps.test_modernizer_helpers",
    "test_as_string_list": "tests.unit.deps.test_modernizer_helpers",
    "test_as_string_list_toml_item": "tests.unit.deps.test_modernizer_helpers",
    "test_canonical_dev_dependencies": "tests.unit.deps.test_modernizer_helpers",
    "test_consolidate_groups_phase_apply_removes_old_groups": "tests.unit.deps.test_modernizer_consolidate",
    "test_consolidate_groups_phase_apply_with_empty_poetry_group": "tests.unit.deps.test_modernizer_consolidate",
    "test_declared_dependency_names_collects_all_supported_groups": "tests.unit.deps.test_modernizer_helpers",
    "test_dedupe_specs": "tests.unit.deps.test_modernizer_helpers",
    "test_dep_name": "tests.unit.deps.test_modernizer_helpers",
    "test_detect_mode_with_nonexistent_path": "tests.unit.deps.test_path_sync_init",
    "test_detect_mode_with_path_object": "tests.unit.deps.test_path_sync_init",
    "test_detection_classify": "tests.unit.deps.test_detection_classify",
    "test_detection_deptry": "tests.unit.deps.test_detection_deptry",
    "test_detection_discover": "tests.unit.deps.test_detection_discover",
    "test_detection_models": "tests.unit.deps.test_detection_models",
    "test_detection_pip_check": "tests.unit.deps.test_detection_pip_check",
    "test_detection_typings": "tests.unit.deps.test_detection_typings",
    "test_detection_typings_flow": "tests.unit.deps.test_detection_typings_flow",
    "test_detection_uncovered": "tests.unit.deps.test_detection_uncovered",
    "test_detector_detect": "tests.unit.deps.test_detector_detect",
    "test_detector_detect_failures": "tests.unit.deps.test_detector_detect_failures",
    "test_detector_init": "tests.unit.deps.test_detector_init",
    "test_detector_main": "tests.unit.deps.test_detector_main",
    "test_detector_models": "tests.unit.deps.test_detector_models",
    "test_detector_report": "tests.unit.deps.test_detector_report",
    "test_detector_report_flags": "tests.unit.deps.test_detector_report_flags",
    "test_ensure_pyrefly_config_phase_apply_errors": "tests.unit.deps.test_modernizer_pyrefly",
    "test_ensure_pyrefly_config_phase_apply_ignore_errors": "tests.unit.deps.test_modernizer_pyrefly",
    "test_ensure_pyrefly_config_phase_apply_python_version": "tests.unit.deps.test_modernizer_pyrefly",
    "test_ensure_pyrefly_config_phase_apply_search_path": "tests.unit.deps.test_modernizer_pyrefly",
    "test_ensure_pytest_config_phase_apply_markers": "tests.unit.deps.test_modernizer_pytest",
    "test_ensure_pytest_config_phase_apply_minversion": "tests.unit.deps.test_modernizer_pytest",
    "test_ensure_pytest_config_phase_apply_python_classes": "tests.unit.deps.test_modernizer_pytest",
    "test_ensure_table": "tests.unit.deps.test_modernizer_helpers",
    "test_extra_paths_manager": "tests.unit.deps.test_extra_paths_manager",
    "test_extra_paths_pep621": "tests.unit.deps.test_extra_paths_pep621",
    "test_extra_paths_sync": "tests.unit.deps.test_extra_paths_sync",
    "test_extract_dep_name": "tests.unit.deps.test_path_sync_helpers",
    "test_extract_requirement_name": "tests.unit.deps.test_path_sync_helpers",
    "test_flext_infra_pyproject_modernizer_find_pyproject_files": "tests.unit.deps.test_modernizer_main_extra",
    "test_flext_infra_pyproject_modernizer_process_file_invalid_toml": "tests.unit.deps.test_modernizer_main_extra",
    "test_helpers_alias_is_reachable_helpers": "tests.unit.deps.test_path_sync_helpers",
    "test_helpers_alias_is_reachable_project_obj": "tests.unit.deps.test_path_sync_main_project_obj",
    "test_init": "tests.unit.deps.test_init",
    "test_inject_comments_phase_apply_banner": "tests.unit.deps.test_modernizer_comments",
    "test_inject_comments_phase_apply_broken_group_section": "tests.unit.deps.test_modernizer_comments",
    "test_inject_comments_phase_apply_markers": "tests.unit.deps.test_modernizer_comments",
    "test_inject_comments_phase_apply_with_optional_dependencies_dev": "tests.unit.deps.test_modernizer_comments",
    "test_inject_comments_phase_deduplicates_family_markers": "tests.unit.deps.test_modernizer_comments",
    "test_inject_comments_phase_marks_pytest_and_coverage_subtables": "tests.unit.deps.test_modernizer_comments",
    "test_inject_comments_phase_removes_auto_banner_and_auto_marker": "tests.unit.deps.test_modernizer_comments",
    "test_inject_comments_phase_repositions_marker_before_section": "tests.unit.deps.test_modernizer_comments",
    "test_internal_sync_discovery": "tests.unit.deps.test_internal_sync_discovery",
    "test_internal_sync_discovery_edge": "tests.unit.deps.test_internal_sync_discovery_edge",
    "test_internal_sync_main": "tests.unit.deps.test_internal_sync_main",
    "test_internal_sync_resolve": "tests.unit.deps.test_internal_sync_resolve",
    "test_internal_sync_sync": "tests.unit.deps.test_internal_sync_sync",
    "test_internal_sync_sync_edge": "tests.unit.deps.test_internal_sync_sync_edge",
    "test_internal_sync_sync_edge_more": "tests.unit.deps.test_internal_sync_sync_edge_more",
    "test_internal_sync_update": "tests.unit.deps.test_internal_sync_update",
    "test_internal_sync_update_checkout_edge": "tests.unit.deps.test_internal_sync_update_checkout_edge",
    "test_internal_sync_validation": "tests.unit.deps.test_internal_sync_validation",
    "test_internal_sync_workspace": "tests.unit.deps.test_internal_sync_workspace",
    "test_main": "tests.unit.deps.test_main",
    "test_main_discovery_failure": "tests.unit.deps.test_path_sync_main_more",
    "test_main_dispatch": "tests.unit.deps.test_main_dispatch",
    "test_main_no_changes_needed": "tests.unit.deps.test_path_sync_main_more",
    "test_main_project_invalid_toml": "tests.unit.deps.test_path_sync_main_more",
    "test_main_project_no_name": "tests.unit.deps.test_path_sync_main_more",
    "test_main_project_non_string_name": "tests.unit.deps.test_path_sync_main_more",
    "test_main_project_obj_not_dict_first_loop": "tests.unit.deps.test_path_sync_main_project_obj",
    "test_main_project_obj_not_dict_second_loop": "tests.unit.deps.test_path_sync_main_project_obj",
    "test_main_success_modes": "tests.unit.deps.test_extra_paths_sync",
    "test_main_sync_failure": "tests.unit.deps.test_extra_paths_sync",
    "test_main_with_changes_and_dry_run": "tests.unit.deps.test_path_sync_main_more",
    "test_main_with_changes_no_dry_run": "tests.unit.deps.test_path_sync_main_more",
    "test_modernizer_comments": "tests.unit.deps.test_modernizer_comments",
    "test_modernizer_consolidate": "tests.unit.deps.test_modernizer_consolidate",
    "test_modernizer_coverage": "tests.unit.deps.test_modernizer_coverage",
    "test_modernizer_helpers": "tests.unit.deps.test_modernizer_helpers",
    "test_modernizer_main": "tests.unit.deps.test_modernizer_main",
    "test_modernizer_main_extra": "tests.unit.deps.test_modernizer_main_extra",
    "test_modernizer_pyrefly": "tests.unit.deps.test_modernizer_pyrefly",
    "test_modernizer_pyright": "tests.unit.deps.test_modernizer_pyright",
    "test_modernizer_pytest": "tests.unit.deps.test_modernizer_pytest",
    "test_modernizer_workspace": "tests.unit.deps.test_modernizer_workspace",
    "test_path_sync_helpers": "tests.unit.deps.test_path_sync_helpers",
    "test_path_sync_init": "tests.unit.deps.test_path_sync_init",
    "test_path_sync_main": "tests.unit.deps.test_path_sync_main",
    "test_path_sync_main_edges": "tests.unit.deps.test_path_sync_main_edges",
    "test_path_sync_main_more": "tests.unit.deps.test_path_sync_main_more",
    "test_path_sync_main_project_obj": "tests.unit.deps.test_path_sync_main_project_obj",
    "test_path_sync_rewrite_deps": "tests.unit.deps.test_path_sync_rewrite_deps",
    "test_path_sync_rewrite_pep621": "tests.unit.deps.test_path_sync_rewrite_pep621",
    "test_path_sync_rewrite_poetry": "tests.unit.deps.test_path_sync_rewrite_poetry",
    "test_project_dev_groups": "tests.unit.deps.test_modernizer_helpers",
    "test_project_dev_groups_missing_sections": "tests.unit.deps.test_modernizer_helpers",
    "test_pyrefly_search_paths_include_workspace_declared_dev_dependencies": "tests.unit.deps.test_extra_paths_manager",
    "test_rewrite_dep_paths_dry_run": "tests.unit.deps.test_path_sync_rewrite_deps",
    "test_rewrite_dep_paths_read_failure": "tests.unit.deps.test_path_sync_rewrite_deps",
    "test_rewrite_dep_paths_with_internal_names": "tests.unit.deps.test_path_sync_rewrite_deps",
    "test_rewrite_dep_paths_with_no_deps": "tests.unit.deps.test_path_sync_rewrite_deps",
    "test_rewrite_pep621_invalid_path_dep_regex": "tests.unit.deps.test_path_sync_rewrite_pep621",
    "test_rewrite_pep621_no_project_table": "tests.unit.deps.test_path_sync_rewrite_pep621",
    "test_rewrite_pep621_non_string_item": "tests.unit.deps.test_path_sync_rewrite_pep621",
    "test_rewrite_poetry_no_poetry_table": "tests.unit.deps.test_path_sync_rewrite_poetry",
    "test_rewrite_poetry_no_tool_table": "tests.unit.deps.test_path_sync_rewrite_poetry",
    "test_rewrite_poetry_with_non_dict_value": "tests.unit.deps.test_path_sync_rewrite_poetry",
    "test_string_zero_return_value": "tests.unit.deps.test_main_dispatch",
    "test_sync_extra_paths_missing_root_pyproject": "tests.unit.deps.test_extra_paths_sync",
    "test_sync_extra_paths_success_modes": "tests.unit.deps.test_extra_paths_sync",
    "test_sync_extra_paths_sync_failure": "tests.unit.deps.test_extra_paths_sync",
    "test_sync_one_edge_cases": "tests.unit.deps.test_extra_paths_sync",
    "test_target_path": "tests.unit.deps.test_path_sync_helpers",
    "test_unwrap_item": "tests.unit.deps.test_modernizer_helpers",
    "test_unwrap_item_toml_item": "tests.unit.deps.test_modernizer_helpers",
    "test_workspace_root_doc_construction": "tests.unit.deps.test_modernizer_workspace",
    "test_workspace_root_fallback": "tests.unit.deps.test_path_sync_main_more",
    "u": ("flext_core.utilities", "FlextUtilities"),
    "x": ("flext_core.mixins", "FlextMixins"),
}

__all__ = [
    "TestBuildProjectReport",
    "TestClassifyIssues",
    "TestCollectInternalDeps",
    "TestCollectInternalDepsEdgeCases",
    "TestConsolidateGroupsPhase",
    "TestConstants",
    "TestDetectMode",
    "TestDetectionUncoveredLines",
    "TestDetectorReportFlags",
    "TestDetectorRunFailures",
    "TestDiscoverProjects",
    "TestEnsureCheckout",
    "TestEnsureCheckoutEdgeCases",
    "TestEnsureCoverageConfigPhase",
    "TestEnsurePyreflyConfigPhase",
    "TestEnsurePyrightConfigPhase",
    "TestEnsurePytestConfigPhase",
    "TestEnsureSymlink",
    "TestEnsureSymlinkEdgeCases",
    "TestFlextInfraDependencyDetectionModels",
    "TestFlextInfraDependencyDetectionService",
    "TestFlextInfraDependencyDetectorModels",
    "TestFlextInfraDependencyPathSync",
    "TestFlextInfraDeps",
    "TestFlextInfraExtraPathsManager",
    "TestFlextInfraInternalDependencySyncService",
    "TestFlextInfraPyprojectModernizer",
    "TestFlextInfraRuntimeDevDependencyDetectorInit",
    "TestFlextInfraRuntimeDevDependencyDetectorRunDetect",
    "TestFlextInfraRuntimeDevDependencyDetectorRunReport",
    "TestFlextInfraRuntimeDevDependencyDetectorRunTypings",
    "TestGetDepPaths",
    "TestInferOwnerFromOrigin",
    "TestInjectCommentsPhase",
    "TestIsInternalPathDep",
    "TestIsRelativeTo",
    "TestIsWorkspaceMode",
    "TestLoadDependencyLimits",
    "TestMain",
    "TestMainDelegation",
    "TestMainEdgeCases",
    "TestMainExceptionHandling",
    "TestMainFunction",
    "TestMainHelpAndErrors",
    "TestMainModuleImport",
    "TestMainReturnValues",
    "TestMainSubcommandDispatch",
    "TestMainSysArgvModification",
    "TestModernizerEdgeCases",
    "TestModernizerRunAndMain",
    "TestModernizerUncoveredLines",
    "TestModuleAndTypingsFlow",
    "TestOwnerFromRemoteUrl",
    "TestParseGitmodules",
    "TestParseRepoMap",
    "TestParser",
    "TestPathDepPathsPep621",
    "TestPathDepPathsPoetry",
    "TestPathSyncEdgeCases",
    "TestReadDoc",
    "TestResolveRef",
    "TestRewriteDepPaths",
    "TestRewritePep621",
    "TestRewritePoetry",
    "TestRunDeptry",
    "TestRunMypyStubHints",
    "TestRunPipCheck",
    "TestSubcommandMapping",
    "TestSync",
    "TestSyncMethodEdgeCases",
    "TestSyncMethodEdgeCasesMore",
    "TestSyncOne",
    "TestSynthesizedRepoMap",
    "TestToInfraValue",
    "TestValidateGitRefEdgeCases",
    "TestWorkspaceRoot",
    "TestWorkspaceRootFromEnv",
    "TestWorkspaceRootFromParents",
    "c",
    "d",
    "doc",
    "e",
    "extract_dep_name",
    "h",
    "m",
    "main",
    "p",
    "pyright_content",
    "r",
    "rewrite_dep_paths",
    "s",
    "t",
    "test_array",
    "test_as_string_list",
    "test_as_string_list_toml_item",
    "test_canonical_dev_dependencies",
    "test_consolidate_groups_phase_apply_removes_old_groups",
    "test_consolidate_groups_phase_apply_with_empty_poetry_group",
    "test_declared_dependency_names_collects_all_supported_groups",
    "test_dedupe_specs",
    "test_dep_name",
    "test_detect_mode_with_nonexistent_path",
    "test_detect_mode_with_path_object",
    "test_detection_classify",
    "test_detection_deptry",
    "test_detection_discover",
    "test_detection_models",
    "test_detection_pip_check",
    "test_detection_typings",
    "test_detection_typings_flow",
    "test_detection_uncovered",
    "test_detector_detect",
    "test_detector_detect_failures",
    "test_detector_init",
    "test_detector_main",
    "test_detector_models",
    "test_detector_report",
    "test_detector_report_flags",
    "test_ensure_pyrefly_config_phase_apply_errors",
    "test_ensure_pyrefly_config_phase_apply_ignore_errors",
    "test_ensure_pyrefly_config_phase_apply_python_version",
    "test_ensure_pyrefly_config_phase_apply_search_path",
    "test_ensure_pytest_config_phase_apply_markers",
    "test_ensure_pytest_config_phase_apply_minversion",
    "test_ensure_pytest_config_phase_apply_python_classes",
    "test_ensure_table",
    "test_extra_paths_manager",
    "test_extra_paths_pep621",
    "test_extra_paths_sync",
    "test_extract_dep_name",
    "test_extract_requirement_name",
    "test_flext_infra_pyproject_modernizer_find_pyproject_files",
    "test_flext_infra_pyproject_modernizer_process_file_invalid_toml",
    "test_helpers_alias_is_reachable_helpers",
    "test_helpers_alias_is_reachable_project_obj",
    "test_init",
    "test_inject_comments_phase_apply_banner",
    "test_inject_comments_phase_apply_broken_group_section",
    "test_inject_comments_phase_apply_markers",
    "test_inject_comments_phase_apply_with_optional_dependencies_dev",
    "test_inject_comments_phase_deduplicates_family_markers",
    "test_inject_comments_phase_marks_pytest_and_coverage_subtables",
    "test_inject_comments_phase_removes_auto_banner_and_auto_marker",
    "test_inject_comments_phase_repositions_marker_before_section",
    "test_internal_sync_discovery",
    "test_internal_sync_discovery_edge",
    "test_internal_sync_main",
    "test_internal_sync_resolve",
    "test_internal_sync_sync",
    "test_internal_sync_sync_edge",
    "test_internal_sync_sync_edge_more",
    "test_internal_sync_update",
    "test_internal_sync_update_checkout_edge",
    "test_internal_sync_validation",
    "test_internal_sync_workspace",
    "test_main",
    "test_main_discovery_failure",
    "test_main_dispatch",
    "test_main_no_changes_needed",
    "test_main_project_invalid_toml",
    "test_main_project_no_name",
    "test_main_project_non_string_name",
    "test_main_project_obj_not_dict_first_loop",
    "test_main_project_obj_not_dict_second_loop",
    "test_main_success_modes",
    "test_main_sync_failure",
    "test_main_with_changes_and_dry_run",
    "test_main_with_changes_no_dry_run",
    "test_modernizer_comments",
    "test_modernizer_consolidate",
    "test_modernizer_coverage",
    "test_modernizer_helpers",
    "test_modernizer_main",
    "test_modernizer_main_extra",
    "test_modernizer_pyrefly",
    "test_modernizer_pyright",
    "test_modernizer_pytest",
    "test_modernizer_workspace",
    "test_path_sync_helpers",
    "test_path_sync_init",
    "test_path_sync_main",
    "test_path_sync_main_edges",
    "test_path_sync_main_more",
    "test_path_sync_main_project_obj",
    "test_path_sync_rewrite_deps",
    "test_path_sync_rewrite_pep621",
    "test_path_sync_rewrite_poetry",
    "test_project_dev_groups",
    "test_project_dev_groups_missing_sections",
    "test_pyrefly_search_paths_include_workspace_declared_dev_dependencies",
    "test_rewrite_dep_paths_dry_run",
    "test_rewrite_dep_paths_read_failure",
    "test_rewrite_dep_paths_with_internal_names",
    "test_rewrite_dep_paths_with_no_deps",
    "test_rewrite_pep621_invalid_path_dep_regex",
    "test_rewrite_pep621_no_project_table",
    "test_rewrite_pep621_non_string_item",
    "test_rewrite_poetry_no_poetry_table",
    "test_rewrite_poetry_no_tool_table",
    "test_rewrite_poetry_with_non_dict_value",
    "test_string_zero_return_value",
    "test_sync_extra_paths_missing_root_pyproject",
    "test_sync_extra_paths_success_modes",
    "test_sync_extra_paths_sync_failure",
    "test_sync_one_edge_cases",
    "test_target_path",
    "test_unwrap_item",
    "test_unwrap_item_toml_item",
    "test_workspace_root_doc_construction",
    "test_workspace_root_fallback",
    "u",
    "x",
]


install_lazy_exports(__name__, globals(), _LAZY_IMPORTS)
