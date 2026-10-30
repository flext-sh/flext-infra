"""Plan declared projections and publish them through the shared publisher.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import os
import time
from collections.abc import Callable, Mapping
from pathlib import Path
from typing import Self, override

from flext_infra import c, m, p, r, settings, t, u, workspace as workspace_services
from flext_infra.codegen import FlextInfraCodegenPreconditions
from flext_infra.codegen._conform.plan import FlextInfraCodegenConformPlan


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
        identity = u.Infra.exact_worktree_root(root)
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
            inputs = u.Infra.load_codegen_inputs(root)
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
            Callable[[tuple[Path, ...]], p.Result[bool]], ...
        ] = (),
        after_cohort_publication: tuple[
            Callable[[tuple[Path, ...]], p.Result[bool]], ...
        ] = (),
    ) -> p.Result[p.Infra.CodegenResult]:
        """Plan the request's projections and publish them once.

        ``after_publication`` runs with the written paths after a successful
        publication; its first failure fails the request.

        Returns:
            The plan and written paths, or the first failure.

        """
        self._begin_planning()
        self.state.control_outcomes = ()
        u.Cli.info(
            f"operation=generate root={request.root} scope={request.scope} "
            # Bind diagnostics to the selected process settings, never an old report.
            f"surface={request.what} pid={os.getpid()} "
            f"profile={settings.Infra.profile} "
            f"profile_output={settings.Infra.profile_output}"
        )
        root = request.root.expanduser().resolve()
        ready = FlextInfraCodegenPreconditions.rendering_engine(root)
        if ready.failure:
            return r[p.Infra.CodegenResult].from_failure(ready)
        if request.what is not c.Infra.CodegenConformSurface.ALL:
            return self._planned(request).flat_map(
                lambda plan: self._published(
                    request,
                    root,
                    plan,
                    after_publication,
                    after_cohort_publication=after_cohort_publication,
                )
            )
        control_plan = self._control_plan(request)
        if control_plan.failure:
            return r[p.Infra.CodegenResult].from_failure(control_plan)
        control = self._published(
            request,
            root,
            control_plan.value,
            (),
            after_cohort_publication=after_cohort_publication,
            prepared_files=control_plan.value.files,
        )
        if control.failure:
            native = next(
                (
                    outcome.native_failure
                    for outcome in self.state.control_outcomes
                    if outcome.native_failure is not None
                ),
                None,
            )
            self.retain_diagnostics(failure=control if native is None else native)
        written = self._written_paths(control)
        refreshed = self._advance_control_inputs(root, written)
        if refreshed.failure:
            self.retain_diagnostics(failure=refreshed)
            return self._execution_failure(
                (control, refreshed) if control.failure else (refreshed,), written
            )
        planned = self._planned(request)
        failures: list[p.FailureLike] = []
        if control.failure:
            failures.append(control)
        if planned.failure:
            failures.append(planned)
            return self._execution_failure(tuple(failures), written)
        published = self._published(
            request,
            root,
            planned.value,
            (),
            after_cohort_publication=after_cohort_publication,
        )
        written = tuple(dict.fromkeys((*written, *self._written_paths(published))))
        if published.failure:
            failures.append(published)
        if failures:
            return self._execution_failure(tuple(failures), written)
        for operation in after_publication:
            completed = operation(written)
            if completed.failure:
                extra = tuple(
                    Path(path)
                    for path in u.type_adapter(t.TypeForm(list[str])).validate_python(
                        (completed.error_data or {}).get("written_files", []),
                        strict=True,
                    )
                )
                return self._execution_failure(
                    (completed,), tuple(dict.fromkeys((*written, *extra)))
                )
        return r[p.Infra.CodegenResult].ok(
            m.Infra.CodegenResult(plan=planned.value, written_files=written)
        )

    def _advance_control_inputs(
        self,
        root: Path,
        written: tuple[Path, ...],
    ) -> p.Result[bool]:
        """Re-elect metadata after own effects without altering old witnesses."""
        if not any(path.name == c.PYPROJECT_FILENAME for path in written):
            return r[bool].ok(value=False)
        scaffold = self.state.initial_workspace is not None
        self.state.initial_workspace = None
        captured = u.Infra.load_codegen_inputs(root)
        if captured.failure:
            return r[bool].from_failure(captured)
        elected = workspace_services.FlextInfraWorkspaceDetector.load_workspace_spec(
            root, inputs=captured.value
        )
        if elected.failure:
            return r[bool].from_failure(elected)
        if scaffold:
            self.state.initial_workspace = elected.value
        return r[bool].ok(value=True)

    @staticmethod
    def _written_paths(
        result: p.Result[p.Infra.CodegenResult],
    ) -> tuple[Path, ...]:
        """Read the existing successful or partial-publication receipt."""
        if result.success:
            return tuple(result.value.written_files)
        return tuple(
            Path(path)
            for path in u.type_adapter(t.TypeForm(list[str])).validate_python(
                (result.error_data or {}).get("written_files", []), strict=True
            )
        )

    def _execution_failure(
        self,
        failures: tuple[p.FailureLike, ...],
        written: tuple[Path, ...],
    ) -> p.Result[p.Infra.CodegenResult]:
        """Retain the first original cause and every independent effect receipt."""
        first = self.state.planning_failure
        if first is None:
            first = failures[0]
        return r[p.Infra.CodegenResult].fail(
            "\n".join(failure.error or str(failure.exception) for failure in failures),
            error_code=first.error_code,
            error_data={
                **(first.error_data or {}),
                "written_files": [str(path) for path in written],
                "errors": [
                    failure.error or str(failure.exception) for failure in failures
                ],
            },
            exception=first.exception,
        )

    def _control_plan(
        self,
        request: p.Infra.CodegenGenerateRequest,
    ) -> p.Result[m.Infra.CodegenPlan]:
        """Plan the native file-only control cohort before Python inventory."""
        result_type = r[m.Infra.CodegenPlan]
        root = request.root.expanduser().resolve()
        captured = u.Infra.load_codegen_inputs(root)
        if captured.failure:
            return result_type.from_failure(captured)
        elected = self._planning_workspace(request, root, inputs=captured.value)
        if elected.failure:
            return result_type.from_failure(elected)
        workspace, current_target, current_repository = elected.value
        selected = self._select_repositories(request, workspace, current_repository)
        if selected.failure:
            return result_type.from_failure(selected)
        by_name = {
            t.Infra.DISTRIBUTION_NAME_ADAPTER.validate_python(
                repository.distribution
            ): repository
            for repository in selected.value
        }
        seed: tuple[m.Infra.CodegenFilePlan, ...] = ()
        if workspace.flext_source is not None:
            initial = self._plan_existing_control(
                current_target, workspace, captured.value
            )
            if initial.failure:
                return result_type.from_failure(initial)
            seed = initial.value.files
        graph = dict(
            u.Infra.workspace_dependency_graph(
                root,
                selected.value,
                inputs=workspace.inputs,
                planned_manifests=tuple(
                    plan for plan in seed if plan.path.name == c.PYPROJECT_FILENAME
                ),
            )
        )
        executor = captured.value.spec.templates.bootstrap_entry.bootstrap_distribution
        owner = t.Infra.DISTRIBUTION_NAME_ADAPTER.validate_python(
            workspace.repository.distribution
        )
        if (
            executor is not None
            and executor in graph
            and owner in graph
            and executor != owner
        ):
            graph[owner] = (*graph[owner], executor)
        ordered = u.Cli.dag_order(graph)
        if ordered.failure:
            return result_type.from_failure(ordered)
        outcomes: list[m.Infra.CodegenRepositoryPlanOutcome] = []
        failures: dict[str, p.FailureLike] = {}
        previous = self.state.provider_plans
        self.state.provider_plans = u.Infra.codegen_compose_file_plans(
            (*(previous or ()), *seed), ordered=True
        )
        try:
            for name in ordered.value:
                repository = by_name[name]
                blocked = next(
                    (
                        failures[dependency]
                        for dependency in graph[name]
                        if dependency in failures
                    ),
                    None,
                )
                planned = (
                    r[m.Infra.CodegenRepositoryPlanOutcome].from_failure(blocked)
                    if blocked is not None
                    else self._control_repository(
                        m.Infra.CodegenRepositoryPlanTask(
                            root=root,
                            workspace=workspace,
                            current_target=current_target,
                            repository=repository,
                            surface=request.what,
                            selected_inputs=(
                                captured.value
                                if repository.name == current_target.repository.name
                                else None
                            ),
                        )
                    )
                )
                if planned.failure:
                    native = blocked if blocked is not None else planned
                    failures[name] = native
                    self.retain_diagnostics(native.exception, failure=native)
                    outcomes.append(
                        m.Infra.CodegenRepositoryPlanOutcome(
                            repository=repository.name,
                            error=native.error or "control planning failed",
                            exception=native.exception,
                            native_failure=native,
                        )
                    )
                else:
                    outcomes.append(planned.value)
                    self.state.provider_plans = u.Infra.codegen_compose_file_plans(
                        (*(self.state.provider_plans or ()), *planned.value.files),
                        ordered=True,
                    )
                self.state.control_outcomes = tuple(outcomes)
        finally:
            self.state.provider_plans = previous
        return result_type.ok(
            m.Infra.CodegenPlan(
                request=request,
                repositories=selected.value,
                workspace=workspace,
                uv_environments=(),
                files=u.Infra.codegen_compose_file_plans(
                    tuple(file for outcome in outcomes for file in outcome.files)
                ),
                outcomes=tuple(outcomes),
                exception=self.state.planning_exception,
            )
        )

    def _control_repository(
        self,
        task: m.Infra.CodegenRepositoryPlanTask,
    ) -> p.Result[m.Infra.CodegenRepositoryPlanOutcome]:
        """Resolve a control target through the existing metadata owners."""
        result_type = r[m.Infra.CodegenRepositoryPlanOutcome]
        resolved = self._resolved_repository_root(
            task.root, task.workspace, task.current_target, task.repository
        )
        if resolved.failure:
            return result_type.from_failure(resolved)
        captured = (
            r[m.Infra.CodegenInputs].ok(task.selected_inputs)
            if task.selected_inputs is not None
            else u.Infra.load_codegen_inputs(resolved.value)
        )
        if captured.failure:
            return result_type.from_failure(captured)
        local = self._repository_planning_inputs(
            resolved.value,
            task.workspace,
            task.current_target,
            task.repository,
            inputs=captured.value,
        )
        if local.failure:
            return result_type.from_failure(local)
        return self._plan_existing_control(
            local.value[1], local.value[2], captured.value
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
        self._begin_planning()
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
        if (
            plan.issues
            or plan.exception is not None
            or any(outcome.failed for outcome in plan.outcomes)
        ):
            return result_type.from_failure(self._admitted_plans(request, plan))
        ports = self.state.ports
        if ports is None:
            return result_type.fail(
                "conformance requires facade-wired file publication"
            )
        changes = self._admitted_plans(request, plan).flat_map(
            lambda files: u.Cli.atomic_verify_binary_file_states(
                tuple(state for file in files for state in (file.before, *file.inputs))
            ).flat_map(lambda _: ports.file_publisher.normalized_codegen_changes(files))
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
        started = time.monotonic()
        u.Cli.info(f"stage=planning state=start root={request.root}")
        planned = (
            self._plan_single_surface(request)
            if request.what in c.Infra.FILE_ONLY_SURFACES
            else self._plan_request(request)
        )
        failed = planned.failure or (
            planned.success
            and (
                bool(planned.value.issues)
                or planned.value.exception is not None
                or any(outcome.failed for outcome in planned.value.outcomes)
            )
        )
        u.Cli.info(
            f"stage=planning state=end root={request.root} "
            f"elapsed={time.monotonic() - started:.3f}s "
            f"files={len(planned.value.files) if planned.success else 0} "
            f"failed={failed}"
        )
        if (
            planned.success
            and not planned.value.files
            and (
                planned.value.issues
                or planned.value.exception is not None
                or any(outcome.failed for outcome in planned.value.outcomes)
            )
        ):
            native = self.state.planning_failure
            if native is None:
                native = next(
                    (
                        outcome.native_failure
                        for outcome in planned.value.outcomes
                        if outcome.native_failure is not None
                    ),
                    None,
                )
            if native is not None:
                return r[m.Infra.CodegenPlan].from_failure(native)
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
        after_publication: tuple[Callable[[tuple[Path, ...]], p.Result[bool]], ...],
        *,
        prepared_files: tuple[m.Infra.CodegenFilePlan, ...] | None = None,
        after_cohort_publication: tuple[
            Callable[[tuple[Path, ...]], p.Result[bool]], ...
        ] = (),
    ) -> p.Result[p.Infra.CodegenResult]:
        """Publish independent authenticated cohorts, retaining every failure.

        Changed providers, consumers and exports share candidate admission.
        Publication failures retain the writer's completed-path receipt;
        unrelated admitted effects remain valid and are included in the final
        failure metadata. Follow-ups require the complete request to succeed.

        Returns:
            The full result, or the first cause with all actual written paths.

        """
        result_type = r[p.Infra.CodegenResult]
        if not plan.outcomes:
            published = self._published_cohort(
                request,
                root,
                plan,
                prepared_files=prepared_files,
                publication_followups=(*after_cohort_publication, *after_publication),
            )
            if published.failure:
                return result_type.fail(
                    published.error or "generation cohort failed",
                    error_code=published.error_code,
                    error_data={
                        **(published.error_data or {}),
                        "failed_repositories": [
                            repository.name for repository in plan.repositories
                        ],
                    },
                    exception=published.exception,
                )
            return published
        ready = {
            repository.name: repository
            for repository in plan.repositories
            if any(
                outcome.repository == repository.name and not outcome.failed
                for outcome in plan.outcomes
            )
        }
        documentation_failure = self._ready_documentation_plans(
            request,
            root,
            plan,
            ready,
            prepared_files,
        )
        if documentation_failure is not None:
            return result_type.from_failure(documentation_failure)
        cohorts = self._publication_cohorts(root, plan)
        if cohorts.failure:
            return result_type.from_failure(cohorts)
        written, failures, failed_repositories = self._published_ordered_cohorts(
            request,
            root,
            cohorts.value,
            after_cohort_publication=after_cohort_publication,
        )
        if not failures:
            for operation in after_publication:
                completed = operation(tuple(written))
                if completed.failure:
                    failures.append(completed)
                    written.extend(
                        Path(path)
                        for path in u.type_adapter(
                            t.TypeForm(list[str])
                        ).validate_python(
                            (completed.error_data or {}).get("written_files", []),
                            strict=True,
                        )
                    )
                    break
        if failures:
            first = failures[0]
            return result_type.fail(
                "\n".join(failure.error or "generation failed" for failure in failures),
                error_code=first.error_code,
                error_data={
                    **(first.error_data or {}),
                    "written_files": [str(path) for path in written],
                    "errors": [
                        failure.error or "generation failed" for failure in failures
                    ],
                    "failed_repositories": sorted(failed_repositories),
                },
                exception=first.exception,
            )
        payload: p.Infra.CodegenResult = m.Infra.CodegenResult(
            plan=plan, written_files=tuple(written)
        )
        return result_type.ok(payload)

    def _ready_documentation_plans(
        self,
        request: p.Infra.CodegenGenerateRequest,
        root: Path,
        plan: m.Infra.CodegenPlan,
        ready: dict[str, m.Infra.CodegenRepository],
        prepared_files: tuple[m.Infra.CodegenFilePlan, ...] | None,
    ) -> p.Result[tuple[m.Infra.CodegenFilePlan, ...]] | None:
        """Fold ready-repository documentation into the published plan.

        A documentation planning failure is attached to the root repository's
        outcome when one exists; without an owning root repository the
        failure aborts publication before any effect.

        Returns:
            ``None`` when the plan carries the documentation files, otherwise
            the documentation planning failure without a root repository owner.

        """
        ready_roots = {
            (root / repository.path).resolve() for repository in ready.values()
        }
        documents = (
            r[tuple[m.Infra.CodegenFilePlan, ...]].ok(prepared_files)
            if prepared_files is not None
            else self._docs_plans(
                request,
                m.Infra.CodegenPlan(
                    request=plan.request,
                    workspace=plan.workspace,
                    repositories=tuple(ready.values()),
                    files=tuple(
                        file for file in plan.files if file.project in ready_roots
                    ),
                    uv_environments=plan.uv_environments,
                ),
            )
        )
        if documents.success:
            plan.files = documents.value
            return None
        owner = next(
            (repository for repository in ready.values() if repository.path == Path()),
            None,
        )
        if owner is None:
            return documents
        self._reconciled_documentation_failure(root, plan, documents, owner)
        return None

    def _reconciled_documentation_failure(
        self,
        root: Path,
        plan: m.Infra.CodegenPlan,
        documents: p.Result[tuple[m.Infra.CodegenFilePlan, ...]],
        owner: m.Infra.CodegenRepository,
    ) -> None:
        """Attach a documentation planning failure to its owning root outcome.

        The owning root repository outcome carries the documentation failure
        as its native cause, and the plan retains the diagnostic with the
        executor's recorded planning failure first.

        Returns:
            None. The plan and its owning outcome are updated in place.

        """
        issue = m.Infra.Issue(
            file=str(root),
            line=0,
            column=0,
            code=c.Infra.ToolOutcome.ERROR.value,
            message=documents.error or "documentation planning failed",
        )
        original = next(
            outcome for outcome in plan.outcomes if outcome.repository == owner.name
        )
        native = original.native_failure
        if native is None and original.exception is not None:
            native = r.fail(original.error, exception=original.exception)
        if native is None:
            native = documents
        original.error = native.error or ""
        original.exception = native.exception
        original.native_failure = native
        original.issues = (*original.issues, issue)
        plan.issues = (*plan.issues, issue)
        first_native = self.state.planning_failure
        plan.exception = (
            first_native.exception
            if first_native is not None
            else plan.exception
            if plan.exception is not None
            else native.exception
        )

    def _published_ordered_cohorts(
        self,
        request: p.Infra.CodegenGenerateRequest,
        root: Path,
        cohorts: tuple[m.Infra.CodegenPlan, ...],
        *,
        after_cohort_publication: tuple[
            Callable[[tuple[Path, ...]], p.Result[bool]], ...
        ] = (),
    ) -> tuple[list[Path], list[p.FailureLike], set[str]]:
        """Publish every cohort, planning failure first, retaining failures.

        Returns:
            Every written path, every cohort failure, and the repositories of
            the failed cohorts, in publication order.

        """
        written: list[Path] = []
        failures: list[p.FailureLike] = []
        failed_repositories: set[str] = set()
        first_native = self.state.planning_failure
        ordered = sorted(
            cohorts,
            key=lambda cohort: (
                not any(
                    outcome.native_failure is first_native
                    for outcome in cohort.outcomes
                )
                if first_native is not None
                else False
            ),
        )
        for cohort in ordered:
            published = self._published_cohort(
                request,
                root,
                cohort,
                prepared_files=cohort.files,
                publication_followups=after_cohort_publication,
            )
            if published.failure:
                failures.append(published)
                failed_repositories.update(
                    repository.name for repository in cohort.repositories
                )
                written.extend(
                    Path(path)
                    for path in u.type_adapter(t.TypeForm(list[str])).validate_python(
                        (published.error_data or {}).get("written_files", []),
                        strict=True,
                    )
                )
                u.Cli.error(published.error or "generation cohort failed")
            else:
                written.extend(published.value.written_files)
        return written, failures, failed_repositories

    @classmethod
    def _publication_cohorts(
        cls,
        root: Path,
        plan: m.Infra.CodegenPlan,
    ) -> p.Result[tuple[m.Infra.CodegenPlan, ...]]:
        """Close candidate effects over authenticated changed-file dependencies.

        Returns:
            Existing plan objects grouped by the native graph component owner.

        """
        result_type = r[tuple[m.Infra.CodegenPlan, ...]]
        outcomes = {outcome.repository: outcome for outcome in plan.outcomes}
        repositories = {repository.name: repository for repository in plan.repositories}
        roots = {
            name: (root / repository.path).resolve()
            for name, repository in repositories.items()
        }
        accounted = tuple(
            issue for outcome in outcomes.values() for issue in outcome.issues
        )
        if any(
            issue not in accounted
            and not any(
                outcome.failed and issue.file == str(roots[outcome.repository])
                for outcome in outcomes.values()
            )
            for issue in plan.issues
        ) or (
            plan.exception is not None
            and not any(
                outcome.exception is plan.exception for outcome in outcomes.values()
            )
        ):
            return result_type.ok((plan,))
        projects: dict[Path, set[str]] = {roots[name]: {name} for name in outcomes}
        for outcome in outcomes.values():
            for file in outcome.files:
                projects.setdefault(file.project, set()).add(outcome.repository)
        files = (
            *(file for outcome in outcomes.values() for file in outcome.files),
            *plan.files,
        )
        unowned = tuple(
            file.path for file in plan.files if file.project not in projects
        )
        if unowned:
            message = f"publication effects have no repository owner: {unowned}"
            return result_type.fail(message)
        edges = cls._cohort_dependency_edges(files, projects, outcomes)
        return result_type.ok(
            cls._component_cohort_plans(root, plan, repositories, projects, edges)
        )

    @classmethod
    def _cohort_dependency_edges(
        cls,
        files: tuple[m.Infra.CodegenFilePlan, ...],
        projects: dict[Path, set[str]],
        outcomes: Mapping[str, m.Infra.CodegenRepositoryPlanOutcome],
    ) -> dict[str, set[str]]:
        """Wire each pending changed path to its owning repositories.

        Returns:
            Undirected dependency edges between the plan's repository names.

        """
        edges: dict[str, set[str]] = {name: set() for name in outcomes}
        pending = frozenset(change.path for change in u.Cli.pending_file_changes(files))
        owners: dict[Path, set[str]] = {}
        for file in files:
            if file.path in pending:
                owners.setdefault(file.path, set()).update(projects[file.project])
        for file in files:
            for path in (
                file.path,
                *file.tracking_dependencies,
                *(state.path for state in file.inputs),
            ):
                for repository in projects[file.project]:
                    for owner in owners.get(path, ()):
                        edges[repository].add(owner)
                        edges[owner].add(repository)
        return edges

    @classmethod
    def _component_cohort_plans(
        cls,
        root: Path,
        plan: m.Infra.CodegenPlan,
        repositories: dict[str, m.Infra.CodegenRepository],
        projects: dict[Path, set[str]],
        edges: dict[str, set[str]],
    ) -> tuple[m.Infra.CodegenPlan, ...]:
        """Group the plan's outcomes into one cohort per graph component.

        Returns:
            One cohort per strongly connected component, the plan's own
            exception first when present.

        """
        roots = {
            name: (root / repository.path).resolve()
            for name, repository in repositories.items()
        }
        cohorts: list[m.Infra.CodegenPlan] = []
        for component in u.Cli.dag_strongly_connected(edges):
            selected = tuple(
                outcome for outcome in plan.outcomes if outcome.repository in component
            )
            issues = tuple(issue for outcome in selected for issue in outcome.issues)
            failed = tuple(outcome for outcome in selected if outcome.failed)
            issues += tuple(
                m.Infra.Issue(
                    file=str(roots[outcome.repository]),
                    line=0,
                    column=0,
                    code=c.Infra.ToolOutcome.ERROR.value,
                    message=(
                        outcome.error_traceback
                        or outcome.error
                        or outcome.error_type
                        or str(outcome.exception)
                    ),
                )
                for outcome in failed
                if outcome.error
                or outcome.error_type
                or outcome.error_traceback
                or outcome.exception is not None
            )
            cohorts.append(
                m.Infra.CodegenPlan(
                    request=plan.request,
                    workspace=plan.workspace,
                    uv_environments=plan.uv_environments,
                    repositories=tuple(
                        repositories[name] for name in sorted(component)
                    ),
                    files=tuple(
                        file
                        for file in plan.files
                        if projects[file.project].intersection(component)
                    ),
                    issues=issues,
                    exception=next(
                        (
                            outcome.exception
                            for outcome in failed
                            if outcome.exception is plan.exception
                        ),
                        next(
                            (
                                outcome.exception
                                for outcome in failed
                                if outcome.exception is not None
                            ),
                            None,
                        ),
                    ),
                    outcomes=selected,
                )
            )
        if plan.exception is not None:
            cohorts.sort(key=lambda cohort: cohort.exception is not plan.exception)
        return tuple(cohorts)

    def _published_cohort(
        self,
        request: p.Infra.CodegenGenerateRequest,
        root: Path,
        plan: m.Infra.CodegenPlan,
        *,
        prepared_files: tuple[m.Infra.CodegenFilePlan, ...] | None = None,
        publication_followups: tuple[
            Callable[[tuple[Path, ...]], p.Result[bool]], ...
        ] = (),
    ) -> p.Result[p.Infra.CodegenResult]:
        """Admit and publish one complete cohort through the existing owners.

        Every planning diagnostic and cold-import failure rejects the cohort
        before the first destination effect. Check and apply share candidate
        admission and the existing guarded publication owner. Each entry of
        ``publication_followups`` runs with the written paths after a
        successful publication.

        Returns:
            The plan and written paths, or the first failure.

        """
        result_type = r[p.Infra.CodegenResult]
        ports = self.state.ports
        if ports is None:
            return result_type.fail(
                "conformance requires facade-wired file publication"
            )
        started = time.monotonic()
        u.Cli.info(f"stage=admission state=start root={root} files={len(plan.files)}")
        admitted = self._admitted_plans(request, plan, prepared_files=prepared_files)
        u.Cli.info(
            f"stage=admission state=end root={root} "
            f"elapsed={time.monotonic() - started:.3f}s failed={admitted.failure}"
        )
        if admitted.failure:
            return result_type.from_failure(admitted)
        started = time.monotonic()
        u.Cli.info(
            f"stage=publication state=start root={root} files={len(admitted.value)}"
        )
        published = ports.file_publisher.publish_codegen_plans(root, admitted.value)
        completed_paths = (
            published.value
            if published.success
            else tuple(
                Path(path)
                for path in u.type_adapter(t.TypeForm(list[str])).validate_python(
                    (published.error_data or {}).get("written_files", []), strict=True
                )
            )
        )
        u.Cli.info(
            f"stage=publication state=end root={root} "
            f"elapsed={time.monotonic() - started:.3f}s "
            f"written={len(completed_paths)} "
            f"failed={published.failure}"
        )
        if published.failure:
            return result_type.from_failure(published)
        snapshot = self.state.snapshot
        if snapshot is not None and snapshot.workspace_root == root:
            u.Infra.workspace_snapshot_rebase(snapshot, published.value)
        for operation in publication_followups:
            completed = operation(published.value)
            if completed.failure:
                return result_type.fail(
                    completed.error or "publication follow-up failed",
                    error_code=completed.error_code,
                    error_data={
                        **(completed.error_data or {}),
                        "written_files": [
                            *(str(path) for path in published.value),
                            *u.type_adapter(t.TypeForm(list[str])).validate_python(
                                (completed.error_data or {}).get("written_files", []),
                                strict=True,
                            ),
                        ],
                    },
                    exception=completed.exception,
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
        *,
        prepared_files: tuple[m.Infra.CodegenFilePlan, ...] | None = None,
    ) -> p.Result[tuple[m.Infra.CodegenFilePlan, ...]]:
        """Validate the normalized dependency cohort before accepting any effects.

        The native preview materializes original file declarations, including
        retirements. Its existing cold-import owner must accept that exact source
        view before the shared publisher may verify and write its destinations.

        Returns:
            The normalized plans, or the original planning or admission failure.

        """
        result_type = r[tuple[m.Infra.CodegenFilePlan, ...]]
        if (
            plan.issues
            or plan.exception is not None
            or any(outcome.failed for outcome in plan.outcomes)
        ):
            return self._planning_native_failure(plan)
        ports = self.state.ports
        if ports is None:
            return result_type.fail(
                "conformance requires facade-wired candidate admission"
            )
        docs = (
            result_type.ok(prepared_files)
            if prepared_files is not None
            else self._docs_plans(request, plan)
        )
        if docs.failure:
            return result_type.from_failure(docs)
        composed = result_type.create_from_callable(
            lambda: u.Infra.codegen_compose_file_plans(docs.value)
        )
        if composed.failure:
            return result_type.from_failure(composed)
        files = composed.value
        changes = ports.file_publisher.normalized_codegen_changes(files)
        if changes.failure:
            return result_type.from_failure(changes)
        normalized = {change.path: change for change in changes.value}
        files = tuple(
            m.Infra.CodegenFilePlan(
                project=file.project,
                path=file.path,
                before=file.before,
                desired_content=normalized[file.path].desired_content,
                desired_mode=normalized[file.path].desired_mode,
                owner=file.owner,
                policy=file.policy,
                tracking=file.tracking,
                index_before=file.index_before,
                tracking_dependencies=file.tracking_dependencies,
                inputs=file.inputs,
            )
            for file in files
        )
        return self._validated_source_plans(request, files, ports)

    def _planning_native_failure(
        self,
        plan: m.Infra.CodegenPlan,
    ) -> p.Result[tuple[m.Infra.CodegenFilePlan, ...]]:
        """Translate the cohort's planning failure to its original cause.

        The executor's recorded planning failure wins when one of the
        cohort's outcomes carries it; otherwise the cohort's own matching
        native failure is retained.

        Returns:
            The translated native planning failure, or the cohort's
            formatted planning issues.

        """
        result_type = r[tuple[m.Infra.CodegenFilePlan, ...]]
        native = next(
            (
                outcome.native_failure
                for outcome in plan.outcomes
                if outcome.native_failure is not None
                and (
                    plan.exception is None
                    or outcome.native_failure.exception is plan.exception
                )
            ),
            None,
        )
        first_native = self.state.planning_failure
        if first_native is not None and any(
            outcome.native_failure is first_native for outcome in plan.outcomes
        ):
            native = first_native
        if native is not None:
            return result_type.from_failure(native)
        return result_type.fail(
            "\n".join(issue.formatted for issue in plan.issues)
            or "generation planning failed",
            exception=plan.exception,
        )

    @staticmethod
    def _validated_source_plans(
        request: p.Infra.CodegenGenerateRequest,
        files: tuple[m.Infra.CodegenFilePlan, ...],
        ports: p.Infra.CodegenConformPorts,
    ) -> p.Result[tuple[m.Infra.CodegenFilePlan, ...]]:
        """Admit the normalized candidate through its injected runtime validator.

        Returns:
            The unchanged normalized plans, or the original validation failure.

        """
        result_type = r[tuple[m.Infra.CodegenFilePlan, ...]]
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
                tuple(
                    sorted({
                        file.project
                        for file in files
                        if file.path.suffix == c.Infra.EXT_PYTHON
                    })
                ),
            ),
            options=m.Infra.CodegenSourcePreviewOptions(
                declared_files=files,
                inputs=tuple(
                    state for file in files for state in (file.before, *file.inputs)
                ),
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
    ) -> p.Result[tuple[m.Infra.CodegenFilePlan, ...]]:
        """Compose managed plans with their derived presentation and documentation.

        Returns:
            The complete candidate, retaining strict independent artifact admission.

        """
        result_type = r[tuple[m.Infra.CodegenFilePlan, ...]]
        owned = tuple(
            repository.name
            for repository in plan.repositories
            if repository.path == Path()
        )
        if request.what is not c.Infra.CodegenConformSurface.ALL or not owned:
            return result_type.ok(tuple(plan.files))
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
        bundle = planner.prepare_bundle(declared_files=tuple(plan.files))
        if bundle.failure:
            return result_type.from_failure(bundle)
        rendered = planner.plan_files(bundle.value)
        if rendered.failure:
            return result_type.from_failure(rendered)
        return result_type.create_from_callable(
            lambda: u.Infra.codegen_compose_file_plans((
                *u.Infra.codegen_compose_file_plans(
                    (*plan.files, *bundle.value.metadata_files), ordered=True
                ),
                *rendered.value,
            ))
        )


__all__: list[str] = ["FlextInfraCodegenConformExecute"]
