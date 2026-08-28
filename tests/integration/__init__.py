# AUTO-GENERATED FILE — Regenerate with: make gen
"""Tests.integration package."""

from __future__ import annotations

from typing import TYPE_CHECKING

from types import MappingProxyType

from flext_core.lazy import build_lazy_import_map, install_lazy_exports

if TYPE_CHECKING:
    from .docs_serve_e2e_tests import TestsFlextInfraIntegrationDocsServeE2e
    from .test_infra_integration import TestsFlextInfraIntegrationInfraIntegration
    from .test_refactor_nesting_file import (
        TestsFlextInfraIntegrationRefactorNestingFile,
    )
    from .test_refactor_nesting_idempotency import (
        TestsFlextInfraIntegrationRefactorNestingIdempotency,
    )
    from .test_refactor_nesting_performance import (
        TestsFlextInfraIntegrationRefactorNestingPerformance,
    )
    from .test_refactor_nesting_project import (
        TestsFlextInfraIntegrationRefactorNestingProject,
    )
    from .test_refactor_nesting_workspace import (
        TestsFlextInfraIntegrationRefactorNestingWorkspace,
    )
__all__: tuple[str, ...] = (
    "TestsFlextInfraIntegrationDocsServeE2e",
    "TestsFlextInfraIntegrationInfraIntegration",
    "TestsFlextInfraIntegrationRefactorNestingFile",
    "TestsFlextInfraIntegrationRefactorNestingIdempotency",
    "TestsFlextInfraIntegrationRefactorNestingPerformance",
    "TestsFlextInfraIntegrationRefactorNestingProject",
    "TestsFlextInfraIntegrationRefactorNestingWorkspace",
)

_LAZY_IMPORTS = MappingProxyType(
    build_lazy_import_map(
        MappingProxyType({
            ".docs_serve_e2e_tests": ("TestsFlextInfraIntegrationDocsServeE2e",),
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
        }),
        alias_groups=MappingProxyType({}),
        sort_keys=False,
    )
)

install_lazy_exports(__name__, globals(), _LAZY_IMPORTS, public_exports=__all__)
