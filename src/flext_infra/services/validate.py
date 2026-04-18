"""Public validation service mixin for the infra API facade."""

from __future__ import annotations

from flext_infra import (
    FlextInfraBaseMkValidator,
    FlextInfraInventoryService,
    FlextInfraPytestDiagExtractor,
    FlextInfraServiceCliRunnerMixin,
    FlextInfraSilentFailureValidator,
    FlextInfraSkillValidator,
    FlextInfraStubSupplyChain,
    FlextInfraTextPatternScanner,
    FlextInfraValidateFreshImport,
    FlextInfraValidateImportCycles,
    FlextInfraValidateLazyMapFreshness,
    FlextInfraValidateTierWhitelist,
    p,
    t,
)
from flext_infra.validate.metadata_discipline import (
    FlextInfraValidateMetadataDiscipline,
)


class FlextInfraServiceValidateMixin(FlextInfraServiceCliRunnerMixin):
    """Expose validation operations through the public infra facade."""

    def validate_basemk(self, params: FlextInfraBaseMkValidator) -> p.Result[bool]:
        """Validate base.mk state through the public facade."""
        return self._dispatch_result(params)

    def generate_inventory(self, params: FlextInfraInventoryService) -> p.Result[bool]:
        """Generate the validation inventory through the public facade."""
        return self._dispatch_result(params)

    def extract_pytest_diag(
        self,
        params: FlextInfraPytestDiagExtractor,
    ) -> p.Result[bool]:
        """Extract pytest diagnostics through the public facade."""
        return self._dispatch_result(params)

    def scan_text(self, params: FlextInfraTextPatternScanner) -> p.Result[bool]:
        """Run text pattern validation through the public facade."""
        return self._dispatch_result(params)

    def validate_skill(self, params: FlextInfraSkillValidator) -> p.Result[bool]:
        """Validate skills through the public facade."""
        return self._dispatch_result(params)

    def validate_silent_failure(
        self,
        params: FlextInfraSilentFailureValidator,
    ) -> p.Result[bool]:
        """Validate silent failure sentinels through the public facade."""
        return self._dispatch_result(params)

    def validate_stub_supply_chain(
        self,
        params: FlextInfraStubSupplyChain,
    ) -> p.Result[bool]:
        """Validate stub supply chains through the public facade."""
        return self._dispatch_result(params)

    def validate_fresh_import(
        self,
        params: FlextInfraValidateFreshImport,
    ) -> p.Result[bool]:
        """Guard 7: run the fresh-process import smoke through the public facade."""
        return self._dispatch_result(params)

    def validate_import_cycles(
        self,
        params: FlextInfraValidateImportCycles,
    ) -> p.Result[bool]:
        """Guard 1: run the ROPE-backed import-cycle detector through the public facade."""
        return self._dispatch_result(params)

    def validate_lazy_map_freshness(
        self,
        params: FlextInfraValidateLazyMapFreshness,
    ) -> p.Result[bool]:
        """Guard 2/3: run the lazy-map freshness validator through the public facade."""
        return self._dispatch_result(params)

    def validate_tier_whitelist(
        self,
        params: FlextInfraValidateTierWhitelist,
    ) -> p.Result[bool]:
        """Guard 5: run the tier-whitelist/abstraction-boundary enforcer through the public facade."""
        return self._dispatch_result(params)

    def validate_metadata_discipline(
        self,
        params: FlextInfraValidateMetadataDiscipline,
    ) -> p.Result[bool]:
        """Guard 8: enforce centralized metadata parser usage."""
        return self._dispatch_result(params)


__all__: t.StrSequence = ("FlextInfraServiceValidateMixin",)
