# AUTO-GENERATED FILE — DO NOT EDIT MANUALLY.
# Regenerate with: make gen
#
"""Core infrastructure services.

Provides foundational services for inventory management, validation rules,
base.mk sync checking, pytest diagnostics, pattern scanning, skill validation,
and stub supply chain management.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import TYPE_CHECKING

from flext_core.lazy import install_lazy_exports

if TYPE_CHECKING:
    from flext_infra.validate import (
        basemk_validator as basemk_validator,
        cli as cli,
        inventory as inventory,
        namespace_validator as namespace_validator,
        pytest_diag as pytest_diag,
        scanner as scanner,
        skill_validator as skill_validator,
        stub_chain as stub_chain,
    )
    from flext_infra.validate.basemk_validator import (
        FlextInfraBaseMkValidator as FlextInfraBaseMkValidator,
    )
    from flext_infra.validate.cli import FlextInfraCliValidate as FlextInfraCliValidate
    from flext_infra.validate.inventory import (
        FlextInfraInventoryService as FlextInfraInventoryService,
    )
    from flext_infra.validate.namespace_validator import (
        FlextInfraNamespaceValidator as FlextInfraNamespaceValidator,
    )
    from flext_infra.validate.pytest_diag import (
        FlextInfraPytestDiagExtractor as FlextInfraPytestDiagExtractor,
    )
    from flext_infra.validate.scanner import (
        FlextInfraTextPatternScanner as FlextInfraTextPatternScanner,
    )
    from flext_infra.validate.skill_validator import (
        FlextInfraSkillValidator as FlextInfraSkillValidator,
    )
    from flext_infra.validate.stub_chain import (
        FlextInfraStubSupplyChain as FlextInfraStubSupplyChain,
    )

_LAZY_IMPORTS: Mapping[str, Sequence[str]] = {
    "FlextInfraBaseMkValidator": [
        "flext_infra.validate.basemk_validator",
        "FlextInfraBaseMkValidator",
    ],
    "FlextInfraCliValidate": ["flext_infra.validate.cli", "FlextInfraCliValidate"],
    "FlextInfraInventoryService": [
        "flext_infra.validate.inventory",
        "FlextInfraInventoryService",
    ],
    "FlextInfraNamespaceValidator": [
        "flext_infra.validate.namespace_validator",
        "FlextInfraNamespaceValidator",
    ],
    "FlextInfraPytestDiagExtractor": [
        "flext_infra.validate.pytest_diag",
        "FlextInfraPytestDiagExtractor",
    ],
    "FlextInfraSkillValidator": [
        "flext_infra.validate.skill_validator",
        "FlextInfraSkillValidator",
    ],
    "FlextInfraStubSupplyChain": [
        "flext_infra.validate.stub_chain",
        "FlextInfraStubSupplyChain",
    ],
    "FlextInfraTextPatternScanner": [
        "flext_infra.validate.scanner",
        "FlextInfraTextPatternScanner",
    ],
    "basemk_validator": ["flext_infra.validate.basemk_validator", ""],
    "cli": ["flext_infra.validate.cli", ""],
    "inventory": ["flext_infra.validate.inventory", ""],
    "namespace_validator": ["flext_infra.validate.namespace_validator", ""],
    "pytest_diag": ["flext_infra.validate.pytest_diag", ""],
    "scanner": ["flext_infra.validate.scanner", ""],
    "skill_validator": ["flext_infra.validate.skill_validator", ""],
    "stub_chain": ["flext_infra.validate.stub_chain", ""],
}

_EXPORTS: Sequence[str] = [
    "FlextInfraBaseMkValidator",
    "FlextInfraCliValidate",
    "FlextInfraInventoryService",
    "FlextInfraNamespaceValidator",
    "FlextInfraPytestDiagExtractor",
    "FlextInfraSkillValidator",
    "FlextInfraStubSupplyChain",
    "FlextInfraTextPatternScanner",
    "basemk_validator",
    "cli",
    "inventory",
    "namespace_validator",
    "pytest_diag",
    "scanner",
    "skill_validator",
    "stub_chain",
]


install_lazy_exports(__name__, globals(), _LAZY_IMPORTS, _EXPORTS)
