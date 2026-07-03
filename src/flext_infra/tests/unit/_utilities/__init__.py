# AUTO-GENERATED FILE — Regenerate with: make gen
"""Utilities package."""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_core.lazy import build_lazy_import_map, install_lazy_exports

if TYPE_CHECKING:
    from flext_infra.tests.unit._utilities.test_discovery_consolidated import (
        TestsFlextInfraUtilitiesdiscoveryconsolidated as TestsFlextInfraUtilitiesdiscoveryconsolidated,
    )
    from flext_infra.tests.unit._utilities.test_formatting import (
        TestsFlextInfraUtilitiesformatting as TestsFlextInfraUtilitiesformatting,
    )
    from flext_infra.tests.unit._utilities.test_protected_edit import (
        TestsFlextInfraUtilitiesProtectedEdit as TestsFlextInfraUtilitiesProtectedEdit,
    )
    from flext_infra.tests.unit._utilities.test_rope_analysis import (
        TestsFlextInfraRopeAnalysis as TestsFlextInfraRopeAnalysis,
    )
    from flext_infra.tests.unit._utilities.test_rope_hooks import (
        TestsFlextInfraUtilitiesRopeHooks as TestsFlextInfraUtilitiesRopeHooks,
    )
    from flext_infra.tests.unit._utilities.test_safety import (
        TestsFlextInfraUtilitiessafety as TestsFlextInfraUtilitiessafety,
    )
    from flext_infra.tests.unit._utilities.test_scanning import (
        TestsFlextInfraUtilitiesscanning as TestsFlextInfraUtilitiesscanning,
    )
_LAZY_IMPORTS = build_lazy_import_map(
    {
        ".test_discovery_consolidated": (
            "TestsFlextInfraUtilitiesdiscoveryconsolidated",
        ),
        ".test_formatting": ("TestsFlextInfraUtilitiesformatting",),
        ".test_protected_edit": ("TestsFlextInfraUtilitiesProtectedEdit",),
        ".test_rope_analysis": ("TestsFlextInfraRopeAnalysis",),
        ".test_rope_hooks": ("TestsFlextInfraUtilitiesRopeHooks",),
        ".test_safety": ("TestsFlextInfraUtilitiessafety",),
        ".test_scanning": ("TestsFlextInfraUtilitiesscanning",),
    },
)


install_lazy_exports(
    __name__,
    globals(),
    _LAZY_IMPORTS,
    publish_all=False,
)
