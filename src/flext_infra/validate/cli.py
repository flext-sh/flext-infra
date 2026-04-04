"""CLI mixin for validate commands."""

from __future__ import annotations

from flext_cli import cli as cli_service
from flext_infra import (
    FlextInfraBaseMkValidator,
    FlextInfraInventoryService,
    FlextInfraPytestDiagExtractor,
    FlextInfraSkillValidator,
    FlextInfraStubSupplyChain,
    FlextInfraTextPatternScanner,
    m,
    t,
)


class FlextInfraCliValidate:
    """Validate CLI group — composed into FlextInfraCli via MRO."""

    def register_validate(self, app: t.Cli.CliApp) -> None:
        """Register validate commands on the given Typer app."""
        basemk_validator = FlextInfraBaseMkValidator()
        inventory_service = FlextInfraInventoryService()
        pytest_diag_extractor = FlextInfraPytestDiagExtractor()
        skill_validator = FlextInfraSkillValidator()
        stub_supply_chain = FlextInfraStubSupplyChain()
        text_pattern_scanner = FlextInfraTextPatternScanner()
        cli_service.register_result_routes(
            app,
            [
                m.Cli.ResultCommandRoute(
                    name="basemk-validate",
                    help_text="Validate base.mk sync",
                    model_cls=m.Infra.ValidateBaseMkInput,
                    handler=basemk_validator.execute_command,
                    failure_message="basemk validation failed",
                ),
                m.Cli.ResultCommandRoute(
                    name="inventory",
                    help_text="Generate scripts inventory",
                    model_cls=m.Infra.ValidateInventoryInput,
                    handler=inventory_service.execute_command,
                    failure_message="inventory failed",
                ),
                m.Cli.ResultCommandRoute(
                    name="pytest-diag",
                    help_text="Extract pytest diagnostics",
                    model_cls=m.Infra.ValidatePytestDiagInput,
                    handler=pytest_diag_extractor.execute_command,
                    failure_message="pytest diagnostics failed",
                ),
                m.Cli.ResultCommandRoute(
                    name="scan",
                    help_text="Scan text files for patterns",
                    model_cls=m.Infra.ValidateScanInput,
                    handler=text_pattern_scanner.execute_command,
                    failure_message="scan failed",
                ),
                m.Cli.ResultCommandRoute(
                    name="skill-validate",
                    help_text="Validate a skill",
                    model_cls=m.Infra.ValidateSkillValidateInput,
                    handler=skill_validator.execute_command,
                    failure_message="skill validation failed",
                ),
                m.Cli.ResultCommandRoute(
                    name="stub-validate",
                    help_text="Validate stub supply chain",
                    model_cls=m.Infra.ValidateStubValidateInput,
                    handler=stub_supply_chain.execute_command,
                    failure_message="stub validation failed",
                ),
            ],
        )


__all__ = ["FlextInfraCliValidate"]
