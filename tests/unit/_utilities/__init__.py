# AUTO-GENERATED FILE — Regenerate with: make gen
"""Utilities package."""

from __future__ import annotations

from flext_core.lazy import build_lazy_import_map, install_lazy_exports

_LAZY_IMPORTS = build_lazy_import_map(
    {
        ".test_discovery_consolidated": (
            "TestsFlextInfraUtilitiesDiscoveryConsolidated",
        ),
        ".test_formatting": ("TestsFlextInfraUtilitiesFormattingRunRuffFix",),
        ".test_iteration": ("TestIterWorkspacePythonModules",),
        ".test_rope_hooks": (
            "test_run_rope_post_hooks_applies_mro_migration",
            "test_run_rope_post_hooks_dry_run_is_non_mutating",
        ),
        ".test_safety": (
            "TestSafetyCheckpoint",
            "TestSafetyRollback",
        ),
        ".test_scanning": ("TestScanModels",),
    },
)


install_lazy_exports(__name__, globals(), _LAZY_IMPORTS, publish_all=False)
