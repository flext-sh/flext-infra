# AUTO-GENERATED FILE — Regenerate with: make gen
"""Basemk package."""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_core.lazy import build_lazy_import_map, install_lazy_exports

if TYPE_CHECKING:
    from tests.unit.basemk.test_generator import (
        TestsFlextInfraBasemkGenerator as TestsFlextInfraBasemkGenerator,
    )
    from tests.unit.basemk.test_generator_edge_cases import (
        TestsFlextInfraBasemkGeneratorEdgeCases as TestsFlextInfraBasemkGeneratorEdgeCases,
    )
    from tests.unit.basemk.test_init import (
        TestsFlextInfraBasemkInit as TestsFlextInfraBasemkInit,
    )
    from tests.unit.basemk.test_main import (
        TestsFlextInfraBasemkMain as TestsFlextInfraBasemkMain,
    )
    from tests.unit.basemk.test_make_contract import (
        TestsFlextInfraBasemkMakeContract as TestsFlextInfraBasemkMakeContract,
    )
    from tests.unit.basemk.test_renderer import (
        TestsFlextInfraBasemkRenderer as TestsFlextInfraBasemkRenderer,
    )
_LAZY_IMPORTS = build_lazy_import_map(
    {
        ".test_generator": ("TestsFlextInfraBasemkGenerator",),
        ".test_generator_edge_cases": ("TestsFlextInfraBasemkGeneratorEdgeCases",),
        ".test_init": ("TestsFlextInfraBasemkInit",),
        ".test_main": ("TestsFlextInfraBasemkMain",),
        ".test_make_contract": ("TestsFlextInfraBasemkMakeContract",),
        ".test_renderer": ("TestsFlextInfraBasemkRenderer",),
    },
)


install_lazy_exports(
    __name__,
    globals(),
    _LAZY_IMPORTS,
    publish_all=False,
)
