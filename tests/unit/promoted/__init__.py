# AUTO-GENERATED FILE — Regenerate with: make gen
"""Tests.unit.promoted package."""

from __future__ import annotations

from types import MappingProxyType
from typing import TYPE_CHECKING

from flext_core.lazy import build_lazy_import_map, install_lazy_exports

if TYPE_CHECKING:
    from .test_execution_contract import TestsFlextInfraPromotedExecutionContract
    from .test_process_boundary import TestsFlextInfraPromotedProcessBoundary
__all__: tuple[str, ...] = (
    "TestsFlextInfraPromotedExecutionContract",
    "TestsFlextInfraPromotedProcessBoundary",
)

_LAZY_IMPORTS = MappingProxyType(
    build_lazy_import_map(
        MappingProxyType({
            ".test_execution_contract": ("TestsFlextInfraPromotedExecutionContract",),
            ".test_process_boundary": ("TestsFlextInfraPromotedProcessBoundary",),
        }),
        alias_groups=MappingProxyType({}),
        sort_keys=False,
    )
)

install_lazy_exports(__name__, globals(), _LAZY_IMPORTS, public_exports=__all__)
