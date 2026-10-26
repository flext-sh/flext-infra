"""Plan declared projections and publish them through the shared publisher.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import os
from collections.abc import Callable
from pathlib import Path
from typing import Self, override

from flext_cli import u

from flext_infra import c, m, p, r, t
from flext_infra import workspace as workspace_services
from flext_infra._utilities.codegen import FlextInfraUtilitiesCodegen as generation
from flext_infra.codegen._conform.plan import FlextInfraCodegenConformPlan
from flext_infra.codegen.codegen_preconditions import FlextInfraCodegenPreconditions


class FlextInfraCodegenConformExecute(FlextInfraCodegenConformPlan):
    """Generate one request: plan every declared projection, publish once."""

    @classmethod
    def from_request(
        cls: type[Self],
        request: m.Infra.CodegenGenerateRequest,
        *,
        execution_context: p.Infra.CodegenExecutionContext | None,
        repository_root: t.Infra.Path | None = None,
    ) -> p.Result[FlextInfraCodegenConformExecute]:
        """Bind one validated request to the projection executor.

        Returns:
            The bound executor or the original admission failure.

        """
        root = request.root.expanduser().resolve()
        identity = generation.exact_worktree_root(root)
        if identity.failure:
            return r[FlextInfraCodegenConformExecute].from_failure(identity)
        generation_root = (
            root if repository_root is None else repository_root.expanduser().resolve()
        )
        state = m.Infra.CodegenConformState(
            repository_root=generation_root,
            request=request,
            ports=(
                None
                if execution_context is None
                else execution_context.codegen_conform_collaborators()
            ),
        )
        if (
            request.what is c.Infra.CodegenConformSurface.ALL
            and not (root / c.PYPROJECT_FILENAME).exists()
        ):
            inputs = generation.load_codegen_inputs(root)
            if inputs.failure:
                return r[FlextInfraCodegenConformExecute].from_failure(inputs)
            observed = (
                workspace_services.FlextInfraWorkspaceDetector.load_workspace_spec(
                    root, inputs=inputs.value
                )
            )
            if observed.failure:
                return r[FlextInfraCodegenConformExecute].from_failure(observed)
            state.initial_workspace = observed.value
        return r[FlextInfraCodegenConformExecute].ok(
            cls(
                repository_root=generation_root,
                state=state,
                runtime_settings=(
                    None if execution_context is None else execution_context.settings
                ),
                initial_context=(
                    None if execution_context is None else execution_context.context
                ),
            ),
        )

    @classmethod
    def execute_request(
        cls: type[Self],
        request: p.Infra.CodegenGenerateRequest,
        *,
        execution_context: p.Infra.CodegenExecutionContext | None,
        repository_root: t.Infra.Path | None = None,
    ) -> p.Result[p.Infra.CodegenResult]:
        """Admit the public request once, then generate it.

        Returns:
            The projection result or its original failure.

        """
        admitted = m.Infra.CodegenGenerateRequest.model_validate(
            request, from_attributes=True
        )
        bound = cls.from_request(
            admitted,
            execution_context=execution_context,
            repository_root=repository_root,
        )
        if bound.failure:
            return r[p.Infra.CodegenResult].from_failure(bound)
        return bound.value.execute()

    @override
    def execute(self) -> p.Result[p.Infra.CodegenResult]:
        """Generate the bound request.

        Returns:
            The projection outcome.

        Raises:
            ValueError: The executor has no bound request.

        """
        request = self.state.request
        if request is None:
            msg = "projection execution requires a bound generation request"
            raise ValueError(msg)
        return self.execute_managed(request)

    def execute_managed(
        self,
        request: p.Infra.CodegenGenerateRequest,
        *,
        after_publication: tuple[
            Callable[[t.VariadicTuple[Path]], p.Result[bool]], ...
        ] = (),
    ) -> p.Result[p.Infra.CodegenResult]:
        """Plan the request's projections and publish them once.

        ``after_publication`` runs with the written paths after a successful
        publication; its first failure fails the request.

        Returns:
            The plan and written paths, or the first failure.

        """
        u.Cli.info(
            f"operation=generate root={request.root} scope={request.scope} "
            f"surface={request.what} pid={os.getpid()}"
        )
        root = request.root.expanduser().resolve()
        return (
            FlextInfraCodegenPreconditions
            .rendering_engine(root)
            .flat_map(lambda _: self._planned(request))
            .flat_map(
                lambda plan: self._published(request, root, plan, after_publication)
            )
        )

    def check_managed(
        self,
        request: p.Infra.CodegenGenerateRequest,
    ) -> p.Result[p.Infra.CodegenResult]:
        """Fail when the request's projections differ from the tree.

        Uses the same plan and normalized view as publication, without effects.

        Returns:
            The plan when every projection is current, or the stale paths.

        """
        root = request.root.expanduser().resolve()
        return (
            FlextInfraCodegenPreconditions
            .rendering_engine(root)
            .flat_map(lambda _: self._planned(request))
            .flat_map(lambda plan: self._checked(request, plan))
        )

    def _checked(
        self,
        request: p.Infra.CodegenGenerateRequest,
        plan: m.Infra.CodegenPlan,
    ) -> p.Result[p.Infra.CodegenResult]:
        """Compare the injected publisher's normalized plan with the tree.

        Check and apply consume the same publication capability; neither resolves
        a utility implementation inside the executor.

        Returns:
            The plan when nothing is pending, or the stale destinations.

        """
        result_type = r[p.Infra.CodegenResult]
        if plan.issues or plan.exception is not None:
            return result_type.fail(
                "\n".join(issue.formatted for issue in plan.issues)
                or "generation planning failed",
                exception=plan.exception,
            )
        ports = self.state.ports
        if ports is None:
            return result_type.fail(
                "conformance requires facade-wired file publication"
            )
        changes = self._admitted_plans(request, plan).flat_map(
            ports.file_publisher.normalized_codegen_changes
        )
        if changes.failure:
            return result_type.from_failure(changes)
        pending = u.Cli.pending_file_changes(changes.value)
        if pending:
            return result_type.fail(
                "generated projections are stale: "
                + ", ".join(sorted(str(change.path) for change in pending))
            )
        payload: p.Infra.CodegenResult = m.Infra.CodegenResult(plan=plan)
        return result_type.ok(payload)

    def _planned(
        self,
        request: p.Infra.CodegenGenerateRequest,
    ) -> p.Result[m.Infra.CodegenPlan]:
        """Plan the request, failing when planning produced only failures.

        Returns:
            The plan, or its planning failure.

        """
        planned = (
            self._plan_single_surface(request)
            if request.what in c.Infra.FILE_ONLY_SURFACES
            else self.plan(request)
        )
        if (
            planned.success
            and not planned.value.files
            and (planned.value.issues or planned.value.exception is not None)
        ):
            return r[m.Infra.CodegenPlan].fail(
                "\n".join(issue.formatted for issue in planned.value.issues)
                or "generation planning failed",
                exception=planned.value.exception,
            )
        return planned

    def _published(
        self,
        request: p.Infra.CodegenGenerateRequest,
        root: Path,
        plan: m.Infra.CodegenPlan,
        after_publication: tuple[
            Callable[[t.VariadicTuple[Path]], p.Result[bool]], ...
        ],
    ) -> p.Result[p.Infra.CodegenResult]:
        """Publish the plan and its docs once, then run the follow-ups.

        Every planning diagnostic and cold-import failure rejects the cohort
        before the first destination effect. Check and apply share candidate
        admission and the existing guarded publication owner.

        Returns:
            The plan and written paths, or the first failure.

        """
        result_type = r[p.Infra.CodegenResult]
        ports = self.state.ports
        if ports is None:
            return result_type.fail(
                "conformance requires facade-wired file publication"
            )
        published = self._admitted_plans(request, plan).flat_map(
            lambda files: ports.file_publisher.publish_codegen_plans(root, files)
        )
        if published.failure:
            return result_type.from_failure(published)
        for operation in after_publication:
            completed = operation(published.value)
            if completed.failure:
                return result_type.from_failure(completed)
        if plan.issues or plan.exception is not None:
            return result_type.fail(
                "\n".join(issue.formatted for issue in plan.issues)
                or "generation planning failed",
                exception=plan.exception,
            )
        payload: p.Infra.CodegenResult = m.Infra.CodegenResult(
            plan=plan,
            written_files=published.value,
        )
        return result_type.ok(payload)

    def _admitted_plans(
        self,
        request: p.Infra.CodegenGenerateRequest,
        plan: m.Infra.CodegenPlan,
    ) -> p.Result[t.VariadicTuple[m.Infra.CodegenFilePlan]]:
        """Validate the normalized dependency cohort before accepting any effects.

        The native preview materializes original file declarations, including
        retirements. Its existing cold-import owner must accept that exact source
        view before the shared publisher may verify and write its destinations.

        Returns:
            The normalized plans, or the original planning or admission failure.

        """
        result_type = r[t.VariadicTuple[m.Infra.CodegenFilePlan]]
        if plan.issues or plan.exception is not None:
            return result_type.fail(
                "\n".join(issue.formatted for issue in plan.issues)
                or "generation planning failed",
                exception=plan.exception,
            )
        ports = self.state.ports
        if ports is None:
            return result_type.fail("conformance requires facade-wired candidate admission")
        docs = self._docs_plans(request, plan)
        if docs.failure:
            return result_type.from_failure(docs)
        files = (*plan.files, *docs.value)
        changes = ports.file_publisher.normalized_codegen_changes(files)
        if changes.failure:
            return result_type.from_failure(changes)
        normalized = {change.path: change for change in changes.value}
        files = tuple(
            file.model_copy(update={
                "desired_content": normalized[file.path].desired_content,
                "desired_mode": normalized[file.path].desired_mode,
            })
            for file in files
        )
        if not any(file.path.suffix == c.Infra.EXT_PYTHON for file in files):
            return result_type.ok(files)
        root = request.root.expanduser().resolve()
        preview = ports.source_preview.preview_sources(
            root,
            {
                file.path: file.desired_content.decode(c.DEFAULT_ENCODING)
                if file.desired_content is not None
                else None
                for file in files
            },
            lambda candidate, _paths: ports.candidate_validator(
                root,
                candidate,
                tuple(sorted({
                    file.project
                    for file in files
                    if file.path.suffix == c.Infra.EXT_PYTHON
                })),
            ),
            options=m.Infra.CodegenSourcePreviewOptions(
                declared_files=files,
                inputs=tuple(file.before for file in files),
            ),
        ).flat_map(lambda outcome: outcome)
        if preview.failure:
            return result_type.from_failure(preview)
        if not preview.value:
            return result_type.fail("native candidate admission returned no acceptance")
        return result_type.ok(files)

    def _docs_plans(
        self,
        request: p.Infra.CodegenGenerateRequest,
        plan: m.Infra.CodegenPlan,
    ) -> p.Result[t.VariadicTuple[m.Infra.CodegenFilePlan]]:
        """Plan the documentation the complete surface owns.

        Returns:
            The documentation file plans, empty outside the complete surface.

        """
        result_type = r[tuple[m.Infra.CodegenFilePlan, ...]]
        owned = tuple(
            repository.name
            for repository in plan.repositories
            if repository.path == Path()
        )
        if request.what is not c.Infra.CodegenConformSurface.ALL or not owned:
            return result_type.ok(())
        ports = self.state.ports
        if ports is None:
            return result_type.fail(
                "complete generation requires the facade-wired docs planner; "
                "run it through FlextInfra.codegen_generate",
            )
        planner = ports.docs_planner(
            repository_root=request.root,
            projects=owned,
            include_root=True,
        )
        return planner.prepare_bundle().flat_map(planner.plan_files)


__all__: list[str] = ["FlextInfraCodegenConformExecute"]
