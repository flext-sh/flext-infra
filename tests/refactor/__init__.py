# AUTO-GENERATED FILE — Regenerate with: make gen
"""Refactor package."""

from __future__ import annotations

import typing as _t

from flext_core.lazy import build_lazy_import_map, install_lazy_exports

if _t.TYPE_CHECKING:
    from flext_tests import (
        c,
        d,
        e,
        h,
        m,
        p,
        r,
        s,
        t,
        td as td,
        tf as tf,
        tk as tk,
        tm as tm,
        tv as tv,
        u,
        x,
    )

    from tests.refactor.test_rope_semantic import (
        TestsFlextInfraRefactorRopeSemantic as TestsFlextInfraRefactorRopeSemantic,
    )
    from tests.refactor.test_rope_stubs import (
        TestsFlextInfraRefactorRopeStubs as TestsFlextInfraRefactorRopeStubs,
    )
_LAZY_IMPORTS = build_lazy_import_map(
    {
        ".test_rope_semantic": ("TestsFlextInfraRefactorRopeSemantic",),
        ".test_rope_stubs": ("TestsFlextInfraRefactorRopeStubs",),
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
