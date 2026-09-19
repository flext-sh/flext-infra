# AUTO-GENERATED FILE — Regenerate with: make gen
"""Tests.unit.deps package."""

from __future__ import annotations

from types import MappingProxyType
from typing import TYPE_CHECKING

from flext_core.lazy import build_lazy_import_map, install_lazy_exports

if TYPE_CHECKING:
    from .extra_paths_support import ExtraPathsTestSupport
    from .test_detection_typings import TestsFlextInfraDepsDetectionTypings
    from .test_detector_init import TestsFlextInfraDepsDetectorInit
    from .test_detector_main import TestsFlextInfraDepsDetectorMain
    from .test_detector_report import TestsFlextInfraDepsDetectorReport
    from .test_detector_report_flags import TestsFlextInfraDepsDetectorReportFlags
    from .test_extra_paths_sync import TestsFlextInfraDepsExtraPathsSync
    from .test_init import TestsFlextInfraDepsInit
    from .test_main_dispatch import TestsFlextInfraDepsMainDispatch
    from .test_modernizer_comments import TestsFlextInfraDepsModernizerComments
    from .test_modernizer_helpers import TestsFlextInfraDepsModernizerHelpers
    from .test_modernizer_packaging import TestsFlextInfraDepsModernizerPackaging
    from .test_modernizer_pyrefly import TestsFlextInfraModernizerPyrefly
    from .test_modernizer_pyright import TestsFlextInfraDepsModernizerPyright
    from .test_modernizer_tooling import TestsFlextInfraDepsModernizerTooling
    from .test_modernizer_workspace import TestsFlextInfraDepsModernizerWorkspace
    from .test_project_gitignore_patterns import TestsFlextInfraProjectGitignorePatterns
    from .test_project_mise_tools import TestsFlextInfraProjectMiseTools
__all__: tuple[str, ...] = (
    "ExtraPathsTestSupport",
    "TestsFlextInfraDepsDetectionTypings",
    "TestsFlextInfraDepsDetectorInit",
    "TestsFlextInfraDepsDetectorMain",
    "TestsFlextInfraDepsDetectorReport",
    "TestsFlextInfraDepsDetectorReportFlags",
    "TestsFlextInfraDepsExtraPathsSync",
    "TestsFlextInfraDepsInit",
    "TestsFlextInfraDepsMainDispatch",
    "TestsFlextInfraDepsModernizerComments",
    "TestsFlextInfraDepsModernizerHelpers",
    "TestsFlextInfraDepsModernizerPackaging",
    "TestsFlextInfraDepsModernizerPyright",
    "TestsFlextInfraDepsModernizerTooling",
    "TestsFlextInfraDepsModernizerWorkspace",
    "TestsFlextInfraModernizerPyrefly",
    "TestsFlextInfraProjectGitignorePatterns",
    "TestsFlextInfraProjectMiseTools",
)

_LAZY_IMPORTS = MappingProxyType(
    build_lazy_import_map(
        MappingProxyType({
            ".extra_paths_support": ("ExtraPathsTestSupport",),
            ".test_detection_typings": ("TestsFlextInfraDepsDetectionTypings",),
            ".test_detector_init": ("TestsFlextInfraDepsDetectorInit",),
            ".test_detector_main": ("TestsFlextInfraDepsDetectorMain",),
            ".test_detector_report": ("TestsFlextInfraDepsDetectorReport",),
            ".test_detector_report_flags": ("TestsFlextInfraDepsDetectorReportFlags",),
            ".test_extra_paths_sync": ("TestsFlextInfraDepsExtraPathsSync",),
            ".test_init": ("TestsFlextInfraDepsInit",),
            ".test_main_dispatch": ("TestsFlextInfraDepsMainDispatch",),
            ".test_modernizer_comments": ("TestsFlextInfraDepsModernizerComments",),
            ".test_modernizer_helpers": ("TestsFlextInfraDepsModernizerHelpers",),
            ".test_modernizer_packaging": ("TestsFlextInfraDepsModernizerPackaging",),
            ".test_modernizer_pyrefly": ("TestsFlextInfraModernizerPyrefly",),
            ".test_modernizer_pyright": ("TestsFlextInfraDepsModernizerPyright",),
            ".test_modernizer_tooling": ("TestsFlextInfraDepsModernizerTooling",),
            ".test_modernizer_workspace": ("TestsFlextInfraDepsModernizerWorkspace",),
            ".test_project_gitignore_patterns": (
                "TestsFlextInfraProjectGitignorePatterns",
            ),
            ".test_project_mise_tools": ("TestsFlextInfraProjectMiseTools",),
        }),
        alias_groups=MappingProxyType({}),
        sort_keys=False,
    )
)

install_lazy_exports(__name__, globals(), _LAZY_IMPORTS, public_exports=__all__)
