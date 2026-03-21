# AUTO-GENERATED FILE — DO NOT EDIT MANUALLY.
# Regenerate with: make codegen
#
"""Tests for flext_infra.deps dependency management modules."""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_core.lazy import cleanup_submodule_namespace, lazy_getattr

if TYPE_CHECKING:
    from flext_core.typings import FlextTypes

    from .test_detection_classify import TestBuildProjectReport, TestClassifyIssues
    from .test_detection_deptry import TestRunDeptry
    from .test_detection_discover import TestDiscoverProjects
    from .test_detection_models import (
        TestFlextInfraDependencyDetectionModels,
        TestFlextInfraDependencyDetectionService,
        TestToInfraValue,
    )
    from .test_detection_pip_check import TestRunPipCheck
    from .test_detection_typings import TestLoadDependencyLimits, TestRunMypyStubHints
    from .test_detection_typings_flow import TestModuleAndTypingsFlow
    from .test_detection_uncovered import TestDetectionUncoveredLines
    from .test_detector_detect import (
        TestFlextInfraRuntimeDevDependencyDetectorRunDetect,
    )
    from .test_detector_detect_failures import TestDetectorRunFailures
    from .test_detector_init import TestFlextInfraRuntimeDevDependencyDetectorInit
    from .test_detector_main import (
        TestFlextInfraRuntimeDevDependencyDetectorRunTypings,
        TestMainFunction,
    )
    from .test_detector_models import TestFlextInfraDependencyDetectorModels
    from .test_detector_report import (
        TestFlextInfraRuntimeDevDependencyDetectorRunReport,
    )
    from .test_detector_report_flags import TestDetectorReportFlags
    from .test_extra_paths_manager import (
        TestConstants,
        TestFlextInfraExtraPathsManager,
        TestGetDepPaths,
        TestSyncOne,
    )
    from .test_extra_paths_pep621 import TestPathDepPathsPep621, TestPathDepPathsPoetry
    from .test_extra_paths_sync import (
        pyright_content,
        test_main_success_modes,
        test_main_sync_failure,
        test_sync_extra_paths_missing_root_pyproject,
        test_sync_extra_paths_success_modes,
        test_sync_extra_paths_sync_failure,
        test_sync_one_edge_cases,
    )
    from .test_init import TestFlextInfraDeps
    from .test_internal_sync_discovery import (
        TestCollectInternalDeps,
        TestParseGitmodules,
        TestParseRepoMap,
    )
    from .test_internal_sync_discovery_edge import TestCollectInternalDepsEdgeCases
    from .test_internal_sync_resolve import (
        TestInferOwnerFromOrigin,
        TestResolveRef,
        TestSynthesizedRepoMap,
    )
    from .test_internal_sync_sync import TestSync
    from .test_internal_sync_sync_edge import TestSyncMethodEdgeCases
    from .test_internal_sync_sync_edge_more import TestSyncMethodEdgeCasesMore
    from .test_internal_sync_update import (
        TestEnsureCheckout,
        TestEnsureSymlink,
        TestEnsureSymlinkEdgeCases,
    )
    from .test_internal_sync_update_checkout_edge import TestEnsureCheckoutEdgeCases
    from .test_internal_sync_validation import (
        TestFlextInfraInternalDependencySyncService,
        TestIsInternalPathDep,
        TestIsRelativeTo,
        TestOwnerFromRemoteUrl,
        TestValidateGitRefEdgeCases,
    )
    from .test_internal_sync_workspace import (
        TestIsWorkspaceMode,
        TestWorkspaceRootFromEnv,
        TestWorkspaceRootFromParents,
    )
    from .test_main import (
        TestMainHelpAndErrors,
        TestMainReturnValues,
        TestSubcommandMapping,
    )
    from .test_main_dispatch import (
        TestMainDelegation,
        TestMainExceptionHandling,
        TestMainModuleImport,
        TestMainSubcommandDispatch,
        TestMainSysArgvModification,
        test_string_zero_return_value,
    )
    from .test_modernizer_comments import (
        TestInjectCommentsPhase,
        test_inject_comments_phase_apply_banner,
        test_inject_comments_phase_apply_broken_group_section,
        test_inject_comments_phase_apply_markers,
        test_inject_comments_phase_apply_with_optional_dependencies_dev,
    )
    from .test_modernizer_consolidate import (
        TestConsolidateGroupsPhase,
        test_consolidate_groups_phase_apply_removes_old_groups,
        test_consolidate_groups_phase_apply_with_empty_poetry_group,
    )
    from .test_modernizer_helpers import (
        doc,
        test_array,
        test_as_string_list,
        test_as_string_list_toml_item,
        test_canonical_dev_dependencies,
        test_dedupe_specs,
        test_dep_name,
        test_ensure_table,
        test_project_dev_groups,
        test_project_dev_groups_missing_sections,
        test_unwrap_item,
        test_unwrap_item_toml_item,
    )
    from .test_modernizer_main import (
        TestFlextInfraPyprojectModernizer,
        TestModernizerRunAndMain,
    )
    from .test_modernizer_main_extra import (
        TestModernizerEdgeCases,
        TestModernizerUncoveredLines,
        test_flext_infra_pyproject_modernizer_find_pyproject_files,
        test_flext_infra_pyproject_modernizer_process_file_invalid_toml,
    )
    from .test_modernizer_pyrefly import (
        TestEnsurePyreflyConfigPhase,
        test_ensure_pyrefly_config_phase_apply_errors,
        test_ensure_pyrefly_config_phase_apply_ignore_errors,
        test_ensure_pyrefly_config_phase_apply_python_version,
        test_ensure_pyrefly_config_phase_apply_search_path,
    )
    from .test_modernizer_pyright import TestEnsurePyrightConfigPhase
    from .test_modernizer_pytest import (
        TestEnsurePytestConfigPhase,
        test_ensure_pytest_config_phase_apply_markers,
        test_ensure_pytest_config_phase_apply_minversion,
        test_ensure_pytest_config_phase_apply_python_classes,
    )
    from .test_modernizer_workspace import (
        TestParser,
        TestReadDoc,
        TestWorkspaceRoot,
        test_workspace_root_doc_construction,
    )
    from .test_path_sync_helpers import (
        extract_dep_name,
        test_extract_dep_name,
        test_extract_requirement_name,
        test_helpers_alias_is_reachable_helpers,
        test_target_path,
    )
    from .test_path_sync_init import (
        TestDetectMode,
        TestFlextInfraDependencyPathSync,
        TestPathSyncEdgeCases,
        test_detect_mode_with_nonexistent_path,
        test_detect_mode_with_path_object,
    )
    from .test_path_sync_main import TestMain
    from .test_path_sync_main_edges import TestMainEdgeCases
    from .test_path_sync_main_more import (
        test_main_discovery_failure,
        test_main_no_changes_needed,
        test_main_project_invalid_toml,
        test_main_project_no_name,
        test_main_project_non_string_name,
        test_main_with_changes_and_dry_run,
        test_main_with_changes_no_dry_run,
        test_workspace_root_fallback,
    )
    from .test_path_sync_main_project_obj import (
        test_helpers_alias_is_reachable_project_obj,
        test_main_project_obj_not_dict_first_loop,
        test_main_project_obj_not_dict_second_loop,
    )
    from .test_path_sync_rewrite_deps import (
        TestRewriteDepPaths,
        rewrite_dep_paths,
        test_rewrite_dep_paths_dry_run,
        test_rewrite_dep_paths_read_failure,
        test_rewrite_dep_paths_with_internal_names,
        test_rewrite_dep_paths_with_no_deps,
    )
    from .test_path_sync_rewrite_pep621 import (
        TestRewritePep621,
        test_rewrite_pep621_invalid_path_dep_regex,
        test_rewrite_pep621_no_project_table,
        test_rewrite_pep621_non_string_item,
    )
    from .test_path_sync_rewrite_poetry import (
        TestRewritePoetry,
        test_rewrite_poetry_no_poetry_table,
        test_rewrite_poetry_no_tool_table,
        test_rewrite_poetry_with_non_dict_value,
    )

