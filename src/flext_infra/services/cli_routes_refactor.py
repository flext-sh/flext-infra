"""Refactor CLI route ownership."""

from __future__ import annotations

from typing import ClassVar

from flext_infra import m
from flext_infra.refactor.accessor_migration import (
    FlextInfraAccessorMigrationOrchestrator,
)
from flext_infra.refactor.census import FlextInfraRefactorCensus
from flext_infra.refactor.migrate_to_class_mro import (
    FlextInfraRefactorMigrateToClassMRO,
)
from flext_infra.refactor.modernize_orchestrator import FlextInfraModernizeOrchestrator
from flext_infra.refactor.namespace_enforcer import FlextInfraNamespaceEnforcer
from flext_infra.refactor.wrapper_root_namespace import (
    FlextInfraWrapperRootNamespaceRefactor,
)
from flext_infra.services.cli_route_base import CliRouteBase
from flext_infra.transformers.cli_modernizer import FlextInfraRefactorCliModernizer
from flext_infra.transformers.logging_modernizer import (
    FlextInfraRefactorLoggingModernizer,
)
from flext_infra.transformers.pattern_modernizer import (
    FlextInfraRefactorPatternModernizer,
)
from flext_infra.transformers.pydantic_modernizer import (
    FlextInfraRefactorPydanticModernizer,
)
from flext_infra.transformers.result_di_modernizer import (
    FlextInfraRefactorResultDiModernizer,
)


class RefactorRoutes(CliRouteBase):
    """Own the complete refactor command tuple."""

    refactor_routes: ClassVar[tuple[m.Cli.ResultCommandRoute, ...]] = (
        m.Cli.ResultCommandRoute(
            name="migrate-mro",
            help_text="Migrate loose declarations into MRO facade classes",
            model_cls=m.Infra.RefactorMigrateMroInput,
            handler=lambda params: FlextInfraRefactorMigrateToClassMRO.execute_command(
                params
            ).map(CliRouteBase.as_route_value),
        ),
        m.Cli.ResultCommandRoute(
            name="namespace-enforce",
            help_text="Scan workspace for namespace governance violations",
            model_cls=m.Infra.RefactorNamespaceEnforceInput,
            handler=lambda params: FlextInfraNamespaceEnforcer.execute_command(
                params
            ).map(CliRouteBase.as_route_value),
        ),
        m.Cli.ResultCommandRoute(
            name="census",
            help_text="Run a Rope-only workspace census for Python objects",
            model_cls=FlextInfraRefactorCensus,
            handler=lambda params: FlextInfraRefactorCensus.execute_command(
                params
            ).map(CliRouteBase.as_route_value),
        ),
        m.Cli.ResultCommandRoute(
            name="accessor-migrate",
            help_text="Preview or apply automated get_/set_/is_ migration",
            model_cls=m.Infra.AccessorMigrationInput,
            handler=lambda params: (
                FlextInfraAccessorMigrationOrchestrator.execute_payload(params).map(
                    CliRouteBase.as_route_value
                )
            ),
        ),
        m.Cli.ResultCommandRoute(
            name="wrapper-root-namespace",
            help_text=(
                "Normalize wrapper alias imports to wrapper root and "
                "flatten *.Core.Tests paths"
            ),
            model_cls=FlextInfraWrapperRootNamespaceRefactor,
            handler=lambda params: params.execute(),
        ),
        m.Cli.ResultCommandRoute(
            name="modernize-patterns",
            help_text=(
                "Fix print(), pdb, bare except and open() encoding in library code"
            ),
            model_cls=m.Infra.ModernizeInput,
            handler=lambda params: FlextInfraModernizeOrchestrator.execute_command(
                params,
                transformer_factory=FlextInfraRefactorPatternModernizer,
                description="pattern modernizer",
            ),
        ),
        m.Cli.ResultCommandRoute(
            name="modernize-pydantic",
            help_text="Migrate Pydantic v1/legacy patterns to Pydantic v2",
            model_cls=m.Infra.ModernizeInput,
            handler=lambda params: FlextInfraModernizeOrchestrator.execute_command(
                params,
                transformer_factory=FlextInfraRefactorPydanticModernizer,
                description="pydantic modernizer",
            ),
        ),
        m.Cli.ResultCommandRoute(
            name="modernize-logging",
            help_text="Migrate logging usage to u.fetch_logger",
            model_cls=m.Infra.ModernizeInput,
            handler=lambda params: FlextInfraModernizeOrchestrator.execute_command(
                params,
                transformer_factory=FlextInfraRefactorLoggingModernizer,
                description="logging modernizer",
            ),
        ),
        m.Cli.ResultCommandRoute(
            name="modernize-result-di",
            help_text=(
                "Migrate result-flow and dependency-injector patterns "
                "to FLEXT canonical forms"
            ),
            model_cls=m.Infra.ModernizeInput,
            handler=lambda params: FlextInfraModernizeOrchestrator.execute_command(
                params,
                transformer_factory=FlextInfraRefactorResultDiModernizer,
                description="result/DI modernizer",
            ),
        ),
        m.Cli.ResultCommandRoute(
            name="modernize-cli",
            help_text=(
                "Remove banned CLI helper imports and route print() "
                "to cli.display_text()"
            ),
            model_cls=m.Infra.ModernizeInput,
            handler=lambda params: FlextInfraModernizeOrchestrator.execute_command(
                params,
                transformer_factory=FlextInfraRefactorCliModernizer,
                description="cli modernizer",
            ),
        ),
    )


__all__: list[str] = ["RefactorRoutes"]
