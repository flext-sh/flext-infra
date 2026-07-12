# AUTO-GENERATED FILE — Regenerate with: make gen
"""Tests.unit. Utilities package."""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_core.lazy import (
    build_lazy_import_map,
    install_lazy_exports,
)

# mro-i6nq.10: The package consumes its manifest's public-export contract.
from tests.unit._utilities.__unit__ import (
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
    from tests.unit._utilities.test_rope_analysis import (
        TestsFlextInfraRopeAnalysis as TestsFlextInfraRopeAnalysis,
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

    # mro-i6nq.10: Static declaration mirrors the installer-owned runtime binding.
    __all__: tuple[str, ...]

_LAZY_IMPORTS = build_lazy_import_map(
    _LAZY_MODULES,
    alias_groups=_LAZY_ALIAS_GROUPS,
    sort_keys=False,
)

# mro-i6nq.10: The installer publishes __all__ from the manifest's literal ABI.
install_lazy_exports(
    __name__,
    globals(),
    _LAZY_IMPORTS,
    public_exports=_PUBLIC_EXPORTS,
)
