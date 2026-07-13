# AUTO-GENERATED FILE — Regenerate with: make gen
"""Tests.unit.deps package."""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_core.lazy import build_lazy_import_map, install_lazy_exports

# mro-i6nq.10: The package consumes its manifest's public-export contract.
from tests.unit.deps.__unit__ import (
    LAZY_ALIAS_GROUPS as _LAZY_ALIAS_GROUPS,
    LAZY_MODULES as _LAZY_MODULES,
    PUBLIC_EXPORTS as _PUBLIC_EXPORTS,
)

if TYPE_CHECKING:
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

    from tests.unit.deps import test_detection_pip_check as test_detection_pip_check
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
    from tests.unit.deps.test_extra_paths_search_paths import (
        TestsFlextInfraExtraPathsSearchPaths as TestsFlextInfraExtraPathsSearchPaths,
    )
    from tests.unit.deps.test_extra_paths_sync import (
        TestsFlextInfraDepsExtraPathsSync as TestsFlextInfraDepsExtraPathsSync,
    )
    from tests.unit.deps.test_extra_paths_uv_sources import (
        TestsFlextInfraExtraPathsUvSources as TestsFlextInfraExtraPathsUvSources,
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

    # mro-i6nq.10: Static declaration mirrors the installer-owned runtime binding.
    __all__: tuple[str, ...]

_LAZY_IMPORTS = build_lazy_import_map(
    _LAZY_MODULES, alias_groups=_LAZY_ALIAS_GROUPS, sort_keys=False
)

# mro-i6nq.10: The installer publishes __all__ from the manifest's literal ABI.
install_lazy_exports(__name__, globals(), _LAZY_IMPORTS, public_exports=_PUBLIC_EXPORTS)
