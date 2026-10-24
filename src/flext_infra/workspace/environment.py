"""Consume generated direnv files through the existing conformance planner.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING

from flext_infra import c, m, r, t, u

if TYPE_CHECKING:
    from pathlib import Path

    from flext_infra import p


class FlextInfraWorkspaceEnvironmentMixin:
    """Consume the current projection and authorize its native environment."""

    @staticmethod
    def sync_environment_files(
        request: m.Infra.WorkspaceEnvironmentSyncRequest,
        *,
        planner: p.Infra.CandidateBootstrapPlanner,
        runner: p.Cli.CommandRunner,
    ) -> p.Result[m.Infra.WorkspaceEnvironmentSyncResult]:
        """Consume the canonical environment without generating or repairing it.

        Returns:
            The consumed file and native authorization status, or the original
            planning, drift, physical-state or process failure.

        """
        result_type = r[m.Infra.WorkspaceEnvironmentSyncResult]
        root = request.repository_root.expanduser().resolve()
        envrc = root / c.Infra.ENVRC_FILENAME
        if envrc.is_symlink():
            return result_type.fail(
                f"refusing to authorize symlinked environment: {envrc}",
            )
        inputs = u.Infra.load_codegen_inputs(root)
        if inputs.failure:
            return result_type.from_failure(inputs)
        planned = FlextInfraWorkspaceEnvironmentMixin._plan_environment_projection(
            root,
            inputs.value,
            planner,
        )
        if planned.failure:
            return result_type.from_failure(planned)
        files = planned.value.files
        environment_file = next(file for file in files if file.path == envrc)
        verified = FlextInfraWorkspaceEnvironmentMixin._verify_environment_consumption(
            inputs.value,
            files,
            envrc=envrc,
        )
        if verified.failure:
            return result_type.from_failure(verified)
        if request.allow_direnv:
            allowed = FlextInfraWorkspaceEnvironmentMixin._authorize_environment(
                root,
                inputs.value,
                files,
                runner,
            )
            if allowed.failure:
                return result_type.from_failure(allowed)
        u.Cli.info(
            f"environment projection consumed: {envrc}; "
            f"authorized={request.allow_direnv}",
        )
        return result_type.ok(
            m.Infra.WorkspaceEnvironmentSyncResult(
                environment_file=environment_file.path,
                authorized=request.allow_direnv,
            ),
        )

    @staticmethod
    def _plan_environment_projection(
        root: Path,
        inputs: m.Infra.CodegenInputs,
        planner: p.Infra.CandidateBootstrapPlanner,
    ) -> p.Result[m.Infra.CodegenPlan]:
        """Plan the exact declared environment closure without publishing it.

        Returns:
            The original fixed-point plan, or its first native failure.

        Raises:
            BaseException: The original native planning exception, unchanged.

        """
        result_type = r[m.Infra.CodegenPlan]
        envrc = root / c.Infra.ENVRC_FILENAME
        planned = planner.plan_repositories(
            m.Infra.CodegenGenerateRequest(
                root=root,
                what=c.Infra.CodegenConformSurface.ENVRC,
            ),
            inputs,
        )
        if planned.failure:
            return result_type.from_failure(planned)
        plan = planned.value
        if plan.exception is not None:
            raise plan.exception
        if plan.issues:
            return result_type.fail(plan.issues[0].formatted)
        destinations = inputs.spec.templates.required_destinations(
            frozenset((c.Infra.ENVRC_FILENAME,))
        )
        expected = frozenset(root / destination for destination in destinations)
        observed = frozenset(file.path for file in plan.files)
        if observed != expected or len(plan.files) != len(expected):
            return result_type.fail(
                f"environment consumption requires its exact declared closure: {envrc}",
            )
        current = u.Infra.codegen_fixed_point(
            plan.files,
            subject=f"environment projection {envrc}",
        )
        if current.failure:
            return result_type.from_failure(current)
        return result_type.ok(plan)

    @staticmethod
    def _verify_environment_consumption(
        inputs: m.Infra.CodegenInputs,
        files: t.SequenceOf[m.Infra.CodegenFilePlan],
        *,
        envrc: Path,
    ) -> p.Result[bool]:
        """Reverify every consumed file state and directory-query boundary.

        Returns:
            The native verification result, preserving the first failure.

        """
        before_states: list[m.Cli.AtomicFileState] = []
        for file in files:
            if not isinstance(file.before, m.Cli.AtomicFileState):
                return r[bool].fail(f"environment dependency is not a file: {envrc}")
            before_states.append(file.before)
        states = (
            *inputs.sources,
            *(state for file in files for state in file.source_states),
            *before_states,
        )
        inventories = tuple(
            query for file in files for query in file.source_directories
        )
        topology = tuple(
            query for file in files for query in file.source_query_topology
        )
        verified = u.Cli.atomic_verify_binary_file_states(states)
        if verified.failure:
            return r[bool].from_failure(verified)
        return u.Cli.atomic_verify_directory_queries(inventories, topology)

    @staticmethod
    def _authorize_environment(
        root: Path,
        inputs: m.Infra.CodegenInputs,
        files: t.SequenceOf[m.Infra.CodegenFilePlan],
        runner: p.Cli.CommandRunner,
    ) -> p.Result[bool]:
        """Authorize the environment and reverify its original consumption proof.

        Returns:
            The post-authorization verification, or the first native failure.

        """
        allowed = runner.run_raw(
            (c.Infra.CLI_DIRENV, "allow", str(root)),
            cwd=root,
            timeout=c.Infra.TIMEOUT_DEFAULT,
        )
        if allowed.failure:
            return r[bool].from_failure(allowed)
        output = allowed.value
        if not u.Cli.process_succeeded(output.outcome):
            return r[bool].fail(
                f"direnv allow failed for {root}: "
                f"{output.stderr.strip() or output.stdout.strip()}",
            )
        return FlextInfraWorkspaceEnvironmentMixin._verify_environment_consumption(
            inputs,
            files,
            envrc=root / c.Infra.ENVRC_FILENAME,
        )

    @staticmethod
    def execute_request(
        request: m.Infra.WorkspaceEnvironmentSyncRequest,
        *,
        synchronize: Callable[
            [m.Infra.WorkspaceEnvironmentSyncRequest],
            p.Result[m.Infra.WorkspaceEnvironmentSyncResult],
        ],
        scope: c.Infra.CodegenConformScope = c.Infra.CodegenConformScope.SELF,
    ) -> p.Result[t.Cli.ResultValue]:
        """Consume one declared repository scope through the facade-bound owner.

        Returns:
            The canonical operation result, with no source-file mutations.

        """

        def sync_repository(repository_root: Path) -> p.Result[t.SequenceOf[Path]]:
            result = synchronize(
                request.model_copy(
                    update={"repository_root": repository_root},
                ),
            )
            if result.failure:
                return r[t.SequenceOf[Path]].from_failure(result)
            return r[t.SequenceOf[Path]].ok(())

        result = u.Infra.repository_operation_batch(
            request.repository_root,
            scope,
            "sync-environment",
            sync_repository,
            mutating=request.allow_direnv,
        )
        if result.failure:
            return r[t.Cli.ResultValue].from_failure(result)
        return r[t.Cli.ResultValue].ok(
            tuple(str(path) for path in result.value),
        )


__all__: list[str] = ["FlextInfraWorkspaceEnvironmentMixin"]
