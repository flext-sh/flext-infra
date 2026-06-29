# AUTO-GENERATED FILE — Regenerate with: make gen
"""Deps package."""

from __future__ import annotations

import typing as _t

from flext_core.lazy import build_lazy_import_map, install_lazy_exports

if _t.TYPE_CHECKING:
    from flext_tests import (
        c as c,
        d as d,
        e as e,
        h as h,
        m as m,
        p as p,
        r as r,
        s as s,
        t as t,
        td as td,
        tf as tf,
        tk as tk,
        tm as tm,
        tv as tv,
        u as u,
        x as x,
    )

    from tests.unit.deps.test_detection_classify import (
        TestsFlextInfraDepsDetectionClassify as TestsFlextInfraDepsDetectionClassify,
    )
    from tests.unit.deps.test_detection_deptry import (
        TestsFlextInfraDepsDetectionDeptry as TestsFlextInfraDepsDetectionDeptry,
    )
    from tests.unit.deps.test_detection_discover import (
        TestsFlextInfraDepsDetectionDiscover as TestsFlextInfraDepsDetectionDiscover,
    )
    from tests.unit.deps.test_detection_models import (
        TestsFlextInfraDepsDetectionModels as TestsFlextInfraDepsDetectionModels,
    )
    from tests.unit.deps.test_detection_typings import (
        TestsFlextInfraDepsDetectionTypings as TestsFlextInfraDepsDetectionTypings,
    )
    from tests.unit.deps.test_detection_typings_flow import (
        TestsFlextInfraDepsDetectionTypingsFlow as TestsFlextInfraDepsDetectionTypingsFlow,
    )
    from tests.unit.deps.test_detection_uncovered import (
        TestsFlextInfraDepsDetectionUncovered as TestsFlextInfraDepsDetectionUncovered,
    )
    from tests.unit.deps.test_detector_detect import (
        TestsFlextInfraDepsDetectorDetect as TestsFlextInfraDepsDetectorDetect,
    )
    from tests.unit.deps.test_detector_detect_failures import (
        TestsFlextInfraDepsDetectorDetectFailures as TestsFlextInfraDepsDetectorDetectFailures,
    )
    from tests.unit.deps.test_detector_init import (
        TestsFlextInfraDepsDetectorInit as TestsFlextInfraDepsDetectorInit,
    )
    from tests.unit.deps.test_detector_main import (
        TestsFlextInfraDepsDetectorMain as TestsFlextInfraDepsDetectorMain,
    )
    from tests.unit.deps.test_detector_models import (
        TestsFlextInfraDepsDetectorModels as TestsFlextInfraDepsDetectorModels,
    )
    from tests.unit.deps.test_detector_report import (
        TestsFlextInfraDepsDetectorReport as TestsFlextInfraDepsDetectorReport,
    )
    from tests.unit.deps.test_detector_report_flags import (
        TestsFlextInfraDepsDetectorReportFlags as TestsFlextInfraDepsDetectorReportFlags,
    )
    from tests.unit.deps.test_extra_paths_manager import (
        TestsFlextInfraExtraPathsManager as TestsFlextInfraExtraPathsManager,
    )
    from tests.unit.deps.test_extra_paths_sync import (
        TestsFlextInfraDepsExtraPathsSync as TestsFlextInfraDepsExtraPathsSync,
    )
    from tests.unit.deps.test_init import (
        TestsFlextInfraDepsInit as TestsFlextInfraDepsInit,
    )
    from tests.unit.deps.test_internal_sync_discovery import (
        TestsFlextInfraDepsInternalSyncDiscovery as TestsFlextInfraDepsInternalSyncDiscovery,
    )
    from tests.unit.deps.test_internal_sync_discovery_edge import (
        TestsFlextInfraDepsInternalSyncDiscoveryEdge as TestsFlextInfraDepsInternalSyncDiscoveryEdge,
    )
    from tests.unit.deps.test_internal_sync_main import (
        TestsFlextInfraDepsInternalSyncMain as TestsFlextInfraDepsInternalSyncMain,
    )
    from tests.unit.deps.test_internal_sync_resolve import (
        TestsFlextInfraDepsInternalSyncResolve as TestsFlextInfraDepsInternalSyncResolve,
    )
    from tests.unit.deps.test_internal_sync_sync import (
        TestsFlextInfraDepsInternalSyncSync as TestsFlextInfraDepsInternalSyncSync,
    )
    from tests.unit.deps.test_internal_sync_sync_edge import (
        TestsFlextInfraDepsInternalSyncSyncEdge as TestsFlextInfraDepsInternalSyncSyncEdge,
    )
    from tests.unit.deps.test_internal_sync_sync_edge_more import (
        TestsFlextInfraDepsInternalSyncSyncEdgeMore as TestsFlextInfraDepsInternalSyncSyncEdgeMore,
    )
    from tests.unit.deps.test_internal_sync_update import (
        TestsFlextInfraDepsInternalSyncUpdate as TestsFlextInfraDepsInternalSyncUpdate,
    )
    from tests.unit.deps.test_internal_sync_update_checkout_edge import (
        TestsFlextInfraDepsInternalSyncUpdateCheckoutEdge as TestsFlextInfraDepsInternalSyncUpdateCheckoutEdge,
    )
    from tests.unit.deps.test_internal_sync_validation import (
        TestsFlextInfraDepsInternalSyncValidation as TestsFlextInfraDepsInternalSyncValidation,
    )
    from tests.unit.deps.test_internal_sync_workspace import (
        TestsFlextInfraDepsInternalSyncWorkspace as TestsFlextInfraDepsInternalSyncWorkspace,
    )
    from tests.unit.deps.test_main_dispatch import (
        TestsFlextInfraDepsMainDispatch as TestsFlextInfraDepsMainDispatch,
    )
    from tests.unit.deps.test_modernizer_comments import (
        TestsFlextInfraDepsModernizerComments as TestsFlextInfraDepsModernizerComments,
    )
    from tests.unit.deps.test_modernizer_consolidate import (
        TestsFlextInfraDepsModernizerConsolidate as TestsFlextInfraDepsModernizerConsolidate,
    )
    from tests.unit.deps.test_modernizer_coverage import (
        TestsFlextInfraDepsModernizerCoverage as TestsFlextInfraDepsModernizerCoverage,
    )
    from tests.unit.deps.test_modernizer_helpers import (
        TestsFlextInfraDepsModernizerHelpers as TestsFlextInfraDepsModernizerHelpers,
    )
    from tests.unit.deps.test_modernizer_main import (
        TestsFlextInfraDepsModernizerMain as TestsFlextInfraDepsModernizerMain,
    )
    from tests.unit.deps.test_modernizer_main_extra import (
        TestsFlextInfraDepsModernizerMainExtra as TestsFlextInfraDepsModernizerMainExtra,
    )
    from tests.unit.deps.test_modernizer_mypy import (
        TestsFlextInfraDepsModernizerMypy as TestsFlextInfraDepsModernizerMypy,
    )
    from tests.unit.deps.test_modernizer_pyrefly import (
        TestsFlextInfraModernizerPyrefly as TestsFlextInfraModernizerPyrefly,
    )
    from tests.unit.deps.test_modernizer_pyright import (
        TestsFlextInfraDepsModernizerPyright as TestsFlextInfraDepsModernizerPyright,
    )
    from tests.unit.deps.test_modernizer_pytest import (
        TestsFlextInfraDepsModernizerPytest as TestsFlextInfraDepsModernizerPytest,
    )
    from tests.unit.deps.test_modernizer_tooling import (
        TestsFlextInfraDepsModernizerTooling as TestsFlextInfraDepsModernizerTooling,
    )
    from tests.unit.deps.test_modernizer_workspace import (
        TestsFlextInfraDepsModernizerWorkspace as TestsFlextInfraDepsModernizerWorkspace,
    )
    from tests.unit.deps.test_path_sync_init import (
        TestsFlextInfraDepsPathSyncInit as TestsFlextInfraDepsPathSyncInit,
    )
    from tests.unit.deps.test_path_sync_main import (
        TestsFlextInfraDepsPathSyncMain as TestsFlextInfraDepsPathSyncMain,
    )
    from tests.unit.deps.test_path_sync_main_edges import (
        TestsFlextInfraDepsPathSyncMainEdges as TestsFlextInfraDepsPathSyncMainEdges,
    )
    from tests.unit.deps.test_path_sync_main_more import (
        TestsFlextInfraDepsPathSyncMainMore as TestsFlextInfraDepsPathSyncMainMore,
    )
    from tests.unit.deps.test_path_sync_main_project_obj import (
        TestsFlextInfraDepsPathSyncMainProjectObj as TestsFlextInfraDepsPathSyncMainProjectObj,
    )
    from tests.unit.deps.test_path_sync_rewrite_deps import (
        TestsFlextInfraDepsPathSyncRewriteDeps as TestsFlextInfraDepsPathSyncRewriteDeps,
    )
    from tests.unit.deps.test_path_sync_rewrite_pep621 import (
        TestsFlextInfraDepsPathSyncRewritePep621 as TestsFlextInfraDepsPathSyncRewritePep621,
    )
    from tests.unit.deps.test_path_sync_rewrite_poetry import (
        TestsFlextInfraDepsPathSyncRewritePoetry as TestsFlextInfraDepsPathSyncRewritePoetry,
    )
