# AUTO-GENERATED FILE — Regenerate with: make gen
"""Integration package."""

from __future__ import annotations

from flext_core.lazy import build_lazy_import_map, install_lazy_exports

_LAZY_IMPORTS = build_lazy_import_map(
    {
        ".test_infra_integration": ("TestsFlextInfraIntegrationInfraIntegration",),
        ".test_refactor_nesting_file": (
            "TestsFlextInfraIntegrationRefactorNestingFile",
        ),
        ".test_refactor_nesting_idempotency": (
            "TestsFlextInfraIntegrationRefactorNestingIdempotency",
        ),
        ".test_refactor_nesting_performance": (
            "TestsFlextInfraIntegrationRefactorNestingPerformance",
        ),
        ".test_refactor_nesting_project": (
            "TestsFlextInfraIntegrationRefactorNestingProject",
        ),
        ".test_refactor_nesting_workspace": (
            "TestsFlextInfraIntegrationRefactorNestingWorkspace",
        ),
        ".test_refactor_policy_mro": ("TestsFlextInfraIntegrationRefactorPolicyMro",),
    },
)


install_lazy_exports(__name__, globals(), _LAZY_IMPORTS, publish_all=False)
