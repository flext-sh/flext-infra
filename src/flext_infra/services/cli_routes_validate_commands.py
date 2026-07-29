"""Validate-command loaders selected by the generated CLI registry."""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_infra.services.cli_route_base import CliRouteBase

if TYPE_CHECKING:
    from flext_infra import p, t


class ValidationCommandRoutes(CliRouteBase):
    """Load exactly one validate-command implementation."""

    @staticmethod
    def load_basemk_validate(
        name: str, help_text: str
    ) -> t.SequenceOf[p.Cli.ResultCommandRoute]:
        """Load the selected base.mk validator."""
        from flext_infra.validate.basemk_validator import FlextInfraBaseMkValidator

        return CliRouteBase.command_route(
            name,
            help_text,
            FlextInfraBaseMkValidator,
            FlextInfraBaseMkValidator.execute_command,
        )

    @staticmethod
    def load_inventory(
        name: str, help_text: str
    ) -> t.SequenceOf[p.Cli.ResultCommandRoute]:
        """Load the selected inventory generator."""
        from flext_infra.validate.inventory import FlextInfraInventoryService

        return CliRouteBase.command_route(
            name,
            help_text,
            FlextInfraInventoryService,
            FlextInfraInventoryService.execute_command,
        )

    @staticmethod
    def load_runtime_census(
        name: str, help_text: str
    ) -> t.SequenceOf[p.Cli.ResultCommandRoute]:
        """Load the selected runtime census."""
        from flext_infra.validate.runtime_census import FlextInfraRuntimeCensusValidator

        return CliRouteBase.command_route(
            name,
            help_text,
            FlextInfraRuntimeCensusValidator,
            FlextInfraRuntimeCensusValidator.execute_command,
        )

    @staticmethod
    def load_pytest_diag(
        name: str, help_text: str
    ) -> t.SequenceOf[p.Cli.ResultCommandRoute]:
        """Load the selected pytest diagnostics route."""
        from flext_infra.validate.pytest_diag import FlextInfraPytestDiagExtractor

        return CliRouteBase.command_route(
            name,
            help_text,
            FlextInfraPytestDiagExtractor,
            FlextInfraPytestDiagExtractor.execute_command,
        )

    @staticmethod
    def load_cprofile_report(
        name: str, help_text: str
    ) -> t.SequenceOf[p.Cli.ResultCommandRoute]:
        """Load the selected typed cProfile report renderer."""
        from flext_infra.validate.cprofile_report import FlextInfraCProfileReport

        return CliRouteBase.command_route(
            name,
            help_text,
            FlextInfraCProfileReport,
            FlextInfraCProfileReport.execute_command,
        )

    @staticmethod
    def load_cprofile_run(
        name: str, help_text: str
    ) -> t.SequenceOf[p.Cli.ResultCommandRoute]:
        """Load the portable cProfile process supervisor."""
        from flext_infra.validate.cprofile_report import FlextInfraCProfileRun

        return CliRouteBase.command_route(
            name,
            help_text,
            FlextInfraCProfileRun,
            FlextInfraCProfileRun.execute_command,
        )

    @staticmethod
    def load_scan(name: str, help_text: str) -> t.SequenceOf[p.Cli.ResultCommandRoute]:
        """Load the selected text scanner."""
        from flext_infra.validate.scanner import FlextInfraTextPatternScanner

        return CliRouteBase.command_route(
            name,
            help_text,
            FlextInfraTextPatternScanner,
            FlextInfraTextPatternScanner.execute_command,
        )

    @staticmethod
    def load_skill_validate(
        name: str, help_text: str
    ) -> t.SequenceOf[p.Cli.ResultCommandRoute]:
        """Load the selected skill validator."""
        from flext_infra.validate.skill_validator import FlextInfraSkillValidator

        return CliRouteBase.command_route(
            name,
            help_text,
            FlextInfraSkillValidator,
            FlextInfraSkillValidator.execute_command,
        )

    @staticmethod
    def load_silent_failure(
        name: str, help_text: str
    ) -> t.SequenceOf[p.Cli.ResultCommandRoute]:
        """Load the selected silent-failure validator."""
        from flext_infra.validate.silent_failure import FlextInfraSilentFailureValidator

        return CliRouteBase.command_route(
            name,
            help_text,
            FlextInfraSilentFailureValidator,
            FlextInfraSilentFailureValidator.execute_command,
        )

    @staticmethod
    def load_stub_validate(
        name: str, help_text: str
    ) -> t.SequenceOf[p.Cli.ResultCommandRoute]:
        """Load the selected stub-chain validator."""
        from flext_infra.validate.stub_chain import FlextInfraStubSupplyChain

        return CliRouteBase.command_route(
            name,
            help_text,
            FlextInfraStubSupplyChain,
            FlextInfraStubSupplyChain.execute_command,
        )

    @staticmethod
    def load_fresh_import(
        name: str, help_text: str
    ) -> t.SequenceOf[p.Cli.ResultCommandRoute]:
        """Load the selected fresh-import validator."""
        from flext_infra.validate.fresh_import import FlextInfraValidateFreshImport

        return CliRouteBase.command_route(
            name,
            help_text,
            FlextInfraValidateFreshImport,
            FlextInfraValidateFreshImport.execute_command,
        )

    @staticmethod
    def load_import_cycles(
        name: str, help_text: str
    ) -> t.SequenceOf[p.Cli.ResultCommandRoute]:
        """Load the selected import-cycle validator."""
        from flext_infra.validate.import_cycles import FlextInfraValidateImportCycles

        return CliRouteBase.command_route(
            name,
            help_text,
            FlextInfraValidateImportCycles,
            FlextInfraValidateImportCycles.execute_command,
        )

    @staticmethod
    def load_lazy_map_freshness(
        name: str, help_text: str
    ) -> t.SequenceOf[p.Cli.ResultCommandRoute]:
        """Load the selected lazy-map validator."""
        from flext_infra.validate.lazy_map_freshness import (
            FlextInfraValidateLazyMapFreshness,
        )

        return CliRouteBase.command_route(
            name,
            help_text,
            FlextInfraValidateLazyMapFreshness,
            FlextInfraValidateLazyMapFreshness.execute_command,
        )

    @staticmethod
    def load_namespace(
        name: str, help_text: str
    ) -> t.SequenceOf[p.Cli.ResultCommandRoute]:
        """Load the selected namespace validator."""
        from flext_infra.validate.namespace_validator import (
            FlextInfraNamespaceValidator,
        )

        return CliRouteBase.command_route(
            name,
            help_text,
            FlextInfraNamespaceValidator,
            FlextInfraNamespaceValidator.execute_command,
        )

    @staticmethod
    def load_tier_whitelist(
        name: str, help_text: str
    ) -> t.SequenceOf[p.Cli.ResultCommandRoute]:
        """Load the selected tier-whitelist validator."""
        from flext_infra.validate.tier_whitelist import FlextInfraValidateTierWhitelist

        return CliRouteBase.command_route(
            name,
            help_text,
            FlextInfraValidateTierWhitelist,
            FlextInfraValidateTierWhitelist.execute_command,
        )

    @staticmethod
    def load_metadata_discipline(
        name: str, help_text: str
    ) -> t.SequenceOf[p.Cli.ResultCommandRoute]:
        """Load the selected metadata-discipline validator."""
        from flext_infra.validate.metadata_discipline import (
            FlextInfraValidateMetadataDiscipline,
        )

        return CliRouteBase.command_route(
            name,
            help_text,
            FlextInfraValidateMetadataDiscipline,
            FlextInfraValidateMetadataDiscipline.execute_command,
        )

    @staticmethod
    def load_manual_cmd(
        name: str, help_text: str
    ) -> t.SequenceOf[p.Cli.ResultCommandRoute]:
        """Load the selected manual-command validator."""
        from flext_infra.validate.manual_command import FlextInfraManualCommandValidator

        return CliRouteBase.command_route(
            name,
            help_text,
            FlextInfraManualCommandValidator,
            FlextInfraManualCommandValidator.execute_command,
        )


__all__: list[str] = ["ValidationCommandRoutes"]
