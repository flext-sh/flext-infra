# AUTO-GENERATED FILE — Regenerate with: make gen
"""Validate package."""

from __future__ import annotations

from flext_core.lazy import build_lazy_import_map, install_lazy_exports

_LAZY_IMPORTS = build_lazy_import_map(
    {
        ".basemk_validator": ("FlextInfraBaseMkValidator",),
        ".fresh_import": ("FlextInfraValidateFreshImport",),
        ".import_cycles": ("FlextInfraValidateImportCycles",),
        ".inventory": ("FlextInfraInventoryService",),
        ".lazy_map_freshness": ("FlextInfraValidateLazyMapFreshness",),
        ".metadata_discipline": ("FlextInfraValidateMetadataDiscipline",),
        ".namespace_rules": ("FlextInfraNamespaceRules",),
        ".namespace_validator": ("FlextInfraNamespaceValidator",),
        ".pytest_diag": ("FlextInfraPytestDiagExtractor",),
        ".scanner": ("FlextInfraTextPatternScanner",),
        ".silent_failure": ("FlextInfraSilentFailureValidator",),
        ".skill_validator": ("FlextInfraSkillValidator",),
        ".stub_chain": ("FlextInfraStubSupplyChain",),
        ".tier_whitelist": ("FlextInfraValidateTierWhitelist",),
    },
)


install_lazy_exports(__name__, globals(), _LAZY_IMPORTS, publish_all=False)
