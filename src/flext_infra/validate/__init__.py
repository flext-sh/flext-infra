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
        basemk_validator,
        cli,
        inventory,
        namespace_validator,
        pytest_diag,
        scanner,
        skill_validator,
        stub_chain,
    )
    from flext_infra.validate.basemk_validator import *
    from flext_infra.validate.cli import *
    from flext_infra.validate.inventory import *
    from flext_infra.validate.namespace_validator import *
    from flext_infra.validate.pytest_diag import *
    from flext_infra.validate.scanner import *
    from flext_infra.validate.skill_validator import *
    from flext_infra.validate.stub_chain import *

_LAZY_IMPORTS: Mapping[str, str | Sequence[str]] = {
    "FlextInfraBaseMkValidator": "flext_infra.validate.basemk_validator",
    "FlextInfraCliValidate": "flext_infra.validate.cli",
    "FlextInfraInventoryService": "flext_infra.validate.inventory",
    "FlextInfraNamespaceValidator": "flext_infra.validate.namespace_validator",
    "FlextInfraPytestDiagExtractor": "flext_infra.validate.pytest_diag",
    "FlextInfraSkillValidator": "flext_infra.validate.skill_validator",
    "FlextInfraStubSupplyChain": "flext_infra.validate.stub_chain",
    "FlextInfraTextPatternScanner": "flext_infra.validate.scanner",
    "basemk_validator": "flext_infra.validate.basemk_validator",
    "cli": "flext_infra.validate.cli",
    "inventory": "flext_infra.validate.inventory",
    "namespace_validator": "flext_infra.validate.namespace_validator",
    "pytest_diag": "flext_infra.validate.pytest_diag",
    "scanner": "flext_infra.validate.scanner",
    "skill_validator": "flext_infra.validate.skill_validator",
    "stub_chain": "flext_infra.validate.stub_chain",
}


install_lazy_exports(__name__, globals(), _LAZY_IMPORTS, sorted(_LAZY_IMPORTS))
