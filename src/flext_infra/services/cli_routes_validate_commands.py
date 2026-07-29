"""Validate-command CLI route ownership."""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_infra.cli_catalog import CliCatalog
from flext_infra.services.cli_route_base import CliRouteBase

if TYPE_CHECKING:
    from flext_infra import m


class ValidationCommandRoutes(CliRouteBase):
    """Load only the selected validate-command implementation."""

    @classmethod
    def routes_for(cls, command: str) -> tuple[m.Cli.ResultCommandRoute, ...]:
        """Build the route selected at the lightweight dispatch boundary."""
        if command == "basemk-validate":
            from flext_infra.validate.basemk_validator import (
                FlextInfraBaseMkValidator,
            )

            implementation = FlextInfraBaseMkValidator
        elif command == "inventory":
            from flext_infra.validate.inventory import FlextInfraInventoryService

            implementation = FlextInfraInventoryService
        elif command == "runtime-census":
            from flext_infra.validate.runtime_census import (
                FlextInfraRuntimeCensusValidator,
            )

            implementation = FlextInfraRuntimeCensusValidator
        elif command == "pytest-diag":
            from flext_infra.validate.pytest_diag import FlextInfraPytestDiagExtractor

            implementation = FlextInfraPytestDiagExtractor
        elif command == "scan":
            from flext_infra.validate.scanner import FlextInfraTextPatternScanner

            implementation = FlextInfraTextPatternScanner
        elif command == "skill-validate":
            from flext_infra.validate.skill_validator import FlextInfraSkillValidator

            implementation = FlextInfraSkillValidator
        elif command == "silent-failure":
            from flext_infra.validate.silent_failure import (
                FlextInfraSilentFailureValidator,
            )

            implementation = FlextInfraSilentFailureValidator
        elif command == "stub-validate":
            from flext_infra.validate.stub_chain import FlextInfraStubSupplyChain

            implementation = FlextInfraStubSupplyChain
        elif command == "fresh-import":
            from flext_infra.validate.fresh_import import FlextInfraValidateFreshImport

            implementation = FlextInfraValidateFreshImport
        elif command == "import-cycles":
            from flext_infra.validate.import_cycles import (
                FlextInfraValidateImportCycles,
            )

            implementation = FlextInfraValidateImportCycles
        elif command == "lazy-map-freshness":
            from flext_infra.validate.lazy_map_freshness import (
                FlextInfraValidateLazyMapFreshness,
            )

            implementation = FlextInfraValidateLazyMapFreshness
        elif command == "namespace":
            from flext_infra.validate.namespace_validator import (
                FlextInfraNamespaceValidator,
            )

            implementation = FlextInfraNamespaceValidator
        elif command == "tier-whitelist":
            from flext_infra.validate.tier_whitelist import (
                FlextInfraValidateTierWhitelist,
            )

            implementation = FlextInfraValidateTierWhitelist
        elif command == "metadata-discipline":
            from flext_infra.validate.metadata_discipline import (
                FlextInfraValidateMetadataDiscipline,
            )

            implementation = FlextInfraValidateMetadataDiscipline
        elif command == "manual-cmd":
            from flext_infra.validate.manual_command import (
                FlextInfraManualCommandValidator,
            )

            implementation = FlextInfraManualCommandValidator
        else:
            return ()

        from flext_infra import m

        return (
            m.Cli.ResultCommandRoute(
                name=command,
                help_text=CliCatalog.description("validate", command),
                model_cls=implementation,
                handler=lambda params, mc=implementation: mc.execute_command(params),
            ),
        )


__all__: list[str] = ["ValidationCommandRoutes"]
