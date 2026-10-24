# AUTO-GENERATED FILE — Regenerate with: make gen
"""Tests.unit.codemod package.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from types import MappingProxyType
from typing import TYPE_CHECKING

from flext_core.lazy import install_lazy_exports

if TYPE_CHECKING:
    from tests.unit.codemod.test_generated_module_utility import (
        TestsFlextInfraCodemodGeneratedModuleUtility,
    )
    from tests.unit.codemod.test_module_member_import_header import (
        TestsFlextInfraCodemodModuleMemberImportHeader,
    )


__all__: tuple[str, ...] = (
    "TestsFlextInfraCodemodGeneratedModuleUtility",
    "TestsFlextInfraCodemodModuleMemberImportHeader",
)

install_lazy_exports(
    __name__,
    globals(),
    MappingProxyType({
        "TestsFlextInfraCodemodGeneratedModuleUtility": (
            ".test_generated_module_utility"
        ),
        "TestsFlextInfraCodemodModuleMemberImportHeader": (
            ".test_module_member_import_header"
        ),
    }),
    public_exports=__all__,
)
