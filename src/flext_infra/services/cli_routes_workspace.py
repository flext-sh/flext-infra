"""Workspace and release CLI route ownership.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

from flext_infra import (
    FlextInfraGitService,
    c,
    check,
    config,
    docs,
    infra,
    m,
    p,
    r,
    t,
    u,
    workspace,
)


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
    def _verify_lane(
        request: p.Infra.GitLaneVerificationRequest,
    ) -> p.Cli.ErasedCommandResult:
        """Publish the live integration identity as its owning model.

        Returns:
            The live integration identity or the original admission failure.

        """
        return FlextInfraGitService.verify_lane(request).map(
            m.Infra.GitOidReport.model_validate
        )

    @staticmethod
    def _git_identity(
        request: p.Infra.GitRepoRequest,
    ) -> p.Cli.ErasedCommandResult:
        """Publish the canonical Git checkout identity as its owning model.

        Returns:
            The checkout identity or the original resolution failure.

        """
        return u.Infra.git_identity(request).map(
            m.Infra.GitIdentityReport.model_validate
        )

    @staticmethod
    def _tests(
        params: p.Infra.WorkspaceTestsRequest,
        *,
        execution_mode: c.Infra.PytestExecutionMode = (
            c.Infra.PytestExecutionMode.GLOBAL_INCREMENTAL
        ),
    ) -> p.Cli.ErasedCommandResult:
        """Preserve the first native test status at the CLI boundary.

        Returns:
            The successful native test result or its unchanged failure.

        """
        full = execution_mode is c.Infra.PytestExecutionMode.FULL
        gate = c.Infra.VERB_TEST_FULL if full else c.Infra.VERB_TEST
        if full:
            u.Infra.gate_repeat_refuse(
                gate,
                params.repository_root,
                config.Infra.gate_admission.repeat.tests_full,
            )
        with u.Infra.gate_admitted(gate, params.repository_root) as ticket:
            completed = infra.workspace_tests(params, execution_mode=execution_mode)
        if completed.failure:
            return r[int].from_failure(completed)
        if completed.value:
            u.Cli.framework_exit(completed.value)
        if full:
            u.Infra.gate_repeat_record(ticket)
        return completed

    @classmethod
    def _tests_full(
        cls, params: p.Infra.WorkspaceTestsRequest
    ) -> p.Cli.ErasedCommandResult:
        """Run one complete native suite without Testmon or an incremental pre-run.

        Returns:
            The native result, preserving the first failing status.

        """
        return cls._tests(params, execution_mode=c.Infra.PytestExecutionMode.FULL)

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
        encoded = u.Cli.json_dumps(u.normalize_to_json_value(payload))
        if encoded.failure:
            return encoded.error or "command payload serialization failed"
        return encoded.value

    @classmethod
    def _capture_gate(
        cls,
        params: p.Infra.GateCaptureRequest,
    ) -> p.Cli.ErasedCommandResult:
        """Retain the original checker process and return its unchanged status.

        Returns:
            The input or capture failure; a captured status exits with itself.

        """
        root = params.repository_root.expanduser().resolve()
        status = u.Infra.load_codegen_inputs(root).flat_map(
            lambda inputs: cls._captured_gate_status(params, inputs)
        )
        if status.success:
            u.Cli.framework_exit(status.value)
        return r[bool].from_failure(status)

    @classmethod
    def _check(
        cls,
        params: p.Infra.GateCaptureRequest,
    ) -> p.Cli.ErasedCommandResult:
        """Run every read-only validation of the check verb in one process.

        The captured checker completes its declared global prerequisites before
        other gates. The projection verdict, lane census (outside CI), and
        documentation follow; a dirty or changing tree is never a check
        condition. The commit hook token selects only commit-stage gates. The
        first failure stops the verb with its original status or cause. The
        verb joins the host queue first and arms the largest declared gate
        budget only once admitted; a complete check that succeeded in this
        checkout inside its repeat window is refused before it queues
        (ADR-032).

        Returns:
            True once every validation passed, or the first failure.

        """
        root = params.repository_root.expanduser().resolve()
        loaded = u.Infra.load_codegen_inputs(root)
        if loaded.failure:
            return r[bool].from_failure(loaded)
        inputs = loaded.value
        make = inputs.spec.make
        spec = workspace.FlextInfraWorkspaceDetector.load_workspace_spec(
            root, inputs=inputs
        )
        if spec.failure:
            return r[bool].from_failure(spec)
        members = spec.value.subprojects
        grace = c.Infra.TIMEOUT_KILL_AFTER_SECONDS
        budget = m.Infra.RouteBudgetSpec(
            budget_seconds=check.FlextInfraGateRegistry(
                project_gates=make.project_check_gates
            ).check_budget_seconds(
                make.check_gates_default,
                (root, *(root / member.path for member in members)),
            )
            + 2 * grace,
            grace_seconds=grace,
        )
        complete = (
            params.phase == c.Infra.CheckPhase.COMPLETE
            and u.Infra.env_value(make.ci.variable) != make.ci.pre_commit_value
        )
        if complete:
            u.Infra.gate_repeat_refuse(
                c.Infra.VERB_CHECK, root, config.Infra.gate_admission.repeat.check
            )
        with u.Infra.gate_admitted_budget(c.Infra.VERB_CHECK, root, budget) as ticket:
            result = cls._check_admitted(params, root, inputs)
        if complete and result.success:
            u.Infra.gate_repeat_record(ticket)
        return result

    @classmethod
    def _check_admitted(
        cls,
        params: p.Infra.GateCaptureRequest,
        root: Path,
        inputs: p.Infra.CodegenInputs,
    ) -> p.Cli.ErasedCommandResult:
        """Run the admitted check validations under the armed budget.

        Returns:
            True once every validation passed, or the first failure.

        """
        make = inputs.spec.make
        token = u.Infra.env_value(make.ci.variable)
        complete = (
            params.phase == c.Infra.CheckPhase.COMPLETE
            and token != make.ci.pre_commit_value
        )
        status = cls._captured_gate_status(params, inputs)
        if status.failure:
            return r[bool].from_failure(status)
        if status.value:
            u.Cli.framework_exit(status.value)
        if complete:
            conformed = infra.codegen_conform(
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
            lanes = FlextInfraGitService.verify_lanes(
                m.Infra.GitLaneVerificationRequest(repo_root=root)
            )
            if lanes.failure:
                return r[bool].from_failure(lanes)
        for service in (docs.FlextInfraDocValidator, docs.FlextInfraDocAuditor):
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
        params: p.Infra.GateCaptureRequest,
        inputs: p.Infra.CodegenInputs,
    ) -> p.Result[int]:
        """Capture the original checker once and return its unchanged status.

        Returns:
            The checker process's raw return code, or the capture failure.

        """
        report_output = u.Infra.env_value(
            inputs.spec.make.check_report_output_environment_variable
        )
        request = (
            params.model_copy(update={"report_output": Path(report_output)})
            if report_output
            else params
        )

        def runtime_identity(gates: Sequence[str]) -> p.Result[str]:
            return check.FlextInfraGateRegistry(
                project_gates=inputs.spec.make.project_check_gates
            ).runtime_identity(
                gates,
                installed_identity=(
                    workspace.FlextInfraWorkspaceEnvironmentProvenance.installed_toolchain_identity()
                ),
            )

        return u.Infra.git_capture_gate(
            request,
            inputs=inputs,
            load_inputs=u.Infra.load_codegen_inputs,
            read_runtime_identity=runtime_identity,
        ).map(lambda captured: captured.process.raw_return_code)

    @staticmethod
    def _attestation_context(
        workspace_path: str,
    ) -> p.Result[p.Infra.WorkspaceRuntimeContext]:
        """Elect the runtime context for one attestation request.

        Returns:
            The elected runtime context or its first election failure.

        """
        return workspace.FlextInfraWorkspaceDetector.resolution_context(
            Path(workspace_path).expanduser().resolve()
        )

    @classmethod
    def _create_gate_attestation(
        cls,
        params: p.Infra.GateAttestationCreateRequest,
    ) -> p.Result[p.Infra.GateAttestationReport]:
        """Sign one original receipt without publishing repository state.

        Returns:
            The signed stage proof or the original verification failure.

        """
        context = cls._attestation_context(params.workspace)
        if context.failure:
            return r[p.Infra.GateAttestationReport].from_failure(context)
        return u.Infra.git_create_gate_attestation(params, context.value)

    @classmethod
    def _verify_gate_attestation(
        cls,
        params: p.Infra.GateAttestationVerifyRequest,
    ) -> p.Result[p.Infra.GateAttestationReport]:
        """Verify one signed stage proof against the elected live runtime.

        Returns:
            The verified stage proof or the original verification failure.

        """
        context = cls._attestation_context(params.workspace)
        if context.failure:
            return r[p.Infra.GateAttestationReport].from_failure(context)
        return u.Infra.git_verify_gate_attestation(params, context.value)

    @classmethod
    def _admit_gate_candidate(
        cls,
        params: p.Infra.GateCandidateAdmissionRequest,
    ) -> p.Result[p.Infra.GateCandidateAdmissionReport]:
        """Admit one exact candidate against a signed stage proof.

        Returns:
            The admission decision or the original verification failure.

        """
        context = cls._attestation_context(params.workspace)
        if context.failure:
            return r[p.Infra.GateCandidateAdmissionReport].from_failure(context)
        return u.Infra.git_admit_gate_candidate(params, context.value)

    @staticmethod
    def release_routes() -> tuple[p.Cli.ResultCommandRoute, ...]:
        """Build the release group's native model and handler bindings.

        Returns:
            The ordered release command routes.

        """
        return u.Infra.result_routes((
            (
                c.Infra.VERB_RUN,
                "Run release orchestration CLI flow",
                m.Infra.ReleaseRunCommand,
                infra.release_run,
                "Release completed successfully",
            ),
        ))

    @classmethod
    def workspace_routes(cls) -> tuple[p.Cli.ResultCommandRoute, ...]:
        """Build the workspace group's native model and handler bindings.

        The routes that format their JSON payload stay explicit; every
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
                name="verify-lanes",
                help_text="Read-only lane inventory, ownership census, and refusals",
                model_cls=m.Infra.GitLaneVerificationRequest,
                handler=FlextInfraGitService.verify_lanes,
                success_formatter=cls._payload_json_formatter,
            ),
            m.Cli.ResultCommandRoute(
                name="lane-ownership",
                help_text="Authenticate a retained and integrated Git checkpoint",
                model_cls=m.Infra.GitLaneOwnershipRequest,
                handler=FlextInfraGitService.lane_ownership,
                success_formatter=cls._payload_json_formatter,
            ),
            m.Cli.ResultCommandRoute(
                name="create-gate-attestation",
                help_text="Sign one original receipt as an immutable stage proof",
                model_cls=m.Infra.GateAttestationCreateRequest,
                handler=cls._create_gate_attestation,
                success_formatter=cls._payload_json_formatter,
            ),
            m.Cli.ResultCommandRoute(
                name="verify-gate-attestation",
                help_text="Verify one signed stage proof against the live runtime",
                model_cls=m.Infra.GateAttestationVerifyRequest,
                handler=cls._verify_gate_attestation,
                success_formatter=cls._payload_json_formatter,
            ),
            m.Cli.ResultCommandRoute(
                name="admit-gate-candidate",
                help_text="Admit an exact candidate against a signed stage proof",
                model_cls=m.Infra.GateCandidateAdmissionRequest,
                handler=cls._admit_gate_candidate,
                success_formatter=cls._payload_json_formatter,
            ),
            m.Cli.ResultCommandRoute(
                name=c.Infra.FLEET_GAPS_ROUTE_NAME,
                help_text=(
                    "Report every declared repository's hygiene gaps (dirty paths, "
                    "open PRs, unmerged branches, violation counts, standards "
                    "presence) and publish the receipt"
                ),
                model_cls=workspace.FlextInfraWorkspaceFleetGaps,
                handler=workspace.FlextInfraWorkspaceFleetGaps.execute_command,
                success_formatter=cls._payload_json_formatter,
            ),
            *u.Infra.result_routes((
                (
                    c.Infra.VERB_TEST,
                    "Run native persistent incremental tests",
                    m.Infra.WorkspaceTestsRequest,
                    cls._tests,
                    None,
                ),
                (
                    c.Infra.VERB_TEST_FULL,
                    "Run the complete selected tests once without Testmon",
                    m.Infra.WorkspaceTestsRequest,
                    cls._tests_full,
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
                    cls._verify_lane,
                    "lane stash and live integration ancestry verified",
                ),
                (
                    "identity",
                    "Report canonical Git checkout identity",
                    m.Infra.GitRepoRequest,
                    cls._git_identity,
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
                    infra.workspace_propagate,
                    None,
                ),
            )),
        )


__all__: list[str] = ["FlextInfraWorkspaceRoutes"]
