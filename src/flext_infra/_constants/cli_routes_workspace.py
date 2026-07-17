"""Workspace, refactor, and release CLI routes for flext-infra."""

from __future__ import annotations

from flext_infra import c, m, t
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
from flext_infra.release.orchestrator import FlextInfraReleaseOrchestrator
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
from flext_infra.workspace.detector import FlextInfraWorkspaceDetector
from flext_infra.workspace.migrator import FlextInfraProjectMigrator
from flext_infra.workspace.orchestrator import FlextInfraOrchestratorService
from flext_infra.workspace.sync import FlextInfraSyncService


def _as_route_value(value: t.Cli.ResultValue) -> t.Cli.ResultValue:
    """Widen a specific result payload to the CLI route contract value.

    Used as the mapper for ``Result.map`` so handlers returning concrete
    ``Result[T]`` satisfy ``t.Cli.ResultRouteHandler`` without any runtime
    change.
    """
    return value


WORKSPACE_ROUTES: dict[str, tuple[m.Cli.ResultCommandRoute, ...]] = {
    c.Infra.CLI_GROUP_REFACTOR: (
        m.Cli.ResultCommandRoute(
            name="migrate-mro",
            help_text="Migrate loose declarations into MRO facade classes",
            model_cls=m.Infra.RefactorMigrateMroInput,
            handler=lambda params: FlextInfraRefactorMigrateToClassMRO.execute_command(
                params
            ).map(_as_route_value),
        ),
        m.Cli.ResultCommandRoute(
            name="namespace-enforce",
            help_text="Scan workspace for namespace governance violations",
            model_cls=m.Infra.RefactorNamespaceEnforceInput,
            handler=lambda params: FlextInfraNamespaceEnforcer.execute_command(
                params
            ).map(_as_route_value),
        ),
        *(
            m.Cli.ResultCommandRoute(
                name=route_name,
                help_text=help_text,
                model_cls=model_cls,
                handler=lambda params, mc=model_cls: mc.execute_command(params),
            )
            for route_name, help_text, model_cls in (
                (
                    "census",
                    "Run a Rope-only workspace census for Python objects",
                    FlextInfraRefactorCensus,
                ),
            )
        ),
        m.Cli.ResultCommandRoute(
            name="accessor-migrate",
            help_text="Preview or apply automated get_/set_/is_ migration",
            model_cls=m.Infra.AccessorMigrationInput,
            handler=lambda params: (
                FlextInfraAccessorMigrationOrchestrator.execute_payload(params).map(
                    _as_route_value
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
            help_text="Fix print(), pdb, bare except and open() encoding in library code",
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
        # mro-j47u: legacy tests are outside production and have no refactor route.
    ),
    c.Infra.CLI_GROUP_RELEASE: (
        m.Cli.ResultCommandRoute(
            name=c.Infra.VERB_RUN,
            help_text="Run release orchestration CLI flow",
            model_cls=FlextInfraReleaseOrchestrator,
            handler=lambda params: FlextInfraReleaseOrchestrator.execute_command(
                params
            ).map(_as_route_value),
            success_message="Release completed successfully",
        ),
    ),
    c.Infra.CLI_GROUP_WORKSPACE: tuple(
        m.Cli.ResultCommandRoute(
            name=route_name,
            help_text=help_text,
            model_cls=model_cls,
            handler=lambda params, mc=model_cls: mc.execute_command(params),
        )
        for route_name, help_text, model_cls in (
            (
                "detect",
                "Detect workspace or standalone mode",
                FlextInfraWorkspaceDetector,
            ),
            ("sync", "Sync base.mk to project root", FlextInfraSyncService),
            (
                "orchestrate",
                "Run make verb across projects",
                FlextInfraOrchestratorService,
            ),
            (
                "migrate",
                "Migrate workspace projects to flext_infra tooling",
                FlextInfraProjectMigrator,
            ),
        )
    ),
}

__all__: list[str] = []
