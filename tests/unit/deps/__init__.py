# AUTO-GENERATED FILE — DO NOT EDIT MANUALLY.
# Regenerate with: make gen
#
"""Tests for flext_infra.deps dependency management modules."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import TYPE_CHECKING

from flext_core.lazy import install_lazy_exports

if TYPE_CHECKING:
    from tests.unit.deps import (
        test_detection_classify,
        test_detection_deptry,
        test_detection_discover,
        test_detection_models,
        test_detection_pip_check,
        test_detection_typings,
        test_detection_typings_flow,
        test_detection_uncovered,
        test_detector_detect,
        test_detector_detect_failures,
        test_detector_init,
        test_detector_main,
        test_detector_models,
        test_detector_report,
        test_detector_report_flags,
        test_extra_paths_manager,
        test_extra_paths_pep621,
        test_extra_paths_sync,
        test_init,
        test_internal_sync_discovery,
        test_internal_sync_discovery_edge,
        test_internal_sync_main,
        test_internal_sync_resolve,
        test_internal_sync_sync,
        test_internal_sync_sync_edge,
        test_internal_sync_sync_edge_more,
        test_internal_sync_update,
        test_internal_sync_update_checkout_edge,
        test_internal_sync_validation,
        test_internal_sync_workspace,
        test_main,
        test_main_dispatch,
        test_modernizer_comments,
        test_modernizer_consolidate,
        test_modernizer_coverage,
        test_modernizer_helpers,
        test_modernizer_main,
        test_modernizer_main_extra,
        test_modernizer_pyrefly,
        test_modernizer_pyright,
        test_modernizer_pytest,
        test_modernizer_workspace,
        test_path_sync_helpers,
        test_path_sync_init,
        test_path_sync_main,
        test_path_sync_main_edges,
        test_path_sync_main_more,
        test_path_sync_main_project_obj,
        test_path_sync_rewrite_deps,
        test_path_sync_rewrite_pep621,
        test_path_sync_rewrite_poetry,
    )
    from tests.unit.deps.test_detection_classify import *
    from tests.unit.deps.test_detection_deptry import *
    from tests.unit.deps.test_detection_discover import *
    from tests.unit.deps.test_detection_models import *
    from tests.unit.deps.test_detection_pip_check import *
    from tests.unit.deps.test_detection_typings import *
    from tests.unit.deps.test_detection_typings_flow import *
    from tests.unit.deps.test_detection_uncovered import *
    from tests.unit.deps.test_detector_detect import *
    from tests.unit.deps.test_detector_detect_failures import *
    from tests.unit.deps.test_detector_init import *
    from tests.unit.deps.test_detector_main import *
    from tests.unit.deps.test_detector_models import *
    from tests.unit.deps.test_detector_report import *
    from tests.unit.deps.test_detector_report_flags import *
    from tests.unit.deps.test_extra_paths_manager import *
    from tests.unit.deps.test_extra_paths_pep621 import *
    from tests.unit.deps.test_extra_paths_sync import *
    from tests.unit.deps.test_init import *
    from tests.unit.deps.test_internal_sync_discovery import *
    from tests.unit.deps.test_internal_sync_discovery_edge import *
    from tests.unit.deps.test_internal_sync_resolve import *
    from tests.unit.deps.test_internal_sync_sync import *
    from tests.unit.deps.test_internal_sync_sync_edge import *
    from tests.unit.deps.test_internal_sync_sync_edge_more import *
    from tests.unit.deps.test_internal_sync_update import *
    from tests.unit.deps.test_internal_sync_update_checkout_edge import *
    from tests.unit.deps.test_internal_sync_validation import *
    from tests.unit.deps.test_internal_sync_workspace import *
    from tests.unit.deps.test_main import *
    from tests.unit.deps.test_main_dispatch import *
    from tests.unit.deps.test_modernizer_comments import *
    from tests.unit.deps.test_modernizer_consolidate import *
    from tests.unit.deps.test_modernizer_coverage import *
    from tests.unit.deps.test_modernizer_helpers import *
    from tests.unit.deps.test_modernizer_main import *
    from tests.unit.deps.test_modernizer_main_extra import *
    from tests.unit.deps.test_modernizer_pyrefly import *
    from tests.unit.deps.test_modernizer_pyright import *
    from tests.unit.deps.test_modernizer_pytest import *
    from tests.unit.deps.test_modernizer_workspace import *
    from tests.unit.deps.test_path_sync_helpers import *
    from tests.unit.deps.test_path_sync_init import *
    from tests.unit.deps.test_path_sync_main import *
    from tests.unit.deps.test_path_sync_main_edges import *
    from tests.unit.deps.test_path_sync_main_more import *
    from tests.unit.deps.test_path_sync_main_project_obj import *
    from tests.unit.deps.test_path_sync_rewrite_deps import *
    from tests.unit.deps.test_path_sync_rewrite_pep621 import *
    from tests.unit.deps.test_path_sync_rewrite_poetry import *

_LAZY_IMPORTS: Mapping[str, str | Sequence[str]] = {
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
    "doc": "tests.unit.deps.test_modernizer_helpers",
    "extract_dep_name": "tests.unit.deps.test_path_sync_helpers",
    "main": "tests.unit.deps.test_main_dispatch",
    "pyright_content": "tests.unit.deps.test_extra_paths_sync",
    "rewrite_dep_paths": "tests.unit.deps.test_path_sync_rewrite_deps",
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
}


install_lazy_exports(__name__, globals(), _LAZY_IMPORTS, sorted(_LAZY_IMPORTS))
