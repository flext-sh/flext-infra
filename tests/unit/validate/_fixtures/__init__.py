# AUTO-GENERATED FILE — Regenerate with: make gen
"""Tests.unit.validate. Fixtures package."""

from __future__ import annotations

from types import MappingProxyType
from typing import TYPE_CHECKING

from flext_core.lazy import build_lazy_import_map, install_lazy_exports

if TYPE_CHECKING:
    from .assertions import TestsFlextInfraValidateAssertions
    from .base import TestsFlextInfraValidateNamespaceBase
    from .project import TestsFlextInfraNamespaceProjectFixture
__all__: tuple[str, ...] = (
    "TestsFlextInfraNamespaceProjectFixture",
    "TestsFlextInfraValidateAssertions",
    "TestsFlextInfraValidateNamespaceBase",
)

_LAZY_IMPORTS = MappingProxyType(
    build_lazy_import_map(
        MappingProxyType({
            ".assertions": ("TestsFlextInfraValidateAssertions",),
            ".base": ("TestsFlextInfraValidateNamespaceBase",),
            ".project": ("TestsFlextInfraNamespaceProjectFixture",),
        }),
        alias_groups=MappingProxyType({}),
        sort_keys=False,
    )
)

install_lazy_exports(__name__, globals(), _LAZY_IMPORTS, public_exports=__all__)
