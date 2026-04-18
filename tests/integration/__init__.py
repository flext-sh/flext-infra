# AUTO-GENERATED FILE — Regenerate with: make gen
"""Integration package."""

from __future__ import annotations

from flext_core.lazy import build_lazy_import_map, install_lazy_exports

_LAZY_IMPORTS = build_lazy_import_map(
    {
        ".test_infra_integration": ("TestInfraIntegration",),
        ".test_refactor_nesting_file": ("test_refactor_nesting_file",),
        ".test_refactor_nesting_idempotency": ("TestIdempotency",),
        ".test_refactor_nesting_performance": ("TestPerformanceBenchmarks",),
        ".test_refactor_nesting_project": ("TestProjectLevelRefactor",),
        ".test_refactor_nesting_workspace": ("TestWorkspaceLevelRefactor",),
        ".test_refactor_policy_mro": ("TestRefactorPolicyMRO",),
    },
)


install_lazy_exports(__name__, globals(), _LAZY_IMPORTS, publish_all=False)
