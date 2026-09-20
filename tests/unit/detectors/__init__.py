# AUTO-GENERATED FILE — Regenerate with: make gen
"""Tests.unit.detectors package."""

from __future__ import annotations

from types import MappingProxyType
from typing import TYPE_CHECKING

from flext_core.lazy import build_lazy_import_map, install_lazy_exports

if TYPE_CHECKING:
    from .test_cyclic_import_detector import TestsFlextInfraCyclicImportDetector
    from .test_deferred_self_reference_ast import (
        TestsFlextInfraDeferredSelfReferenceDetector,
    )
__all__: tuple[str, ...] = (
    "TestsFlextInfraCyclicImportDetector", "TestsFlextInfraDeferredSelfReferenceDetector",
)

_LAZY_IMPORTS = MappingProxyType(
    build_lazy_import_map(
        MappingProxyType({
            ".test_cyclic_import_detector": ("TestsFlextInfraCyclicImportDetector",),
            ".test_deferred_self_reference_ast": (
                "TestsFlextInfraDeferredSelfReferenceDetector",
            ),
        }),
        alias_groups=MappingProxyType({}),
        sort_keys=False,
    )
)

install_lazy_exports(__name__, globals(), _LAZY_IMPORTS, public_exports=__all__)
