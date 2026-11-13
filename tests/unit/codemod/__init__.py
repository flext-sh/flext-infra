# AUTO-GENERATED FILE — Regenerate with: make gen
"""Tests.unit.codemod package.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_core.lazy import install_lazy_exports

if TYPE_CHECKING:
    from tests.unit.codemod.test_assertion_cutover import (
        TestsFlextInfraTestAssertionCutover,
    )
    from tests.unit.codemod.test_codemod_import_cycle_source_scan import (
        TestsFlextInfraCodemodImportCycleSourceScan,
    )
    from tests.unit.codemod.test_codemod_own_package_roles import (
        TestsFlextInfraCodemodOwnPackageRoles,
    )
    from tests.unit.codemod.test_codemod_own_package_scans import (
        TestsFlextInfraCodemodOwnPackageScans,
    )
    from tests.unit.codemod.test_compat_read_all_letters import (
        TestsFlextInfraCodemodCompatReadAllLetters,
    )
    from tests.unit.codemod.test_concrete_mixin_shells import (
        TestsFlextInfraConcreteMixinShells,
    )
    from tests.unit.codemod.test_deep_import_own_root import (
        TestsFlextInfraCodemodDeepImportOwnRoot,
    )
    from tests.unit.codemod.test_generated_module_utility import (
        TestsFlextInfraCodemodGeneratedModuleUtility,
    )
    from tests.unit.codemod.test_mod_selection_preflight import (
        TestsFlextInfraModSelectionPreflight,
    )
    from tests.unit.codemod.test_module_member_import_header import (
        TestsFlextInfraCodemodModuleMemberImportHeader,
    )
    from tests.unit.codemod.test_namespace_import_cutover import (
        TestsFlextInfraTestNamespaceImportCutover,
    )
    from tests.unit.codemod.test_promoted_header_migration import (
        TestsFlextInfraPromotedHeaderMigration,
    )
    from tests.unit.codemod.test_scan_cache_content_key import (
        TestsFlextInfraCodemodScanCacheContentKey,
    )


__all__: tuple[str, ...] = (
    "TestsFlextInfraCodemodCompatReadAllLetters",
    "TestsFlextInfraCodemodDeepImportOwnRoot",
    "TestsFlextInfraCodemodGeneratedModuleUtility",
    "TestsFlextInfraCodemodImportCycleSourceScan",
    "TestsFlextInfraCodemodModuleMemberImportHeader",
    "TestsFlextInfraCodemodOwnPackageRoles",
    "TestsFlextInfraCodemodOwnPackageScans",
    "TestsFlextInfraCodemodScanCacheContentKey",
    "TestsFlextInfraConcreteMixinShells",
    "TestsFlextInfraModSelectionPreflight",
    "TestsFlextInfraPromotedHeaderMigration",
    "TestsFlextInfraTestAssertionCutover",
    "TestsFlextInfraTestNamespaceImportCutover",
)

install_lazy_exports(
    __name__,
    globals(),
    {
        "TestsFlextInfraCodemodCompatReadAllLetters": ".test_compat_read_all_letters",
        "TestsFlextInfraCodemodDeepImportOwnRoot": ".test_deep_import_own_root",
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
        "TestsFlextInfraCodemodScanCacheContentKey": ".test_scan_cache_content_key",
        "TestsFlextInfraConcreteMixinShells": ".test_concrete_mixin_shells",
        "TestsFlextInfraModSelectionPreflight": ".test_mod_selection_preflight",
        "TestsFlextInfraPromotedHeaderMigration": ".test_promoted_header_migration",
        "TestsFlextInfraTestAssertionCutover": ".test_assertion_cutover",
        "TestsFlextInfraTestNamespaceImportCutover": ".test_namespace_import_cutover",
    },
    public_exports=__all__,
)
