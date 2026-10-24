"""Consume generated direnv files through the existing conformance planner.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from flext_infra import c, m, p, r, t, u


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
        if request.allow_direnv:
            allowed = FlextInfraWorkspaceEnvironmentMixin._authorize_environment(
                root, runner
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
            The original fixed-point plan, or its first native failure; a native
            planning exception escapes unchanged.

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
    def _authorize_environment(
        root: Path,
        runner: p.Cli.CommandRunner,
    ) -> p.Result[bool]:
        """Authorize the consumed environment through direnv.

        Returns:
            Success, or the first native failure.

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
        return r[bool].ok(value=True)

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
        synchronized: t.Cli.ResultValue = [str(path) for path in result.value]
        return r[t.Cli.ResultValue].ok(synchronized)


__all__: list[str] = ["FlextInfraWorkspaceEnvironmentMixin"]
