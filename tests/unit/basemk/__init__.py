# AUTO-GENERATED FILE — Regenerate with: make gen
"""Basemk package."""

from __future__ import annotations

from flext_core.lazy import build_lazy_import_map, install_lazy_exports

_LAZY_IMPORTS = build_lazy_import_map(
    {
        ".test_engine": ("TestsFlextInfraBasemkEngine",),
        ".test_generator": ("TestsFlextInfraBasemkGenerator",),
        ".test_generator_edge_cases": ("TestsFlextInfraBasemkGeneratorEdgeCases",),
        ".test_init": ("TestsFlextInfraBasemkInit",),
        ".test_main": ("TestsFlextInfraBasemkMain",),
        ".test_make_contract": ("TestsFlextInfraBasemkMakeContract",),
    },
)


install_lazy_exports(__name__, globals(), _LAZY_IMPORTS, publish_all=False)
