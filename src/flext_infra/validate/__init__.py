# AUTO-GENERATED FILE — Regenerate with: make gen
"""Validate package."""

from __future__ import annotations

from flext_core.lazy import install_lazy_exports

_LAZY_IMPORTS = {
    "FlextInfraBaseMkValidator": ".basemk_validator",
    "FlextInfraCliValidate": ".cli",
    "FlextInfraInventoryService": ".inventory",
    "FlextInfraNamespaceRules": ".namespace_rules",
    "FlextInfraNamespaceValidator": ".namespace_validator",
    "FlextInfraPytestDiagExtractor": ".pytest_diag",
    "FlextInfraSkillValidator": ".skill_validator",
    "FlextInfraStubSupplyChain": ".stub_chain",
    "FlextInfraTextPatternScanner": ".scanner",
}


install_lazy_exports(__name__, globals(), _LAZY_IMPORTS, publish_all=False)
