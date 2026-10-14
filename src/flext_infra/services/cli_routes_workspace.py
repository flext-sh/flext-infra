"""Workspace and release CLI route ownership.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import MutableMapping
from typing import ClassVar

from flext_infra import FlextInfraGitService, c, infra, m, p, r, t, u
from flext_infra.check.gate_registry import FlextInfraGateRegistry
from flext_infra.release.orchestrator import FlextInfraReleaseOrchestrator
from flext_infra.services.cli_routes_refactor import FlextInfraRefactorRoutes
from flext_infra.workspace import (
    FlextInfraFlextBindingService,
    FlextInfraWorkspaceDetector,
    FlextInfraWorkspaceEnvironmentMixin,
    FlextInfraWorkspaceEnvironmentProvenance,
    FlextInfraWorkspaceFleetGaps,
    FlextInfraWorkspaceFleetVerbs,
    FlextInfraWorkspaceLifecycle,
    FlextInfraWorkspaceLockCompleteness,
    FlextInfraWorkspacePropagation,
)


class FlextInfraWorkspaceRoutes(FlextInfraRefactorRoutes):
    """Own refactor, release, and workspace routes."""

    @staticmethod
    def _editable_members(
        params: m.Infra.WorkspaceRequest,
    ) -> p.Cli.ErasedCommandResult:
        """Print eligible relative member paths from installed provenance.

        Returns:
            The eligible count or the original provenance failure.

        """
        selected = FlextInfraWorkspaceEnvironmentProvenance.editable_members(
            params.repository_root,
        )
        if selected.failure:
            return selected
        for repository in selected.value:
            u.Cli.emit_raw(f"{repository.path}\n")
        return r[int].ok(len(selected.value))

    @staticmethod
    def _apply_flext_binding(
        params: m.Infra.FlextBindingRequest,
    ) -> p.Cli.ErasedCommandResult:
        """Apply the typed binding request through its service owner.

        Returns:
            The canonical CLI result view.

        """
        return FlextInfraFlextBindingService.apply(
            consumer_root=params.repository_root,
            flext_root=params.flext_root,
            python=params.python,
        )

    @staticmethod
    def _sync_environment(
        params: m.Infra.WorkspaceEnvironmentCliRequest,
    ) -> p.Cli.ErasedCommandResult:
        """Keep the internal beads render context off the public CLI surface.

        Returns:
            The canonical CLI result view.

        """
        request = m.Infra.WorkspaceEnvironmentSyncRequest.model_validate(
            params.model_dump(exclude={"scope"}),
        )
        return FlextInfraWorkspaceEnvironmentMixin.execute_request(
            request,
            scope=params.scope,
        )

    @staticmethod
    def _payload_json_formatter(payload: t.JsonPayload) -> str:
        """Serialize an erased command payload through the canonical JSON owner.

        Returns:
            The canonical JSON text of the payload.

        """
        encoded = u.Cli.json_dumps(u.normalize_to_json_value(payload))
        if encoded.failure:
            return encoded.error or "command payload serialization failed"
        return encoded.value

    @staticmethod
    def _capture_gate(
        params: m.Infra.GateCaptureRequest,
    ) -> p.Cli.ErasedCommandResult:
        """Retain the original checker process and return its unchanged status."""
        root = params.repository_root.expanduser().resolve()
        captured = u.Infra.git_capture_gate(
            params,
            inputs=u.Infra.load_codegen_inputs(root).unwrap(),
            load_inputs=u.Infra.load_codegen_inputs,
            read_runtime_identity=FlextInfraWorkspaceRoutes._check_runtime_identity,
        ).unwrap()
        u.Cli.framework_exit(captured.process.raw_return_code)

    @staticmethod
    def _check_runtime_identity(gate_ids: t.StrSequence) -> p.Result[str]:
        """Compose actual installed Python provenance and declared scanners.

        Returns:
            The resulting ``p.Result[str]``.
        """
        return FlextInfraGateRegistry.default().runtime_identity(
            gate_ids,
            installed_identity=(
                FlextInfraWorkspaceEnvironmentProvenance.installed_toolchain_identity()
            ),
        )

    workspace_routes: ClassVar[
        MutableMapping[str, t.VariadicTuple[m.Cli.ResultCommandRoute]]
    ] = {
        c.Infra.CLI_GROUP_REFACTOR: FlextInfraRefactorRoutes.refactor_routes,
        c.Infra.CLI_GROUP_RELEASE: (
            m.Cli.ResultCommandRoute(
                name=c.Infra.VERB_RUN,
                help_text="Run release orchestration CLI flow",
                model_cls=FlextInfraReleaseOrchestrator,
                handler=infra.release_run,
                success_message="Release completed successfully",
            ),
        ),
        c.Infra.CLI_GROUP_WORKSPACE: (
            m.Cli.ResultCommandRoute(
                name="signing-identity",
                help_text="Inspect native public signing references without key access",
                model_cls=m.Infra.GitRepoRequest,
                handler=u.Infra.git_signing_identity,
                success_formatter=_payload_json_formatter,
            ),
            m.Cli.ResultCommandRoute(
                name="capture-gate",
                help_text="Execute the original checker once and publish its receipt",
                model_cls=m.Infra.GateCaptureRequest,
                handler=_capture_gate,
            ),
            m.Cli.ResultCommandRoute(
                name="validate-lifecycle",
                help_text="Validate the root and governed member lifecycles serially",
                model_cls=m.Infra.WorkspaceRequest,
                handler=FlextInfraWorkspaceLifecycle.execute_request,
                success_message="workspace serial lifecycle validated",
            ),
            m.Cli.ResultCommandRoute(
                name="verify-lane",
                help_text=(
                    "Verify stash absence and declared live integration ancestry "
                    "without effects"
                ),
                model_cls=m.Infra.GitLaneVerificationRequest,
                handler=FlextInfraGitService.verify_lane,
                success_message="lane stash and live integration ancestry verified",
            ),
            m.Cli.ResultCommandRoute(
                name="verify-lanes",
                help_text="Read-only lane inventory, ownership census, and refusals",
                model_cls=m.Infra.GitLaneVerificationRequest,
                handler=FlextInfraGitService.verify_lanes,
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
                    "Reject staged, unstaged, untracked changes and stash entries"
                ),
                model_cls=m.Infra.GitStatusRequest,
                handler=FlextInfraGitService.verify_clean,
                success_message=(
                    "workspace Git worktree is clean and has no stash entries"
                ),
            ),
            m.Cli.ResultCommandRoute(
                name="editable-members",
                help_text=(
                    "List declared members with authenticated installed editables"
                ),
                model_cls=m.Infra.WorkspaceRequest,
                handler=_editable_members,
            ),
            m.Cli.ResultCommandRoute(
                name="verify-environment",
                help_text="Verify live workspace editable provenance",
                model_cls=m.Infra.WorkspaceRequest,
                handler=FlextInfraWorkspaceEnvironmentProvenance.execute_request,
                success_message="workspace editable provenance verified",
            ),
            m.Cli.ResultCommandRoute(
                name="verify-lock",
                help_text="Verify the committed uv.lock carries every referenced "
                "package",
                model_cls=m.Infra.WorkspaceRequest,
                handler=FlextInfraWorkspaceLockCompleteness.execute_request,
                success_message="lock completeness verified",
            ),
            m.Cli.ResultCommandRoute(
                name="flext-binding",
                help_text="Bind this project onto a flext worktree for the session",
                model_cls=m.Infra.FlextBindingRequest,
                handler=_apply_flext_binding,
                success_message="flext worktree binding applied",
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
                        FlextInfraWorkspaceDetector,
                        FlextInfraWorkspaceDetector.execute_command,
                    ),
                    (
                        "propagate",
                        "Publish this workspace's flext-infra to every member",
                        FlextInfraWorkspacePropagation,
                        infra.workspace_propagate,
                    ),
                    (
                        "sync-environment",
                        "Sync generated direnv/mise environment files",
                        m.Infra.WorkspaceEnvironmentCliRequest,
                        _sync_environment,
                    ),
                    (
                        c.Infra.FLEET_ROUTE_NAME,
                        (
                            "Run one mutating verb in every governed member "
                            "in dependency order and publish its receipts"
                        ),
                        FlextInfraWorkspaceFleetVerbs,
                        FlextInfraWorkspaceFleetVerbs.execute_command,
                    ),
                    (
                        c.Infra.FLEET_GAPS_ROUTE_NAME,
                        (
                            "Report every declared repository's hygiene gaps "
                            "(dirty paths, open PRs, unmerged branches, "
                            "violation counts, standards presence) and publish "
                            "the receipt"
                        ),
                        FlextInfraWorkspaceFleetGaps,
                        FlextInfraWorkspaceFleetGaps.execute_command,
                    ),
                )
            ),
        ),
    }


__all__: list[str] = ["FlextInfraWorkspaceRoutes"]
