# AUTO-GENERATED FILE — DO NOT EDIT MANUALLY.
# Regenerate with: make gen
#
"""Discovery package."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import TYPE_CHECKING

from flext_core.lazy import install_lazy_exports

if TYPE_CHECKING:
    from tests.unit.discovery import (
        test_infra_discovery as test_infra_discovery,
        test_infra_discovery_edge_cases as test_infra_discovery_edge_cases,
    )
    from tests.unit.discovery.test_infra_discovery import (
        TestFlextInfraDiscoveryService as TestFlextInfraDiscoveryService,
    )
    from tests.unit.discovery.test_infra_discovery_edge_cases import (
        TestFlextInfraDiscoveryServiceUncoveredLines as TestFlextInfraDiscoveryServiceUncoveredLines,
    )

_LAZY_IMPORTS: Mapping[str, Sequence[str]] = {
    "TestFlextInfraDiscoveryService": [
        "tests.unit.discovery.test_infra_discovery",
        "TestFlextInfraDiscoveryService",
    ],
    "TestFlextInfraDiscoveryServiceUncoveredLines": [
        "tests.unit.discovery.test_infra_discovery_edge_cases",
        "TestFlextInfraDiscoveryServiceUncoveredLines",
    ],
    "test_infra_discovery": ["tests.unit.discovery.test_infra_discovery", ""],
    "test_infra_discovery_edge_cases": [
        "tests.unit.discovery.test_infra_discovery_edge_cases",
        "",
    ],
}

_EXPORTS: Sequence[str] = [
    "TestFlextInfraDiscoveryService",
    "TestFlextInfraDiscoveryServiceUncoveredLines",
    "test_infra_discovery",
    "test_infra_discovery_edge_cases",
]


install_lazy_exports(__name__, globals(), _LAZY_IMPORTS, _EXPORTS)
