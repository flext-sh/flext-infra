# AUTO-GENERATED FILE — DO NOT EDIT MANUALLY.
# Regenerate with: make gen
#
"""Basemk package."""

from __future__ import annotations

import typing as _t

from flext_core.lazy import install_lazy_exports

if _t.TYPE_CHECKING:
    import tests.unit.basemk.test_engine as _tests_unit_basemk_test_engine

    test_engine = _tests_unit_basemk_test_engine
    import tests.unit.basemk.test_generator as _tests_unit_basemk_test_generator
    from tests.unit.basemk.test_engine import basemk_main

    test_generator = _tests_unit_basemk_test_generator
    import tests.unit.basemk.test_generator_edge_cases as _tests_unit_basemk_test_generator_edge_cases

    test_generator_edge_cases = _tests_unit_basemk_test_generator_edge_cases
    import tests.unit.basemk.test_init as _tests_unit_basemk_test_init

    test_init = _tests_unit_basemk_test_init
    import tests.unit.basemk.test_main as _tests_unit_basemk_test_main

    test_main = _tests_unit_basemk_test_main
    import tests.unit.basemk.test_make_contract as _tests_unit_basemk_test_make_contract

    test_make_contract = _tests_unit_basemk_test_make_contract
    from flext_core.decorators import FlextDecorators as d
    from flext_core.exceptions import FlextExceptions as e
    from flext_core.handlers import FlextHandlers as h
    from flext_core.mixins import FlextMixins as x
    from flext_core.result import FlextResult as r
    from flext_core.service import FlextService as s
_LAZY_IMPORTS = {
    "basemk_main": ("tests.unit.basemk.test_engine", "basemk_main"),
    "d": ("flext_core.decorators", "FlextDecorators"),
    "e": ("flext_core.exceptions", "FlextExceptions"),
    "h": ("flext_core.handlers", "FlextHandlers"),
    "r": ("flext_core.result", "FlextResult"),
    "s": ("flext_core.service", "FlextService"),
    "test_engine": "tests.unit.basemk.test_engine",
    "test_generator": "tests.unit.basemk.test_generator",
    "test_generator_edge_cases": "tests.unit.basemk.test_generator_edge_cases",
    "test_init": "tests.unit.basemk.test_init",
    "test_main": "tests.unit.basemk.test_main",
    "test_make_contract": "tests.unit.basemk.test_make_contract",
    "x": ("flext_core.mixins", "FlextMixins"),
}

__all__ = [
    "basemk_main",
    "d",
    "e",
    "h",
    "r",
    "s",
    "test_engine",
    "test_generator",
    "test_generator_edge_cases",
    "test_init",
    "test_main",
    "test_make_contract",
    "x",
]


install_lazy_exports(__name__, globals(), _LAZY_IMPORTS)
