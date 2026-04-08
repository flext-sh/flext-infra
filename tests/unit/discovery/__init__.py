# AUTO-GENERATED FILE — DO NOT EDIT MANUALLY.
# Regenerate with: make gen
#
"""Discovery package."""

from __future__ import annotations

from flext_core.lazy import install_lazy_exports

_LAZY_IMPORTS = {
    "test_infra_discovery": "tests.unit.discovery.test_infra_discovery",
    "test_infra_discovery_edge_cases": "tests.unit.discovery.test_infra_discovery_edge_cases",
}


install_lazy_exports(__name__, globals(), _LAZY_IMPORTS, publish_all=False)
