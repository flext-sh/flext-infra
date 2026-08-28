# AUTO-GENERATED FILE — Regenerate with: make gen
"""Tests.unit.basemk package."""

from __future__ import annotations

from typing import TYPE_CHECKING

from types import MappingProxyType

from flext_core.lazy import build_lazy_import_map, install_lazy_exports

if TYPE_CHECKING:
    from flext_tests import c, d, e, h, m, p, r, s, t, td, tf, tk, tm, tv, u, x

    from .test_bootstrap_refname_safety import TestsBootstrapRefnameSafety
    from .test_builtin_handlers_derive_from_ssot import (
        test_every_invoked_handler_is_declared_in_the_ssot,
        test_every_routed_handler_is_defined,
        test_routing_declares_one_allowed_whats_per_verb,
    )
    from .test_generator import TestsFlextInfraBasemkGenerator
    from .test_generator_edge_cases import TestsFlextInfraBasemkGeneratorEdgeCases
    from .test_init import TestsFlextInfraBasemkInit
    from .test_main import TestsFlextInfraBasemkMain, basemk_main
    from .test_make_contract import TestsFlextInfraBasemkMakeContract
    from .test_renderer import TestsFlextInfraBasemkRenderer
__all__: tuple[str, ...] = (
    "TestsBootstrapRefnameSafety",
    "TestsFlextInfraBasemkGenerator",
    "TestsFlextInfraBasemkGeneratorEdgeCases",
    "TestsFlextInfraBasemkInit",
    "TestsFlextInfraBasemkMain",
    "TestsFlextInfraBasemkMakeContract",
    "TestsFlextInfraBasemkRenderer",
    "basemk_main",
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
    "test_every_invoked_handler_is_declared_in_the_ssot",
    "test_every_routed_handler_is_defined",
    "test_routing_declares_one_allowed_whats_per_verb",
    "tf",
    "tk",
    "tm",
    "tv",
    "u",
    "x",
)

_LAZY_IMPORTS = MappingProxyType(
    build_lazy_import_map(
        MappingProxyType({
            ".test_bootstrap_refname_safety": ("TestsBootstrapRefnameSafety",),
            ".test_builtin_handlers_derive_from_ssot": (
                "test_every_invoked_handler_is_declared_in_the_ssot",
                "test_every_routed_handler_is_defined",
                "test_routing_declares_one_allowed_whats_per_verb",
            ),
            ".test_generator": ("TestsFlextInfraBasemkGenerator",),
            ".test_generator_edge_cases": ("TestsFlextInfraBasemkGeneratorEdgeCases",),
            ".test_init": ("TestsFlextInfraBasemkInit",),
            ".test_main": ("TestsFlextInfraBasemkMain", "basemk_main"),
            ".test_make_contract": ("TestsFlextInfraBasemkMakeContract",),
            ".test_renderer": ("TestsFlextInfraBasemkRenderer",),
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
        }),
        alias_groups=MappingProxyType({}),
        sort_keys=False,
    )
)

install_lazy_exports(__name__, globals(), _LAZY_IMPORTS, public_exports=__all__)
