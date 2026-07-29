"""Refactor CLI route ownership."""

from __future__ import annotations

from collections.abc import Mapping
from types import MappingProxyType
from typing import TYPE_CHECKING, ClassVar

from flext_infra.services.cli_route_base import CliRouteBase

if TYPE_CHECKING:
    from flext_infra import m


class RefactorRoutes(CliRouteBase):
    """Load only the selected refactor-command implementation."""

    descriptions: ClassVar[Mapping[str, str]] = MappingProxyType({
        "apply-renames": "Check or apply an old,new CSV rename list",
        "migrate-mro": "Migrate loose declarations into MRO facade classes",
        "namespace-enforce": "Scan workspace for namespace governance violations",
        "census": "Run a Rope-only workspace census for Python objects",
        "accessor-migrate": "Preview or apply automated get_/set_/is_ migration",
        "wrapper-root-namespace": (
            "Normalize wrapper alias imports to wrapper root and "
            "flatten *.Core.Tests paths"
        ),
        "modernize-patterns": (
            "Fix u.Cli.print(), pdb, bare except and open() encoding in library code"
        ),
        "modernize-pydantic": "Migrate Pydantic v1/legacy patterns to Pydantic v2",
        "modernize-logging": "Migrate logging usage to u.fetch_logger",
        "modernize-result-di": (
            "Migrate result-flow and dependency-injector patterns "
            "to FLEXT canonical forms"
        ),
        "modernize-cli": (
            "Remove banned CLI helper imports and route u.Cli.print() "
            "to cli.display_text()"
        ),
    })

    @classmethod
    def routes_for(cls, command: str) -> tuple[m.Cli.ResultCommandRoute, ...]:
        """Build the route selected at the lightweight dispatch boundary."""
        from flext_infra import m

        if command == "apply-renames":
            from flext_infra.codemod.rules.refactor.apply_renames import (
                FlextInfraApplyRenames,
            )

            return (
                m.Cli.ResultCommandRoute(
                    name=command,
                    help_text=cls.descriptions[command],
                    model_cls=m.Infra.ApplyRenamesInput,
                    handler=lambda params: FlextInfraApplyRenames.execute_command(
                        params
                    ),
                ),
            )
        if command == "migrate-mro":
            from flext_infra.refactor.migrate_to_class_mro import (
                FlextInfraRefactorMigrateToClassMRO,
            )

            return (
                m.Cli.ResultCommandRoute(
                    name=command,
                    help_text=cls.descriptions[command],
                    model_cls=m.Infra.RefactorMigrateMroInput,
                    handler=lambda params: (
                        FlextInfraRefactorMigrateToClassMRO.execute_command(params).map(
                            CliRouteBase.as_route_value
                        )
                    ),
                ),
            )
        if command == "namespace-enforce":
            from flext_infra.refactor.namespace_enforcer import (
                FlextInfraNamespaceEnforcer,
            )

            return (
                m.Cli.ResultCommandRoute(
                    name=command,
                    help_text=cls.descriptions[command],
                    model_cls=m.Infra.RefactorNamespaceEnforceInput,
                    handler=lambda params: FlextInfraNamespaceEnforcer.execute_command(
                        params
                    ).map(CliRouteBase.as_route_value),
                ),
            )
        if command == "census":
            from flext_infra.refactor.census import FlextInfraRefactorCensus

            return (
                m.Cli.ResultCommandRoute(
                    name=command,
                    help_text=cls.descriptions[command],
                    model_cls=FlextInfraRefactorCensus,
                    handler=lambda params: FlextInfraRefactorCensus.execute_command(
                        params
                    ).map(CliRouteBase.as_route_value),
                ),
            )
        if command == "accessor-migrate":
            from flext_infra.refactor.accessor_migration import (
                FlextInfraAccessorMigrationOrchestrator,
            )

            return (
                m.Cli.ResultCommandRoute(
                    name=command,
                    help_text=cls.descriptions[command],
                    model_cls=m.Infra.AccessorMigrationInput,
                    handler=lambda params: (
                        FlextInfraAccessorMigrationOrchestrator.execute_payload(
                            params
                        ).map(CliRouteBase.as_route_value)
                    ),
                ),
            )
        if command == "wrapper-root-namespace":
            from flext_infra.refactor.wrapper_root_namespace import (
                FlextInfraWrapperRootNamespaceRefactor,
            )

            return (
                m.Cli.ResultCommandRoute(
                    name=command,
                    help_text=cls.descriptions[command],
                    model_cls=FlextInfraWrapperRootNamespaceRefactor,
                    handler=lambda params: params.execute(),
                ),
            )

        if command == "modernize-patterns":
            from flext_infra.transformers.pattern_modernizer import (
                FlextInfraRefactorPatternModernizer,
            )

            transformer = FlextInfraRefactorPatternModernizer
            description = "pattern modernizer"
        elif command == "modernize-pydantic":
            from flext_infra.transformers.pydantic_modernizer import (
                FlextInfraRefactorPydanticModernizer,
            )

            transformer = FlextInfraRefactorPydanticModernizer
            description = "pydantic modernizer"
        elif command == "modernize-logging":
            from flext_infra.transformers.logging_modernizer import (
                FlextInfraRefactorLoggingModernizer,
            )

            transformer = FlextInfraRefactorLoggingModernizer
            description = "logging modernizer"
        elif command == "modernize-result-di":
            from flext_infra.transformers.result_di_modernizer import (
                FlextInfraRefactorResultDiModernizer,
            )

            transformer = FlextInfraRefactorResultDiModernizer
            description = "result/DI modernizer"
        elif command == "modernize-cli":
            from flext_infra.transformers.cli_modernizer import (
                FlextInfraRefactorCliModernizer,
            )

            transformer = FlextInfraRefactorCliModernizer
            description = "cli modernizer"
        else:
            return ()

        from flext_infra.refactor.modernize_orchestrator import (
            FlextInfraModernizeOrchestrator,
        )

        return (
            m.Cli.ResultCommandRoute(
                name=command,
                help_text=cls.descriptions[command],
                model_cls=m.Infra.ModernizeInput,
                handler=lambda params: FlextInfraModernizeOrchestrator.execute_command(
                    params, transformer_factory=transformer, description=description
                ),
            ),
        )


__all__: list[str] = ["RefactorRoutes"]
