# AUTO-GENERATED FILE — Regenerate with: make gen
"""Tests.unit.deps package."""

from __future__ import annotations

from typing import TYPE_CHECKING

from types import MappingProxyType

from flext_core.lazy import build_lazy_import_map, install_lazy_exports

if TYPE_CHECKING:
    from flext_tests import c, d, e, h, m, p, r, s, t, td, tf, tk, tm, tv, u, x

    from .test_detection_classify import TestsFlextInfraDepsDetectionClassify
    from .test_detection_deptry import TestsFlextInfraDepsDetectionDeptry
    from .test_detection_discover import TestsFlextInfraDepsDetectionDiscover
    from .test_detection_models import TestsFlextInfraDepsDetectionModels
    from .test_detection_typings import TestsFlextInfraDepsDetectionTypings
    from .test_detection_typings_flow import TestsFlextInfraDepsDetectionTypingsFlow
    from .test_detection_uncovered import TestsFlextInfraDepsDetectionUncovered
    from .test_detector_detect import TestsFlextInfraDepsDetectorDetect
    from .test_detector_detect_failures import TestsFlextInfraDepsDetectorDetectFailures
    from .test_detector_init import TestsFlextInfraDepsDetectorInit
    from .test_detector_main import TestsFlextInfraDepsDetectorMain
    from .test_detector_models import TestsFlextInfraDepsDetectorModels
    from .test_detector_report import TestsFlextInfraDepsDetectorReport
    from .test_detector_report_flags import TestsFlextInfraDepsDetectorReportFlags
    from .test_extra_paths_manager import TestsFlextInfraExtraPathsManager
    from .test_extra_paths_search_paths import TestsFlextInfraExtraPathsSearchPaths
    from .test_extra_paths_sync import (
        TestsFlextInfraDepsExtraPathsSync,
        pyright_content,
    )
    from .test_init import TestsFlextInfraDepsInit
    from .test_main_dispatch import TestsFlextInfraDepsMainDispatch
    from .test_modernizer_comments import TestsFlextInfraDepsModernizerComments
    from .test_modernizer_consolidate import TestsFlextInfraDepsModernizerConsolidate
    from .test_modernizer_coverage import TestsFlextInfraDepsModernizerCoverage
    from .test_modernizer_helpers import TestsFlextInfraDepsModernizerHelpers, doc
    from .test_modernizer_main import TestsFlextInfraDepsModernizerMain
    from .test_modernizer_main_extra import TestsFlextInfraDepsModernizerMainExtra
    from .test_modernizer_mypy import TestsFlextInfraDepsModernizerMypy
    from .test_modernizer_pyrefly import TestsFlextInfraModernizerPyrefly
    from .test_modernizer_pyright import TestsFlextInfraDepsModernizerPyright
    from .test_modernizer_pytest import TestsFlextInfraDepsModernizerPytest
    from .test_modernizer_tooling import TestsFlextInfraDepsModernizerTooling
    from .test_modernizer_workspace import TestsFlextInfraDepsModernizerWorkspace
    from .test_pytest_fail_closed_config import TestsFlextInfraPytestFailClosedConfig
    from .test_pytest_timeout_config import TestsFlextInfraPytestTimeoutConfig
