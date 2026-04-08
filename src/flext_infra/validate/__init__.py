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
}


install_lazy_exports(__name__, globals(), _LAZY_IMPORTS, publish_all=False)
