# AUTO-GENERATED FILE — Regenerate with: make gen
"""Discovery package."""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_core.lazy import build_lazy_import_map, install_lazy_exports

if TYPE_CHECKING:
    from flext_infra.tests.unit.discovery.test_infra_discovery_edge_cases import (
        TestsFlextInfraDiscoveryInfraDiscoveryEdgeCases as TestsFlextInfraDiscoveryInfraDiscoveryEdgeCases,
    )
_LAZY_IMPORTS = build_lazy_import_map(
    {
        ".test_infra_discovery": ("test_infra_discovery",),
        ".test_infra_discovery_edge_cases": (
            "TestsFlextInfraDiscoveryInfraDiscoveryEdgeCases",
        ),
    },
)


install_lazy_exports(
    __name__,
    globals(),
    _LAZY_IMPORTS,
    publish_all=False,
)
