# AUTO-GENERATED FILE — Regenerate with: make gen
"""Flext Infra.codegen. Conform package."""

from __future__ import annotations

from types import MappingProxyType
from typing import TYPE_CHECKING

from flext_core.lazy import build_lazy_import_map, install_lazy_exports

if TYPE_CHECKING:
    from .base import FlextInfraCodegenConform
    from .bootstrap import FlextInfraCodegenConformBootstrap
    from .execute import FlextInfraCodegenConformExecute
    from .misc import FlextInfraCodegenConformMisc
    from .plan import FlextInfraCodegenConformPlan
    from .render import FlextInfraCodegenConformRender
__all__: tuple[str, ...] = (
    "FlextInfraCodegenConform",
    "FlextInfraCodegenConformBootstrap",
    "FlextInfraCodegenConformExecute",
    "FlextInfraCodegenConformMisc",
    "FlextInfraCodegenConformPlan",
    "FlextInfraCodegenConformRender",
)

_LAZY_IMPORTS = MappingProxyType(
    build_lazy_import_map(
        MappingProxyType({
            ".base": ("FlextInfraCodegenConform",),
            ".bootstrap": ("FlextInfraCodegenConformBootstrap",),
            ".execute": ("FlextInfraCodegenConformExecute",),
            ".misc": ("FlextInfraCodegenConformMisc",),
            ".plan": ("FlextInfraCodegenConformPlan",),
            ".render": ("FlextInfraCodegenConformRender",),
        }),
        alias_groups=MappingProxyType({}),
        sort_keys=False,
    )
)

install_lazy_exports(__name__, globals(), _LAZY_IMPORTS, public_exports=__all__)
