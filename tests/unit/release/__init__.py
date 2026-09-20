# AUTO-GENERATED FILE — Regenerate with: make gen
"""Tests.unit.release package."""

from __future__ import annotations

from types import MappingProxyType
from typing import TYPE_CHECKING

from flext_core.lazy import build_lazy_import_map, install_lazy_exports

if TYPE_CHECKING:
    from .artifact_boundary_tests import TestsFlextInfraReleaseArchiveBoundary
    from .dependency_order_tests import TestsFlextInfraReleaseDependencyOrder
    from .orchestrator_publish_tests import TestsFlextInfraReleasePublish
    from .policy_fixture_root_tests import TestsFlextInfraReleasePolicyOwner
    from .protocol_tests import TestsFlextInfraReleaseProtocol
__all__: tuple[str, ...] = (
    "TestsFlextInfraReleaseArchiveBoundary", "TestsFlextInfraReleaseDependencyOrder", "TestsFlextInfraReleasePolicyOwner", "TestsFlextInfraReleaseProtocol",
    "TestsFlextInfraReleasePublish",
)

_LAZY_IMPORTS = MappingProxyType(
    build_lazy_import_map(
        MappingProxyType({
            ".artifact_boundary_tests": ("TestsFlextInfraReleaseArchiveBoundary",),
            ".dependency_order_tests": ("TestsFlextInfraReleaseDependencyOrder",),
            ".orchestrator_publish_tests": ("TestsFlextInfraReleasePublish",),
            ".policy_fixture_root_tests": ("TestsFlextInfraReleasePolicyOwner",),
            ".protocol_tests": ("TestsFlextInfraReleaseProtocol",),
        }),
        alias_groups=MappingProxyType({}),
        sort_keys=False,
    )
)

install_lazy_exports(__name__, globals(), _LAZY_IMPORTS, public_exports=__all__)