_LAZY_IMPORTS = build_lazy_import_map(
    {
        ".test_detection_classify": ("TestsFlextInfraDepsDetectionClassify",),
        ".test_detection_deptry": ("TestsFlextInfraDepsDetectionDeptry",),
        ".test_detection_discover": ("TestsFlextInfraDepsDetectionDiscover",),
        ".test_detection_models": ("TestsFlextInfraDepsDetectionModels",),
        ".test_detection_pip_check": ("test_detection_pip_check",),
        ".test_detection_typings": ("TestsFlextInfraDepsDetectionTypings",),
        ".test_detection_typings_flow": ("TestsFlextInfraDepsDetectionTypingsFlow",),
        ".test_detection_uncovered": ("TestsFlextInfraDepsDetectionUncovered",),
        ".test_detector_detect": ("TestsFlextInfraDepsDetectorDetect",),
        ".test_detector_detect_failures": (
            "TestsFlextInfraDepsDetectorDetectFailures",
        ),
        ".test_detector_init": ("TestsFlextInfraDepsDetectorInit",),
        ".test_detector_main": ("TestsFlextInfraDepsDetectorMain",),
        ".test_detector_models": ("TestsFlextInfraDepsDetectorModels",),
        ".test_detector_report": ("TestsFlextInfraDepsDetectorReport",),
        ".test_detector_report_flags": ("TestsFlextInfraDepsDetectorReportFlags",),
        ".test_extra_paths_manager": ("TestsFlextInfraExtraPathsManager",),
        ".test_extra_paths_sync": ("TestsFlextInfraDepsExtraPathsSync",),
        ".test_init": ("TestsFlextInfraDepsInit",),
        ".test_internal_sync_discovery": ("TestsFlextInfraDepsInternalSyncDiscovery",),
        ".test_internal_sync_discovery_edge": (
            "TestsFlextInfraDepsInternalSyncDiscoveryEdge",
        ),
        ".test_internal_sync_main": ("TestsFlextInfraDepsInternalSyncMain",),
        ".test_internal_sync_resolve": ("TestsFlextInfraDepsInternalSyncResolve",),
        ".test_internal_sync_sync": ("TestsFlextInfraDepsInternalSyncSync",),
        ".test_internal_sync_sync_edge": ("TestsFlextInfraDepsInternalSyncSyncEdge",),
        ".test_internal_sync_sync_edge_more": (
            "TestsFlextInfraDepsInternalSyncSyncEdgeMore",
        ),
        ".test_internal_sync_update": ("TestsFlextInfraDepsInternalSyncUpdate",),
        ".test_internal_sync_update_checkout_edge": (
            "TestsFlextInfraDepsInternalSyncUpdateCheckoutEdge",
        ),
        ".test_internal_sync_validation": (
            "TestsFlextInfraDepsInternalSyncValidation",
        ),
        ".test_internal_sync_workspace": ("TestsFlextInfraDepsInternalSyncWorkspace",),
        ".test_main_dispatch": ("TestsFlextInfraDepsMainDispatch",),
        ".test_modernizer_comments": ("TestsFlextInfraDepsModernizerComments",),
        ".test_modernizer_consolidate": ("TestsFlextInfraDepsModernizerConsolidate",),
        ".test_modernizer_coverage": ("TestsFlextInfraDepsModernizerCoverage",),
        ".test_modernizer_helpers": ("TestsFlextInfraDepsModernizerHelpers",),
        ".test_modernizer_main": ("TestsFlextInfraDepsModernizerMain",),
        ".test_modernizer_main_extra": ("TestsFlextInfraDepsModernizerMainExtra",),
        ".test_modernizer_mypy": ("TestsFlextInfraDepsModernizerMypy",),
        ".test_modernizer_pyrefly": ("TestsFlextInfraModernizerPyrefly",),
        ".test_modernizer_pyright": ("TestsFlextInfraDepsModernizerPyright",),
        ".test_modernizer_pytest": ("TestsFlextInfraDepsModernizerPytest",),
        ".test_modernizer_tooling": ("TestsFlextInfraDepsModernizerTooling",),
        ".test_modernizer_workspace": ("TestsFlextInfraDepsModernizerWorkspace",),
        ".test_path_sync_init": ("TestsFlextInfraDepsPathSyncInit",),
        ".test_path_sync_main": ("TestsFlextInfraDepsPathSyncMain",),
        ".test_path_sync_main_edges": ("TestsFlextInfraDepsPathSyncMainEdges",),
        ".test_path_sync_main_more": ("TestsFlextInfraDepsPathSyncMainMore",),
        ".test_path_sync_main_project_obj": (
            "TestsFlextInfraDepsPathSyncMainProjectObj",
        ),
        ".test_path_sync_rewrite_deps": ("TestsFlextInfraDepsPathSyncRewriteDeps",),
        ".test_path_sync_rewrite_pep621": ("TestsFlextInfraDepsPathSyncRewritePep621",),
        ".test_path_sync_rewrite_poetry": ("TestsFlextInfraDepsPathSyncRewritePoetry",),
        "flext_tests": (
            "c",
            "d",
            "e",
            "h",
            "m",
            "p",
            "r",
            "s",
            "t",
            "td",
            "tf",
            "tk",
            "tm",
            "tv",
            "u",
            "x",
        ),
    },
)


install_lazy_exports(__name__, globals(), _LAZY_IMPORTS, publish_all=False)
