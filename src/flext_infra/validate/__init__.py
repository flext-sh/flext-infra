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
    "cli": "flext_infra.validate.cli",
    "inventory": "flext_infra.validate.inventory",
    "namespace_rules": "flext_infra.validate.namespace_rules",
    "namespace_validator": "flext_infra.validate.namespace_validator",
    "pytest_diag": "flext_infra.validate.pytest_diag",
    "scanner": "flext_infra.validate.scanner",
    "skill_validator": "flext_infra.validate.skill_validator",
    "stub_chain": "flext_infra.validate.stub_chain",
}


install_lazy_exports(__name__, globals(), _LAZY_IMPORTS, publish_all=False)
