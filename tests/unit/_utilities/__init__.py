# AUTO-GENERATED FILE — Regenerate with: make gen
"""Utilities package."""

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

    from tests.unit._utilities.test_discovery_consolidated import (
        TestsFlextInfraUtilitiesdiscoveryconsolidated as TestsFlextInfraUtilitiesdiscoveryconsolidated,
    )
    from tests.unit._utilities.test_formatting import (
        TestsFlextInfraUtilitiesformatting as TestsFlextInfraUtilitiesformatting,
    )
    from tests.unit._utilities.test_protected_edit import (
        TestsFlextInfraUtilitiesProtectedEdit as TestsFlextInfraUtilitiesProtectedEdit,
    )
    from tests.unit._utilities.test_rope_hooks import (
        TestsFlextInfraUtilitiesRopeHooks as TestsFlextInfraUtilitiesRopeHooks,
    )
    from tests.unit._utilities.test_safety import (
        TestsFlextInfraUtilitiessafety as TestsFlextInfraUtilitiessafety,
    )
    from tests.unit._utilities.test_scanning import (
        TestsFlextInfraUtilitiesscanning as TestsFlextInfraUtilitiesscanning,
    )
_LAZY_IMPORTS = build_lazy_import_map(
    {
        ".test_discovery_consolidated": (
            "TestsFlextInfraUtilitiesdiscoveryconsolidated",
        ),
        ".test_formatting": ("TestsFlextInfraUtilitiesformatting",),
        ".test_protected_edit": ("TestsFlextInfraUtilitiesProtectedEdit",),
        ".test_rope_hooks": ("TestsFlextInfraUtilitiesRopeHooks",),
        ".test_safety": ("TestsFlextInfraUtilitiessafety",),
        ".test_scanning": ("TestsFlextInfraUtilitiesscanning",),
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
