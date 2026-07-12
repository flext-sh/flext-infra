# AUTO-GENERATED FILE — Regenerate with: make gen
"""Flext Infra.validate package."""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_core.lazy import (
    build_lazy_import_map,
    install_lazy_exports,
)

# mro-i6nq.10: The package consumes its manifest's public-export contract.
from flext_infra.validate.__unit__ import (
    LAZY_ALIAS_GROUPS as _LAZY_ALIAS_GROUPS,
    LAZY_MODULES as _LAZY_MODULES,
    PUBLIC_EXPORTS as _PUBLIC_EXPORTS,
)

if TYPE_CHECKING:
    from flext_infra.validate.basemk_validator import (
        FlextInfraBaseMkValidator as FlextInfraBaseMkValidator,
    )
    from flext_infra.validate.fresh_import import (
        FlextInfraValidateFreshImport as FlextInfraValidateFreshImport,
    )
    from flext_infra.validate.gate_contract import (
        FlextInfraGateContractValidator as FlextInfraGateContractValidator,
    )
    from flext_infra.validate.gate_contract_checks import (
        FlextInfraGateContractChecksMixin as FlextInfraGateContractChecksMixin,
    )
    from flext_infra.validate.gate_contract_content import (
        FlextInfraGateContractContentMixin as FlextInfraGateContractContentMixin,
    )
    from flext_infra.validate.gate_contract_models import (
        FlextInfraGateContractModels as FlextInfraGateContractModels,
    )
    from flext_infra.validate.gate_contract_report import (
        FlextInfraGateContractReportMixin as FlextInfraGateContractReportMixin,
    )
    from flext_infra.validate.gate_contract_scan import (
        FlextInfraGateContractScanMixin as FlextInfraGateContractScanMixin,
    )
    from flext_infra.validate.import_cycles import (
        FlextInfraValidateImportCycles as FlextInfraValidateImportCycles,
    )
    from flext_infra.validate.inventory import (
        FlextInfraInventoryService as FlextInfraInventoryService,
    )
    from flext_infra.validate.lazy_map_freshness import (
        FlextInfraValidateLazyMapFreshness as FlextInfraValidateLazyMapFreshness,
    )
    from flext_infra.validate.loc_delta import (
        FlextInfraLocDeltaValidator as FlextInfraLocDeltaValidator,
    )
    from flext_infra.validate.manual_command import (
        FlextInfraManualCommandValidator as FlextInfraManualCommandValidator,
    )
    from flext_infra.validate.metadata_discipline import (
        FlextInfraValidateMetadataDiscipline as FlextInfraValidateMetadataDiscipline,
    )
    from flext_infra.validate.namespace_rules import (
        FlextInfraNamespaceRules as FlextInfraNamespaceRules,
    )
    from flext_infra.validate.namespace_validator import (
        FlextInfraNamespaceValidator as FlextInfraNamespaceValidator,
    )
    from flext_infra.validate.pytest_diag import (
        FlextInfraPytestDiagExtractor as FlextInfraPytestDiagExtractor,
    )
    from flext_infra.validate.runtime_census import (
        FlextInfraRuntimeCensusValidator as FlextInfraRuntimeCensusValidator,
    )
    from flext_infra.validate.scanner import (
        FlextInfraTextPatternScanner as FlextInfraTextPatternScanner,
    )
    from flext_infra.validate.silent_failure import (
        FlextInfraSilentFailureValidator as FlextInfraSilentFailureValidator,
    )
    from flext_infra.validate.skill_validator import (
        FlextInfraSkillValidator as FlextInfraSkillValidator,
    )
    from flext_infra.validate.stub_chain import (
        FlextInfraStubSupplyChain as FlextInfraStubSupplyChain,
    )
    from flext_infra.validate.tier_whitelist import (
        FlextInfraValidateTierWhitelist as FlextInfraValidateTierWhitelist,
    )

    # mro-i6nq.10: Static declaration mirrors the installer-owned runtime binding.
    __all__: tuple[str, ...]

_LAZY_IMPORTS = build_lazy_import_map(
    _LAZY_MODULES,
    alias_groups=_LAZY_ALIAS_GROUPS,
    sort_keys=False,
)

# mro-i6nq.10: The installer publishes __all__ from the manifest's literal ABI.
install_lazy_exports(
    __name__,
    globals(),
    _LAZY_IMPORTS,
    public_exports=_PUBLIC_EXPORTS,
)
