# AUTO-GENERATED FILE — Regenerate with: make gen
"""Integration package."""

from __future__ import annotations

import typing as _t

from flext_core.lazy import build_lazy_import_map, install_lazy_exports

if _t.TYPE_CHECKING:
    from flext_tests import (
        c as c,
        d as d,
        e as e,
        h as h,
        m as m,
        p as p,
        r as r,
        s as s,
        t as t,
        td as td,
        tf as tf,
        tk as tk,
        tm as tm,
        tv as tv,
        u as u,
        x as x,
    )

    from tests.integration.test_infra_integration import (
        TestsFlextInfraIntegrationInfraIntegration as TestsFlextInfraIntegrationInfraIntegration,
    )
    from tests.integration.test_refactor_nesting_file import (
        TestsFlextInfraIntegrationRefactorNestingFile as TestsFlextInfraIntegrationRefactorNestingFile,
    )
    from tests.integration.test_refactor_nesting_idempotency import (
        TestsFlextInfraIntegrationRefactorNestingIdempotency as TestsFlextInfraIntegrationRefactorNestingIdempotency,
    )
    from tests.integration.test_refactor_nesting_performance import (
        TestsFlextInfraIntegrationRefactorNestingPerformance as TestsFlextInfraIntegrationRefactorNestingPerformance,
    )
    from tests.integration.test_refactor_nesting_project import (
        TestsFlextInfraIntegrationRefactorNestingProject as TestsFlextInfraIntegrationRefactorNestingProject,
    )
    from tests.integration.test_refactor_nesting_workspace import (
        TestsFlextInfraIntegrationRefactorNestingWorkspace as TestsFlextInfraIntegrationRefactorNestingWorkspace,
    )
    from tests.integration.test_refactor_policy_mro import (
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
        "flext_tests": (
            "c",
            "d",
            "e",
            "h",
            "m",
            "p",
            "r",
            "s",
            "t",
            "td",
            "tf",
            "tk",
            "tm",
            "tv",
            "u",
            "x",
        ),
    },
)


install_lazy_exports(__name__, globals(), _LAZY_IMPORTS, publish_all=False)
