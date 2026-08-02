# AUTO-GENERATED FILE — Regenerate with: make gen

"""Flext Infra.validate package."""

from __future__ import annotations
from flext_core.lazy import build_lazy_import_map, install_lazy_exports

_LAZY_MODULES: dict[str, tuple[str, ...]] = {
    ".cprofile_report": ("FlextInfraCProfileReport",),
    ".fresh_import": ("FlextInfraValidateFreshImport",),
    ".gate_contract": ("FlextInfraGateContractValidator",),
    ".gate_contract_checks": ("FlextInfraGateContractChecksMixin",),
    ".gate_contract_content": ("FlextInfraGateContractContentMixin",),
    ".gate_contract_models": ("FlextInfraGateContractModels",),
    ".gate_contract_report": ("FlextInfraGateContractReportMixin",),
    ".gate_contract_scan": ("FlextInfraGateContractScanMixin",),
    ".import_cycles": ("FlextInfraValidateImportCycles",),
    ".inventory": ("FlextInfraInventoryService",),
    ".lazy_map_freshness": ("FlextInfraValidateLazyMapFreshness",),
    ".loc_delta": ("FlextInfraLocDeltaValidator",),
    ".manual_command": ("FlextInfraManualCommandValidator",),
    ".metadata_discipline": ("FlextInfraValidateMetadataDiscipline",),
    ".namespace_rules": ("FlextInfraNamespaceRules",),
    ".namespace_validator": ("FlextInfraNamespaceValidator",),
    ".pytest_diag": ("FlextInfraPytestDiagExtractor",),
    ".pytest_runner": ("FlextInfraPytestRunner",),
    ".pytest_selector": ("FlextInfraPytestSelectorValidator",),
    ".runtime_census": ("FlextInfraRuntimeCensusValidator",),
    ".scanner": ("FlextInfraTextPatternScanner",),
    ".silent_failure": ("FlextInfraSilentFailureValidator",),
    ".skill_validator": ("FlextInfraSkillValidator",),
    ".stub_chain": ("FlextInfraStubSupplyChain",),
    ".tier_whitelist": ("FlextInfraValidateTierWhitelist",),
}

_LAZY_ALIAS_GROUPS: dict[str, tuple[tuple[str, str], ...]] = {}

_LAZY_IMPORTS = build_lazy_import_map(
    _LAZY_MODULES, alias_groups=_LAZY_ALIAS_GROUPS, sort_keys=False
)

__all__: tuple[str, ...] = ()

install_lazy_exports(__name__, globals(), _LAZY_IMPORTS, public_exports=__all__)
