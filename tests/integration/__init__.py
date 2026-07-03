# AUTO-GENERATED FILE — Regenerate with: make gen
"""Integration package."""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_core.lazy import build_lazy_import_map, install_lazy_exports

if TYPE_CHECKING:
    from flext_infra.tests.integration.test_infra_integration import (
        TestsFlextInfraIntegrationInfraIntegration as TestsFlextInfraIntegrationInfraIntegration,
    )
    from flext_infra.tests.integration.test_refactor_nesting_file import (
        TestsFlextInfraIntegrationRefactorNestingFile as TestsFlextInfraIntegrationRefactorNestingFile,
    )
    from flext_infra.tests.integration.test_refactor_nesting_idempotency import (
        TestsFlextInfraIntegrationRefactorNestingIdempotency as TestsFlextInfraIntegrationRefactorNestingIdempotency,
    )
    from flext_infra.tests.integration.test_refactor_nesting_performance import (
        TestsFlextInfraIntegrationRefactorNestingPerformance as TestsFlextInfraIntegrationRefactorNestingPerformance,
    )
    from flext_infra.tests.integration.test_refactor_nesting_project import (
        TestsFlextInfraIntegrationRefactorNestingProject as TestsFlextInfraIntegrationRefactorNestingProject,
    )
    from flext_infra.tests.integration.test_refactor_nesting_workspace import (
        TestsFlextInfraIntegrationRefactorNestingWorkspace as TestsFlextInfraIntegrationRefactorNestingWorkspace,
    )
    from flext_infra.tests.integration.test_refactor_policy_mro import (
        TestsFlextInfraIntegrationRefactorPolicyMro as TestsFlextInfraIntegrationRefactorPolicyMro,
    )
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


install_lazy_exports(
    __name__,
    globals(),
    _LAZY_IMPORTS,
    publish_all=False,
)
