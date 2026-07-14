# AUTO-GENERATED FILE — Regenerate with: make gen
"""Tests.unit.release package."""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_core.lazy import build_lazy_import_map, install_lazy_exports

# mro-i6nq.10: The package consumes its manifest's public-export contract.
from tests.unit.release.__unit__ import (
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

    from tests.unit.release import (
        flow_tests as flow_tests,
        main_tests as main_tests,
        orchestrator_git_tests as orchestrator_git_tests,
        orchestrator_helpers_tests as orchestrator_helpers_tests,
        orchestrator_publish_tests as orchestrator_publish_tests,
        orchestrator_tests as orchestrator_tests,
        version_resolution_tests as version_resolution_tests,
    )
    from tests.unit.release.test_release_dag import (
        TestsFlextInfraReleaseDag as TestsFlextInfraReleaseDag,
    )

    # mro-i6nq.10: Static declaration mirrors the installer-owned runtime binding.
    __all__: tuple[str, ...]

_LAZY_IMPORTS = build_lazy_import_map(
    _LAZY_MODULES, alias_groups=_LAZY_ALIAS_GROUPS, sort_keys=False
)

# mro-i6nq.10: The installer publishes __all__ from the manifest's literal ABI.
install_lazy_exports(__name__, globals(), _LAZY_IMPORTS, public_exports=_PUBLIC_EXPORTS)
