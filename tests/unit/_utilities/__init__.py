# AUTO-GENERATED FILE — Regenerate with: make gen
"""Tests.unit. Utilities package."""

from __future__ import annotations

from typing import TYPE_CHECKING

from types import MappingProxyType

from flext_core.lazy import build_lazy_import_map, install_lazy_exports

if TYPE_CHECKING:
    from .test_formatting import TestsFlextInfraUtilitiesformatting
    from .test_git_facet_gitpython import TestsFlextInfraGitFacet
    from .test_protected_edit import TestsFlextInfraUtilitiesProtectedEdit
    from .test_resource_limits import TestsFlextInfraUtilitiesResourceLimits
    from .test_rope_analysis import TestsFlextInfraRopeAnalysis
    from .test_rope_structure import TestsFlextInfraRopeStructure
    from .test_safety import TestsFlextInfraUtilitiessafety
    from .test_scanning import TestsFlextInfraUtilitiesscanning
__all__: tuple[str, ...] = (
    "TestsFlextInfraGitFacet",
    "TestsFlextInfraRopeAnalysis",
    "TestsFlextInfraRopeStructure",
    "TestsFlextInfraUtilitiesProtectedEdit",
    "TestsFlextInfraUtilitiesResourceLimits",
    "TestsFlextInfraUtilitiesformatting",
    "TestsFlextInfraUtilitiessafety",
    "TestsFlextInfraUtilitiesscanning",
)

_LAZY_IMPORTS = MappingProxyType(
    build_lazy_import_map(
        MappingProxyType({
            ".test_formatting": ("TestsFlextInfraUtilitiesformatting",),
            ".test_git_facet_gitpython": ("TestsFlextInfraGitFacet",),
            ".test_protected_edit": ("TestsFlextInfraUtilitiesProtectedEdit",),
            ".test_resource_limits": ("TestsFlextInfraUtilitiesResourceLimits",),
            ".test_rope_analysis": ("TestsFlextInfraRopeAnalysis",),
            ".test_rope_structure": ("TestsFlextInfraRopeStructure",),
            ".test_safety": ("TestsFlextInfraUtilitiessafety",),
            ".test_scanning": ("TestsFlextInfraUtilitiesscanning",),
        }),
        alias_groups=MappingProxyType({}),
        sort_keys=False,
    )
)

install_lazy_exports(__name__, globals(), _LAZY_IMPORTS, public_exports=__all__)
