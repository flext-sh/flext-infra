# AUTO-GENERATED FILE — DO NOT EDIT MANUALLY.
# Regenerate with: make gen
#
"""Integration package."""

from __future__ import annotations

import typing as _t

from flext_core.lazy import install_lazy_exports

if _t.TYPE_CHECKING:
    import tests.integration.test_infra_integration as _tests_integration_test_infra_integration

    test_infra_integration = _tests_integration_test_infra_integration
    import tests.integration.test_refactor_nesting_file as _tests_integration_test_refactor_nesting_file

    test_refactor_nesting_file = _tests_integration_test_refactor_nesting_file
    import tests.integration.test_refactor_nesting_idempotency as _tests_integration_test_refactor_nesting_idempotency

    test_refactor_nesting_idempotency = (
        _tests_integration_test_refactor_nesting_idempotency
    )
    import tests.integration.test_refactor_nesting_performance as _tests_integration_test_refactor_nesting_performance

    test_refactor_nesting_performance = (
        _tests_integration_test_refactor_nesting_performance
    )
    import tests.integration.test_refactor_nesting_project as _tests_integration_test_refactor_nesting_project

    test_refactor_nesting_project = _tests_integration_test_refactor_nesting_project
    import tests.integration.test_refactor_nesting_workspace as _tests_integration_test_refactor_nesting_workspace

    test_refactor_nesting_workspace = _tests_integration_test_refactor_nesting_workspace
    import tests.integration.test_refactor_policy_mro as _tests_integration_test_refactor_policy_mro

    test_refactor_policy_mro = _tests_integration_test_refactor_policy_mro
    from flext_core.decorators import FlextDecorators as d
    from flext_core.exceptions import FlextExceptions as e
    from flext_core.handlers import FlextHandlers as h
    from flext_core.mixins import FlextMixins as x
    from flext_core.result import FlextResult as r
    from flext_core.service import FlextService as s
_LAZY_IMPORTS = {
    "d": ("flext_core.decorators", "FlextDecorators"),
    "e": ("flext_core.exceptions", "FlextExceptions"),
    "h": ("flext_core.handlers", "FlextHandlers"),
    "r": ("flext_core.result", "FlextResult"),
    "s": ("flext_core.service", "FlextService"),
    "test_infra_integration": "tests.integration.test_infra_integration",
    "test_refactor_nesting_file": "tests.integration.test_refactor_nesting_file",
    "test_refactor_nesting_idempotency": "tests.integration.test_refactor_nesting_idempotency",
    "test_refactor_nesting_performance": "tests.integration.test_refactor_nesting_performance",
    "test_refactor_nesting_project": "tests.integration.test_refactor_nesting_project",
    "test_refactor_nesting_workspace": "tests.integration.test_refactor_nesting_workspace",
    "test_refactor_policy_mro": "tests.integration.test_refactor_policy_mro",
    "x": ("flext_core.mixins", "FlextMixins"),
}

__all__ = [
    "d",
    "e",
    "h",
    "r",
    "s",
    "test_infra_integration",
    "test_refactor_nesting_file",
    "test_refactor_nesting_idempotency",
    "test_refactor_nesting_performance",
    "test_refactor_nesting_project",
    "test_refactor_nesting_workspace",
    "test_refactor_policy_mro",
    "x",
]


install_lazy_exports(__name__, globals(), _LAZY_IMPORTS)
