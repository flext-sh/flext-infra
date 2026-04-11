# AUTO-GENERATED FILE — Regenerate with: make gen
"""Integration package."""

from __future__ import annotations

from flext_core.lazy import build_lazy_import_map, install_lazy_exports

_LAZY_IMPORTS = build_lazy_import_map(
    {
        ".test_infra_integration": ("test_infra_integration",),
        ".test_refactor_nesting_file": ("test_refactor_nesting_file",),
        ".test_refactor_nesting_idempotency": ("test_refactor_nesting_idempotency",),
        ".test_refactor_nesting_performance": ("test_refactor_nesting_performance",),
        ".test_refactor_nesting_project": ("test_refactor_nesting_project",),
        ".test_refactor_nesting_workspace": ("test_refactor_nesting_workspace",),
        ".test_refactor_policy_mro": ("test_refactor_policy_mro",),
    },
)


install_lazy_exports(__name__, globals(), _LAZY_IMPORTS, publish_all=False)
