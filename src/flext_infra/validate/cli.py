"""CLI registration for the validate domain."""

from __future__ import annotations

from flext_infra.cli_registry import FlextInfraCliGroupBase
from flext_infra.typings import t
from flext_infra.validate.basemk_validator import FlextInfraBaseMkValidator
from flext_infra.validate.fresh_import import FlextInfraValidateFreshImport
from flext_infra.validate.import_cycles import FlextInfraValidateImportCycles
from flext_infra.validate.inventory import FlextInfraInventoryService
from flext_infra.validate.lazy_map_freshness import FlextInfraValidateLazyMapFreshness
from flext_infra.validate.metadata_discipline import (
    FlextInfraValidateMetadataDiscipline,
)
from flext_infra.validate.pytest_diag import FlextInfraPytestDiagExtractor
from flext_infra.validate.scanner import FlextInfraTextPatternScanner
from flext_infra.validate.silent_failure import FlextInfraSilentFailureValidator
from flext_infra.validate.skill_validator import FlextInfraSkillValidator
from flext_infra.validate.stub_chain import FlextInfraStubSupplyChain
from flext_infra.validate.tier_whitelist import FlextInfraValidateTierWhitelist


class FlextInfraCliValidate(FlextInfraCliGroupBase):
    """Owns validate CLI route declarations."""

    routes = (
        FlextInfraCliGroupBase.route(
            name="basemk-validate",
            help_text="Validate base.mk sync",
            model_cls=FlextInfraBaseMkValidator,
            handler=FlextInfraBaseMkValidator.execute_command,
            failure_message="basemk validation failed",
        ),
        FlextInfraCliGroupBase.route(
            name="inventory",
            help_text="Generate scripts inventory",
            model_cls=FlextInfraInventoryService,
            handler=FlextInfraInventoryService.execute_command,
            failure_message="inventory failed",
        ),
        FlextInfraCliGroupBase.route(
            name="pytest-diag",
            help_text="Extract pytest diagnostics",
            model_cls=FlextInfraPytestDiagExtractor,
            handler=FlextInfraPytestDiagExtractor.execute_command,
            failure_message="pytest diagnostics failed",
        ),
        FlextInfraCliGroupBase.route(
            name="scan",
            help_text="Scan text files for patterns",
            model_cls=FlextInfraTextPatternScanner,
            handler=FlextInfraTextPatternScanner.execute_command,
            failure_message="scan failed",
        ),
        FlextInfraCliGroupBase.route(
            name="skill-validate",
            help_text="Validate a skill",
            model_cls=FlextInfraSkillValidator,
            handler=FlextInfraSkillValidator.execute_command,
            failure_message="skill validation failed",
        ),
        FlextInfraCliGroupBase.route(
            name="silent-failure",
            help_text="Validate silent failure sentinel returns",
            model_cls=FlextInfraSilentFailureValidator,
            handler=FlextInfraSilentFailureValidator.execute_command,
            failure_message="silent failure validation failed",
        ),
        FlextInfraCliGroupBase.route(
            name="stub-validate",
            help_text="Validate stub supply chain",
            model_cls=FlextInfraStubSupplyChain,
            handler=FlextInfraStubSupplyChain.execute_command,
            failure_message="stub validation failed",
        ),
        FlextInfraCliGroupBase.route(
            name="fresh-import",
            help_text="Guard 7: fresh-process import smoke test",
            model_cls=FlextInfraValidateFreshImport,
            handler=FlextInfraValidateFreshImport.execute_command,
            failure_message="fresh-import validation failed",
        ),
        FlextInfraCliGroupBase.route(
            name="import-cycles",
            help_text="Guard 1: ROPE-backed import cycle detector",
            model_cls=FlextInfraValidateImportCycles,
            handler=FlextInfraValidateImportCycles.execute_command,
            failure_message="import-cycles validation failed",
        ),
        FlextInfraCliGroupBase.route(
            name="lazy-map-freshness",
            help_text="Guard 2/3: lazy-map freshness validator",
            model_cls=FlextInfraValidateLazyMapFreshness,
            handler=FlextInfraValidateLazyMapFreshness.execute_command,
            failure_message="lazy-map freshness validation failed",
        ),
        FlextInfraCliGroupBase.route(
            name="tier-whitelist",
            help_text="Guard 5: tier-whitelist/abstraction-boundary enforcer",
            model_cls=FlextInfraValidateTierWhitelist,
            handler=FlextInfraValidateTierWhitelist.execute_command,
            failure_message="tier-whitelist validation failed",
        ),
        FlextInfraCliGroupBase.route(
            name="metadata-discipline",
            help_text="Guard 8: centralized metadata parser discipline",
            model_cls=FlextInfraValidateMetadataDiscipline,
            handler=FlextInfraValidateMetadataDiscipline.execute_command,
            failure_message="metadata-discipline validation failed",
        ),
    )

    def register_validate(self, app: t.Cli.CliApp) -> None:
        """Register validate routes."""
        FlextInfraCliValidate.register_routes(app)


__all__: list[str] = ["FlextInfraCliValidate"]
