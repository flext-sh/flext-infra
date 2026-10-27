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
    from tests.unit.codemod.test_codemod_import_cycle_source_scan import (
        TestsFlextInfraCodemodImportCycleSourceScan,
    )
    from tests.unit.codemod.test_codemod_own_package_roles import (
        TestsFlextInfraCodemodOwnPackageRoles,
    )
    from tests.unit.codemod.test_codemod_own_package_scans import (
        TestsFlextInfraCodemodOwnPackageScans,
    )
    from tests.unit.codemod.test_concrete_mixin_shells import (
        TestsFlextInfraConcreteMixinShells,
    )
    from tests.unit.codemod.test_generated_module_utility import (
        TestsFlextInfraCodemodGeneratedModuleUtility,
    )
    from tests.unit.codemod.test_module_member_import_header import (
        TestsFlextInfraCodemodModuleMemberImportHeader,
    )


__all__: tuple[str, ...] = (
    "TestsFlextInfraCodemodGeneratedModuleUtility",
    "TestsFlextInfraCodemodImportCycleSourceScan",
    "TestsFlextInfraCodemodModuleMemberImportHeader",
    "TestsFlextInfraCodemodOwnPackageRoles",
    "TestsFlextInfraCodemodOwnPackageScans",
    "TestsFlextInfraConcreteMixinShells",
)

install_lazy_exports(
    __name__,
    globals(),
    MappingProxyType({
        "TestsFlextInfraCodemodGeneratedModuleUtility": (
            ".test_generated_module_utility"
        ),
        "TestsFlextInfraCodemodImportCycleSourceScan": (
            ".test_codemod_import_cycle_source_scan"
        ),
        "TestsFlextInfraCodemodModuleMemberImportHeader": (
            ".test_module_member_import_header"
        ),
        "TestsFlextInfraCodemodOwnPackageRoles": ".test_codemod_own_package_roles",
        "TestsFlextInfraCodemodOwnPackageScans": ".test_codemod_own_package_scans",
        "TestsFlextInfraConcreteMixinShells": ".test_concrete_mixin_shells",
    }),
    public_exports=__all__,
)
