# AUTO-GENERATED FILE — Regenerate with: make gen
"""Tests.refactor package."""

from __future__ import annotations

from typing import TYPE_CHECKING

from types import MappingProxyType

from flext_core.lazy import build_lazy_import_map, install_lazy_exports

if TYPE_CHECKING:
    from .test_rope_semantic import TestsFlextInfraRefactorRopeSemantic
    from .test_rope_stubs import TestsFlextInfraRefactorRopeStubs
__all__: tuple[str, ...] = (
    "TestsFlextInfraRefactorRopeSemantic",
    "TestsFlextInfraRefactorRopeStubs",
)

_LAZY_IMPORTS = MappingProxyType(
    build_lazy_import_map(
        MappingProxyType({
            ".test_rope_semantic": ("TestsFlextInfraRefactorRopeSemantic",),
            ".test_rope_stubs": ("TestsFlextInfraRefactorRopeStubs",),
        }),
        alias_groups=MappingProxyType({}),
        sort_keys=False,
    )
)

install_lazy_exports(__name__, globals(), _LAZY_IMPORTS, public_exports=__all__)
