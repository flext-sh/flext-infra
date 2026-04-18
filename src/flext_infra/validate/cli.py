"""CLI mixin for validate commands."""

from __future__ import annotations

from flext_cli import cli
from flext_infra import (
    FlextInfraBaseMkValidator,
    FlextInfraInventoryService,
    FlextInfraPytestDiagExtractor,
    FlextInfraServiceValidateMixin,
    FlextInfraSilentFailureValidator,
    FlextInfraSkillValidator,
    FlextInfraStubSupplyChain,
    FlextInfraTextPatternScanner,
    FlextInfraValidateFreshImport,
    FlextInfraValidateImportCycles,
    FlextInfraValidateLazyMapFreshness,
    FlextInfraValidateTierWhitelist,
    m,
    t,
)
from flext_infra.validate.metadata_discipline import (
    FlextInfraValidateMetadataDiscipline,
)


class FlextInfraCliValidate(FlextInfraServiceValidateMixin):
    """Validate CLI group — composed into FlextInfraCli via MRO."""

    def register_validate(
        self,
        app: t.Cli.CliApp,
    ) -> None:
        """Register validate commands on the given Typer app."""
        cli.register_result_routes(
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
                m.Cli.ResultCommandRoute(
                    name="fresh-import",
                    help_text="Guard 7: fresh-process import smoke test",
                    model_cls=FlextInfraValidateFreshImport,
                    handler=self.validate_fresh_import,
                    failure_message="fresh-import validation failed",
                ),
                m.Cli.ResultCommandRoute(
                    name="import-cycles",
                    help_text="Guard 1: ROPE-backed import cycle detector",
                    model_cls=FlextInfraValidateImportCycles,
                    handler=self.validate_import_cycles,
                    failure_message="import-cycles validation failed",
                ),
                m.Cli.ResultCommandRoute(
                    name="lazy-map-freshness",
                    help_text="Guard 2/3: lazy-map freshness validator",
                    model_cls=FlextInfraValidateLazyMapFreshness,
                    handler=self.validate_lazy_map_freshness,
                    failure_message="lazy-map freshness validation failed",
                ),
                m.Cli.ResultCommandRoute(
                    name="tier-whitelist",
                    help_text="Guard 5: tier-whitelist/abstraction-boundary enforcer",
                    model_cls=FlextInfraValidateTierWhitelist,
                    handler=self.validate_tier_whitelist,
                    failure_message="tier-whitelist validation failed",
                ),
                m.Cli.ResultCommandRoute(
                    name="metadata-discipline",
                    help_text="Guard 8: centralized metadata parser discipline",
                    model_cls=FlextInfraValidateMetadataDiscipline,
                    handler=self.validate_metadata_discipline,
                    failure_message="metadata-discipline validation failed",
                ),
            ],
        )


__all__: list[str] = ["FlextInfraCliValidate"]
