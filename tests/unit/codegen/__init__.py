# AUTO-GENERATED FILE — Regenerate with: make gen
"""Tests.unit.codegen package."""

from __future__ import annotations

from types import MappingProxyType
from typing import TYPE_CHECKING

from flext_core.lazy import build_lazy_import_map, install_lazy_exports

if TYPE_CHECKING:
    from .test_codegen_make_authentication import (
        TestsFlextInfraCodegenMakeAuthentication,
    )
    from .test_codegen_make_gate_suspensions import (
        TestsFlextInfraCodegenMakeGateSuspensions,
    )
    from .test_codegen_make_lock_contract import TestsFlextInfraCodegenMakeLockContract
    from .test_codegen_upg_workspace import TestsFlextInfraCodegenUpgWorkspace


__all__: tuple[str, ...] = (
    "TestsFlextInfraCodegenMakeAuthentication",
    "TestsFlextInfraCodegenMakeGateSuspensions",
    "TestsFlextInfraCodegenMakeLockContract",
    "TestsFlextInfraCodegenUpgWorkspace",
)

_LAZY_IMPORTS = MappingProxyType(
    build_lazy_import_map(
        MappingProxyType({
            ".test_codegen_make_authentication": (
                "TestsFlextInfraCodegenMakeAuthentication",
            ),
            ".test_codegen_make_gate_suspensions": (
                "TestsFlextInfraCodegenMakeGateSuspensions",
            ),
            ".test_codegen_make_lock_contract": (
                "TestsFlextInfraCodegenMakeLockContract",
            ),
            ".test_codegen_upg_workspace": ("TestsFlextInfraCodegenUpgWorkspace",),
        }),
        alias_groups=MappingProxyType({}),
        sort_keys=False,
    )
)

install_lazy_exports(__name__, globals(), _LAZY_IMPORTS, public_exports=__all__)
