# AUTO-GENERATED FILE — Regenerate with: make gen
"""Flext Infra. Utilities. Rope package."""

from __future__ import annotations

from types import MappingProxyType
from typing import TYPE_CHECKING

from flext_core.lazy import build_lazy_import_map, install_lazy_exports

if TYPE_CHECKING:
    from .pep695_patch import FlextInfraUtilitiesRopePep695Patch
    from .project import FlextInfraRopeProject
    from .signature_patch import FlextInfraUtilitiesRopeSignaturePatch


__all__: tuple[str, ...] = (
    "FlextInfraRopeProject",
    "FlextInfraUtilitiesRopePep695Patch",
    "FlextInfraUtilitiesRopeSignaturePatch",
)

_LAZY_IMPORTS = MappingProxyType(
    build_lazy_import_map(
        MappingProxyType({
            ".pep695_patch": ("FlextInfraUtilitiesRopePep695Patch",),
            ".project": ("FlextInfraRopeProject",),
            ".signature_patch": ("FlextInfraUtilitiesRopeSignaturePatch",),
        }),
        alias_groups=MappingProxyType({}),
        sort_keys=False,
    )
)

install_lazy_exports(__name__, globals(), _LAZY_IMPORTS, public_exports=__all__)
