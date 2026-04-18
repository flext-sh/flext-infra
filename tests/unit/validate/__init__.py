# AUTO-GENERATED FILE — Regenerate with: make gen
"""Validate package."""

from __future__ import annotations

from flext_core.lazy import build_lazy_import_map, install_lazy_exports

_LAZY_IMPORTS = build_lazy_import_map(
    {
        ".basemk_validator_tests": ("basemk_validator_tests",),
        ".fresh_import_tests": ("fresh_import_tests",),
        ".import_cycles_tests": ("import_cycles_tests",),
        ".init_tests": ("init_tests",),
        ".inventory_tests": ("inventory_tests",),
        ".lazy_map_freshness_tests": ("lazy_map_freshness_tests",),
        ".main_cli_tests": ("TestValidateCli",),
        ".main_tests": ("main_tests",),
        ".namespace_validator_tests": ("TestFlextInfraNamespaceValidator",),
        ".pytest_diag": ("pytest_diag",),
        ".scanner_tests": ("scanner_tests",),
        ".silent_failure_tests": ("silent_failure_tests",),
        ".skill_validator_tests": ("skill_validator_tests",),
        ".stub_chain_tests": ("stub_chain_tests",),
    },
)


install_lazy_exports(__name__, globals(), _LAZY_IMPORTS, publish_all=False)
