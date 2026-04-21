# AUTO-GENERATED FILE — Regenerate with: make gen
"""Deps package."""

from __future__ import annotations

from flext_core.lazy import build_lazy_import_map, install_lazy_exports

_LAZY_IMPORTS = build_lazy_import_map(
    {
        ".test_detection_classify": (
            "TestBuildProjectReport",
            "TestClassifyIssues",
            "TestDetectionUncoveredLinesClassify",
        ),
        ".test_detection_deptry": (
            "TestDiscoverProjectPathsDeptry",
            "TestRunDeptry",
        ),
        ".test_detection_discover": ("TestDiscoverProjectPathsSelection",),
        ".test_detection_models": (
            "TestFlextInfraDependencyDetectionService",
            "TestFlextInfraModelsDependencyDetection",
            "TestToInfraValue",
        ),
        ".test_detection_pip_check": ("test_detection_pip_check",),
        ".test_detection_typings": (
            "TestLoadDependencyLimits",
            "TestRunMypyStubHints",
        ),
        ".test_detection_typings_flow": ("TestDetectionTypingsFlow",),
        ".test_detection_uncovered": ("TestDetectionUncoveredLines",),
        ".test_detector_detect": (
            "TestFlextInfraRuntimeDevDependencyDetectorRunDetect",
        ),
        ".test_detector_detect_failures": ("TestDetectorRunFailures",),
        ".test_detector_init": ("TestFlextInfraRuntimeDevDependencyDetectorInit",),
        ".test_detector_main": (
            "TestFlextInfraRuntimeDevDependencyDetectorRunTypings",
            "TestMainFunction",
        ),
        ".test_detector_models": ("TestFlextInfraModelsDependencyDetector",),
        ".test_detector_report": (
            "TestFlextInfraRuntimeDevDependencyDetectorRunReport",
        ),
        ".test_detector_report_flags": ("TestDetectorReportFlags",),
        ".test_extra_paths_manager": (
            "TestConstants",
            "TestFlextInfraExtraPathsManager",
            "TestSyncOne",
        ),
        ".test_extra_paths_sync": ("test_extra_paths_sync",),
        ".test_init": ("TestFlextInfraDeps",),
        ".test_internal_sync_discovery": (
            "TestCollectInternalDeps",
            "TestParseGitmodules",
            "TestParseRepoMap",
        ),
        ".test_internal_sync_discovery_edge": ("TestCollectInternalDepsEdgeCases",),
        ".test_internal_sync_main": ("TestMain",),
        ".test_internal_sync_resolve": ("test_internal_sync_resolve",),
        ".test_internal_sync_sync": ("TestSync",),
        ".test_internal_sync_sync_edge": ("TestSyncMethodEdgeCases",),
        ".test_internal_sync_sync_edge_more": ("TestSyncMethodEdgeCasesMore",),
        ".test_internal_sync_update": ("test_internal_sync_update",),
        ".test_internal_sync_update_checkout_edge": ("TestEnsureCheckoutEdgeCases",),
        ".test_internal_sync_validation": (
            "TestFlextInfraInternalDependencySyncService",
            "TestIsRelativeTo",
            "TestOwnerFromRemoteUrl",
            "TestResolveInternalRepoName",
            "TestValidateGitRefEdgeCases",
        ),
        ".test_internal_sync_workspace": ("test_internal_sync_workspace",),
        ".test_main": ("TestPublicDepsSurface",),
        ".test_main_dispatch": ("TestDepsGroupEntry",),
        ".test_modernizer_comments": ("TestInjectCommentsPhase",),
        ".test_modernizer_consolidate": ("TestConsolidateGroupsPhase",),
        ".test_modernizer_coverage": ("TestEnsureCoverageConfigPhase",),
        ".test_modernizer_helpers": ("test_modernizer_helpers",),
        ".test_modernizer_main": ("TestFlextInfraPyprojectModernizer",),
        ".test_modernizer_main_extra": ("TestFlextInfraPyprojectModernizerEdgeCases",),
        ".test_modernizer_mypy": ("TestDepsModernizerMypy",),
        ".test_modernizer_pyrefly": ("TestEnsurePyreflyConfigPhase",),
        ".test_modernizer_pyright": ("TestDepsModernizerPyright",),
        ".test_modernizer_pytest": ("TestEnsurePytestConfigPhase",),
        ".test_modernizer_tooling": ("TestDepsModernizerTooling",),
        ".test_modernizer_workspace": ("TestFlextInfraPyprojectModernizerWorkspace",),
        ".test_path_sync_init": (
            "TestDetectMode",
            "TestFlextInfraDependencyPathSync",
            "TestPathSyncEdgeCases",
        ),
        ".test_path_sync_main": ("test_path_sync_main",),
        ".test_path_sync_main_edges": ("test_path_sync_main_edges",),
        ".test_path_sync_main_more": ("test_path_sync_main_more",),
        ".test_path_sync_main_project_obj": ("test_path_sync_main_project_obj",),
        ".test_path_sync_rewrite_deps": ("TestRewriteDepPaths",),
        ".test_path_sync_rewrite_pep621": ("TestRewritePep621",),
        ".test_path_sync_rewrite_poetry": ("TestRewritePoetry",),
    },
)


install_lazy_exports(__name__, globals(), _LAZY_IMPORTS, publish_all=False)
