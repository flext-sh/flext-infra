# AUTO-GENERATED FILE — Regenerate with: make gen
"""Workspace package."""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_core.lazy import build_lazy_import_map, install_lazy_exports

# mro-i6nq.10: The package consumes its manifest's public-export contract.
from tests.unit.workspace.__unit__ import (
    LAZY_ALIAS_GROUPS as _LAZY_ALIAS_GROUPS,
    LAZY_MODULES as _LAZY_MODULES,
    PUBLIC_EXPORTS as _PUBLIC_EXPORTS,
)

if TYPE_CHECKING:
    from flext_tests import (
        c as c,
        d as d,
        e as e,
        h as h,
        m as m,
        p,
        r as r,
        s as s,
        t as t,
        td as td,
        tf as tf,
        tk as tk,
        tm as tm,
        tv as tv,
        u,
        x as x,
    )

    from tests.unit.workspace import (
        make_constants_tests as make_constants_tests,
        resolve_what_tests as resolve_what_tests,
    )
    from tests.unit.workspace.test_main import (
        TestsFlextInfraWorkspaceMain as TestsFlextInfraWorkspaceMain,
    )
    from tests.unit.workspace.test_makefile_dry_run import (
        TestsFlextInfraWorkspaceMakefileDryRun as TestsFlextInfraWorkspaceMakefileDryRun,
    )
    from tests.unit.workspace.test_makefile_generator import (
        TestsFlextInfraWorkspaceMakefileGenerator as TestsFlextInfraWorkspaceMakefileGenerator,
    )
    from tests.unit.workspace.test_sync import (
        TestsFlextInfraWorkspaceSync as TestsFlextInfraWorkspaceSync,
    )
    from tests.unit.workspace.test_sync_environment import (
        TestsFlextInfraWorkspaceSyncEnvironment as TestsFlextInfraWorkspaceSyncEnvironment,
    )

__all__: tuple[str, ...] = (
    "TestsFlextInfraWorkspaceMain",
    "TestsFlextInfraWorkspaceMakefileDryRun",
    "TestsFlextInfraWorkspaceMakefileGenerator",
    "TestsFlextInfraWorkspaceSync",
    "TestsFlextInfraWorkspaceSyncEnvironment",
)
