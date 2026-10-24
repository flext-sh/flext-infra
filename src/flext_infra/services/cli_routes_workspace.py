"""Workspace and release CLI route ownership.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

from flext_core import FlextRuntime

import flext_infra
from flext_infra import c, check, m, p, r, t, u, workspace


class FlextInfraWorkspaceRoutes:
    """Own release and workspace command routes."""

    @staticmethod
    def _editable_members(
        params: p.Infra.WorkspaceRequest,
    ) -> p.Cli.ErasedCommandResult:
        """Print eligible relative member paths from installed provenance.

        Returns:
            The eligible count or the original provenance failure.

        """
        selected = workspace.FlextInfraWorkspaceEnvironmentProvenance.editable_members(
            params.repository_root,
        )
        if selected.failure:
            return r[int].from_failure(selected)
        for repository in selected.value:
            u.Cli.emit_raw(f"{repository.path}\n")
        return r[int].ok(len(selected.value))

    @staticmethod
    def _detect_workspace(
        params: workspace.FlextInfraWorkspaceDetector,
    ) -> p.Result[str]:
        """Expose the detected profile's wire value through the CLI transport.

        Returns:
            The profile string or the unchanged detection failure.

        """
        return workspace.FlextInfraWorkspaceDetector.execute_command(params).map(
            lambda profile: profile.value,
        )

    @staticmethod
    def _sync_environment(
        params: m.Infra.WorkspaceEnvironmentCliRequest,
    ) -> p.Cli.ErasedCommandResult:
        """Consume generated environment files through the public API binding.

        Returns:
            The canonical CLI result view.

        """
        request = m.Infra.WorkspaceEnvironmentSyncRequest.model_validate(
            params.model_dump(exclude={"scope"}),
        )
        return workspace.FlextInfraWorkspaceEnvironmentMixin.execute_request(
            request,
            synchronize=flext_infra.infra.sync_environment_files,
            scope=params.scope,
        )

    @staticmethod
    def _payload_json_formatter(payload: t.JsonPayload) -> str:
        """Serialize an erased command payload through the canonical JSON owner.

        Returns:
            The canonical JSON text of the payload.

        """
        encoded = u.Cli.json_dumps(FlextRuntime.normalize_to_json_value(payload))
        if encoded.failure:
            return encoded.error or "command payload serialization failed"
        return encoded.value

    @staticmethod
    def _capture_gate(
        params: m.Infra.GateCaptureRequest,
    ) -> p.Cli.ErasedCommandResult:
        """Retain the original checker process and return its unchanged status."""
        root = params.repository_root.expanduser().resolve()
        inputs = u.Infra.load_codegen_inputs(root).unwrap()
        report_output = u.Infra.env_value(
            inputs.spec.make.check_report_output_environment_variable
        )
        request = (
            params.model_copy(update={"report_output": Path(report_output)})
            if report_output
            else params
        )
        captured = u.Infra.git_capture_gate(
            request,
            inputs=inputs,
            load_inputs=u.Infra.load_codegen_inputs,
            read_runtime_identity=lambda gates: check.FlextInfraGateRegistry(
                project_gates=inputs.spec.make.project_check_gates
            ).runtime_identity(
                gates,
                installed_identity=(
                    workspace.FlextInfraWorkspaceEnvironmentProvenance.installed_toolchain_identity()
                ),
            ),
        ).unwrap()
        u.Cli.framework_exit(captured.process.raw_return_code)

    @staticmethod
    def release_routes() -> t.VariadicTuple[m.Cli.ResultCommandRoute]:
        """Build the release group's native model and handler bindings.

        Returns:
            The ordered release command routes.

        """
        return (
            m.Cli.ResultCommandRoute(
                name=c.Infra.VERB_RUN,
                help_text="Run release orchestration CLI flow",
                model_cls=m.Infra.ReleaseRunCommand,
                handler=flext_infra.infra.release_run,
                success_message="Release completed successfully",
            ),
        )

    @classmethod
    def workspace_routes(cls) -> t.VariadicTuple[m.Cli.ResultCommandRoute]:
        """Build the workspace group's native model and handler bindings.

        Returns:
            The ordered workspace command routes.

        """
        return (
            m.Cli.ResultCommandRoute(
                name="signing-identity",
                help_text="Inspect native public signing references without key access",
                model_cls=m.Infra.GitRepoRequest,
                handler=u.Infra.git_signing_identity,
                success_formatter=cls._payload_json_formatter,
            ),
            m.Cli.ResultCommandRoute(
                name="capture-gate",
                help_text="Execute the original checker once and publish its receipt",
                model_cls=m.Infra.GateCaptureRequest,
                handler=cls._capture_gate,
            ),
            m.Cli.ResultCommandRoute(
                name="validate-lifecycle",
                help_text="Validate the root and governed member lifecycles serially",
                model_cls=m.Infra.WorkspaceRequest,
                handler=workspace.FlextInfraWorkspaceLifecycle.execute_request,
                success_message="workspace serial lifecycle validated",
            ),
            m.Cli.ResultCommandRoute(
                name="lane-ownership",
                help_text="Authenticate a retained and integrated Git checkpoint",
                model_cls=m.Infra.GitLaneOwnershipRequest,
                handler=flext_infra.FlextInfraGitService.lane_ownership,
                success_formatter=cls._payload_json_formatter,
            ),
            m.Cli.ResultCommandRoute(
                name="verify-lane",
                help_text=(
                    "Verify stash absence and declared live integration ancestry "
                    "without effects"
                ),
                model_cls=m.Infra.GitLaneVerificationRequest,
                handler=flext_infra.FlextInfraGitService.verify_lane,
                success_message="lane stash and live integration ancestry verified",
            ),
            m.Cli.ResultCommandRoute(
                name="verify-lanes",
                help_text="Read-only lane inventory, ownership census, and refusals",
                model_cls=m.Infra.GitLaneVerificationRequest,
                handler=flext_infra.FlextInfraGitService.verify_lanes,
                success_message="lane inventory verified",
            ),
            m.Cli.ResultCommandRoute(
                name="identity",
                help_text="Report canonical Git checkout identity",
                model_cls=m.Infra.GitRepoRequest,
                handler=u.Infra.git_identity,
                success_message="workspace Git identity resolved",
            ),
            m.Cli.ResultCommandRoute(
                name="verify-clean",
                help_text=(
                    "Report staged, unstaged, and untracked changes without "
                    "rejecting WIP or requiring recovery cleanup"
                ),
                model_cls=m.Infra.GitStatusRequest,
                handler=flext_infra.FlextInfraGitService.verify_clean,
                success_message=(
                    "workspace Git status reported; existing work preserved"
                ),
            ),
            m.Cli.ResultCommandRoute(
                name="editable-members",
                help_text=(
                    "List declared members with authenticated installed editables"
                ),
                model_cls=m.Infra.WorkspaceRequest,
                handler=cls._editable_members,
            ),
            m.Cli.ResultCommandRoute(
                name="verify-environment",
                help_text="Verify live workspace editable provenance",
                model_cls=m.Infra.WorkspaceRequest,
                handler=(
                    workspace.FlextInfraWorkspaceEnvironmentProvenance.execute_request
                ),
                success_message="workspace editable provenance verified",
            ),
            m.Cli.ResultCommandRoute(
                name="verify-lock",
                help_text="Verify the committed uv.lock carries every referenced "
                "package",
                model_cls=m.Infra.WorkspaceRequest,
                handler=workspace.FlextInfraWorkspaceLockCompleteness.execute_request,
                success_message="lock completeness verified",
            ),
            *(
                m.Cli.ResultCommandRoute(
                    name=route_name,
                    help_text=help_text,
                    model_cls=model_cls,
                    handler=handler,
                )
                for route_name, help_text, model_cls, handler in (
                    (
                        "detect",
                        "Detect workspace or standalone mode",
                        workspace.FlextInfraWorkspaceDetector,
                        cls._detect_workspace,
                    ),
                    (
                        "propagate",
                        "Publish this workspace's flext-infra to every member",
                        workspace.FlextInfraWorkspacePropagation,
                        flext_infra.infra.workspace_propagate,
                    ),
                    (
                        "sync-environment",
                        "Sync generated direnv/mise environment files",
                        m.Infra.WorkspaceEnvironmentCliRequest,
                        cls._sync_environment,
                    ),
                    (
                        c.Infra.FLEET_ROUTE_NAME,
                        (
                            "Run one mutating verb in every governed member "
                            "in dependency order and publish its receipts"
                        ),
                        workspace.FlextInfraWorkspaceFleetVerbs,
                        workspace.FlextInfraWorkspaceFleetVerbs.execute_command,
                    ),
                    (
                        c.Infra.FLEET_GAPS_ROUTE_NAME,
                        (
                            "Report every declared repository's hygiene gaps "
                            "(dirty paths, open PRs, unmerged branches, "
                            "violation counts, standards presence) and publish "
                            "the receipt"
                        ),
                        workspace.FlextInfraWorkspaceFleetGaps,
                        workspace.FlextInfraWorkspaceFleetGaps.execute_command,
                    ),
                )
            ),
        )


__all__: list[str] = ["FlextInfraWorkspaceRoutes"]
