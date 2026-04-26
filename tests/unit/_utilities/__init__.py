# AUTO-GENERATED FILE — Regenerate with: make gen
"""Utilities package."""

from __future__ import annotations

from flext_core.lazy import build_lazy_import_map, install_lazy_exports

_LAZY_IMPORTS = build_lazy_import_map(
    {
        ".test_discovery_consolidated": (
            "TestsFlextInfraUtilitiesdiscoveryconsolidated",
        ),
        ".test_formatting": ("TestsFlextInfraUtilitiesformatting",),
        ".test_guard_gates": ("TestsFlextInfraUtilitiesGuardGates",),
        ".test_rope_hooks": ("TestsFlextInfraUtilitiesRopeHooks",),
        ".test_safety": ("TestsFlextInfraUtilitiessafety",),
        ".test_scanning": ("TestsFlextInfraUtilitiesscanning",),
        ".test_scope_selector": ("TestsFlextInfraUtilitiesScopeSelector",),
        ".test_snapshot": ("TestsFlextInfraUtilitiesSnapshot",),
    },
)


install_lazy_exports(__name__, globals(), _LAZY_IMPORTS, publish_all=False)
