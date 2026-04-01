# AUTO-GENERATED FILE — DO NOT EDIT MANUALLY.
# Regenerate with: make gen
#
"""Discovery package."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import TYPE_CHECKING as _TYPE_CHECKING

from flext_core.lazy import install_lazy_exports

if _TYPE_CHECKING:
    from flext_core import FlextTypes

    from tests.unit.discovery.test_infra_discovery import *
    from tests.unit.discovery.test_infra_discovery_edge_cases import *

_LAZY_IMPORTS: Mapping[str, str | Sequence[str]] = {
    "TestFlextInfraDiscoveryService": "tests.unit.discovery.test_infra_discovery",
    "TestFlextInfraDiscoveryServiceUncoveredLines": "tests.unit.discovery.test_infra_discovery_edge_cases",
    "test_infra_discovery": "tests.unit.discovery.test_infra_discovery",
    "test_infra_discovery_edge_cases": "tests.unit.discovery.test_infra_discovery_edge_cases",
}


install_lazy_exports(__name__, globals(), _LAZY_IMPORTS)
