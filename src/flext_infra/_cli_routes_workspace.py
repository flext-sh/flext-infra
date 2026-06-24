"""Workspace-cluster CLI route definitions for flext-infra."""

from __future__ import annotations

from flext_infra import (
    FlextInfraAccessorMigrationOrchestrator,
    FlextInfraNamespaceEnforcer,
    FlextInfraOrchestratorService,
    FlextInfraProjectMigrator,
    FlextInfraRefactorCensus,
    FlextInfraRefactorMigrateToClassMRO,
    FlextInfraReleaseOrchestrator,
    FlextInfraSyncService,
    FlextInfraWorkspaceDetector,
    c,
    m,
)
from flext_infra.refactor.wrapper_root_namespace import (
    FlextInfraWrapperRootNamespaceRefactor,
)

ROUTES: dict[str, tuple[m.Cli.ResultCommandRoute, ...]] = {
    c.Infra.CLI_GROUP_REFACTOR: (
        # ``migrate-mro`` and ``namespace-enforce`` register one input model
        # but dispatch to a different orchestrator's classmethod; the rest
        # follow the model_cls.execute_command default.
        m.Cli.ResultCommandRoute(
            name="migrate-mro",
            help_text="Migrate loose declarations into MRO facade classes",
            model_cls=m.Infra.RefactorMigrateMroInput,
            handler=lambda params: FlextInfraRefactorMigrateToClassMRO.execute_command(
                params
            ),
        ),
        m.Cli.ResultCommandRoute(
            name="namespace-enforce",
            help_text="Scan workspace for namespace governance violations",
            model_cls=m.Infra.RefactorNamespaceEnforceInput,
            handler=lambda params: FlextInfraNamespaceEnforcer.execute_command(params),
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
                (
                    "accessor-migrate",
                    "Preview or apply automated get_/set_/is_ migration",
                    FlextInfraAccessorMigrationOrchestrator,
                ),
            )
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
    ),
    c.Infra.CLI_GROUP_RELEASE: (
        m.Cli.ResultCommandRoute(
            name=c.Infra.VERB_RUN,
            help_text="Run release orchestration CLI flow",
            model_cls=FlextInfraReleaseOrchestrator,
            handler=lambda params: FlextInfraReleaseOrchestrator.execute_command(
                params
            ),
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
            (
                "sync",
                "Sync base.mk to project root",
                FlextInfraSyncService,
            ),
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

__all__: list[str] = ["ROUTES"]
