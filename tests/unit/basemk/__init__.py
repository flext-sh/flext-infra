# AUTO-GENERATED FILE — DO NOT EDIT MANUALLY.
# Regenerate with: make gen
#
"""Basemk package."""

from __future__ import annotations

from flext_core.lazy import install_lazy_exports

_LAZY_IMPORTS = {
    "test_engine": "tests.unit.basemk.test_engine",
    "test_generator": "tests.unit.basemk.test_generator",
    "test_generator_edge_cases": "tests.unit.basemk.test_generator_edge_cases",
    "test_init": "tests.unit.basemk.test_init",
    "test_main": "tests.unit.basemk.test_main",
    "test_make_contract": "tests.unit.basemk.test_make_contract",
}


install_lazy_exports(__name__, globals(), _LAZY_IMPORTS, publish_all=False)
