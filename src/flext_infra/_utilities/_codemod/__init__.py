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
    from flext_infra._utilities._codemod.codemod_binding_chain import (
        FlextInfraUtilitiesCodemodBindingChain,
    )
    from flext_infra._utilities._codemod.codemod_import_law_rules import (
        FlextInfraUtilitiesCodemodImportLawRules,
    )
    from flext_infra._utilities._codemod.codemod_native_cascade import (
        FlextInfraUtilitiesCodemodNativeCascade,
    )
    from flext_infra._utilities._codemod.codemod_native_package_utilities import (
        FlextInfraUtilitiesCodemodNativePackage,
    )
    from flext_infra._utilities._codemod.codemod_native_utilities import (
        FlextInfraUtilitiesCodemodNative,
    )
    from flext_infra._utilities._codemod.codemod_project import (
        FlextInfraUtilitiesCodemodProject,
    )
    from flext_infra._utilities._codemod.codemod_project_facts import (
        FlextInfraUtilitiesCodemodProjectFacts,
    )
    from flext_infra._utilities._codemod.codemod_rules import (
        FlextInfraUtilitiesCodemodRules,
    )
    from flext_infra._utilities._codemod.codemod_scopes import (
        FlextInfraUtilitiesCodemodScopes,
    )
    from flext_infra._utilities._codemod.codemod_type_set_rules import (
        FlextInfraUtilitiesCodemodTypeSetRules,
    )
    from flext_infra._utilities._codemod.rules_distributions import (
        FlextInfraUtilitiesCodemodRulesDistributions,
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
        "FlextInfraUtilitiesCodemodBindingChain": ".codemod_binding_chain",
        "FlextInfraUtilitiesCodemodImportLawRules": ".codemod_import_law_rules",
        "FlextInfraUtilitiesCodemodNativeCascade": ".codemod_native_cascade",
        "FlextInfraUtilitiesCodemodNativePackage": (
            ".codemod_native_package_utilities"
        ),
        "FlextInfraUtilitiesCodemodNative": ".codemod_native_utilities",
        "FlextInfraUtilitiesCodemodProject": ".codemod_project",
        "FlextInfraUtilitiesCodemodProjectFacts": ".codemod_project_facts",
        "FlextInfraUtilitiesCodemodRules": ".codemod_rules",
        "FlextInfraUtilitiesCodemodRulesDistributions": ".rules_distributions",
        "FlextInfraUtilitiesCodemodScopes": ".codemod_scopes",
        "FlextInfraUtilitiesCodemodTypeSetRules": ".codemod_type_set_rules",
    }),
    public_exports=__all__,
)
