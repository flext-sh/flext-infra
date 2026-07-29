"""Workspace and release loaders selected by the generated CLI registry."""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_infra.services.cli_route_base import CliRouteBase

if TYPE_CHECKING:
    from flext_infra import p, t


class WorkspaceRoutes(CliRouteBase):
    """Load exactly one workspace or release implementation."""

    @staticmethod
    def load_run(name: str, help_text: str) -> t.SequenceOf[p.Cli.ResultCommandRoute]:
        """Load the selected release route."""
        from flext_infra.release.orchestrator import FlextInfraReleaseOrchestrator

        return CliRouteBase.command_route(
            name,
            help_text,
            FlextInfraReleaseOrchestrator,
            lambda params: FlextInfraReleaseOrchestrator.execute_command(params).map(
                CliRouteBase.as_route_value
            ),
            success_message="Release completed successfully",
        )

    @staticmethod
    def load_verify_environment(
        name: str, help_text: str
    ) -> t.SequenceOf[p.Cli.ResultCommandRoute]:
        """Load the selected environment-provenance route."""
        from flext_infra import m
        from flext_infra.workspace.environment_provenance import (
            FlextInfraWorkspaceEnvironmentProvenance,
        )

        return CliRouteBase.command_route(
            name,
            help_text,
            m.Infra.WorkspaceEnvironmentRequest,
            lambda params: FlextInfraWorkspaceEnvironmentProvenance.execute_request(
                params
            ).map(CliRouteBase.as_route_value),
            success_message="workspace editable provenance verified",
        )

    @staticmethod
    def load_detect(
        name: str, help_text: str
    ) -> t.SequenceOf[p.Cli.ResultCommandRoute]:
        """Load the selected workspace detector."""
        from flext_infra.workspace.detector import FlextInfraWorkspaceDetector

        return CliRouteBase.command_route(
            name,
            help_text,
            FlextInfraWorkspaceDetector,
            FlextInfraWorkspaceDetector.execute_command,
        )

    @staticmethod
    def load_sync(name: str, help_text: str) -> t.SequenceOf[p.Cli.ResultCommandRoute]:
        """Load the selected workspace sync route."""
        from flext_infra.workspace.sync import FlextInfraSyncService

        return CliRouteBase.command_route(
            name,
            help_text,
            FlextInfraSyncService,
            FlextInfraSyncService.execute_command,
        )

    @staticmethod
    def load_orchestrate(
        name: str, help_text: str
    ) -> t.SequenceOf[p.Cli.ResultCommandRoute]:
        """Load the selected workspace orchestration route."""
        from flext_infra.workspace.orchestrator import FlextInfraOrchestratorService

        return CliRouteBase.command_route(
            name,
            help_text,
            FlextInfraOrchestratorService,
            FlextInfraOrchestratorService.execute_command,
        )

    @staticmethod
    def load_serialize_make(
        name: str, help_text: str
    ) -> t.SequenceOf[p.Cli.ResultCommandRoute]:
        """Load the selected serialized Make route."""
        from flext_infra.workspace.make_serialization import (
            FlextInfraMakeSerializationService,
        )

        return CliRouteBase.command_route(
            name,
            help_text,
            FlextInfraMakeSerializationService,
            FlextInfraMakeSerializationService.execute_command,
        )

    @staticmethod
    def load_migrate(
        name: str, help_text: str
    ) -> t.SequenceOf[p.Cli.ResultCommandRoute]:
        """Load the selected workspace migration route."""
        from flext_infra.workspace.migrator import FlextInfraProjectMigrator

        return CliRouteBase.command_route(
            name,
            help_text,
            FlextInfraProjectMigrator,
            FlextInfraProjectMigrator.execute_command,
        )

    @staticmethod
    def load_worktree(
        name: str, help_text: str
    ) -> t.SequenceOf[p.Cli.ResultCommandRoute]:
        """Load the selected worktree route."""
        from flext_infra import FlextInfraWorktreeService

        return CliRouteBase.command_route(
            name,
            help_text,
            FlextInfraWorktreeService,
            FlextInfraWorktreeService.execute_command,
        )


__all__: list[str] = ["WorkspaceRoutes"]
