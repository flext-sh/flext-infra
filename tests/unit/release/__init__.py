# AUTO-GENERATED FILE — Regenerate with: make gen
"""Tests.unit.release package."""

from __future__ import annotations

from types import MappingProxyType
from typing import TYPE_CHECKING

from flext_core.lazy import build_lazy_import_map, install_lazy_exports

if TYPE_CHECKING:
    from flext_tests import c, d, e, h, m, p, r, s, t, td, tf, tk, tm, tv, u, x

    from .artifact_boundary_tests import TestsFlextInfraReleaseArchiveBoundary
    from .dependency_order_tests import TestsFlextInfraReleaseDependencyOrder
    from .main_tests import TestsFlextInfraReleaseCli
    from .orchestrator_helpers_tests import TestsFlextInfraReleaseHelpers
    from .orchestrator_publish_tests import TestsFlextInfraReleasePublish
    from .policy_fixture_root_tests import TestsFlextInfraReleasePolicyOwner
    from .protocol_tests import TestsFlextInfraReleaseProtocol
    from .test_release_dag import TestsFlextInfraReleaseDag
__all__: tuple[str, ...] = (
    "TestsFlextInfraReleaseArchiveBoundary", "TestsFlextInfraReleaseCli", "TestsFlextInfraReleaseDag", "TestsFlextInfraReleaseDependencyOrder",
    "TestsFlextInfraReleaseHelpers", "TestsFlextInfraReleasePolicyOwner", "TestsFlextInfraReleaseProtocol", "TestsFlextInfraReleasePublish",
    "c", "d", "e", "h",
    "m", "p", "r", "s",
    "t", "td", "tf", "tk",
    "tm", "tv", "u", "x",
)

_LAZY_IMPORTS = MappingProxyType(
    build_lazy_import_map(
        MappingProxyType({
            ".artifact_boundary_tests": ("TestsFlextInfraReleaseArchiveBoundary",),
            ".dependency_order_tests": ("TestsFlextInfraReleaseDependencyOrder",),
            ".main_tests": ("TestsFlextInfraReleaseCli",),
            ".orchestrator_helpers_tests": ("TestsFlextInfraReleaseHelpers",),
            ".orchestrator_publish_tests": ("TestsFlextInfraReleasePublish",),
            ".policy_fixture_root_tests": ("TestsFlextInfraReleasePolicyOwner",),
            ".protocol_tests": ("TestsFlextInfraReleaseProtocol",),
            ".test_release_dag": ("TestsFlextInfraReleaseDag",),
            "flext_tests": (
                "c", "d", "e", "h", "m", "p", "r", "s", "t", "td", "tf", "tk", "tm",
                "tv", "u", "x",
            ),
        }),
        alias_groups=MappingProxyType({}),
        sort_keys=False,
    )
)

install_lazy_exports(__name__, globals(), _LAZY_IMPORTS, public_exports=__all__)
