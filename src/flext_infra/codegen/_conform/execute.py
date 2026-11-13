"""Plan declared projections and publish them through the shared publisher.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import os
import time
from collections.abc import Callable, Mapping
from contextlib import ExitStack
from pathlib import Path
from typing import Self, override

from typing_extensions import TypeForm

from flext_infra import (
    c,
    config,
    e,
    m,
    p,
    r,
    settings,
    t,
    u,
    workspace as workspace_services,
)
from flext_infra.codegen._conform import FlextInfraCodegenConformPlan


class FlextInfraCodegenConformExecute(FlextInfraCodegenConformPlan):
    """Generate one request: plan every declared projection, publish once."""

    @classmethod
    def from_request(
        cls: type[Self],
        request: p.Infra.CodegenGenerateRequest,
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
        if execution_context is None:
            return r[p.Infra.CodegenResult].fail(
                "source bootstrap requires bound generation collaborators"
            )
        # Facades and their initializers precede the protocols projected
        # through them: those surfaces publish first, and the next generation
        # projects the members.
        if request.what is c.Infra.CodegenConformSurface.ALL:
            bootstrap = u.Infra.bootstrap_protocol_model_sources(
                request.root, ports=execution_context.codegen_conform_collaborators()
            )
            if bootstrap.failure:
                return r[p.Infra.CodegenResult].from_failure(bootstrap)
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
        publication; its first failure fails the request. Every cohort
        publication also authorizes each ``.envrc`` it wrote.

        Returns:
            The plan and written paths, or the first failure.

        """
        after_cohort_publication = (
            *after_cohort_publication,
            self.authorize_published_envrc,
        )
        u.Cli.info(
            f"operation=generate root={request.root} scope={request.scope} "
            # Bind diagnostics to the selected process settings, never an old report.
            f"surface={request.what} pid={os.getpid()} "
            f"profile={settings.Infra.profile} "
            f"profile_output={settings.Infra.profile_output}"
        )
        root = request.root.expanduser().resolve()
        # Concurrent writers are the normal operating state: planning reads
        # without a tree-wide lock, the atomic publisher verifies every
        # destination's observed state, and a destination changed by another
        # actor triggers a reconciling replan over the new state instead of
        # waiting for, or failing because of, that actor.
        attempts = config.Infra.mutation_lock.reconcile_attempts

        def _run_once() -> p.Result[p.Infra.CodegenResult]:
            self.state.source_inputs.clear()
            self.state.source_imports.clear()
            try:
                return self._execute_once(
                    request, root, after_publication, after_cohort_publication
                )
            except e.OperationError as exc:
                if c.Infra.ATOMIC_SOURCE_CHANGED not in str(exc):
                    raise
                return r[p.Infra.CodegenResult].fail(str(exc))

        result = _run_once()
        while (
            attempts > 0
            and result.failure
            and c.Infra.ATOMIC_SOURCE_CHANGED in (result.error or "")
        ):
            attempts -= 1
            u.Cli.info(
                f"operation=generate root={root} reconcile=replan "
                f"cause={(result.error or '').split(';', 1)[0]}"
            )
            result = _run_once()
        return result

    def _execute_once(
        self,
        request: p.Infra.CodegenGenerateRequest,
        root: Path,
        after_publication: tuple[Callable[[tuple[Path, ...]], p.Result[bool]], ...],
        after_cohort_publication: tuple[
            Callable[[tuple[Path, ...]], p.Result[bool]], ...
        ],
    ) -> p.Result[p.Infra.CodegenResult]:
        """Plan over the current tree and publish atomically once.

        Returns:
            The plan and written paths, or the first failure.

        """
        with ExitStack() as sources:
            previous = self.state.snapshot
            if request.what is c.Infra.CodegenConformSurface.FACADES:
                self.state.snapshot = sources.enter_context(
                    u.Infra.workspace_snapshot(root, (root,))
                )
            try:
                if request.what is not c.Infra.CodegenConformSurface.ALL:
                    return self._planned(request).flat_map(
                        lambda plan: self._published(
                            request,
                            plan,
                            after_publication,
                            after_cohort_publication=after_cohort_publication,
                        )
                    )
                return self._execute_all_surfaces(
                    request,
                    after_publication=after_publication,
                    after_cohort_publication=after_cohort_publication,
                )
            finally:
                self.state.snapshot = previous

    def authorize_published_envrc(
        self,
        written_files: tuple[Path, ...],
    ) -> p.Result[bool]:
        """Authorize with native direnv every ``.envrc`` this publication wrote.

        The generator owns the activation file it renders. Rewriting one
        changes its content hash, and direnv then blocks every later command
        in that checkout, including a workspace member's ``make check`` and
        its commit hook. The publisher therefore authorizes each published
        ``.envrc`` (root and members alike) in the same operation, outside CI,
        with the direnv the root's locked Mise toolchain resolves, never one
        found on the caller's PATH.

        Returns:
            Whether any file was authorized, or the first native failure.

        """
        ci = config.Infra.codegen.make.ci
        if (u.Infra.env_lookup(ci.variable) or "").strip() == ci.value:
            return r[bool].ok(value=False)
        roots = {
            path.expanduser().resolve().parent
            for path in written_files
            if path.name == c.Infra.ENVRC_FILENAME
        }
        for root in sorted(roots):
            direnv = u.Infra.managed_mise_binary(
                c.Infra.CLI_DIRENV, self.state.repository_root
            )
            if direnv.failure:
                return r[bool].from_failure(direnv)
            result = u.Cli.run_raw(
                (str(direnv.value), "allow", str(root)),
                cwd=root,
                timeout=c.Infra.TIMEOUT_SHORT,
            )
            if result.failure:
                return r[bool].from_failure(result)
            if not u.Cli.process_succeeded(result.value.outcome):
                return r[bool].fail(
                    f"direnv allow failed for {root}: "
                    f"{result.value.stderr.strip() or result.value.stdout.strip()}",
                )
        return r[bool].ok(value=bool(roots))

    def _execute_all_surfaces(
        self,
        request: p.Infra.CodegenGenerateRequest,
        *,
        after_publication: tuple[Callable[[tuple[Path, ...]], p.Result[bool]], ...],
        after_cohort_publication: tuple[
            Callable[[tuple[Path, ...]], p.Result[bool]], ...
        ],
    ) -> p.Result[p.Infra.CodegenResult]:
        """Plan the control cohort and the full request, then publish them once.

        The control cohort is planned first so a pre-Python refusal surfaces
        before source analysis, but nothing is published until the complete
        request is planned and admitted: a later planning failure leaves the
        tree untouched. Both plans read the same original tree, the one view
        ``check_managed`` compares; the full plan's final form supersedes the
        control candidate of a shared destination.

        Returns:
            The plan and written paths, or the first failure.

        """
        control_plan = self._control_plan(request)
        if control_plan.failure:
            return r[p.Infra.CodegenResult].from_failure(control_plan)
        planned = self._planned(request)
        if planned.failure:
            return r[p.Infra.CodegenResult].from_failure(planned)
        plan = m.Infra.CodegenPlan.model_validate(planned.value)
        plan.files = tuple(
            m.Infra.CodegenFilePlan.model_validate(file)
            for file in u.Infra.codegen_compose_file_plans(
                (*control_plan.value.files, *plan.files), ordered=True
            )
        )
        return self._published(
            request,
            plan,
            after_publication,
            after_cohort_publication=after_cohort_publication,
        )

    def _control_plan(
        self,
        request: p.Infra.CodegenGenerateRequest,
    ) -> p.Result[p.Infra.CodegenPlan]:
        """Plan the native file-only control cohort before Python inventory.

        The cohort exists to materialize a scaffold's declared project metadata
        before member planning when the manifest is not on disk yet. An
        existing workspace already publishes every control destination from
        the full managed plan of the same original tree, so planning it twice
        only repeated the render and its Git probes; those destinations keep
        their single owner in the full plan and the refusal still happens
        before the run's one publication.

        Returns:
            The control cohort plan with every repository outcome, or the
            first workspace, selection, seed or ordering failure.

        """
        result_type = r[p.Infra.CodegenPlan]
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
        if workspace.flext_source is None:
            return result_type.ok(
                m.Infra.CodegenPlan(
                    request=request,
                    repositories=selected.value,
                    workspace=workspace,
                    uv_environments=(),
                    files=(),
                )
            )
        return self._scaffold_control_plan(
            request,
            root,
            (workspace, current_target, current_repository),
            captured.value,
            selected.value,
        )

    def _scaffold_control_plan(
        self,
        request: p.Infra.CodegenGenerateRequest,
        root: Path,
        planning: tuple[
            p.Infra.WorkspaceSpec,
            p.Infra.RepositoryConformTarget,
            p.Infra.RepositoryRef,
        ],
        inputs: p.Infra.CodegenInputs,
        selected: tuple[p.Infra.RepositoryRef, ...],
    ) -> p.Result[p.Infra.CodegenPlan]:
        """Plan the control cohort a scaffold needs before its members.

        Returns:
            The control cohort plan, or the first selection, seed or ordering
            failure.

        """
        result_type = r[p.Infra.CodegenPlan]
        workspace, current_target, _current_repository = planning
        identities = self._control_identities(selected)
        if identities.failure:
            return result_type.from_failure(identities)
        seed = self._control_seed(current_target, workspace, inputs)
        if seed.failure:
            return result_type.from_failure(seed)
        graph = self._control_graph(root, workspace, inputs, selected, seed.value)
        ordered = u.Cli.dag_order(graph)
        if ordered.failure:
            return result_type.from_failure(ordered)
        previous = self.state.provider_plans
        self.state.provider_plans = tuple(
            m.Infra.CodegenFilePlan.model_validate(file)
            for file in u.Infra.codegen_compose_file_plans(
                (*(previous or ()), *seed.value), ordered=True
            )
        )
        try:
            outcomes = tuple(
                self._control_outcome(
                    m.Infra.CodegenRepositoryPlanTask.model_validate({
                        "root": (root),
                        "workspace": (workspace),
                        "current_target": (current_target),
                        "repository": (identities.value[name]),
                        "surface": (request.what),
                        "selected_inputs": (
                            inputs
                            if identities.value[name].name
                            == current_target.repository.name
                            else None
                        ),
                    }),
                )
                for name in ordered.value
            )
        finally:
            self.state.provider_plans = previous
        return result_type.ok(
            m.Infra.CodegenPlan(
                request=request,
                repositories=selected,
                workspace=workspace,
                uv_environments=(),
                files=u.Infra.codegen_compose_file_plans(
                    tuple(file for outcome in outcomes for file in outcome.files)
                ),
                outcomes=outcomes,
            )
        )

    @staticmethod
    def _control_identities(
        selected: tuple[p.Infra.RepositoryRef, ...],
    ) -> p.Result[dict[str, p.Infra.RepositoryRef]]:
        """Index the selected repositories by their unique distribution identity.

        Returns:
            The selected repositories keyed by distribution name, in selection
            order, or the duplicate-identity failure.

        """
        result_type = r[dict[str, p.Infra.RepositoryRef]]
        by_name = {
            t.Infra.DISTRIBUTION_NAME_ADAPTER.validate_python(
                repository.distribution
            ): repository
            for repository in selected
        }
        if len(by_name) != len(selected):
            return result_type.fail(
                "workspace declares duplicate distribution identities"
            )
        if len({repository.name for repository in selected}) != len(selected):
            return result_type.fail(
                "workspace declares duplicate repository identities"
            )
        return result_type.ok(by_name)

    def _control_seed(
        self,
        current_target: p.Infra.RepositoryConformTarget,
        workspace: p.Infra.WorkspaceSpec,
        inputs: p.Infra.CodegenInputs,
    ) -> p.Result[tuple[p.Infra.CodegenFilePlan, ...]]:
        """Plan the invoking target's existing control files for a sourced workspace.

        Returns:
            The invoking target's control file plans, empty without a declared
            FLEXT source, or the original planning failure.

        """
        result_type = r[tuple[p.Infra.CodegenFilePlan, ...]]
        if workspace.flext_source is None:
            return result_type.ok(())
        initial = self._plan_existing_control(current_target, workspace, inputs)
        if initial.failure:
            return result_type.from_failure(initial)
        return result_type.ok(initial.value.files)

    @staticmethod
    def _control_graph(
        root: Path,
        workspace: p.Infra.WorkspaceSpec,
        inputs: p.Infra.CodegenInputs,
        selected: tuple[p.Infra.RepositoryRef, ...],
        seed: tuple[p.Infra.CodegenFilePlan, ...],
    ) -> dict[str, tuple[str, ...]]:
        """Read the local dependency graph with its bootstrap executor edge.

        Returns:
            The dependency graph of the selected repositories, the workspace
            owner depending on the declared bootstrap executor.

        """
        graph = dict(
            u.Infra.workspace_dependency_graph(
                root,
                selected,
                inputs=workspace.inputs,
                planned_manifests=tuple(
                    plan for plan in seed if plan.path.name == c.PYPROJECT_FILENAME
                ),
            )
        )
        executor = inputs.spec.templates.bootstrap_entry.bootstrap_distribution
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
        return graph

    def _control_outcome(
        self,
        task: p.Infra.CodegenRepositoryPlanTask,
    ) -> p.Infra.CodegenRepositoryPlanOutcome:
        """Plan one control repository; its first failure stops the cohort.

        A success extends the provider plans visible to later repositories.

        Returns:
            The repository's planning outcome.

        """
        planned = self._control_repository(task)
        if planned.failure:
            u.Infra.codegen_raise_failure(
                (task.root / task.repository.path).resolve(), planned
            )
        self.state.provider_plans = tuple(
            m.Infra.CodegenFilePlan.model_validate(file)
            for file in u.Infra.codegen_compose_file_plans(
                (*(self.state.provider_plans or ()), *planned.value.files),
                ordered=True,
            )
        )
        return planned.value

    def _control_repository(
        self,
        task: p.Infra.CodegenRepositoryPlanTask,
    ) -> p.Result[p.Infra.CodegenRepositoryPlanOutcome]:
        """Resolve a control target through the existing metadata owners.

        Returns:
            The control target's planning outcome, or its first failure.

        """
        result_type = r[p.Infra.CodegenRepositoryPlanOutcome]
        resolved = self._resolved_repository_root(
            task.root, task.workspace, task.current_target, task.repository
        )
        if resolved.failure:
            return result_type.from_failure(resolved)
        captured = (
            r[p.Infra.CodegenInputs].ok(task.selected_inputs)
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
        return self._planned(request).flat_map(
            lambda plan: self._checked(request, plan)
        )

    def _checked(
        self,
        request: p.Infra.CodegenGenerateRequest,
        plan: p.Infra.CodegenPlan,
    ) -> p.Result[p.Infra.CodegenResult]:
        """Compare the injected publisher's normalized plan with the tree.

        Check and apply consume the same publication capability; neither resolves
        a utility implementation inside the executor.

        Returns:
            The plan when nothing is pending, or the stale destinations.

        """
        result_type = r[p.Infra.CodegenResult]
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
        payload: p.Infra.CodegenResult = m.Infra.CodegenResult.model_validate({
            "plan": (plan)
        })
        return result_type.ok(payload)

    def _planned(
        self,
        request: p.Infra.CodegenGenerateRequest,
    ) -> p.Result[p.Infra.CodegenPlan]:
        """Plan the request; a planning exception propagates with its traceback.

        Returns:
            The plan, or its typed admission failure.

        """
        started = time.monotonic()
        u.Cli.info(f"stage=planning state=start root={request.root}")
        planned = (
            self._plan_single_surface(request)
            if request.what in c.Infra.FILE_ONLY_SURFACES
            else self._plan_request(request)
        )
        u.Cli.info(
            f"stage=planning state=end root={request.root} "
            f"elapsed={time.monotonic() - started:.3f}s "
            f"files={len(planned.value.files) if planned.success else 0} "
            f"failed={planned.failure}"
        )
        return planned

    def _published(
        self,
        request: p.Infra.CodegenGenerateRequest,
        plan: p.Infra.CodegenPlan,
        after_publication: tuple[Callable[[tuple[Path, ...]], p.Result[bool]], ...],
        *,
        after_cohort_publication: tuple[
            Callable[[tuple[Path, ...]], p.Result[bool]], ...
        ] = (),
    ) -> p.Result[p.Infra.CodegenResult]:
        """Admit every authenticated cohort, then publish the request once.

        Changed providers, consumers and exports share candidate admission per
        cohort. The first admission failure rejects the whole request before
        any destination effect; the admitted cohorts are published together
        through one publisher call. Follow-ups require that publication to
        succeed.

        Returns:
            The full result, or the first cause with the actual written paths.

        """
        result_type = r[p.Infra.CodegenResult]
        root = request.root.expanduser().resolve()
        selection: tuple[
            tuple[p.Infra.CodegenPlan, tuple[p.Infra.CodegenFilePlan, ...] | None],
            ...,
        ] = ((plan, None),)
        if plan.outcomes:
            ready = {
                repository.name: repository
                for repository in plan.repositories
                if any(
                    outcome.repository == repository.name for outcome in plan.outcomes
                )
            }
            documentation_failure = self._ready_documentation_plans(
                request, root, plan, ready
            )
            if documentation_failure is not None:
                return result_type.from_failure(documentation_failure)
            cohorts = self._publication_cohorts(root, plan)
            if cohorts.failure:
                return result_type.from_failure(cohorts)
            selection = tuple((cohort, cohort.files) for cohort in cohorts.value)
        admitted = self._admitted_cohorts(request, root, selection)
        if admitted.failure:
            return result_type.from_failure(admitted)
        return self._published_admitted(
            root,
            plan,
            admitted.value,
            publication_followups=(*after_cohort_publication, *after_publication),
        )

    def _ready_documentation_plans(
        self,
        request: p.Infra.CodegenGenerateRequest,
        root: Path,
        plan: p.Infra.CodegenPlan,
        ready: Mapping[str, p.Infra.RepositoryRef],
    ) -> p.Result[tuple[p.Infra.CodegenFilePlan, ...]] | None:
        """Fold ready-repository documentation into the published plan.

        A documentation planning failure aborts publication before any effect.

        Returns:
            ``None`` when the plan carries the documentation files, otherwise
            the documentation planning failure.

        """
        plan = m.Infra.CodegenPlan.model_validate(plan)
        ready_roots = {
            (root / repository.path).resolve() for repository in ready.values()
        }
        documents = self._docs_plans(
            request,
            m.Infra.CodegenPlan(
                request=plan.request,
                workspace=plan.workspace,
                repositories=tuple(ready.values()),
                files=tuple(file for file in plan.files if file.project in ready_roots),
                uv_environments=plan.uv_environments,
            ),
        )
        if documents.failure:
            return documents
        plan.files = tuple(
            m.Infra.CodegenFilePlan.model_validate(file) for file in documents.value
        )
        return None

    def _admitted_cohorts(
        self,
        request: p.Infra.CodegenGenerateRequest,
        root: Path,
        cohorts: tuple[
            tuple[p.Infra.CodegenPlan, tuple[p.Infra.CodegenFilePlan, ...] | None],
            ...,
        ],
    ) -> p.Result[tuple[p.Infra.CodegenFilePlan, ...]]:
        """Admit every cohort before any effect; the first refusal stops all.

        Each cohort carries its prepared files, or ``None`` to derive its
        documentation during admission.

        Returns:
            The admitted plans of every cohort in cohort order, or the first
            admission failure naming its cohort's repositories.

        """
        result_type = r[tuple[p.Infra.CodegenFilePlan, ...]]
        admitted: list[p.Infra.CodegenFilePlan] = []
        for cohort, prepared_files in cohorts:
            files = self._admitted_cohort(
                request, root, cohort, prepared_files=prepared_files
            )
            if files.failure:
                return result_type.fail(
                    files.error or "generation cohort admission failed",
                    error_code=files.error_code,
                    error_data={
                        **(files.error_data or {}),
                        "failed_repositories": [
                            repository.name for repository in cohort.repositories
                        ],
                    },
                    exception=files.exception,
                )
            admitted.extend(files.value)
        return result_type.ok(tuple(admitted))

    @classmethod
    def _publication_cohorts(
        cls,
        root: Path,
        plan: p.Infra.CodegenPlan,
    ) -> p.Result[tuple[p.Infra.CodegenPlan, ...]]:
        """Close candidate effects over authenticated changed-file dependencies.

        Returns:
            Existing plan objects grouped by the native graph component owner.

        """
        result_type = r[tuple[p.Infra.CodegenPlan, ...]]
        outcomes = {outcome.repository: outcome for outcome in plan.outcomes}
        repositories = {repository.name: repository for repository in plan.repositories}
        roots = {
            name: (root / repository.path).resolve()
            for name, repository in repositories.items()
        }
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
            cls._component_cohort_plans(plan, repositories, projects, edges)
        )

    @classmethod
    def _cohort_dependency_edges(
        cls,
        files: tuple[p.Infra.CodegenFilePlan, ...],
        projects: dict[Path, set[str]],
        outcomes: Mapping[str, p.Infra.CodegenRepositoryPlanOutcome],
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

    @staticmethod
    def _component_cohort_plans(
        plan: p.Infra.CodegenPlan,
        repositories: dict[str, p.Infra.RepositoryRef],
        projects: dict[Path, set[str]],
        edges: dict[str, set[str]],
    ) -> tuple[p.Infra.CodegenPlan, ...]:
        """Group the plan's outcomes into one cohort per graph component.

        Returns:
            One cohort per strongly connected component.

        """
        return tuple(
            m.Infra.CodegenPlan(
                request=plan.request,
                workspace=plan.workspace,
                uv_environments=plan.uv_environments,
                repositories=tuple(repositories[name] for name in sorted(component)),
                files=tuple(
                    file
                    for file in plan.files
                    if projects[file.project].intersection(component)
                ),
                outcomes=tuple(
                    outcome
                    for outcome in plan.outcomes
                    if outcome.repository in component
                ),
            )
            for component in u.Cli.dag_strongly_connected(edges)
        )

    def _admitted_cohort(
        self,
        request: p.Infra.CodegenGenerateRequest,
        root: Path,
        plan: p.Infra.CodegenPlan,
        *,
        prepared_files: tuple[p.Infra.CodegenFilePlan, ...] | None = None,
    ) -> p.Result[tuple[p.Infra.CodegenFilePlan, ...]]:
        """Admit one cohort without any destination effect.

        Every planning diagnostic and cold-import failure rejects the cohort
        before the first destination effect. Check and apply share this
        candidate admission.

        Returns:
            The admitted normalized plans, or the first admission failure.

        """
        started = time.monotonic()
        u.Cli.info(f"stage=admission state=start root={root} files={len(plan.files)}")
        admitted = self._admitted_plans(request, plan, prepared_files=prepared_files)
        u.Cli.info(
            f"stage=admission state=end root={root} "
            f"elapsed={time.monotonic() - started:.3f}s failed={admitted.failure}"
        )
        return admitted

    def _published_admitted(
        self,
        root: Path,
        plan: p.Infra.CodegenPlan,
        admitted: tuple[p.Infra.CodegenFilePlan, ...],
        *,
        publication_followups: tuple[
            Callable[[tuple[Path, ...]], p.Result[bool]], ...
        ] = (),
    ) -> p.Result[p.Infra.CodegenResult]:
        """Publish admitted plans once through the guarded publication owner.

        Each entry of ``publication_followups`` runs with the written paths
        after a successful publication.

        Returns:
            The plan and written paths, or the first failure.

        """
        result_type = r[p.Infra.CodegenResult]
        plan = m.Infra.CodegenPlan.model_validate(plan)
        ports = self.state.ports
        if ports is None:
            return result_type.fail(
                "conformance requires facade-wired file publication"
            )
        started = time.monotonic()
        u.Cli.info(f"stage=publication state=start root={root} files={len(admitted)}")
        # Admission already normalized these bytes; publish them as admitted.
        published = ports.file_publisher.publish_normalized_codegen_plans(
            root, admitted, admitted
        )
        completed_paths = (
            published.value
            if published.success
            else tuple(
                Path(path)
                for path in u.type_adapter(TypeForm(list[str])).validate_python(
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
                            *u.type_adapter(TypeForm(list[str])).validate_python(
                                (completed.error_data or {}).get("written_files", []),
                                strict=True,
                            ),
                        ],
                    },
                    exception=completed.exception,
                )
        plan.files = tuple(
            m.Infra.CodegenFilePlan.model_validate(file) for file in admitted
        )
        payload: p.Infra.CodegenResult = m.Infra.CodegenResult.model_validate({
            "plan": (plan),
            "written_files": (published.value),
        })
        return result_type.ok(payload)

    def _admitted_plans(
        self,
        request: p.Infra.CodegenGenerateRequest,
        plan: p.Infra.CodegenPlan,
        *,
        prepared_files: tuple[p.Infra.CodegenFilePlan, ...] | None = None,
    ) -> p.Result[tuple[p.Infra.CodegenFilePlan, ...]]:
        """Validate the normalized dependency cohort before accepting any effects.

        The native preview materializes original file declarations, including
        retirements. Its existing cold-import owner must accept that exact source
        view before the shared publisher may verify and write its destinations.

        Returns:
            The normalized plans, or the original planning or admission failure.

        """
        result_type = r[tuple[p.Infra.CodegenFilePlan, ...]]
        ports = self.state.ports
        if ports is None:
            return result_type.fail(
                "conformance requires facade-wired candidate admission"
            )
        u.Cli.info("stage=admission-docs state=start")
        docs = (
            result_type.ok(prepared_files)
            if prepared_files is not None
            else self._docs_plans(request, plan)
        )
        if docs.failure:
            return result_type.from_failure(docs)
        u.Cli.info(f"stage=admission-docs state=end files={len(docs.value)}")
        composed = result_type.create_from_callable(
            lambda: u.Infra.codegen_compose_file_plans(docs.value)
        )
        if composed.failure:
            return result_type.from_failure(composed)
        files = composed.value
        u.Cli.info(f"stage=admission-normalization state=start files={len(files)}")
        changes = ports.file_publisher.normalized_codegen_changes(files)
        if changes.failure:
            return result_type.from_failure(changes)
        u.Cli.info("stage=admission-normalization state=end")
        normalized = {change.path: change for change in changes.value}
        captured = self._admission_captured_sources(request, files)
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
                inputs=(*file.inputs, *(captured if index == 0 else ())),
            )
            for index, file in enumerate(files)
        )
        return self._validated_source_plans(request, files, self.state)

    def _admission_captured_sources(
        self,
        request: p.Infra.CodegenGenerateRequest,
        files: tuple[p.Infra.CodegenFilePlan, ...],
    ) -> tuple[p.Cli.AtomicFileState, ...]:
        """Carry the original witnesses of the cohort's own projects.

        Admission materializes every source it is handed and follows the
        candidate's import closure from there. The run reads every selected
        repository while planning, so handing it the whole run's witnesses
        copied unrelated members into every cohort. The candidate closure
        already reads each imported dependency from the run snapshot, so the
        captured set retains the cohort's own sources (and the invoking root)
        and excludes only members this cohort does not plan.

        Returns:
            The captured source witnesses in planning order.

        """
        captured = tuple(self.state.source_inputs.values())
        topology = self._planning_topology
        workspace = None if topology is None else topology[0]
        if workspace is None or not workspace.subprojects:
            return captured
        root = request.root.expanduser().resolve()
        included = {file.project.resolve() for file in files}
        members = tuple(
            (root / repository.path).resolve() for repository in workspace.subprojects
        )
        foreign = tuple(member for member in members if member not in included)
        if not foreign:
            return captured
        return tuple(
            state
            for state in captured
            if not any(state.path.is_relative_to(member) for member in foreign)
        )

    @staticmethod
    def _validated_source_plans(
        request: p.Infra.CodegenGenerateRequest,
        files: tuple[p.Infra.CodegenFilePlan, ...],
        run: p.Infra.CodegenConformState,
    ) -> p.Result[tuple[p.Infra.CodegenFilePlan, ...]]:
        """Admit the normalized candidate through its injected runtime validator.

        Admission validates a change: a candidate whose Python sources all
        keep their captured content is the live tree itself, so it publishes
        no Python effect and needs no staged preview.

        Returns:
            The unchanged normalized plans, or the original validation failure.

        """
        result_type = r[tuple[p.Infra.CodegenFilePlan, ...]]
        if not any(
            file.path.suffix == c.Infra.EXT_PYTHON
            and file.desired_content != file.before.content
            for file in files
        ):
            return result_type.ok(files)
        ports, snapshot = run.ports, run.snapshot
        if ports is None:
            return result_type.fail("candidate admission requires its bound ports")
        root = request.root.expanduser().resolve()
        inputs: dict[Path, p.Cli.AtomicFileState] = {}
        for file in files:
            for state in (file.before, *file.inputs):
                original = inputs.setdefault(state.path, state)
                if original != state:
                    return result_type.fail(
                        f"candidate has conflicting source observations: {state.path}"
                    )
        u.Cli.info(f"stage=admission-preview state=start root={root}")
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
            options=m.Infra.StageSourceOptions.model_validate({
                "declared_files": (files),
                "inputs": (tuple(inputs.values())),
                "snapshot": (snapshot),
                # The cohort's witnesses exclude foreign members, so do its
                # import facts; the closure reads those members from the snapshot.
                "import_edges": {
                    path: edges
                    for path, edges in run.source_imports.items()
                    if path in inputs
                },
            }),
        ).flat_map(lambda outcome: outcome)
        if preview.failure:
            return result_type.from_failure(preview)
        u.Cli.info("stage=admission-preview state=end")
        if not preview.value:
            return result_type.fail("native candidate admission returned no acceptance")
        return result_type.ok(files)

    def _docs_plans(
        self,
        request: p.Infra.CodegenGenerateRequest,
        plan: p.Infra.CodegenPlan,
    ) -> p.Result[tuple[p.Infra.CodegenFilePlan, ...]]:
        """Compose managed plans with their derived presentation and documentation.

        Returns:
            The complete candidate, retaining strict independent artifact admission.

        """
        result_type = r[tuple[p.Infra.CodegenFilePlan, ...]]
        owned = tuple(
            # The docs selector names PROJECTS (what docs discovery indexes:
            # the distribution), not the repository catalog key (git slug).
            repository.distribution
            for repository in plan.repositories
            if repository.path == Path()
        )
        # Documentation analyzes the published project (its pyproject and
        # sources on disk); a new project's first generation publishes them,
        # and the bootstrap's next generation documents what it published.
        published = (request.root / c.PYPROJECT_FILENAME).is_file()
        if (
            request.what is not c.Infra.CodegenConformSurface.ALL
            or not owned
            or not published
        ):
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
