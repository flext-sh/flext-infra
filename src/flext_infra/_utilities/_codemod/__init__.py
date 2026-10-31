# AUTO-GENERATED FILE — Regenerate with: make gen
"""Flext Infra. Utilities. Codemod package.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from types import MappingProxyType
from typing import TYPE_CHECKING

from flext_core.lazy import install_lazy_exports

if TYPE_CHECKING:
    from flext_infra._utilities._codemod.binding_chain import (
        FlextInfraUtilitiesCodemodBindingChain,
    )
    from flext_infra._utilities._codemod.import_law_rules import (
        FlextInfraUtilitiesCodemodImportLawRules,
    )
    from flext_infra._utilities._codemod.native_cascade import (
        FlextInfraUtilitiesCodemodNativeCascade,
    )
    from flext_infra._utilities._codemod.native_package_utilities import (
        FlextInfraUtilitiesCodemodNativePackage,
    )
    from flext_infra._utilities._codemod.native_utilities import (
        FlextInfraUtilitiesCodemodNative,
    )
    from flext_infra._utilities._codemod.project import (
        FlextInfraUtilitiesCodemodProject,
    )
    from flext_infra._utilities._codemod.project_facts import (
        FlextInfraUtilitiesCodemodProjectFacts,
    )
    from flext_infra._utilities._codemod.rules import FlextInfraUtilitiesCodemodRules
    from flext_infra._utilities._codemod.rules_distributions import (
        FlextInfraUtilitiesCodemodRulesDistributions,
    )
    from flext_infra._utilities._codemod.scopes import FlextInfraUtilitiesCodemodScopes
    from flext_infra._utilities._codemod.type_set_rules import (
        FlextInfraUtilitiesCodemodTypeSetRules,
    )


__all__: tuple[str, ...] = (
    "FlextInfraUtilitiesCodemodBindingChain",
    "FlextInfraUtilitiesCodemodImportLawRules",
    "FlextInfraUtilitiesCodemodNative",
    "FlextInfraUtilitiesCodemodNativeCascade",
    "FlextInfraUtilitiesCodemodNativePackage",
    "FlextInfraUtilitiesCodemodProject",
    "FlextInfraUtilitiesCodemodProjectFacts",
    "FlextInfraUtilitiesCodemodRules",
    "FlextInfraUtilitiesCodemodRulesDistributions",
    "FlextInfraUtilitiesCodemodScopes",
    "FlextInfraUtilitiesCodemodTypeSetRules",
)

install_lazy_exports(
    __name__,
    globals(),
    MappingProxyType({
        "FlextInfraUtilitiesCodemodBindingChain": ".binding_chain",
        "FlextInfraUtilitiesCodemodImportLawRules": ".import_law_rules",
        "FlextInfraUtilitiesCodemodNativeCascade": ".native_cascade",
        "FlextInfraUtilitiesCodemodNativePackage": ".native_package_utilities",
        "FlextInfraUtilitiesCodemodNative": ".native_utilities",
        "FlextInfraUtilitiesCodemodProject": ".project",
        "FlextInfraUtilitiesCodemodProjectFacts": ".project_facts",
        "FlextInfraUtilitiesCodemodRules": ".rules",
        "FlextInfraUtilitiesCodemodRulesDistributions": ".rules_distributions",
        "FlextInfraUtilitiesCodemodScopes": ".scopes",
        "FlextInfraUtilitiesCodemodTypeSetRules": ".type_set_rules",
    }),
    public_exports=__all__,
)
