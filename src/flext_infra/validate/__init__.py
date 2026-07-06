# AUTO-GENERATED FILE — Regenerate with: make gen
"""Validate package."""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_core.lazy import build_lazy_import_map, install_lazy_exports

if TYPE_CHECKING:
    from flext_infra.validate.basemk_validator import FlextInfraBaseMkValidator
    from flext_infra.validate.fresh_import import FlextInfraValidateFreshImport
    from flext_infra.validate.gate_contract import FlextInfraGateContractValidator
    from flext_infra.validate.gate_contract_checks import (
        FlextInfraGateContractChecksMixin,
    )
    from flext_infra.validate.gate_contract_content import (
        FlextInfraGateContractContentMixin,
    )
    from flext_infra.validate.gate_contract_models import FlextInfraGateContractModels
    from flext_infra.validate.gate_contract_report import (
        FlextInfraGateContractReportMixin,
    )
    from flext_infra.validate.gate_contract_scan import FlextInfraGateContractScanMixin
    from flext_infra.validate.import_cycles import FlextInfraValidateImportCycles
    from flext_infra.validate.inventory import FlextInfraInventoryService
    from flext_infra.validate.lazy_map_freshness import (
        FlextInfraValidateLazyMapFreshness,
    )
    from flext_infra.validate.loc_delta import FlextInfraLocDeltaValidator
    from flext_infra.validate.manual_command import FlextInfraManualCommandValidator
    from flext_infra.validate.metadata_discipline import (
        FlextInfraValidateMetadataDiscipline,
    )
    from flext_infra.validate.namespace_rules import FlextInfraNamespaceRules
    from flext_infra.validate.namespace_validator import FlextInfraNamespaceValidator
    from flext_infra.validate.pytest_diag import FlextInfraPytestDiagExtractor
    from flext_infra.validate.runtime_census import FlextInfraRuntimeCensusValidator
    from flext_infra.validate.scanner import FlextInfraTextPatternScanner
    from flext_infra.validate.silent_failure import FlextInfraSilentFailureValidator
    from flext_infra.validate.skill_validator import FlextInfraSkillValidator
    from flext_infra.validate.stub_chain import FlextInfraStubSupplyChain
    from flext_infra.validate.tier_whitelist import FlextInfraValidateTierWhitelist
_LAZY_IMPORTS = build_lazy_import_map(
    {
        ".basemk_validator": ("FlextInfraBaseMkValidator",),
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
        ".runtime_census": ("FlextInfraRuntimeCensusValidator",),
        ".scanner": ("FlextInfraTextPatternScanner",),
        ".silent_failure": ("FlextInfraSilentFailureValidator",),
        ".skill_validator": ("FlextInfraSkillValidator",),
        ".stub_chain": ("FlextInfraStubSupplyChain",),
        ".tier_whitelist": ("FlextInfraValidateTierWhitelist",),
    },
)


install_lazy_exports(
    __name__,
    globals(),
    _LAZY_IMPORTS,
    publish_all=False,
)
