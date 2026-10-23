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
        planned = planner.plan_repositories(
            m.Infra.CodegenConformRequest(
                root=root,
                what=c.Infra.CodegenConformSurface.ENVRC,
                scope=c.Infra.CodegenConformScope.SELF,
                mode=c.Infra.CodegenConformMode.CHECK,
            ),
            inputs.value,
        )
        if planned.failure:
            return result_type.from_failure(planned)
        plan = planned.value
        if plan.exception is not None:
            raise plan.exception
        if plan.issues:
            return result_type.fail(plan.issues[0].formatted)
        if tuple(file.path for file in plan.files) != (envrc,):
            return result_type.fail(
                f"environment consumption requires one declared projection: {envrc}",
            )
        current = u.Infra.codegen_fixed_point(
            plan.files,
            subject=f"environment projection {envrc}",
        )
        if current.failure:
            return result_type.from_failure(current)
        file = plan.files[0]
        if not isinstance(file.before, m.Cli.AtomicFileState):
            return result_type.fail(f"environment projection is not a file: {envrc}")
        states = (*inputs.value.sources, *file.source_states, file.before)
        verified = u.Cli.atomic_verify_binary_file_states(states)
        if verified.failure:
            return result_type.from_failure(verified)
        if request.allow_direnv:
            allowed = runner.run_raw(
                (c.Infra.CLI_DIRENV, "allow", str(root)),
                cwd=root,
                timeout=c.Infra.TIMEOUT_DEFAULT,
            )
            if allowed.failure:
                return result_type.from_failure(allowed)
            output = allowed.value
            if not u.Cli.process_succeeded(output.outcome):
                return result_type.fail(
                    f"direnv allow failed for {root}: "
                    f"{output.stderr.strip() or output.stdout.strip()}",
                )
            verified = u.Cli.atomic_verify_binary_file_states(states)
            if verified.failure:
                return result_type.from_failure(verified)
        u.Cli.info(
            f"environment projection consumed: {envrc}; "
            f"authorized={request.allow_direnv}",
        )
        return result_type.ok(
            m.Infra.WorkspaceEnvironmentSyncResult(
                environment_file=envrc,
                authorized=request.allow_direnv,
            ),
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
