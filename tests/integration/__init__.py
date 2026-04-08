# AUTO-GENERATED FILE — DO NOT EDIT MANUALLY.
# Regenerate with: make gen
#
"""Integration package."""

from __future__ import annotations

from flext_core.lazy import install_lazy_exports

_LAZY_IMPORTS = {
    "c": ("flext_core.constants", "FlextConstants"),
    "d": ("flext_core.decorators", "FlextDecorators"),
    "e": ("flext_core.exceptions", "FlextExceptions"),
    "h": ("flext_core.handlers", "FlextHandlers"),
    "m": ("flext_core.models", "FlextModels"),
    "p": ("flext_core.protocols", "FlextProtocols"),
    "r": ("flext_core.result", "FlextResult"),
    "s": ("flext_core.service", "FlextService"),
    "t": ("flext_core.typings", "FlextTypes"),
    "test_infra_integration": "tests.integration.test_infra_integration",
    "test_refactor_nesting_file": "tests.integration.test_refactor_nesting_file",
    "test_refactor_nesting_idempotency": "tests.integration.test_refactor_nesting_idempotency",
    "test_refactor_nesting_performance": "tests.integration.test_refactor_nesting_performance",
    "test_refactor_nesting_project": "tests.integration.test_refactor_nesting_project",
    "test_refactor_nesting_workspace": "tests.integration.test_refactor_nesting_workspace",
    "test_refactor_policy_mro": "tests.integration.test_refactor_policy_mro",
    "u": ("flext_core.utilities", "FlextUtilities"),
    "x": ("flext_core.mixins", "FlextMixins"),
}


install_lazy_exports(__name__, globals(), _LAZY_IMPORTS, publish_all=False)
