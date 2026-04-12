"""CLI mixin for validate commands."""

from __future__ import annotations

from flext_cli.api import cli as cli_service
from flext_infra import (
    FlextInfraBaseMkValidator,
    FlextInfraInventoryService,
    FlextInfraPytestDiagExtractor,
    FlextInfraServiceValidateMixin,
    FlextInfraSilentFailureValidator,
    FlextInfraSkillValidator,
    FlextInfraStubSupplyChain,
    FlextInfraTextPatternScanner,
    m,
    t,
)


class FlextInfraCliValidate(FlextInfraServiceValidateMixin):
    """Validate CLI group — composed into FlextInfraCli via MRO."""

    def register_validate(
        self,
        app: t.Cli.CliApp,
    ) -> None:
        """Register validate commands on the given Typer app."""
        cli_service.register_result_routes(
            app,
            [
                m.Cli.ResultCommandRoute(
                    name="basemk-validate",
                    help_text="Validate base.mk sync",
                    model_cls=FlextInfraBaseMkValidator,
                    handler=self.validate_basemk,
                    failure_message="basemk validation failed",
                ),
                m.Cli.ResultCommandRoute(
                    name="inventory",
                    help_text="Generate scripts inventory",
                    model_cls=FlextInfraInventoryService,
                    handler=self.generate_inventory,
                    failure_message="inventory failed",
                ),
                m.Cli.ResultCommandRoute(
                    name="pytest-diag",
                    help_text="Extract pytest diagnostics",
                    model_cls=FlextInfraPytestDiagExtractor,
                    handler=self.extract_pytest_diag,
                    failure_message="pytest diagnostics failed",
                ),
                m.Cli.ResultCommandRoute(
                    name="scan",
                    help_text="Scan text files for patterns",
                    model_cls=FlextInfraTextPatternScanner,
                    handler=self.scan_text,
                    failure_message="scan failed",
                ),
                m.Cli.ResultCommandRoute(
                    name="skill-validate",
                    help_text="Validate a skill",
                    model_cls=FlextInfraSkillValidator,
                    handler=self.validate_skill,
                    failure_message="skill validation failed",
                ),
                m.Cli.ResultCommandRoute(
                    name="silent-failure",
                    help_text="Validate silent failure sentinel returns",
                    model_cls=FlextInfraSilentFailureValidator,
                    handler=self.validate_silent_failure,
                    failure_message="silent failure validation failed",
                ),
                m.Cli.ResultCommandRoute(
                    name="stub-validate",
                    help_text="Validate stub supply chain",
                    model_cls=FlextInfraStubSupplyChain,
                    handler=self.validate_stub_supply_chain,
                    failure_message="stub validation failed",
                ),
            ],
        )


__all__: list[str] = ["FlextInfraCliValidate"]
