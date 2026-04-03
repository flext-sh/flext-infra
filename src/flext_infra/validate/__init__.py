# AUTO-GENERATED FILE — DO NOT EDIT MANUALLY.
# Regenerate with: make gen
#
"""Validate package."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import TYPE_CHECKING as _TYPE_CHECKING

from flext_core.lazy import install_lazy_exports

if _TYPE_CHECKING:
    from flext_core import FlextTypes
    from flext_core.constants import FlextConstants as c
    from flext_core.decorators import FlextDecorators as d
    from flext_core.exceptions import FlextExceptions as e
    from flext_core.handlers import FlextHandlers as h
    from flext_core.mixins import FlextMixins as x
    from flext_core.models import FlextModels as m
    from flext_core.protocols import FlextProtocols as p
    from flext_core.result import FlextResult as r
    from flext_core.service import FlextService as s
    from flext_core.typings import FlextTypes as t
    from flext_core.utilities import FlextUtilities as u
    from flext_infra.validate import (
        _constants,
        _models,
        basemk_validator,
        cli,
        inventory,
        namespace_rules,
        namespace_validator,
        pytest_diag,
        scanner,
        skill_validator,
        stub_chain,
    )
    from flext_infra.validate._constants import (
        FlextInfraCoreConstants,
        FlextInfraSharedInfraConstants,
    )
    from flext_infra.validate._models import FlextInfraCoreModels
    from flext_infra.validate.basemk_validator import FlextInfraBaseMkValidator
    from flext_infra.validate.cli import FlextInfraCliValidate
    from flext_infra.validate.inventory import FlextInfraInventoryService
    from flext_infra.validate.namespace_rules import FlextInfraNamespaceRules
    from flext_infra.validate.namespace_validator import FlextInfraNamespaceValidator
    from flext_infra.validate.pytest_diag import FlextInfraPytestDiagExtractor
    from flext_infra.validate.scanner import FlextInfraTextPatternScanner
    from flext_infra.validate.skill_validator import FlextInfraSkillValidator
    from flext_infra.validate.stub_chain import FlextInfraStubSupplyChain

_LAZY_IMPORTS: FlextTypes.LazyImportIndex = {
    "FlextInfraBaseMkValidator": "flext_infra.validate.basemk_validator",
    "FlextInfraCliValidate": "flext_infra.validate.cli",
    "FlextInfraCoreConstants": "flext_infra.validate._constants",
    "FlextInfraCoreModels": "flext_infra.validate._models",
    "FlextInfraInventoryService": "flext_infra.validate.inventory",
    "FlextInfraNamespaceRules": "flext_infra.validate.namespace_rules",
    "FlextInfraNamespaceValidator": "flext_infra.validate.namespace_validator",
    "FlextInfraPytestDiagExtractor": "flext_infra.validate.pytest_diag",
    "FlextInfraSharedInfraConstants": "flext_infra.validate._constants",
    "FlextInfraSkillValidator": "flext_infra.validate.skill_validator",
    "FlextInfraStubSupplyChain": "flext_infra.validate.stub_chain",
    "FlextInfraTextPatternScanner": "flext_infra.validate.scanner",
    "_constants": "flext_infra.validate._constants",
    "_models": "flext_infra.validate._models",
    "basemk_validator": "flext_infra.validate.basemk_validator",
    "c": ("flext_core.constants", "FlextConstants"),
    "cli": "flext_infra.validate.cli",
    "d": ("flext_core.decorators", "FlextDecorators"),
    "e": ("flext_core.exceptions", "FlextExceptions"),
    "h": ("flext_core.handlers", "FlextHandlers"),
    "inventory": "flext_infra.validate.inventory",
    "m": ("flext_core.models", "FlextModels"),
    "namespace_rules": "flext_infra.validate.namespace_rules",
    "namespace_validator": "flext_infra.validate.namespace_validator",
    "p": ("flext_core.protocols", "FlextProtocols"),
    "pytest_diag": "flext_infra.validate.pytest_diag",
    "r": ("flext_core.result", "FlextResult"),
    "s": ("flext_core.service", "FlextService"),
    "scanner": "flext_infra.validate.scanner",
    "skill_validator": "flext_infra.validate.skill_validator",
    "stub_chain": "flext_infra.validate.stub_chain",
    "t": ("flext_core.typings", "FlextTypes"),
    "u": ("flext_core.utilities", "FlextUtilities"),
    "x": ("flext_core.mixins", "FlextMixins"),
}


install_lazy_exports(__name__, globals(), _LAZY_IMPORTS)
