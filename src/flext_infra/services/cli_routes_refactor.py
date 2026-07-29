"""Refactor-command loaders selected by the generated CLI registry."""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_infra.services.cli_route_base import CliRouteBase

if TYPE_CHECKING:
    from flext_infra import p, t


class RefactorRoutes(CliRouteBase):
    """Load exactly one refactor implementation."""

    @staticmethod
    def load_apply_renames(
        name: str, help_text: str
    ) -> t.SequenceOf[p.Cli.ResultCommandRoute]:
        """Load the selected rename route."""
        from flext_infra import m
        from flext_infra.codemod.rules.refactor.apply_renames import (
            FlextInfraApplyRenames,
        )

        return CliRouteBase.command_route(
            name,
            help_text,
            m.Infra.ApplyRenamesInput,
            FlextInfraApplyRenames.execute_command,
        )

    @staticmethod
    def load_migrate_mro(
        name: str, help_text: str
    ) -> t.SequenceOf[p.Cli.ResultCommandRoute]:
        """Load the selected MRO migration route."""
        from flext_infra import m
        from flext_infra.refactor.migrate_to_class_mro import (
            FlextInfraRefactorMigrateToClassMRO,
        )

        return CliRouteBase.command_route(
            name,
            help_text,
            m.Infra.RefactorMigrateMroInput,
            lambda params: FlextInfraRefactorMigrateToClassMRO.execute_command(
                params
            ).map(CliRouteBase.as_route_value),
        )

    @staticmethod
    def load_namespace_enforce(
        name: str, help_text: str
    ) -> t.SequenceOf[p.Cli.ResultCommandRoute]:
        """Load the selected namespace-enforcement route."""
        from flext_infra import m
        from flext_infra.refactor.namespace_enforcer import FlextInfraNamespaceEnforcer

        return CliRouteBase.command_route(
            name,
            help_text,
            m.Infra.RefactorNamespaceEnforceInput,
            lambda params: FlextInfraNamespaceEnforcer.execute_command(params).map(
                CliRouteBase.as_route_value
            ),
        )

    @staticmethod
    def load_census(
        name: str, help_text: str
    ) -> t.SequenceOf[p.Cli.ResultCommandRoute]:
        """Load the selected refactor census route."""
        from flext_infra.refactor.census import FlextInfraRefactorCensus

        return CliRouteBase.command_route(
            name,
            help_text,
            FlextInfraRefactorCensus,
            lambda params: FlextInfraRefactorCensus.execute_command(params).map(
                CliRouteBase.as_route_value
            ),
        )

    @staticmethod
    def load_accessor_migrate(
        name: str, help_text: str
    ) -> t.SequenceOf[p.Cli.ResultCommandRoute]:
        """Load the selected accessor migration route."""
        from flext_infra import m
        from flext_infra.refactor.accessor_migration import (
            FlextInfraAccessorMigrationOrchestrator,
        )

        return CliRouteBase.command_route(
            name,
            help_text,
            m.Infra.AccessorMigrationInput,
            lambda params: FlextInfraAccessorMigrationOrchestrator.execute_payload(
                params
            ).map(CliRouteBase.as_route_value),
        )

    @staticmethod
    def load_wrapper_root_namespace(
        name: str, help_text: str
    ) -> t.SequenceOf[p.Cli.ResultCommandRoute]:
        """Load the selected wrapper-root route."""
        from flext_infra.refactor.wrapper_root_namespace import (
            FlextInfraWrapperRootNamespaceRefactor,
        )

        return CliRouteBase.command_route(
            name,
            help_text,
            FlextInfraWrapperRootNamespaceRefactor,
            lambda params: params.execute(),
        )

    @staticmethod
    def load_modernize_patterns(
        name: str, help_text: str
    ) -> t.SequenceOf[p.Cli.ResultCommandRoute]:
        """Load the selected pattern modernizer."""
        from flext_infra import m
        from flext_infra.refactor.modernize_orchestrator import (
            FlextInfraModernizeOrchestrator,
        )
        from flext_infra.transformers.pattern_modernizer import (
            FlextInfraRefactorPatternModernizer,
        )

        return CliRouteBase.command_route(
            name,
            help_text,
            m.Infra.ModernizeInput,
            lambda params: FlextInfraModernizeOrchestrator.execute_command(
                params,
                transformer_factory=FlextInfraRefactorPatternModernizer,
                description="pattern modernizer",
            ),
        )

    @staticmethod
    def load_modernize_pydantic(
        name: str, help_text: str
    ) -> t.SequenceOf[p.Cli.ResultCommandRoute]:
        """Load the selected Pydantic modernizer."""
        from flext_infra import m
        from flext_infra.refactor.modernize_orchestrator import (
            FlextInfraModernizeOrchestrator,
        )
        from flext_infra.transformers.pydantic_modernizer import (
            FlextInfraRefactorPydanticModernizer,
        )

        return CliRouteBase.command_route(
            name,
            help_text,
            m.Infra.ModernizeInput,
            lambda params: FlextInfraModernizeOrchestrator.execute_command(
                params,
                transformer_factory=FlextInfraRefactorPydanticModernizer,
                description="pydantic modernizer",
            ),
        )

    @staticmethod
    def load_modernize_logging(
        name: str, help_text: str
    ) -> t.SequenceOf[p.Cli.ResultCommandRoute]:
        """Load the selected logging modernizer."""
        from flext_infra import m
        from flext_infra.refactor.modernize_orchestrator import (
            FlextInfraModernizeOrchestrator,
        )
        from flext_infra.transformers.logging_modernizer import (
            FlextInfraRefactorLoggingModernizer,
        )

        return CliRouteBase.command_route(
            name,
            help_text,
            m.Infra.ModernizeInput,
            lambda params: FlextInfraModernizeOrchestrator.execute_command(
                params,
                transformer_factory=FlextInfraRefactorLoggingModernizer,
                description="logging modernizer",
            ),
        )

    @staticmethod
    def load_modernize_result_di(
        name: str, help_text: str
    ) -> t.SequenceOf[p.Cli.ResultCommandRoute]:
        """Load the selected result/DI modernizer."""
        from flext_infra import m
        from flext_infra.refactor.modernize_orchestrator import (
            FlextInfraModernizeOrchestrator,
        )
        from flext_infra.transformers.result_di_modernizer import (
            FlextInfraRefactorResultDiModernizer,
        )

        return CliRouteBase.command_route(
            name,
            help_text,
            m.Infra.ModernizeInput,
            lambda params: FlextInfraModernizeOrchestrator.execute_command(
                params,
                transformer_factory=FlextInfraRefactorResultDiModernizer,
                description="result/DI modernizer",
            ),
        )

    @staticmethod
    def load_modernize_cli(
        name: str, help_text: str
    ) -> t.SequenceOf[p.Cli.ResultCommandRoute]:
        """Load the selected CLI modernizer."""
        from flext_infra import m
        from flext_infra.refactor.modernize_orchestrator import (
            FlextInfraModernizeOrchestrator,
        )
        from flext_infra.transformers.cli_modernizer import (
            FlextInfraRefactorCliModernizer,
        )

        return CliRouteBase.command_route(
            name,
            help_text,
            m.Infra.ModernizeInput,
            lambda params: FlextInfraModernizeOrchestrator.execute_command(
                params,
                transformer_factory=FlextInfraRefactorCliModernizer,
                description="cli modernizer",
            ),
        )


__all__: list[str] = ["RefactorRoutes"]
