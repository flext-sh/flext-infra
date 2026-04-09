"""Public validation service mixin for the infra API facade."""

from __future__ import annotations

from collections.abc import Sequence

from flext_core import r
from flext_infra import (
    FlextInfraBaseMkValidator,
    FlextInfraInventoryService,
    FlextInfraPytestDiagExtractor,
    FlextInfraSkillValidator,
    FlextInfraStubSupplyChain,
    FlextInfraTextPatternScanner,
)
from flext_infra.validate.silent_failure import FlextInfraSilentFailureValidator


class FlextInfraServiceValidateMixin:
    """Expose validation operations through the public infra facade."""

    def validate_basemk(self, params: FlextInfraBaseMkValidator) -> r[bool]:
        """Validate base.mk state through the public facade."""
        return params.execute()

    def generate_inventory(self, params: FlextInfraInventoryService) -> r[bool]:
        """Generate the validation inventory through the public facade."""
        return params.execute()

    def extract_pytest_diag(
        self,
        params: FlextInfraPytestDiagExtractor,
    ) -> r[bool]:
        """Extract pytest diagnostics through the public facade."""
        return params.execute()

    def scan_text(self, params: FlextInfraTextPatternScanner) -> r[bool]:
        """Run text pattern validation through the public facade."""
        return params.execute()

    def validate_skill(self, params: FlextInfraSkillValidator) -> r[bool]:
        """Validate skills through the public facade."""
        return params.execute()

    def validate_silent_failure(
        self,
        params: FlextInfraSilentFailureValidator,
    ) -> r[bool]:
        """Validate silent failure sentinels through the public facade."""
        return params.execute()

    def validate_stub_supply_chain(
        self,
        params: FlextInfraStubSupplyChain,
    ) -> r[bool]:
        """Validate stub supply chains through the public facade."""
        return params.execute()


__all__: Sequence[str] = ("FlextInfraServiceValidateMixin",)
