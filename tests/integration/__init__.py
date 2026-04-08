# AUTO-GENERATED FILE — DO NOT EDIT MANUALLY.
# Regenerate with: make gen
#
"""Integration package."""

from __future__ import annotations

from flext_core.lazy import install_lazy_exports

_LAZY_IMPORTS = {
    "test_infra_integration": "tests.integration.test_infra_integration",
    "test_refactor_nesting_file": "tests.integration.test_refactor_nesting_file",
    "test_refactor_nesting_idempotency": "tests.integration.test_refactor_nesting_idempotency",
    "test_refactor_nesting_performance": "tests.integration.test_refactor_nesting_performance",
    "test_refactor_nesting_project": "tests.integration.test_refactor_nesting_project",
    "test_refactor_nesting_workspace": "tests.integration.test_refactor_nesting_workspace",
    "test_refactor_policy_mro": "tests.integration.test_refactor_policy_mro",
}


install_lazy_exports(__name__, globals(), _LAZY_IMPORTS, publish_all=False)
