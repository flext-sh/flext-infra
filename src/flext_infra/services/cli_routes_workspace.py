"""Workspace and release CLI route ownership.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

from flext_core import FlextRuntime

import flext_infra
from flext_infra import c, check, m, p, r, t, u, workspace
from flext_infra.docs import FlextInfraDocAuditor, FlextInfraDocValidator


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
    def _tests(params: m.Infra.WorkspaceTestsRequest) -> p.Cli.ErasedCommandResult:
        """Preserve the first native test status at the CLI boundary.

        Returns:
            The successful native test result or its unchanged failure.

        """
        completed = flext_infra.infra.workspace_tests(params)
        if completed.failure:
            return r[int].from_failure(completed)
        if completed.value:
            u.Cli.framework_exit(completed.value)
        return completed

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
    def _payload_json_formatter(payload: t.JsonPayload) -> str:
        """Serialize an erased command payload through the canonical JSON owner.

        Returns:
            The canonical JSON text of the payload.

        """
        encoded = u.Cli.json_dumps(FlextRuntime.normalize_to_json_value(payload))
        if encoded.failure:
            return encoded.error or "command payload serialization failed"
        return encoded.value

    @classmethod
    def _capture_gate(
        cls,
        params: m.Infra.GateCaptureRequest,
    ) -> p.Cli.ErasedCommandResult:
        """Retain the original checker process and return its unchanged status."""
        root = params.repository_root.expanduser().resolve()
        inputs = u.Infra.load_codegen_inputs(root).unwrap()
        u.Cli.framework_exit(cls._captured_gate_status(params, inputs))

    @classmethod
    def _check(
        cls,
        params: m.Infra.GateCaptureRequest,
    ) -> p.Cli.ErasedCommandResult:
        """Run every read-only validation of the check verb in one process.

        The captured checker completes its declared global prerequisites before
        other gates. The projection verdict, lane census (outside CI), and
        documentation follow; a dirty or changing tree is never a check
        condition. The commit hook token selects only commit-stage gates. The
        first failure stops the verb with its original status or cause.

        Returns:
            True once every validation passed, or the first failure.

        """
        root = params.repository_root.expanduser().resolve()
        inputs = u.Infra.load_codegen_inputs(root).unwrap()
        make = inputs.spec.make
        token = u.Infra.env_value(make.ci.variable)
        complete = token != make.ci.pre_commit_value
        status = cls._captured_gate_status(params, inputs)
        if status:
            u.Cli.framework_exit(status)
        if complete:
            conformed = flext_infra.infra.codegen_conform(
                m.Infra.CodegenConformRequest(
                    root=root,
                    scope=c.Infra.CodegenConformScope.SELF,
                    mode=c.Infra.CodegenConformMode.CHECK,
                )
            )
            if conformed.failure:
                return r[bool].from_failure(conformed)
        if not complete:
            return r[bool].ok(value=True)
        if token != make.ci.value:
            lanes = flext_infra.FlextInfraGitService.verify_lanes(
                m.Infra.GitLaneVerificationRequest(repo_root=root)
            )
            if lanes.failure:
                return r[bool].from_failure(lanes)
        for service in (FlextInfraDocValidator, FlextInfraDocAuditor):
            documented = service(
                repository_root=root,
                output_dir=make.docs.reports_dir,
                selected_projects=(Path().as_posix(),),
            ).execute()
            if documented.failure:
                return r[bool].from_failure(documented)
        return r[bool].ok(value=True)

    @staticmethod
    def _captured_gate_status(
        params: m.Infra.GateCaptureRequest,
        inputs: m.Infra.CodegenInputs,
    ) -> int:
        """Capture the original checker once and return its unchanged status.

        Returns:
            The checker process's raw return code.

        """
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
        return captured.process.raw_return_code

    @staticmethod
    def release_routes() -> t.VariadicTuple[m.Cli.ResultCommandRoute]:
        """Build the release group's native model and handler bindings.

        Returns:
            The ordered release command routes.

        """
        return u.Infra.result_routes((
            (
                c.Infra.VERB_RUN,
                "Run release orchestration CLI flow",
                m.Infra.ReleaseRunCommand,
                flext_infra.infra.release_run,
                "Release completed successfully",
            ),
        ))

    @classmethod
    def workspace_routes(cls) -> t.VariadicTuple[m.Cli.ResultCommandRoute]:
        """Build the workspace group's native model and handler bindings.

        The two routes that format their JSON payload stay explicit; every
        other route is one data row of the shared route-table builder.

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
                name="lane-ownership",
                help_text="Authenticate a retained and integrated Git checkpoint",
                model_cls=m.Infra.GitLaneOwnershipRequest,
                handler=flext_infra.FlextInfraGitService.lane_ownership,
                success_formatter=cls._payload_json_formatter,
            ),
            *u.Infra.result_routes((
                (
                    c.Infra.VERB_TEST,
                    "Run persistent incremental tests after global source admission",
                    m.Infra.WorkspaceTestsRequest,
                    cls._tests,
                    None,
                ),
                (
                    "capture-gate",
                    "Execute the original checker once and publish its receipt",
                    m.Infra.GateCaptureRequest,
                    cls._capture_gate,
                    None,
                ),
                (
                    c.Infra.VERB_CHECK,
                    "Run every read-only validation of the check verb in one process",
                    m.Infra.GateCaptureRequest,
                    cls._check,
                    "check verb validations passed",
                ),
                (
                    "verify-lane",
                    (
                        "Verify stash absence and declared live integration ancestry "
                        "without effects"
                    ),
                    m.Infra.GitLaneVerificationRequest,
                    flext_infra.FlextInfraGitService.verify_lane,
                    "lane stash and live integration ancestry verified",
                ),
                (
                    "verify-lanes",
                    "Read-only lane inventory, ownership census, and refusals",
                    m.Infra.GitLaneVerificationRequest,
                    flext_infra.FlextInfraGitService.verify_lanes,
                    "lane inventory verified",
                ),
                (
                    "identity",
                    "Report canonical Git checkout identity",
                    m.Infra.GitRepoRequest,
                    u.Infra.git_identity,
                    "workspace Git identity resolved",
                ),
                (
                    "editable-members",
                    "List declared members with authenticated installed editables",
                    m.Infra.WorkspaceRequest,
                    cls._editable_members,
                    None,
                ),
                (
                    c.Infra.FLEXT_EDITABLE_ROUTE_NAME,
                    (
                        "Install and record setup's FLEXT editable selection; without "
                        "--flext-root remove the receipt"
                    ),
                    m.Infra.FlextEditableRequest,
                    workspace.FlextInfraWorkspaceFlextEditable.execute_request,
                    None,
                ),
                (
                    "verify-environment",
                    "Verify live workspace editable provenance",
                    m.Infra.WorkspaceRequest,
                    workspace.FlextInfraWorkspaceEnvironmentProvenance.execute_request,
                    "workspace editable provenance verified",
                ),
                (
                    "verify-lock",
                    "Verify the committed uv.lock carries every referenced package",
                    m.Infra.WorkspaceRequest,
                    workspace.FlextInfraWorkspaceLockCompleteness.execute_request,
                    "lock completeness verified",
                ),
                (
                    "detect",
                    "Detect workspace or standalone mode",
                    workspace.FlextInfraWorkspaceDetector,
                    cls._detect_workspace,
                    None,
                ),
                (
                    "propagate",
                    "Publish this workspace's flext-infra to every member",
                    workspace.FlextInfraWorkspacePropagation,
                    flext_infra.infra.workspace_propagate,
                    None,
                ),
                (
                    c.Infra.FLEET_GAPS_ROUTE_NAME,
                    (
                        "Report every declared repository's hygiene gaps (dirty paths, "
                        "open PRs, unmerged branches, violation counts, standards "
                        "presence) and publish the receipt"
                    ),
                    workspace.FlextInfraWorkspaceFleetGaps,
                    workspace.FlextInfraWorkspaceFleetGaps.execute_command,
                    None,
                ),
            )),
        )


__all__: list[str] = ["FlextInfraWorkspaceRoutes"]