_LAZY_IMPORTS: dict[str, tuple[str, str]] = {
    "TestBuildProjectReport": (
        "tests.unit.deps.test_detection_classify",
        "TestBuildProjectReport",
    ),
    "TestClassifyIssues": (
        "tests.unit.deps.test_detection_classify",
        "TestClassifyIssues",
    ),
    "TestCollectInternalDeps": (
        "tests.unit.deps.test_internal_sync_discovery",
        "TestCollectInternalDeps",
    ),
    "TestCollectInternalDepsEdgeCases": (
        "tests.unit.deps.test_internal_sync_discovery_edge",
        "TestCollectInternalDepsEdgeCases",
    ),
    "TestConsolidateGroupsPhase": (
        "tests.unit.deps.test_modernizer_consolidate",
        "TestConsolidateGroupsPhase",
    ),
    "TestConstants": ("tests.unit.deps.test_extra_paths_manager", "TestConstants"),
    "TestDetectMode": ("tests.unit.deps.test_path_sync_init", "TestDetectMode"),
    "TestDetectionUncoveredLines": (
        "tests.unit.deps.test_detection_uncovered",
        "TestDetectionUncoveredLines",
    ),
    "TestDetectorReportFlags": (
        "tests.unit.deps.test_detector_report_flags",
        "TestDetectorReportFlags",
    ),
    "TestDetectorRunFailures": (
        "tests.unit.deps.test_detector_detect_failures",
        "TestDetectorRunFailures",
    ),
    "TestDiscoverProjects": (
        "tests.unit.deps.test_detection_discover",
        "TestDiscoverProjects",
    ),
    "TestEnsureCheckout": (
        "tests.unit.deps.test_internal_sync_update",
        "TestEnsureCheckout",
    ),
    "TestEnsureCheckoutEdgeCases": (
        "tests.unit.deps.test_internal_sync_update_checkout_edge",
        "TestEnsureCheckoutEdgeCases",
    ),
    "TestEnsurePyreflyConfigPhase": (
        "tests.unit.deps.test_modernizer_pyrefly",
        "TestEnsurePyreflyConfigPhase",
    ),
    "TestEnsurePyrightConfigPhase": (
        "tests.unit.deps.test_modernizer_pyright",
        "TestEnsurePyrightConfigPhase",
    ),
    "TestEnsurePytestConfigPhase": (
        "tests.unit.deps.test_modernizer_pytest",
        "TestEnsurePytestConfigPhase",
    ),
    "TestEnsureSymlink": (
        "tests.unit.deps.test_internal_sync_update",
        "TestEnsureSymlink",
    ),
    "TestEnsureSymlinkEdgeCases": (
        "tests.unit.deps.test_internal_sync_update",
        "TestEnsureSymlinkEdgeCases",
    ),
    "TestFlextInfraDependencyDetectionModels": (
        "tests.unit.deps.test_detection_models",
        "TestFlextInfraDependencyDetectionModels",
    ),
    "TestFlextInfraDependencyDetectionService": (
        "tests.unit.deps.test_detection_models",
        "TestFlextInfraDependencyDetectionService",
    ),
    "TestFlextInfraDependencyDetectorModels": (
        "tests.unit.deps.test_detector_models",
        "TestFlextInfraDependencyDetectorModels",
    ),
    "TestFlextInfraDependencyPathSync": (
        "tests.unit.deps.test_path_sync_init",
        "TestFlextInfraDependencyPathSync",
    ),
    "TestFlextInfraDeps": ("tests.unit.deps.test_init", "TestFlextInfraDeps"),
    "TestFlextInfraExtraPathsManager": (
        "tests.unit.deps.test_extra_paths_manager",
        "TestFlextInfraExtraPathsManager",
    ),
    "TestFlextInfraInternalDependencySyncService": (
        "tests.unit.deps.test_internal_sync_validation",
        "TestFlextInfraInternalDependencySyncService",
    ),
    "TestFlextInfraPyprojectModernizer": (
        "tests.unit.deps.test_modernizer_main",
        "TestFlextInfraPyprojectModernizer",
    ),
    "TestFlextInfraRuntimeDevDependencyDetectorInit": (
        "tests.unit.deps.test_detector_init",
        "TestFlextInfraRuntimeDevDependencyDetectorInit",
    ),
    "TestFlextInfraRuntimeDevDependencyDetectorRunDetect": (
        "tests.unit.deps.test_detector_detect",
        "TestFlextInfraRuntimeDevDependencyDetectorRunDetect",
    ),
    "TestFlextInfraRuntimeDevDependencyDetectorRunReport": (
        "tests.unit.deps.test_detector_report",
        "TestFlextInfraRuntimeDevDependencyDetectorRunReport",
    ),
    "TestFlextInfraRuntimeDevDependencyDetectorRunTypings": (
        "tests.unit.deps.test_detector_main",
        "TestFlextInfraRuntimeDevDependencyDetectorRunTypings",
    ),
    "TestGetDepPaths": ("tests.unit.deps.test_extra_paths_manager", "TestGetDepPaths"),
    "TestInferOwnerFromOrigin": (
        "tests.unit.deps.test_internal_sync_resolve",
        "TestInferOwnerFromOrigin",
    ),
    "TestInjectCommentsPhase": (
        "tests.unit.deps.test_modernizer_comments",
        "TestInjectCommentsPhase",
    ),
    "TestIsInternalPathDep": (
        "tests.unit.deps.test_internal_sync_validation",
        "TestIsInternalPathDep",
    ),
    "TestIsRelativeTo": (
        "tests.unit.deps.test_internal_sync_validation",
        "TestIsRelativeTo",
    ),
    "TestIsWorkspaceMode": (
        "tests.unit.deps.test_internal_sync_workspace",
        "TestIsWorkspaceMode",
    ),
    "TestLoadDependencyLimits": (
        "tests.unit.deps.test_detection_typings",
        "TestLoadDependencyLimits",
    ),
    "TestMain": ("tests.unit.deps.test_path_sync_main", "TestMain"),
    "TestMainDelegation": ("tests.unit.deps.test_main_dispatch", "TestMainDelegation"),
    "TestMainEdgeCases": (
        "tests.unit.deps.test_path_sync_main_edges",
        "TestMainEdgeCases",
    ),
    "TestMainExceptionHandling": (
        "tests.unit.deps.test_main_dispatch",
        "TestMainExceptionHandling",
    ),
    "TestMainFunction": ("tests.unit.deps.test_detector_main", "TestMainFunction"),
    "TestMainHelpAndErrors": ("tests.unit.deps.test_main", "TestMainHelpAndErrors"),
    "TestMainModuleImport": (
        "tests.unit.deps.test_main_dispatch",
        "TestMainModuleImport",
    ),
    "TestMainReturnValues": ("tests.unit.deps.test_main", "TestMainReturnValues"),
    "TestMainSubcommandDispatch": (
        "tests.unit.deps.test_main_dispatch",
        "TestMainSubcommandDispatch",
    ),
    "TestMainSysArgvModification": (
        "tests.unit.deps.test_main_dispatch",
        "TestMainSysArgvModification",
    ),
    "TestModernizerEdgeCases": (
        "tests.unit.deps.test_modernizer_main_extra",
        "TestModernizerEdgeCases",
    ),
    "TestModernizerRunAndMain": (
        "tests.unit.deps.test_modernizer_main",
        "TestModernizerRunAndMain",
    ),
    "TestModernizerUncoveredLines": (
        "tests.unit.deps.test_modernizer_main_extra",
        "TestModernizerUncoveredLines",
    ),
    "TestModuleAndTypingsFlow": (
        "tests.unit.deps.test_detection_typings_flow",
        "TestModuleAndTypingsFlow",
    ),
    "TestOwnerFromRemoteUrl": (
        "tests.unit.deps.test_internal_sync_validation",
        "TestOwnerFromRemoteUrl",
    ),
    "TestParseGitmodules": (
        "tests.unit.deps.test_internal_sync_discovery",
        "TestParseGitmodules",
    ),
    "TestParseRepoMap": (
        "tests.unit.deps.test_internal_sync_discovery",
        "TestParseRepoMap",
    ),
    "TestParser": ("tests.unit.deps.test_modernizer_workspace", "TestParser"),
    "TestPathDepPathsPep621": (
        "tests.unit.deps.test_extra_paths_pep621",
        "TestPathDepPathsPep621",
    ),
    "TestPathDepPathsPoetry": (
        "tests.unit.deps.test_extra_paths_pep621",
        "TestPathDepPathsPoetry",
    ),
    "TestPathSyncEdgeCases": (
        "tests.unit.deps.test_path_sync_init",
        "TestPathSyncEdgeCases",
    ),
    "TestReadDoc": ("tests.unit.deps.test_modernizer_workspace", "TestReadDoc"),
    "TestResolveRef": ("tests.unit.deps.test_internal_sync_resolve", "TestResolveRef"),
    "TestRewriteDepPaths": (
        "tests.unit.deps.test_path_sync_rewrite_deps",
        "TestRewriteDepPaths",
    ),
    "TestRewritePep621": (
        "tests.unit.deps.test_path_sync_rewrite_pep621",
        "TestRewritePep621",
    ),
    "TestRewritePoetry": (
        "tests.unit.deps.test_path_sync_rewrite_poetry",
        "TestRewritePoetry",
    ),
    "TestRunDeptry": ("tests.unit.deps.test_detection_deptry", "TestRunDeptry"),
    "TestRunMypyStubHints": (
        "tests.unit.deps.test_detection_typings",
        "TestRunMypyStubHints",
    ),
    "TestRunPipCheck": ("tests.unit.deps.test_detection_pip_check", "TestRunPipCheck"),
    "TestSubcommandMapping": ("tests.unit.deps.test_main", "TestSubcommandMapping"),
    "TestSync": ("tests.unit.deps.test_internal_sync_sync", "TestSync"),
    "TestSyncMethodEdgeCases": (
        "tests.unit.deps.test_internal_sync_sync_edge",
        "TestSyncMethodEdgeCases",
    ),
    "TestSyncMethodEdgeCasesMore": (
        "tests.unit.deps.test_internal_sync_sync_edge_more",
        "TestSyncMethodEdgeCasesMore",
    ),
    "TestSyncOne": ("tests.unit.deps.test_extra_paths_manager", "TestSyncOne"),
    "TestSynthesizedRepoMap": (
        "tests.unit.deps.test_internal_sync_resolve",
        "TestSynthesizedRepoMap",
    ),
    "TestToInfraValue": ("tests.unit.deps.test_detection_models", "TestToInfraValue"),
    "TestValidateGitRefEdgeCases": (
        "tests.unit.deps.test_internal_sync_validation",
        "TestValidateGitRefEdgeCases",
    ),
    "TestWorkspaceRoot": (
        "tests.unit.deps.test_modernizer_workspace",
        "TestWorkspaceRoot",
    ),
    "TestWorkspaceRootFromEnv": (
        "tests.unit.deps.test_internal_sync_workspace",
        "TestWorkspaceRootFromEnv",
    ),
    "TestWorkspaceRootFromParents": (
        "tests.unit.deps.test_internal_sync_workspace",
        "TestWorkspaceRootFromParents",
    ),
    "doc": ("tests.unit.deps.test_modernizer_helpers", "doc"),
    "extract_dep_name": ("tests.unit.deps.test_path_sync_helpers", "extract_dep_name"),
    "pyright_content": ("tests.unit.deps.test_extra_paths_sync", "pyright_content"),
    "rewrite_dep_paths": (
        "tests.unit.deps.test_path_sync_rewrite_deps",
        "rewrite_dep_paths",
    ),
    "test_array": ("tests.unit.deps.test_modernizer_helpers", "test_array"),
    "test_as_string_list": (
        "tests.unit.deps.test_modernizer_helpers",
        "test_as_string_list",
    ),
    "test_as_string_list_toml_item": (
        "tests.unit.deps.test_modernizer_helpers",
        "test_as_string_list_toml_item",
    ),
    "test_canonical_dev_dependencies": (
        "tests.unit.deps.test_modernizer_helpers",
        "test_canonical_dev_dependencies",
    ),
    "test_consolidate_groups_phase_apply_removes_old_groups": (
        "tests.unit.deps.test_modernizer_consolidate",
        "test_consolidate_groups_phase_apply_removes_old_groups",
    ),
    "test_consolidate_groups_phase_apply_with_empty_poetry_group": (
        "tests.unit.deps.test_modernizer_consolidate",
        "test_consolidate_groups_phase_apply_with_empty_poetry_group",
    ),
    "test_dedupe_specs": (
        "tests.unit.deps.test_modernizer_helpers",
        "test_dedupe_specs",
    ),
    "test_dep_name": ("tests.unit.deps.test_modernizer_helpers", "test_dep_name"),
    "test_detect_mode_with_nonexistent_path": (
        "tests.unit.deps.test_path_sync_init",
        "test_detect_mode_with_nonexistent_path",
    ),
    "test_detect_mode_with_path_object": (
        "tests.unit.deps.test_path_sync_init",
        "test_detect_mode_with_path_object",
    ),
    "test_ensure_pyrefly_config_phase_apply_errors": (
        "tests.unit.deps.test_modernizer_pyrefly",
        "test_ensure_pyrefly_config_phase_apply_errors",
    ),
    "test_ensure_pyrefly_config_phase_apply_ignore_errors": (
        "tests.unit.deps.test_modernizer_pyrefly",
        "test_ensure_pyrefly_config_phase_apply_ignore_errors",
    ),
    "test_ensure_pyrefly_config_phase_apply_python_version": (
        "tests.unit.deps.test_modernizer_pyrefly",
        "test_ensure_pyrefly_config_phase_apply_python_version",
    ),
    "test_ensure_pyrefly_config_phase_apply_search_path": (
        "tests.unit.deps.test_modernizer_pyrefly",
        "test_ensure_pyrefly_config_phase_apply_search_path",
    ),
    "test_ensure_pytest_config_phase_apply_markers": (
        "tests.unit.deps.test_modernizer_pytest",
        "test_ensure_pytest_config_phase_apply_markers",
    ),
    "test_ensure_pytest_config_phase_apply_minversion": (
        "tests.unit.deps.test_modernizer_pytest",
        "test_ensure_pytest_config_phase_apply_minversion",
    ),
    "test_ensure_pytest_config_phase_apply_python_classes": (
        "tests.unit.deps.test_modernizer_pytest",
        "test_ensure_pytest_config_phase_apply_python_classes",
    ),
    "test_ensure_table": (
        "tests.unit.deps.test_modernizer_helpers",
        "test_ensure_table",
    ),
    "test_extract_dep_name": (
        "tests.unit.deps.test_path_sync_helpers",
        "test_extract_dep_name",
    ),
    "test_extract_requirement_name": (
        "tests.unit.deps.test_path_sync_helpers",
        "test_extract_requirement_name",
    ),
    "test_flext_infra_pyproject_modernizer_find_pyproject_files": (
        "tests.unit.deps.test_modernizer_main_extra",
        "test_flext_infra_pyproject_modernizer_find_pyproject_files",
    ),
    "test_flext_infra_pyproject_modernizer_process_file_invalid_toml": (
        "tests.unit.deps.test_modernizer_main_extra",
        "test_flext_infra_pyproject_modernizer_process_file_invalid_toml",
    ),
    "test_helpers_alias_is_reachable_helpers": (
        "tests.unit.deps.test_path_sync_helpers",
        "test_helpers_alias_is_reachable_helpers",
    ),
    "test_helpers_alias_is_reachable_project_obj": (
        "tests.unit.deps.test_path_sync_main_project_obj",
        "test_helpers_alias_is_reachable_project_obj",
    ),
    "test_inject_comments_phase_apply_banner": (
        "tests.unit.deps.test_modernizer_comments",
        "test_inject_comments_phase_apply_banner",
    ),
    "test_inject_comments_phase_apply_broken_group_section": (
        "tests.unit.deps.test_modernizer_comments",
        "test_inject_comments_phase_apply_broken_group_section",
    ),
    "test_inject_comments_phase_apply_markers": (
        "tests.unit.deps.test_modernizer_comments",
        "test_inject_comments_phase_apply_markers",
    ),
    "test_inject_comments_phase_apply_with_optional_dependencies_dev": (
        "tests.unit.deps.test_modernizer_comments",
        "test_inject_comments_phase_apply_with_optional_dependencies_dev",
    ),
    "test_main_discovery_failure": (
        "tests.unit.deps.test_path_sync_main_more",
        "test_main_discovery_failure",
    ),
    "test_main_no_changes_needed": (
        "tests.unit.deps.test_path_sync_main_more",
        "test_main_no_changes_needed",
    ),
    "test_main_project_invalid_toml": (
        "tests.unit.deps.test_path_sync_main_more",
        "test_main_project_invalid_toml",
    ),
    "test_main_project_no_name": (
        "tests.unit.deps.test_path_sync_main_more",
        "test_main_project_no_name",
    ),
    "test_main_project_non_string_name": (
        "tests.unit.deps.test_path_sync_main_more",
        "test_main_project_non_string_name",
    ),
    "test_main_project_obj_not_dict_first_loop": (
        "tests.unit.deps.test_path_sync_main_project_obj",
        "test_main_project_obj_not_dict_first_loop",
    ),
    "test_main_project_obj_not_dict_second_loop": (
        "tests.unit.deps.test_path_sync_main_project_obj",
        "test_main_project_obj_not_dict_second_loop",
    ),
    "test_main_success_modes": (
        "tests.unit.deps.test_extra_paths_sync",
        "test_main_success_modes",
    ),
    "test_main_sync_failure": (
        "tests.unit.deps.test_extra_paths_sync",
        "test_main_sync_failure",
    ),
    "test_main_with_changes_and_dry_run": (
        "tests.unit.deps.test_path_sync_main_more",
        "test_main_with_changes_and_dry_run",
    ),
    "test_main_with_changes_no_dry_run": (
        "tests.unit.deps.test_path_sync_main_more",
        "test_main_with_changes_no_dry_run",
    ),
    "test_project_dev_groups": (
        "tests.unit.deps.test_modernizer_helpers",
        "test_project_dev_groups",
    ),
    "test_project_dev_groups_missing_sections": (
        "tests.unit.deps.test_modernizer_helpers",
        "test_project_dev_groups_missing_sections",
    ),
    "test_rewrite_dep_paths_dry_run": (
        "tests.unit.deps.test_path_sync_rewrite_deps",
        "test_rewrite_dep_paths_dry_run",
    ),
    "test_rewrite_dep_paths_read_failure": (
        "tests.unit.deps.test_path_sync_rewrite_deps",
        "test_rewrite_dep_paths_read_failure",
    ),
    "test_rewrite_dep_paths_with_internal_names": (
        "tests.unit.deps.test_path_sync_rewrite_deps",
        "test_rewrite_dep_paths_with_internal_names",
    ),
    "test_rewrite_dep_paths_with_no_deps": (
        "tests.unit.deps.test_path_sync_rewrite_deps",
        "test_rewrite_dep_paths_with_no_deps",
    ),
    "test_rewrite_pep621_invalid_path_dep_regex": (
        "tests.unit.deps.test_path_sync_rewrite_pep621",
        "test_rewrite_pep621_invalid_path_dep_regex",
    ),
    "test_rewrite_pep621_no_project_table": (
        "tests.unit.deps.test_path_sync_rewrite_pep621",
        "test_rewrite_pep621_no_project_table",
    ),
    "test_rewrite_pep621_non_string_item": (
        "tests.unit.deps.test_path_sync_rewrite_pep621",
        "test_rewrite_pep621_non_string_item",
    ),
    "test_rewrite_poetry_no_poetry_table": (
        "tests.unit.deps.test_path_sync_rewrite_poetry",
        "test_rewrite_poetry_no_poetry_table",
    ),
    "test_rewrite_poetry_no_tool_table": (
        "tests.unit.deps.test_path_sync_rewrite_poetry",
        "test_rewrite_poetry_no_tool_table",
    ),
    "test_rewrite_poetry_with_non_dict_value": (
        "tests.unit.deps.test_path_sync_rewrite_poetry",
        "test_rewrite_poetry_with_non_dict_value",
    ),
    "test_string_zero_return_value": (
        "tests.unit.deps.test_main_dispatch",
        "test_string_zero_return_value",
    ),
    "test_sync_extra_paths_missing_root_pyproject": (
        "tests.unit.deps.test_extra_paths_sync",
        "test_sync_extra_paths_missing_root_pyproject",
    ),
    "test_sync_extra_paths_success_modes": (
        "tests.unit.deps.test_extra_paths_sync",
        "test_sync_extra_paths_success_modes",
    ),
    "test_sync_extra_paths_sync_failure": (
        "tests.unit.deps.test_extra_paths_sync",
        "test_sync_extra_paths_sync_failure",
    ),
    "test_sync_one_edge_cases": (
        "tests.unit.deps.test_extra_paths_sync",
        "test_sync_one_edge_cases",
    ),
    "test_target_path": ("tests.unit.deps.test_path_sync_helpers", "test_target_path"),
    "test_unwrap_item": ("tests.unit.deps.test_modernizer_helpers", "test_unwrap_item"),
    "test_unwrap_item_toml_item": (
        "tests.unit.deps.test_modernizer_helpers",
        "test_unwrap_item_toml_item",
    ),
    "test_workspace_root_doc_construction": (
        "tests.unit.deps.test_modernizer_workspace",
        "test_workspace_root_doc_construction",
    ),
    "test_workspace_root_fallback": (
        "tests.unit.deps.test_path_sync_main_more",
        "test_workspace_root_fallback",
    ),
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
    "doc",
    "extract_dep_name",
    "pyright_content",
    "rewrite_dep_paths",
    "test_array",
    "test_as_string_list",
    "test_as_string_list_toml_item",
    "test_canonical_dev_dependencies",
    "test_consolidate_groups_phase_apply_removes_old_groups",
    "test_consolidate_groups_phase_apply_with_empty_poetry_group",
    "test_dedupe_specs",
    "test_dep_name",
    "test_detect_mode_with_nonexistent_path",
    "test_detect_mode_with_path_object",
    "test_ensure_pyrefly_config_phase_apply_errors",
    "test_ensure_pyrefly_config_phase_apply_ignore_errors",
    "test_ensure_pyrefly_config_phase_apply_python_version",
    "test_ensure_pyrefly_config_phase_apply_search_path",
    "test_ensure_pytest_config_phase_apply_markers",
    "test_ensure_pytest_config_phase_apply_minversion",
    "test_ensure_pytest_config_phase_apply_python_classes",
    "test_ensure_table",
    "test_extract_dep_name",
    "test_extract_requirement_name",
    "test_flext_infra_pyproject_modernizer_find_pyproject_files",
    "test_flext_infra_pyproject_modernizer_process_file_invalid_toml",
    "test_helpers_alias_is_reachable_helpers",
    "test_helpers_alias_is_reachable_project_obj",
    "test_inject_comments_phase_apply_banner",
    "test_inject_comments_phase_apply_broken_group_section",
    "test_inject_comments_phase_apply_markers",
    "test_inject_comments_phase_apply_with_optional_dependencies_dev",
    "test_main_discovery_failure",
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
    "test_project_dev_groups",
    "test_project_dev_groups_missing_sections",
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
