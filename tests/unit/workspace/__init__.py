# AUTO-GENERATED FILE — Regenerate with: make gen
"""Workspace package."""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_core.lazy import build_lazy_import_map, install_lazy_exports

if TYPE_CHECKING:
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
_LAZY_IMPORTS = build_lazy_import_map(
    {
        ".make_constants_tests": ("make_constants_tests",),
        ".resolve_what_tests": ("resolve_what_tests",),
        ".test_main": ("TestsFlextInfraWorkspaceMain",),
        ".test_makefile_dry_run": ("TestsFlextInfraWorkspaceMakefileDryRun",),
        ".test_makefile_generator": ("TestsFlextInfraWorkspaceMakefileGenerator",),
        ".test_sync": ("TestsFlextInfraWorkspaceSync",),
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


install_lazy_exports(
    __name__,
    globals(),
    _LAZY_IMPORTS,
    publish_all=False,
)
