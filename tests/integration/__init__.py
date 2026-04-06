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
    from tests.integration.test_infra_integration import TestInfraIntegration

    test_refactor_nesting_file = _tests_integration_test_refactor_nesting_file
    import tests.integration.test_refactor_nesting_idempotency as _tests_integration_test_refactor_nesting_idempotency
    from tests.integration.test_refactor_nesting_file import (
        pytestmark,
        test_class_nesting_refactor_single_file_end_to_end,
    )

    test_refactor_nesting_idempotency = (
        _tests_integration_test_refactor_nesting_idempotency
    )
    import tests.integration.test_refactor_nesting_performance as _tests_integration_test_refactor_nesting_performance
    from tests.integration.test_refactor_nesting_idempotency import TestIdempotency

    test_refactor_nesting_performance = (
        _tests_integration_test_refactor_nesting_performance
    )
    import tests.integration.test_refactor_nesting_project as _tests_integration_test_refactor_nesting_project
    from tests.integration.test_refactor_nesting_performance import (
        TestPerformanceBenchmarks,
    )

    test_refactor_nesting_project = _tests_integration_test_refactor_nesting_project
    import tests.integration.test_refactor_nesting_workspace as _tests_integration_test_refactor_nesting_workspace
    from tests.integration.test_refactor_nesting_project import TestProjectLevelRefactor

    test_refactor_nesting_workspace = _tests_integration_test_refactor_nesting_workspace
    import tests.integration.test_refactor_policy_mro as _tests_integration_test_refactor_policy_mro
    from tests.integration.test_refactor_nesting_workspace import (
        TestWorkspaceLevelRefactor,
    )

    test_refactor_policy_mro = _tests_integration_test_refactor_policy_mro
    from tests.integration.test_refactor_policy_mro import TestRefactorPolicyMRO

    from flext_core.constants import FlextConstants as c
    from flext_core.decorators import FlextDecorators as d
    from flext_core.exceptions import FlextExceptions as e
    from flext_core.handlers import FlextHandlers as h
    from flext_core.mixins import FlextMixins as x
    from flext_core.models import FlextModels as m
    from flext_core.protocols import FlextProtocols as p
    from flext_core.result import FlextResult as r
    from flext_core.service import FlextService as s
    from flext_core.typings import FlextTypes as t
    from flext_core.utilities import FlextUtilities as u
_LAZY_IMPORTS = {
    "TestIdempotency": (
        "tests.integration.test_refactor_nesting_idempotency",
        "TestIdempotency",
    ),
    "TestInfraIntegration": (
        "tests.integration.test_infra_integration",
        "TestInfraIntegration",
    ),
    "TestPerformanceBenchmarks": (
        "tests.integration.test_refactor_nesting_performance",
        "TestPerformanceBenchmarks",
    ),
    "TestProjectLevelRefactor": (
        "tests.integration.test_refactor_nesting_project",
        "TestProjectLevelRefactor",
    ),
    "TestRefactorPolicyMRO": (
        "tests.integration.test_refactor_policy_mro",
        "TestRefactorPolicyMRO",
    ),
    "TestWorkspaceLevelRefactor": (
        "tests.integration.test_refactor_nesting_workspace",
        "TestWorkspaceLevelRefactor",
    ),
    "c": ("flext_core.constants", "FlextConstants"),
    "d": ("flext_core.decorators", "FlextDecorators"),
    "e": ("flext_core.exceptions", "FlextExceptions"),
    "h": ("flext_core.handlers", "FlextHandlers"),
    "m": ("flext_core.models", "FlextModels"),
    "p": ("flext_core.protocols", "FlextProtocols"),
    "pytestmark": ("tests.integration.test_refactor_nesting_file", "pytestmark"),
    "r": ("flext_core.result", "FlextResult"),
    "s": ("flext_core.service", "FlextService"),
    "t": ("flext_core.typings", "FlextTypes"),
    "test_class_nesting_refactor_single_file_end_to_end": (
        "tests.integration.test_refactor_nesting_file",
        "test_class_nesting_refactor_single_file_end_to_end",
    ),
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

__all__ = [
    "TestIdempotency",
    "TestInfraIntegration",
    "TestPerformanceBenchmarks",
    "TestProjectLevelRefactor",
    "TestRefactorPolicyMRO",
    "TestWorkspaceLevelRefactor",
    "c",
    "d",
    "e",
    "h",
    "m",
    "p",
    "pytestmark",
    "r",
    "s",
    "t",
    "test_class_nesting_refactor_single_file_end_to_end",
    "test_infra_integration",
    "test_refactor_nesting_file",
    "test_refactor_nesting_idempotency",
    "test_refactor_nesting_performance",
    "test_refactor_nesting_project",
    "test_refactor_nesting_workspace",
    "test_refactor_policy_mro",
    "u",
    "x",
]


install_lazy_exports(__name__, globals(), _LAZY_IMPORTS)
