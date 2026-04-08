# AUTO-GENERATED FILE — DO NOT EDIT MANUALLY.
# Regenerate with: make gen
#
"""Validate package."""

from __future__ import annotations

from flext_core.lazy import install_lazy_exports

_LAZY_IMPORTS = {
    "FlextInfraBaseMkValidator": (
        "flext_infra.validate.basemk_validator",
        "FlextInfraBaseMkValidator",
    ),
    "FlextInfraCliValidate": ("flext_infra.validate.cli", "FlextInfraCliValidate"),
    "FlextInfraInventoryService": (
        "flext_infra.validate.inventory",
        "FlextInfraInventoryService",
    ),
    "FlextInfraNamespaceRules": (
        "flext_infra.validate.namespace_rules",
        "FlextInfraNamespaceRules",
    ),
    "FlextInfraNamespaceValidator": (
        "flext_infra.validate.namespace_validator",
        "FlextInfraNamespaceValidator",
    ),
    "FlextInfraPytestDiagExtractor": (
        "flext_infra.validate.pytest_diag",
        "FlextInfraPytestDiagExtractor",
    ),
    "FlextInfraSkillValidator": (
        "flext_infra.validate.skill_validator",
        "FlextInfraSkillValidator",
    ),
    "FlextInfraStubSupplyChain": (
        "flext_infra.validate.stub_chain",
        "FlextInfraStubSupplyChain",
    ),
    "FlextInfraTextPatternScanner": (
        "flext_infra.validate.scanner",
        "FlextInfraTextPatternScanner",
    ),
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


install_lazy_exports(__name__, globals(), _LAZY_IMPORTS, publish_all=False)