__all__: tuple[str, ...] = (
    "TestsFlextInfraDepsDetectionClassify",
    "TestsFlextInfraDepsDetectionDeptry",
    "TestsFlextInfraDepsDetectionDiscover",
    "TestsFlextInfraDepsDetectionModels",
    "TestsFlextInfraDepsDetectionTypings",
    "TestsFlextInfraDepsDetectionTypingsFlow",
    "TestsFlextInfraDepsDetectionUncovered",
    "TestsFlextInfraDepsDetectorDetect",
    "TestsFlextInfraDepsDetectorDetectFailures",
    "TestsFlextInfraDepsDetectorInit",
    "TestsFlextInfraDepsDetectorMain",
    "TestsFlextInfraDepsDetectorModels",
    "TestsFlextInfraDepsDetectorReport",
    "TestsFlextInfraDepsDetectorReportFlags",
    "TestsFlextInfraDepsExtraPathsSync",
    "TestsFlextInfraDepsInit",
    "TestsFlextInfraDepsMainDispatch",
    "TestsFlextInfraDepsModernizerComments",
    "TestsFlextInfraDepsModernizerConsolidate",
    "TestsFlextInfraDepsModernizerCoverage",
    "TestsFlextInfraDepsModernizerHelpers",
    "TestsFlextInfraDepsModernizerMain",
    "TestsFlextInfraDepsModernizerMainExtra",
    "TestsFlextInfraDepsModernizerMypy",
    "TestsFlextInfraDepsModernizerPyright",
    "TestsFlextInfraDepsModernizerPytest",
    "TestsFlextInfraDepsModernizerTooling",
    "TestsFlextInfraDepsModernizerWorkspace",
    "TestsFlextInfraExtraPathsManager",
    "TestsFlextInfraExtraPathsSearchPaths",
    "TestsFlextInfraModernizerPyrefly",
    "TestsFlextInfraPytestFailClosedConfig",
    "TestsFlextInfraPytestTimeoutConfig",
    "c",
    "d",
    "doc",
    "e",
    "h",
    "m",
    "p",
    "pyright_content",
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
)

_LAZY_IMPORTS = MappingProxyType(
    build_lazy_import_map(
        MappingProxyType({
            ".test_detection_classify": ("TestsFlextInfraDepsDetectionClassify",),
            ".test_detection_deptry": ("TestsFlextInfraDepsDetectionDeptry",),
            ".test_detection_discover": ("TestsFlextInfraDepsDetectionDiscover",),
            ".test_detection_models": ("TestsFlextInfraDepsDetectionModels",),
            ".test_detection_typings": ("TestsFlextInfraDepsDetectionTypings",),
            ".test_detection_typings_flow": (
                "TestsFlextInfraDepsDetectionTypingsFlow",
            ),
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
            ".test_extra_paths_search_paths": ("TestsFlextInfraExtraPathsSearchPaths",),
            ".test_extra_paths_sync": (
                "TestsFlextInfraDepsExtraPathsSync",
                "pyright_content",
            ),
            ".test_init": ("TestsFlextInfraDepsInit",),
            ".test_main_dispatch": ("TestsFlextInfraDepsMainDispatch",),
            ".test_modernizer_comments": ("TestsFlextInfraDepsModernizerComments",),
            ".test_modernizer_consolidate": (
                "TestsFlextInfraDepsModernizerConsolidate",
            ),
            ".test_modernizer_coverage": ("TestsFlextInfraDepsModernizerCoverage",),
            ".test_modernizer_helpers": ("TestsFlextInfraDepsModernizerHelpers", "doc"),
            ".test_modernizer_main": ("TestsFlextInfraDepsModernizerMain",),
            ".test_modernizer_main_extra": ("TestsFlextInfraDepsModernizerMainExtra",),
            ".test_modernizer_mypy": ("TestsFlextInfraDepsModernizerMypy",),
            ".test_modernizer_pyrefly": ("TestsFlextInfraModernizerPyrefly",),
            ".test_modernizer_pyright": ("TestsFlextInfraDepsModernizerPyright",),
            ".test_modernizer_pytest": ("TestsFlextInfraDepsModernizerPytest",),
            ".test_modernizer_tooling": ("TestsFlextInfraDepsModernizerTooling",),
            ".test_modernizer_workspace": ("TestsFlextInfraDepsModernizerWorkspace",),
            ".test_pytest_fail_closed_config": (
                "TestsFlextInfraPytestFailClosedConfig",
            ),
            ".test_pytest_timeout_config": ("TestsFlextInfraPytestTimeoutConfig",),
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
        }),
        alias_groups=MappingProxyType({}),
        sort_keys=False,
    )
)

install_lazy_exports(__name__, globals(), _LAZY_IMPORTS, public_exports=__all__)
