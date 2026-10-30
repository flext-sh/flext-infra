"""Conformance plan selection and repository topology resolution.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import operator
import time
import traceback
from collections.abc import Mapping, MutableMapping, Sequence
from contextlib import ExitStack
from pathlib import Path
from typing import Literal

from flext_infra import c, m, p, r, u, workspace as workspace_services
from flext_infra.codegen import FlextInfraCodegenLazyInit
from flext_infra.codegen._conform.scaffold_plan import (
    FlextInfraCodegenConformScaffoldPlan,
)


class FlextInfraCodegenConformPlan(FlextInfraCodegenConformScaffoldPlan):
    """Conformance planning across scaffold and existing repositories."""

    def plan(
        self,
        request: p.Infra.CodegenGenerateRequest,
    ) -> p.Result[m.Infra.CodegenPlan]:
        """Build and validate the complete selection without writing.

        Returns:
            The resulting ``p.Result[m.Infra.CodegenPlan]``.

        """
        self._begin_planning()
        return self._plan_request(request)

    def _plan_request(
        self,
        request: p.Infra.CodegenGenerateRequest,
    ) -> p.Result[m.Infra.CodegenPlan]:
        """Plan the active invocation without resetting its retained diagnostics.

        Returns:
            The resulting ``p.Result[m.Infra.CodegenPlan]``.

        """
        inputs = u.Infra.load_codegen_inputs(request.root.expanduser().resolve())
        if inputs.failure:
            return r[m.Infra.CodegenPlan].from_failure(inputs)
        return self._plan_repositories(request, inputs.value)

    def _plan_single_surface(
        self,
        request: p.Infra.CodegenGenerateRequest,
        *,
        inputs: m.Infra.CodegenInputs | None = None,
    ) -> p.Result[m.Infra.CodegenPlan]:
        """Plan the declared facade or lazy-init surface of one repository.

        Returns:
            The surface plan, or its first planning failure.

        """
        if inputs is None:
            loaded = u.Infra.load_codegen_inputs(request.root.expanduser().resolve())
            if loaded.failure:
                return r[m.Infra.CodegenPlan].from_failure(loaded)
            inputs = loaded.value
        if request.what == c.Infra.CodegenConformSurface.FACADES:
            return self.plan_facade(request, inputs)
        return self._plan_lazy_init(request, inputs)

    def plan_repositories(
        self,
        request: p.Infra.CodegenGenerateRequest,
        inputs: m.Infra.CodegenInputs,
    ) -> p.Result[m.Infra.CodegenPlan]:
        """Dispatch the declared surface using its captured repository inputs.

        Returns:
            The complete repository plan or its first planning failure.

        """
        self._begin_planning()
        return self._plan_repositories(request, inputs)

    def _plan_repositories(
        self,
        request: p.Infra.CodegenGenerateRequest,
        inputs: m.Infra.CodegenInputs,
    ) -> p.Result[m.Infra.CodegenPlan]:
        """Compose repository phases within the active planning invocation.

        Returns:
            The resulting ``p.Result[m.Infra.CodegenPlan]``.

        """
        if request.what in c.Infra.FILE_ONLY_SURFACES:
            return self._plan_single_surface(request, inputs=inputs)
        root = request.root.expanduser().resolve()
        targets = self._planning_workspace(request, root, inputs=inputs)
        if targets.failure:
            return r[m.Infra.CodegenPlan].from_failure(targets)
        workspace, _current_target, current_repository = targets.value
        selected_result = self._select_repositories(
            request,
            workspace,
            current_repository,
        )
        if selected_result.failure:
            return r[m.Infra.CodegenPlan].from_failure(selected_result)
        selected = selected_result.value
        gathered = self._gathered_repository_plans(
            root,
            targets.value,
            selected,
            request.what,
            inputs,
        )
        if gathered.failure:
            return r[m.Infra.CodegenPlan].from_failure(gathered)
        files, environments, issues, outcomes = gathered.value
        return r[m.Infra.CodegenPlan].ok(
            m.Infra.CodegenPlan(
                request=request,
                repositories=selected,
                workspace=workspace,
                uv_environments=tuple(environments),
                files=tuple(files),
                issues=tuple(issues),
                exception=self.state.planning_exception,
                outcomes=outcomes,
            ),
        )

    def plan_facade(
        self,
        request: p.Infra.CodegenGenerateRequest,
        inputs: m.Infra.CodegenInputs,
    ) -> p.Result[m.Infra.CodegenPlan]:
        """Admit a destination and close its recursive family dependency cohort.

        The selected facade, native component moves, dependent initializers and
        consumer imports share the existing fixed point and publication owner.

        Args:
            request: The conform request containing the root and destination module.
            inputs: The effective codegen policy.

        Returns:
            The facade plan, or the first failure.

        """
        result_type = r[m.Infra.CodegenPlan]
        root = request.root.expanduser().resolve()
        topology = self._planning_workspace(request, root, inputs=inputs)
        if topology.failure:
            return result_type.from_failure(topology)
        workspace, target, repository = topology.value
        files = self._facade_file_plans(
            root, request.module, inputs.spec, profile=target.make_profile.value
        )
        if files.failure:
            return result_type.from_failure(files)
        return result_type.ok(
            m.Infra.CodegenPlan(
                request=request,
                repositories=(repository,),
                workspace=workspace,
                uv_environments=(),
                files=files.value,
                issues=tuple(self.state.planning_issues),
                exception=self.state.planning_exception,
            )
        )

    def _facade_file_plans(
        self,
        root: Path,
        module: str | None,
        codegen: m.Infra.CodegenConfigSpec,
        *,
        profile: str,
    ) -> p.Result[tuple[m.Infra.CodegenFilePlan, ...]]:
        """Authenticate one facade and use the existing source convergence owner.

        The current module elects the family; directory spelling never elects a
        namespace identity. The caller's snapshot authority is restored on exit.

        Returns:
            The dependency-complete selected cohort, or its planning failure.

        """
        result_type = r[tuple[m.Infra.CodegenFilePlan, ...]]
        previous_snapshot = self.state.snapshot
        with (
            u.Infra.workspace_snapshot(root, (root,)) as snapshot,
            self.shared_source_views(),
        ):
            self.state.snapshot = snapshot
            try:
                cohort = tuple(self.state.provider_plans or ())
                with self._source_view(root, declared_files=cohort) as (
                    project,
                    sources,
                ):
                    selected = self._facade_source_selection(
                        root, module, project, sources
                    )
                    if selected.failure:
                        return result_type.from_failure(selected)
                    destination, _mode = selected.value
                    family = self._facade_family(
                        u.Infra.facade_letter_names_at(project, destination)
                    )
                    if family.failure:
                        return result_type.from_failure(family)
                return self._converged_custom_sources(
                    root,
                    (codegen, profile),
                    cohort=cohort,
                    normalize_imports=True,
                    selection=(destination, c.Infra.FacadeFamily(family.value)),
                ).map(operator.itemgetter(0))
            finally:
                self.state.snapshot = previous_snapshot

    @staticmethod
    def _facade_source_selection(
        root: Path,
        module: str | None,
        project: p.Infra.RopeProject,
        sources: Mapping[Path, str],
    ) -> p.Result[tuple[Path, int]]:
        """Select the declared facade input and its original mode.

        Returns:
            The declared destination and mode, or its first failure.

        """
        result_type = r[tuple[Path, int]]
        if module is None:
            return result_type.fail(
                "facades requires an existing package and destination"
            )
        destination = next(
            (
                path
                for path in sources
                if path.name not in {c.Infra.INIT_PY, c.Infra.INIT_PYI}
                and u.Infra.module_name_for_file(
                    path, project_root=root, source_project=project
                )
                == module
            ),
            None,
        )
        if destination is None:
            return result_type.fail(f"facade input is absent: {module}")
        if not destination.resolve().is_relative_to(root):
            return result_type.fail(f"facade input escapes repository: {destination}")
        selected = u.Cli.atomic_read_binary_file_state(destination, required=True)
        if selected.failure:
            return result_type.from_failure(selected)
        if selected.value.content is None or selected.value.mode is None:
            return result_type.fail(f"facade input is absent: {destination}")
        return result_type.ok((destination, selected.value.mode))

    @staticmethod
    def _facade_family(
        names: frozenset[str],
    ) -> p.Result[Literal["c", "t", "u", "p", "m"]]:
        """Identify the selected renderer from the module's published declaration.

        Returns:
            The unique supported facade family or a declaration failure.

        """
        result_type = r[Literal["c", "t", "u", "p", "m"]]
        match tuple(sorted(names)):
            case ("c",):
                return result_type.ok("c")
            case ("t",):
                return result_type.ok("t")
            case ("u",):
                return result_type.ok("u")
            case ("p",):
                return result_type.ok("p")
            case ("m",):
                return result_type.ok("m")
            case _:
                return result_type.fail(
                    "selected facade destination must declare one supported family",
                )

    @staticmethod
    def _render_facade(
        destination: Path,
        family: Literal["c", "t", "u", "p", "m"],
        sources: Mapping[Path, str],
        *,
        project: p.Infra.RopeProject,
    ) -> p.Result[str]:
        """Reuse the canonical renderer without selecting a different destination.

        Returns:
            Rendered source for exactly the requested declaring module.

        """
        if family == "t":
            return u.Infra.render_type_facade(
                destination.parent, destination, sources, project=project
            )
        elected = u.Infra.facade_module_path(
            destination.parent, family, project=project, sources=sources
        )
        if elected is None:
            return r[str].fail("selected facade has no declaring module")
        if elected.failure:
            return r[str].from_failure(elected)
        if elected.value != destination:
            return r[str].fail("selected facade differs from its declaring module")
        rendered = u.Infra.render_utility_facade(
            destination.parent, family=family, project=project, sources=sources
        )
        if rendered is None:
            return r[str].fail(f"selected facade has no private {family} owners")
        return rendered

    def _plan_lazy_init(
        self,
        request: p.Infra.CodegenGenerateRequest,
        inputs: m.Infra.CodegenInputs,
    ) -> p.Result[m.Infra.CodegenPlan]:
        """Converge initializers with their facade and source-consumer dependencies.

        Withholding a private child's exports changes the interfaces its generated
        parent facades consume. The existing source convergence owns those coupled
        plans; an initializer-only filter must not split that publication cohort.
        Each selected repository retains its own snapshot authority through the
        same invocation, including declared-subproject scope.
        The complete initial lazy plan supplies the existing provider-seed path;
        its unchanged-input predicate still elects whether replanning is required.
        Caller-owned provider plans and snapshots are restored on every exit.
        A module-selected package remains selected through source convergence;
        dependency reads do not admit unrelated facade publication domains.

        Returns:
            The dependency-complete source plan, or the first planning failure.

        """
        result_type = r[m.Infra.CodegenPlan]
        root = request.root.expanduser().resolve()
        selected = self._lazy_init_repositories(request, root, inputs)
        if selected.failure:
            return result_type.from_failure(selected)
        workspace, repositories = selected.value
        participants = tuple(
            participant
            for participant in repositories
            if participant.kind is c.Infra.ProjectKind.INTERNAL_FLEXT
        )
        roots = tuple(
            (root / participant.path).resolve() for participant in participants
        )
        previous = self.state.snapshot, self.state.provider_plans
        with (
            u.Infra.workspace_snapshot(root, roots) as snapshot,
            ExitStack() as repository_snapshots,
            self.shared_source_views(),
        ):
            self.state.snapshot = snapshot
            try:
                planned = FlextInfraCodegenLazyInit(
                    repository_root=root,
                    project_scope_roots=roots,
                    module=request.module,
                ).plan_files(snapshot=snapshot)
                if planned.failure:
                    return result_type.from_failure(planned)
                self.state.provider_plans = planned.value
                files = {file.path: file for file in planned.value}
                for participant in participants:
                    project = (root / participant.path).resolve()
                    self.state.snapshot = (
                        snapshot
                        if project == root
                        else repository_snapshots.enter_context(
                            u.Infra.workspace_snapshot(project, ())
                        )
                    )
                    project_inputs = (
                        r[m.Infra.CodegenInputs].ok(inputs)
                        if project == root
                        else u.Infra.load_codegen_inputs(project)
                    )
                    if project_inputs.failure:
                        return result_type.from_failure(project_inputs)
                    selection: tuple[Path, c.Infra.FacadeFamily | None] | None = None
                    if request.module is not None:
                        with self._source_view(
                            project, declared_files=tuple(files.values())
                        ) as (source_project, _sources):
                            destinations = tuple(
                                file.path
                                for file in planned.value
                                if file.project == project
                                and u.Infra.module_name_for_file(
                                    file.path,
                                    project_root=project,
                                    source_project=source_project,
                                )
                                == request.module
                            )
                        if not destinations:
                            continue
                        if len(destinations) != 1:
                            return result_type.fail(
                                f"lazy package selection is ambiguous: {request.module}"
                            )
                        selection = (destinations[0], None)
                    converged = self._converged_custom_sources(
                        project,
                        (project_inputs.value.spec, participant.role.value),
                        cohort=tuple(files.values()),
                        normalize_imports=True,
                        selection=selection,
                    )
                    if converged.failure:
                        return result_type.from_failure(converged)
                    files.update((file.path, file) for file in converged.value[0])
            finally:
                self.state.snapshot, self.state.provider_plans = previous
        return result_type.ok(
            m.Infra.CodegenPlan(
                request=request,
                repositories=repositories,
                workspace=workspace,
                uv_environments=(),
                files=tuple(files[path] for path in sorted(files)),
                issues=tuple(self.state.planning_issues),
                exception=self.state.planning_exception,
            )
        )

    def _lazy_init_repositories(
        self,
        request: p.Infra.CodegenGenerateRequest,
        root: Path,
        inputs: m.Infra.CodegenInputs,
    ) -> p.Result[tuple[m.Infra.WorkspaceSpec, tuple[m.Infra.RepositoryRef, ...]]]:
        """Resolve initializer participants through the existing topology owner.

        Returns:
            The workspace and its selected repositories, or the original failure.

        """
        result_type = r[tuple[m.Infra.WorkspaceSpec, tuple[m.Infra.RepositoryRef, ...]]]
        topology = self._planning_workspace(request, root, inputs=inputs)
        if topology.failure:
            return result_type.from_failure(topology)
        workspace, _target, repository = topology.value
        selected = self._select_repositories(request, workspace, repository)
        return selected.map(lambda repositories: (workspace, repositories))

    def _planning_workspace(
        self,
        request: p.Infra.CodegenGenerateRequest,
        root: Path,
        *,
        inputs: m.Infra.CodegenInputs,
    ) -> p.Result[
        tuple[
            m.Infra.WorkspaceSpec,
            m.Infra.RepositoryConformTarget,
            m.Infra.RepositoryRef,
        ]
    ]:
        """Load the planning workspace and its current conformance target.

        Returns:
            The resulting ``p.Result[tuple[m.Infra.WorkspaceSpec,
                m.Infra.RepositoryConformTarget, m.Infra.RepositoryRef]]``.

        """
        result_type = r[
            tuple[
                m.Infra.WorkspaceSpec,
                m.Infra.RepositoryConformTarget,
                m.Infra.RepositoryRef,
            ]
        ]
        workspace = self.state.initial_workspace
        if workspace is None:
            workspace_result = (
                workspace_services.FlextInfraWorkspaceDetector.load_workspace_spec(
                    root,
                    inputs=inputs,
                    allow_unprovisioned_members=(
                        request.what in c.Infra.ALLOW_UNPROVISIONED_SURFACES
                    ),
                )
            )
            if workspace_result.failure:
                return result_type.from_failure(workspace_result)
            workspace = workspace_result.value
        current_repository = workspace.repository
        if (
            self.state.initial_workspace is None
            and request.what not in c.Infra.DECLARED_TARGET_SURFACES
        ):
            current_target_result = (
                workspace_services.FlextInfraWorkspaceDetector.conform_target(
                    root,
                    workspace,
                    inputs=inputs,
                )
            )
            if current_target_result.failure:
                return result_type.from_failure(current_target_result)
            current_target = current_target_result.value
            current_repository = current_target.repository
        else:
            current_target = m.Infra.RepositoryConformTarget(
                repository=current_repository,
                root=root,
                toolchain_root=self.state.repository_root,
                make_profile=current_repository.role,
                beads=workspace.beads,
                project=workspace.project,
                canonical_project_name=current_repository.distribution,
                ci_enabled=inputs.spec.repository.ci_enabled,
                publishes_release=current_repository.publishes_release,
                gascity_enabled=workspace.gascity_enabled,
                external_dependency_paths=workspace.external_dependency_paths,
            )
        return result_type.ok((workspace, current_target, current_repository))

    @staticmethod
    def _planning_report_evidence(
        root: Path,
        outcomes: Sequence[m.Infra.CodegenRepositoryPlanOutcome],
        repository_paths: Mapping[str, Path],
    ) -> p.Result[m.Infra.CodegenPlanningReport]:
        """Project original planning outcomes into payload-free publication evidence.

        Returns:
            Candidate and target evidence, or the original Git identity failure.

        """
        evidence: list[m.Infra.CodegenPlanningRepositoryEvidence] = []
        for outcome in outcomes:
            project_root = repository_paths[outcome.repository].resolve()
            probe = u.Infra.git_is_inside_work_tree(
                m.Infra.GitRepoRequest(repo_root=project_root),
                search_parent_directories=False,
            )
            if probe.failure:
                return r[m.Infra.CodegenPlanningReport].from_failure(probe)
            candidate_sha: str | None = None
            candidate_dirty: bool | None = None
            candidate_kind: Literal["git", "unversioned"] = "unversioned"
            # A scaffold does not inherit its containing checkout's identity.
            # Existing Git metadata must still expose its original identity failure.
            if probe.value.value or (project_root / c.GIT_DIR_NAME).exists():
                identity = u.Infra.git_identity(
                    m.Infra.GitRepoRequest(repo_root=project_root),
                )
                if identity.failure:
                    return r[m.Infra.CodegenPlanningReport].from_failure(identity)
                if identity.value.repo_root.resolve() == project_root:
                    candidate_kind = "git"
                    candidate_sha = identity.value.head_oid
                    candidate_dirty = identity.value.dirty
            evidence.append(
                m.Infra.CodegenPlanningRepositoryEvidence(
                    repository=outcome.repository,
                    root=project_root,
                    candidate_kind=candidate_kind,
                    candidate_sha=candidate_sha,
                    candidate_dirty=candidate_dirty,
                    files=tuple(
                        m.Infra.CodegenPlanningFileEvidence(
                            path=file.path,
                            desired_digest=(
                                None
                                if file.desired_content is None
                                else (
                                    f"sha256:{u.Cli.sha256_bytes(file.desired_content)}"
                                )
                            ),
                            desired_mode=file.desired_mode,
                            owner=file.owner,
                            policy=file.policy,
                        )
                        for file in outcome.files
                    ),
                    issues=outcome.issues,
                    error=outcome.error
                    or (
                        str(outcome.exception) if outcome.exception is not None else ""
                    ),
                    error_type=outcome.error_type
                    or (
                        f"{type(outcome.exception).__module__}."
                        f"{type(outcome.exception).__qualname__}"
                        if outcome.exception is not None
                        else ""
                    ),
                    error_traceback=outcome.error_traceback,
                    elapsed=outcome.elapsed,
                ),
            )
        return r[m.Infra.CodegenPlanningReport].ok(
            m.Infra.CodegenPlanningReport(root=root, outcomes=tuple(evidence)),
        )

    def _repository_plan_outcomes(
        self,
        tasks: Sequence[m.Infra.CodegenRepositoryPlanTask],
        surface: c.Infra.CodegenConformSurface,
        inputs: m.Infra.CodegenInputs,
        snapshots: Mapping[str, p.Infra.WorkspaceSnapshot],
    ) -> tuple[m.Infra.CodegenRepositoryPlanOutcome, ...]:
        """Plan the read-only cohort before any serial evidence publication.

        Returns:
            Ordered outcomes retaining original failures and desired native metadata.

        """
        contract = self.surface_contract(surface, codegen=inputs.spec)
        selected_pyproject = contract.pyproject and (
            contract.destinations is None
            or c.PYPROJECT_FILENAME in contract.destinations
        )
        outcomes = (
            self._governed_plan_outcomes(
                tasks, snapshots, selected_pyproject=selected_pyproject
            )
            if contract.complete_governed and tasks
            else tuple(
                type(self).plan_repository_task(task, snapshots[task.repository.name])
                for task in tasks
            )
        )
        self.retain_diagnostics(
            *(outcome.exception for outcome in outcomes),
            failure=next(
                (
                    outcome.native_failure
                    for outcome in outcomes
                    if outcome.native_failure is not None
                ),
                None,
            ),
        )
        return outcomes

    @staticmethod
    def _failed_outcome(
        repository: str,
        exception: BaseException,
        elapsed: float = 0.0,
    ) -> m.Infra.CodegenRepositoryPlanOutcome:
        """Retain one native planning failure, with its traceback, as data.

        Returns:
            The failed outcome carrying the original cause.

        """
        traceback.print_exception(exception)
        return m.Infra.CodegenRepositoryPlanOutcome(
            repository=repository,
            native_failure=r.fail(str(exception), exception=exception),
            error=str(exception),
            error_type=f"{type(exception).__module__}.{type(exception).__qualname__}",
            error_traceback="".join(traceback.format_exception(exception)),
            exception=exception,
            elapsed=elapsed,
        )

    def _cohort_failure(
        self,
        failure: m.Infra.CodegenRepositoryPlanOutcome,
        outcomes: tuple[m.Infra.CodegenRepositoryPlanOutcome, ...],
    ) -> tuple[m.Infra.CodegenRepositoryPlanOutcome, ...]:
        """Record shared admission failure without relabeling completed targets.

        Returns:
            Original target outcomes, retaining the failure at its actual owner.

        """
        self.retain_diagnostics(
            failure.exception,
            failure=failure.native_failure,
            issues=(
                m.Infra.Issue(
                    file="",
                    line=0,
                    column=0,
                    code=c.Infra.ToolOutcome.ERROR.value,
                    message=(
                        failure.error_traceback
                        or failure.error
                        or "\n".join(issue.formatted for issue in failure.issues)
                        or "generation cohort admission failed"
                    ),
                ),
            ),
        )
        for outcome in outcomes:
            if not outcome.failed and outcome.repository == failure.repository:
                outcome.error = failure.error
                outcome.error_type = failure.error_type
                outcome.error_traceback = failure.error_traceback
                outcome.issues = failure.issues
                outcome.exception = failure.exception
                outcome.native_failure = failure.native_failure
        return outcomes

    def _governed_plan_outcomes(
        self,
        tasks: Sequence[m.Infra.CodegenRepositoryPlanTask],
        snapshots: Mapping[str, p.Infra.WorkspaceSnapshot],
        *,
        selected_pyproject: bool,
    ) -> tuple[m.Infra.CodegenRepositoryPlanOutcome, ...]:
        """Plan lazy providers, then managed surfaces in dependency order.

        One process loops over the repositories: every lazy plan first, then
        root metadata fixes the runtime dependency order, and each managed
        plan reads the plans staged by the repositories before it. A
        cohort-wide failure fails every planned repository and keeps no
        provider.

        Returns:
            The ordered outcomes.

        """
        plan = type(self).plan_repository_task
        lazy = tuple(
            plan(
                task.model_copy(
                    update={"surface": c.Infra.CodegenConformSurface.LAZY_INIT}
                ),
                snapshots[task.repository.name],
            )
            for task in tasks
        )
        self.retain_diagnostics(
            *(outcome.exception for outcome in lazy),
            failure=next(
                (
                    outcome.native_failure
                    for outcome in lazy
                    if outcome.native_failure is not None
                ),
                None,
            ),
        )
        providers = tuple(
            file
            for outcome in lazy
            if self._plannable_outcome(outcome)
            for file in outcome.files
        )
        ready = {
            task.repository.distribution: task
            for task, outcome in zip(tasks, lazy, strict=True)
            if self._plannable_outcome(outcome)
        }
        scaffold_tasks = tuple(
            task
            for task in ready.values()
            if selected_pyproject
            and task.initial_workspace is not None
            and task.repository.name == task.initial_workspace.repository.name
        )
        metadata_files: tuple[m.Infra.CodegenFilePlan, ...] = ()
        if scaffold_tasks:
            metadata = tuple(
                plan(
                    task.model_copy(
                        update={
                            "surface": c.Infra.CodegenConformSurface.PYPROJECT,
                            "provider_plans": providers,
                        },
                    ),
                    snapshots[task.repository.name],
                )
                for task in scaffold_tasks
            )
            failed = next((item for item in metadata if item.failed), None)
            if failed is not None:
                self.retain_diagnostics(failed.exception, failure=failed.native_failure)
                return self._cohort_failure(failed, lazy)
            metadata_files = tuple(file for item in metadata for file in item.files)
        try:
            manifests, _dependencies, waves = self._planned_dependency_waves(
                tasks, scaffold_tasks, metadata_files
            )
        except (OSError, ValueError, TypeError) as exc:
            failure = self._failed_outcome(tasks[0].repository.name, exc)
            return self._cohort_failure(failure, lazy)
        planned = self._managed_plan_outcomes(
            tuple(
                tuple(ready[name] for name in wave if name in ready) for wave in waves
            ),
            providers,
            snapshots,
            failed={
                u.Infra.dep_name(task.repository.distribution): outcome
                for task, outcome in zip(tasks, lazy, strict=True)
                if outcome.failed
            },
        )
        outcomes = tuple(
            self._merged_repository_outcome(outcome, planned[outcome.repository])
            if outcome.repository in planned
            else outcome
            for outcome in lazy
        )
        try:
            for manifest in manifests:
                self._verify_root_manifest(manifest, outcomes, tasks)
        except (OSError, ValueError, TypeError, RuntimeError) as exc:
            failure = self._failed_outcome(tasks[0].repository.name, exc)
            return self._cohort_failure(failure, outcomes)
        return outcomes

    @staticmethod
    def _plannable_outcome(
        outcome: m.Infra.CodegenRepositoryPlanOutcome,
    ) -> bool:
        """Retain scoped candidates, never preflight failures.

        Returns:
            Whether completed candidates remain available for further planning.

        """
        return not outcome.failed

    @classmethod
    def _merged_repository_outcome(
        cls,
        lazy: m.Infra.CodegenRepositoryPlanOutcome,
        managed: m.Infra.CodegenRepositoryPlanOutcome,
    ) -> m.Infra.CodegenRepositoryPlanOutcome:
        """Compose ordered projections without losing original failures.

        Managed planning may rederive an initializer after facade projection.
        Its final desired bytes supersede the lazy candidate only for the same
        physical original and owner.

        Returns:
            Every final candidate and the original failures in execution order.

        Raises:
            ValueError: If phases disagree about a destination's original owner.

        """
        if lazy.repository != managed.repository:
            msg = "repository planning phases have different owners"
            raise ValueError(msg)
        files = u.Infra.codegen_compose_file_plans(
            (
                *(lazy.files if cls._plannable_outcome(managed) else ()),
                *managed.files,
            ),
            ordered=True,
        )
        native = lazy.native_failure
        if native is None:
            native = managed.native_failure
        managed.files = files
        managed.issues = (*lazy.issues, *managed.issues)
        managed.native_failure = native
        managed.exception = (
            native.exception
            if native is not None
            else lazy.exception
            if lazy.exception is not None
            else managed.exception
        )
        managed.error = "\n".join(
            value for value in (lazy.error, managed.error) if value
        )
        if native is not None:
            managed.error_type = (
                f"{type(native.exception).__module__}.{type(native.exception).__qualname__}"
                if native.exception is not None
                else ""
            )
            managed.error_traceback = (
                "".join(traceback.format_exception(native.exception))
                if native.exception is not None
                else ""
            )
        else:
            managed.error_type = lazy.error_type or managed.error_type
            managed.error_traceback = "\n".join(
                value
                for value in (lazy.error_traceback, managed.error_traceback)
                if value
            )
        managed.elapsed += lazy.elapsed
        return managed

    @staticmethod
    def _planned_dependency_waves(
        tasks: Sequence[m.Infra.CodegenRepositoryPlanTask],
        scaffold_tasks: Sequence[m.Infra.CodegenRepositoryPlanTask],
        metadata_files: tuple[m.Infra.CodegenFilePlan, ...],
    ) -> tuple[
        tuple[m.Infra.CodegenFilePlan, ...],
        Mapping[str, tuple[str, ...]],
        Sequence[Sequence[str]],
    ]:
        """Select each declared scaffold manifest and derive dependency waves.

        Returns:
            The single owned manifest per scaffold, and the shared waves.

        Raises:
            ValueError: If a scaffold has no single owned pyproject plan.

        """
        manifests: list[m.Infra.CodegenFilePlan] = []
        for task in scaffold_tasks:
            project = (task.root / task.repository.path).resolve()
            selected = tuple(
                file
                for file in metadata_files
                if file.project.resolve() == project
                and file.path.resolve() == project / c.PYPROJECT_FILENAME
                and file.desired_content is not None
            )
            if len(selected) != 1:
                msg = f"scaffold requires exactly one owned pyproject plan: {project}"
                raise ValueError(msg)
            manifests.extend(selected)
        graph = u.Infra.workspace_dependency_graph(
            tasks[0].root,
            tuple(task.repository for task in tasks),
            planned_manifests=tuple(manifests),
        )
        waves = u.Cli.dag_waves(graph)
        if waves.failure:
            raise ValueError(waves.error)
        distributions = {
            u.Infra.dep_name(task.repository.distribution): task.repository.distribution
            for task in tasks
        }
        return (
            tuple(manifests),
            graph,
            tuple(tuple(distributions[name] for name in wave) for wave in waves.value),
        )

    def _managed_plan_outcomes(
        self,
        waves: Sequence[tuple[m.Infra.CodegenRepositoryPlanTask, ...]],
        providers: tuple[m.Infra.CodegenFilePlan, ...],
        snapshots: Mapping[str, p.Infra.WorkspaceSnapshot],
        *,
        failed: MutableMapping[str, m.Infra.CodegenRepositoryPlanOutcome],
    ) -> Mapping[str, m.Infra.CodegenRepositoryPlanOutcome]:
        """Plan managed surfaces in dependency order over the staged plans.

        Each repository plans in the one loop over the plans staged by the
        repositories before it. A failed repository withdraws its own lazy
        providers. Only authenticated complete source output survives an
        unrelated managed failure, never incoming lazy inputs. A failed
        dependency never short-circuits a dependent's own planning: the
        dependent still corrects everything its reduced staged set supports
        and records its own outcome; the check gates judge the result.

        Returns:
            The managed outcome per repository.

        """
        planned: MutableMapping[str, m.Infra.CodegenRepositoryPlanOutcome] = {}
        staged = {file.path: file for file in providers}
        for wave in waves:
            for task in wave:
                distribution = u.Infra.dep_name(task.repository.distribution)
                outcome = type(self).plan_repository_task(
                    task.model_copy(update={"provider_plans": tuple(staged.values())}),
                    snapshots[task.repository.name],
                )
                self.retain_diagnostics(
                    outcome.exception, failure=outcome.native_failure
                )
                if outcome.failed:
                    failed[distribution] = outcome
                files = outcome.files
                if outcome.failed and not self._plannable_outcome(outcome):
                    project_root = (task.root / task.repository.path).resolve()
                    staged = {
                        path: file
                        for path, file in staged.items()
                        if file.project != project_root
                    }
                    files = ()
                staged.update((file.path, file) for file in files)
                planned[outcome.repository] = outcome
        return planned

    @staticmethod
    def _verify_root_manifest(
        manifest: m.Infra.CodegenFilePlan,
        outcomes: tuple[m.Infra.CodegenRepositoryPlanOutcome, ...],
        tasks: Sequence[m.Infra.CodegenRepositoryPlanTask],
    ) -> None:
        """Prove the planned root manifest kept one payload and a stable graph.

        Raises:
            ValueError: When the final root metadata lost its single payload or
                its internal dependency edges changed after metadata planning.

        """
        repository = next(
            task.repository.name
            for task in tasks
            if (task.root / task.repository.path).resolve()
            == manifest.project.resolve()
        )
        final = next(item for item in outcomes if item.repository == repository)
        if final.failed:
            return
        selected = tuple(file for file in final.files if file.path == manifest.path)
        if len(selected) != 1 or selected[0].desired_content is None:
            msg = "final root metadata has no single pyproject payload"
            raise ValueError(msg)
        names = {u.Infra.dep_name(task.repository.distribution) for task in tasks}
        edges: set[frozenset[str]] = set()
        for file in (manifest, selected[0]):
            if file.desired_content is None:
                msg = "root dependency manifest has no payload"
                raise ValueError(msg)
            payload = u.Cli.toml_mapping_from_text(
                file.desired_content.decode(c.DEFAULT_ENCODING),
            )
            if payload is None:
                msg = "invalid root dependency manifest"
                raise ValueError(msg)
            edges.add(
                frozenset(
                    name
                    for name in u.Infra.project_dependency_names_from_payload(payload)
                    if name in names
                ),
            )
        if len(edges) != 1:
            msg = "root dependency graph changed after metadata planning"
            raise ValueError(msg)

    def _blocked_control_outcomes(
        self,
        root: Path,
        tasks: Sequence[m.Infra.CodegenRepositoryPlanTask],
    ) -> Mapping[str, m.Infra.CodegenRepositoryPlanOutcome]:
        """Close failed controls before any target Python source is opened."""
        controlled = {
            outcome.repository: outcome
            for outcome in self.state.control_outcomes
            if outcome.failed
        }
        failures = {
            u.Infra.dep_name(task.repository.distribution): controlled[
                task.repository.name
            ]
            for task in tasks
            if task.repository.name in controlled
        }
        if not failures:
            return {}
        for failure in failures.values():
            if failure.native_failure is None:
                failure.native_failure = r.fail(
                    failure.error
                    or "\n".join(issue.formatted for issue in failure.issues),
                    exception=failure.exception,
                )
            self.retain_diagnostics(failure.exception, failure=failure.native_failure)
        graph = r[Mapping[str, tuple[str, ...]]].create_from_callable(
            lambda: u.Infra.workspace_dependency_graph(
                root, tuple(task.repository for task in tasks)
            )
        )
        blocked: dict[str, m.Infra.CodegenRepositoryPlanOutcome] = {}
        if graph.success:
            dependents = {
                name: tuple(
                    consumer
                    for consumer, dependencies in graph.value.items()
                    if name in dependencies
                )
                for name in graph.value
            }
            for name, failure in failures.items():
                affected = u.Cli.dag_closure(dependents, frozenset((name,)))
                if affected.failure:
                    graph = r[Mapping[str, tuple[str, ...]]].from_failure(affected)
                    break
                for dependent in affected.value:
                    blocked.setdefault(dependent, failure)
        if graph.failure:
            self.retain_diagnostics(
                graph.exception,
                failure=graph,
                issues=(
                    m.Infra.Issue(
                        file=str(root),
                        line=0,
                        column=0,
                        code=c.Infra.ToolOutcome.ERROR.value,
                        message=graph.error or "source dependency inventory failed",
                    ),
                ),
            )
            first = next(iter(failures.values()))
            blocked = {
                u.Infra.dep_name(task.repository.distribution): first for task in tasks
            }
        outcomes: dict[str, m.Infra.CodegenRepositoryPlanOutcome] = {}
        for task in tasks:
            cause = blocked.get(u.Infra.dep_name(task.repository.distribution))
            if cause is None:
                continue
            detail = cause.error
            if not detail and cause.native_failure is not None:
                detail = (
                    cause.native_failure.error
                    or cause.native_failure.error_code
                    or "control failed"
                )
            outcomes[task.repository.name] = m.Infra.CodegenRepositoryPlanOutcome(
                repository=task.repository.name,
                error=(
                    f"not planned: control prerequisite {cause.repository} failed: "
                    f"{detail or cause.exception}"
                ),
                native_failure=cause.native_failure,
                exception=cause.exception,
                error_type=cause.error_type,
                error_traceback=cause.error_traceback,
            )
        return outcomes

    def _gathered_repository_plans(
        self,
        root: Path,
        planning: tuple[
            m.Infra.WorkspaceSpec,
            m.Infra.RepositoryConformTarget,
            m.Infra.RepositoryRef,
        ],
        selected: tuple[m.Infra.RepositoryRef, ...],
        surface: c.Infra.CodegenConformSurface,
        inputs: m.Infra.CodegenInputs,
    ) -> p.Result[
        tuple[
            list[m.Infra.CodegenFilePlan],
            list[m.Infra.UvEnvironmentPlan],
            list[m.Infra.Issue],
            tuple[m.Infra.CodegenRepositoryPlanOutcome, ...],
        ]
    ]:
        """Plan every selected repository and collect its governed file plans.

        Args:
            root: Resolved repository root of the request.
            planning: The loaded workspace, its conform target and current
                repository reference.
            selected: Repository references selected for planning.
            surface: Conform surface being planned.
            inputs: Loaded codegen inputs of the request root.

        Returns:
            The resulting ``p.Result[tuple[list[m.Infra.CodegenFilePlan],
                list[m.Infra.UvEnvironmentPlan]]]``.

        """
        current_target = planning[1]
        result_type = r[
            tuple[
                list[m.Infra.CodegenFilePlan],
                list[m.Infra.UvEnvironmentPlan],
                list[m.Infra.Issue],
                tuple[m.Infra.CodegenRepositoryPlanOutcome, ...],
            ]
        ]
        u.Cli.info(f"stage=plan repositories={len(selected)}")
        tasks: list[m.Infra.CodegenRepositoryPlanTask] = []
        for repository in selected:
            if repository.kind is not c.Infra.ProjectKind.INTERNAL_FLEXT:
                u.Cli.info(
                    f"  stage=skip repository={repository.name} "
                    f"kind={repository.kind.value} is not rewritten by generation",
                )
                continue
            initial_workspace = self.state.initial_workspace
            selected_inputs = (
                inputs if repository.name == current_target.repository.name else None
            )
            project_root = (root / repository.path).resolve()
            if (
                surface is c.Infra.CodegenConformSurface.ALL
                and not (project_root / c.PYPROJECT_FILENAME).exists()
                and repository.name != current_target.repository.name
            ):
                captured = u.Infra.load_codegen_inputs(project_root)
                local = (
                    r[m.Infra.WorkspaceSpec].from_failure(captured)
                    if captured.failure
                    else self._member_local_workspace(
                        planning[0], repository, project_root, inputs=captured.value
                    )
                )
                if local.failure:
                    return result_type.from_failure(local)
                selected_inputs = captured.value
                initial_workspace = local.value
            tasks.append(
                m.Infra.CodegenRepositoryPlanTask(
                    ports=self.state.ports,
                    root=root,
                    workspace=planning[0],
                    initial_workspace=initial_workspace,
                    current_target=current_target,
                    repository=repository,
                    surface=surface,
                    selected_inputs=selected_inputs,
                ),
            )
        # Each repository retains its own native election through the lazy
        # provider and managed passes. Inventory membership identifies nested
        # checkouts without merging their internal package names into one engine.
        roots = {
            task.repository.name: (root / task.repository.path).resolve()
            for task in tasks
        }
        blocked = self._blocked_control_outcomes(root, tasks)
        eligible = tuple(task for task in tasks if task.repository.name not in blocked)
        with ExitStack() as stack:
            snapshots = {
                name: stack.enter_context(
                    u.Infra.workspace_snapshot(
                        project_root,
                        tuple(
                            member
                            for member in roots.values()
                            if member.is_relative_to(project_root)
                        ),
                    )
                )
                for name, project_root in roots.items()
                if name not in blocked
            }
            planned = self._repository_plan_outcomes(
                eligible, surface, inputs, snapshots
            )
            observed = {outcome.repository: outcome for outcome in planned}
            outcomes = tuple(
                blocked[task.repository.name]
                if task.repository.name in blocked
                else observed[task.repository.name]
                for task in tasks
            )
            for name, snapshot in snapshots.items():
                verified = u.Infra.workspace_snapshot_verify(
                    snapshot, tuple(snapshot.sources)
                )
                if verified.failure:
                    self.retain_diagnostics(verified.exception, failure=verified)
                    outcome = next(item for item in outcomes if item.repository == name)
                    outcome.error = "\n".join(
                        value
                        for value in (
                            outcome.error,
                            verified.error or "source observation changed",
                        )
                        if value
                    )
                    if outcome.native_failure is None:
                        outcome.native_failure = verified
                    outcome.exception = outcome.native_failure.exception
        return self._reported_repository_plans(root, selected, outcomes)

    def _reported_repository_plans(
        self,
        root: Path,
        selected: tuple[m.Infra.RepositoryRef, ...],
        outcomes: tuple[m.Infra.CodegenRepositoryPlanOutcome, ...],
    ) -> p.Result[
        tuple[
            list[m.Infra.CodegenFilePlan],
            list[m.Infra.UvEnvironmentPlan],
            list[m.Infra.Issue],
            tuple[m.Infra.CodegenRepositoryPlanOutcome, ...],
        ]
    ]:
        """Publish planning evidence and collect the same observed outcomes.

        Returns:
            Planned files, environments and issues, or the evidence failure.

        """
        result_type = r[
            tuple[
                list[m.Infra.CodegenFilePlan],
                list[m.Infra.UvEnvironmentPlan],
                list[m.Infra.Issue],
                tuple[m.Infra.CodegenRepositoryPlanOutcome, ...],
            ]
        ]
        repository_paths = {
            repository.name: root / repository.path for repository in selected
        }
        evidence = self._planning_report_evidence(root, outcomes, repository_paths)
        published = (
            evidence
            if evidence.failure
            else u.Infra.publish_refactor_report_evidence(
                root,
                evidence.value,
                relative_path=c.Infra.CODEGEN_PLAN_REPORT_RELATIVE_PATH,
            )
        )
        if published.failure:
            return result_type.from_failure(published)
        files: list[m.Infra.CodegenFilePlan] = []
        environments: list[m.Infra.UvEnvironmentPlan] = []
        issues: list[m.Infra.Issue] = list(self.state.planning_issues)
        for index, outcome in enumerate(outcomes, start=1):
            issues.extend(outcome.issues)
            files.extend(outcome.files)
            self.retain_diagnostics(outcome.exception, failure=outcome.native_failure)
            u.Cli.progress(index, len(outcomes), outcome.repository, "plan")
            if (
                outcome.error
                or outcome.error_type
                or outcome.error_traceback
                or outcome.exception is not None
            ):
                u.Cli.status(
                    "plan",
                    outcome.repository,
                    result=False,
                    elapsed=outcome.elapsed,
                )
                u.Cli.error(
                    f"{outcome.repository}: {outcome.error_type}: "
                    f"{outcome.error or outcome.exception}",
                )
                issues.append(
                    m.Infra.Issue(
                        file=str(repository_paths[outcome.repository]),
                        line=0,
                        column=0,
                        code=c.Infra.ToolOutcome.ERROR.value,
                        message=outcome.error_traceback
                        or outcome.error
                        or str(outcome.exception),
                    ),
                )
                continue
            if outcome.environment is not None:
                environments.append(outcome.environment)
            for issue in outcome.issues:
                u.Cli.error(issue.formatted)
            u.Cli.status(
                "plan",
                outcome.repository,
                result=not outcome.failed,
                elapsed=outcome.elapsed,
            )
        return result_type.ok((files, environments, issues, outcomes))

    @classmethod
    def plan_repository_task(
        cls,
        task: m.Infra.CodegenRepositoryPlanTask,
        snapshot: p.Infra.WorkspaceSnapshot,
    ) -> m.Infra.CodegenRepositoryPlanOutcome:
        """Preserve a planning failure as data without retry or publication.

        Returns:
            The outcome of the repository planning task, including any failure
            information.

        """
        started = time.monotonic()
        u.Cli.info(
            f"stage=repository state=start repository={task.repository.name} "
            f"root={(task.root / task.repository.path).resolve()} "
            f"source_root={snapshot.engine.root.real_path} "
            f"surface={task.surface} role={task.repository.role.value}"
        )
        try:
            outcome = cls._plan_repository_task(task, snapshot)
        except Exception as exc:
            outcome = cls._failed_outcome(
                task.repository.name, exc, time.monotonic() - started
            )
        u.Cli.info(
            f"stage=repository state=end repository={task.repository.name} "
            f"surface={task.surface} elapsed={time.monotonic() - started:.3f}s "
            f"files={len(outcome.files)} failed={outcome.failed}"
        )
        return outcome

    @classmethod
    def _plan_repository_task(
        cls,
        task: m.Infra.CodegenRepositoryPlanTask,
        snapshot: p.Infra.WorkspaceSnapshot,
    ) -> m.Infra.CodegenRepositoryPlanOutcome:
        """Plan one repository from its task over the run's one snapshot.

        The repository planner is built from the task and reads the run's
        workspace snapshot; failures return as data instead of live results.

        Returns:
            The repository's file and environment plans, or its failure.

        """
        started = time.monotonic()
        repository = task.repository
        planner = cls(
            repository_root=task.current_target.toolchain_root,
            state=m.Infra.CodegenConformState(
                repository_root=task.current_target.toolchain_root,
                initial_workspace=task.initial_workspace,
                provider_plans=task.provider_plans,
                ports=task.ports,
                snapshot=snapshot,
            ),
        )
        resolved = planner._resolved_repository_root(
            task.root,
            task.workspace,
            task.current_target,
            repository,
        )
        if resolved.failure:
            return m.Infra.CodegenRepositoryPlanOutcome(
                repository=repository.name,
                native_failure=resolved,
                error=resolved.error or f"checkout root failed: {repository.name}",
                exception=resolved.exception,
                elapsed=time.monotonic() - started,
            )
        if task.surface is c.Infra.CodegenConformSurface.LAZY_INIT:
            planned = (
                r[Sequence[m.Infra.CodegenFilePlan]].ok(())
                if task.initial_workspace is not None
                and task.initial_workspace.project is not None
                and repository.name == task.initial_workspace.repository.name
                else planner._planned_lazy_init_files(resolved.value)
            )
            native = planner.state.planning_failure
            if native is None and planned.failure:
                native = planned
            return m.Infra.CodegenRepositoryPlanOutcome(
                repository=repository.name,
                native_failure=native,
                files=() if planned.failure else tuple(planned.value),
                error=(native.error or "" if native is not None else ""),
                exception=(
                    native.exception
                    if native is not None
                    else planner.state.planning_exception
                ),
                issues=tuple(planner.state.planning_issues),
                elapsed=time.monotonic() - started,
            )
        inputs = task.selected_inputs
        if inputs is None:
            loaded = u.Infra.load_codegen_inputs(resolved.value)
            if loaded.failure:
                return m.Infra.CodegenRepositoryPlanOutcome(
                    repository=repository.name,
                    native_failure=loaded,
                    error=loaded.error or f"configuration failed: {repository.name}",
                    exception=loaded.exception,
                    elapsed=time.monotonic() - started,
                )
            inputs = loaded.value
        planned_inputs = planner._repository_planning_inputs(
            resolved.value,
            task.workspace,
            task.current_target,
            repository,
            inputs=inputs,
        )
        if planned_inputs.failure:
            return m.Infra.CodegenRepositoryPlanOutcome(
                repository=repository.name,
                native_failure=planned_inputs,
                error=(
                    planned_inputs.error or f"planning inputs failed: {repository.name}"
                ),
                exception=planned_inputs.exception,
                elapsed=time.monotonic() - started,
            )
        repository_root, target, local_workspace = planned_inputs.value
        target = target.model_copy(
            update={
                "vscode_spec": inputs.spec.vscode,
                "vscode_sources": inputs.sources,
            },
        )
        try:
            with planner.shared_source_views():
                planned = planner._governed_repository_plans(
                    target,
                    local_workspace,
                    planner.surface_contract(
                        c.Infra.CodegenConformSurface(task.surface),
                        codegen=inputs.spec,
                    ),
                    inputs,
                    scaffold=(
                        task.initial_workspace is not None
                        and task.initial_workspace.project is not None
                        and repository.name == task.initial_workspace.repository.name
                    ),
                )
                if planned.failure:
                    planner.retain_diagnostics(planned.exception, failure=planned)
        except (OSError, ValueError, TypeError, RuntimeError) as exc:
            caught = cls._failed_outcome(
                repository.name, exc, time.monotonic() - started
            )
            native = planner.state.planning_failure
            caught.issues = tuple(planner.state.planning_issues)
            if native is not None:
                caught.issues += (
                    m.Infra.Issue(
                        file=str(repository_root),
                        line=0,
                        column=0,
                        code=c.Infra.ToolOutcome.ERROR.value,
                        message=caught.error_traceback or caught.error,
                    ),
                )
                caught.native_failure = native
                caught.exception = native.exception
                caught.error = native.error or ""
                caught.error_type = (
                    f"{type(native.exception).__module__}.{type(native.exception).__qualname__}"
                    if native.exception is not None
                    else ""
                )
                caught.error_traceback = (
                    "".join(traceback.format_exception(native.exception))
                    if native.exception is not None
                    else ""
                )
            return caught
        if planned.failure:
            native = (
                planner.state.planning_failure
                if planner.state.planning_failure is not None
                else planned
            )
            planning_failure = native.exception
            if planning_failure is not None:
                traceback.print_exception(planning_failure)
            outcome = m.Infra.CodegenRepositoryPlanOutcome(
                repository=repository.name,
                files=tuple(
                    file
                    for file in planner.state.completed_source_plans or ()
                    if file.project == repository_root
                ),
                error=native.error or "",
                native_failure=native,
                exception=planning_failure,
                error_type=(
                    f"{type(planning_failure).__module__}."
                    f"{type(planning_failure).__qualname__}"
                    if planning_failure is not None
                    else ""
                ),
                error_traceback=(
                    "".join(traceback.format_exception(planning_failure))
                    if planning_failure is not None
                    else ""
                ),
                issues=tuple(planner.state.planning_issues),
                elapsed=time.monotonic() - started,
            )
        else:
            governed_plans, retired_plans = planned.value
            planning_failure = planner.state.planning_exception
            outcome = m.Infra.CodegenRepositoryPlanOutcome(
                repository=repository.name,
                files=(*governed_plans, *retired_plans),
                environment=planner.uv_environment_plan(
                    root=repository_root,
                    target=target,
                    workspace=local_workspace,
                    config=inputs.spec,
                ),
                elapsed=time.monotonic() - started,
                issues=tuple(planner.state.planning_issues),
                exception=planner.state.planning_exception,
                native_failure=planner.state.planning_failure,
                error=str(planning_failure) if planning_failure is not None else "",
                error_traceback=(
                    "".join(traceback.format_exception(planning_failure))
                    if planning_failure is not None
                    else ""
                ),
            )
        return outcome

    def _repository_planning_inputs(
        self,
        repository_root: Path,
        workspace: m.Infra.WorkspaceSpec,
        current_target: m.Infra.RepositoryConformTarget,
        repository: m.Infra.RepositoryRef,
        *,
        inputs: m.Infra.CodegenInputs,
    ) -> p.Result[
        tuple[
            Path,
            m.Infra.RepositoryConformTarget,
            m.Infra.WorkspaceSpec,
        ]
    ]:
        """Resolve one repository's checkout root, target, and local workspace.

        Returns:
            The resulting ``p.Result[tuple[Path,
                m.Infra.RepositoryConformTarget, m.Infra.WorkspaceSpec]]``.

        """
        result_type = r[
            tuple[
                Path,
                m.Infra.RepositoryConformTarget,
                m.Infra.WorkspaceSpec,
            ]
        ]
        is_current_repository = repository.name == current_target.repository.name
        if is_current_repository:
            return result_type.ok(
                (repository_root, current_target, workspace),
            )
        local = self._member_local_workspace(
            workspace,
            repository,
            repository_root,
            inputs=inputs,
        )
        if local.failure:
            return result_type.from_failure(local)
        local_workspace = local.value
        target_result = workspace_services.FlextInfraWorkspaceDetector.conform_target(
            repository_root,
            local_workspace,
            inputs=inputs,
        )
        if target_result.failure:
            return result_type.from_failure(target_result)
        target = target_result.value.model_copy(
            update={"toolchain_root": current_target.toolchain_root},
        )
        if repository.path != Path():
            target = target.model_copy(update={"repository": repository})
        return result_type.ok((repository_root, target, local_workspace))

    def _resolved_repository_root(
        self,
        root: Path,
        workspace: m.Infra.WorkspaceSpec,
        current_target: m.Infra.RepositoryConformTarget,
        repository: m.Infra.RepositoryRef,
    ) -> p.Result[Path]:
        """Resolve and authenticate one repository's checkout root.

        Returns:
            The resulting ``p.Result[Path]``.

        """
        result_type = r[Path]
        is_current_repository = repository.name == current_target.repository.name
        if is_current_repository:
            repository_root = current_target.root
            if repository_root != root:
                return result_type.fail(
                    "current conformance target differs from the requested root: "
                    f"{repository_root} != {root}",
                )
            return result_type.ok(repository_root)
        # The governing root is the requested checkout, never the
        # previous iteration's member: resolving the second declared
        # repository against the first produced <root>/alpha/beta.
        repository_root_result = self._repository_root(root, workspace, repository)
        if repository_root_result.failure:
            return result_type.from_failure(repository_root_result)
        repository_root = repository_root_result.value
        if repository_root.exists() and not repository_root.is_dir():
            return result_type.fail(
                f"declared repository path is not a directory: {repository_root}",
            )
        if not repository_root.is_dir() and self.state.initial_workspace is None:
            return result_type.fail(
                f"declared repository checkout is missing: {repository_root}",
            )
        return result_type.ok(repository_root)

    @staticmethod
    def _member_local_workspace(
        workspace: m.Infra.WorkspaceSpec,
        repository: m.Infra.RepositoryRef,
        repository_root: Path,
        *,
        inputs: m.Infra.CodegenInputs,
    ) -> p.Result[m.Infra.WorkspaceSpec]:
        """Load the local workspace a declared member plans from.

        Returns:
            The resulting ``p.Result[m.Infra.WorkspaceSpec]``.

        """
        declared_member = (
            workspace_services.FlextInfraWorkspaceDetector.load_workspace_spec(
                repository_root,
                inputs=inputs,
            )
        )
        if declared_member.failure or repository.path == Path():
            return declared_member
        # The parent owns topology; the member owns its local project metadata.
        return r[m.Infra.WorkspaceSpec].ok(
            declared_member.value.model_copy(
                update={
                    "name": repository.name,
                    "repository": repository.model_copy(update={"path": Path()}),
                    "candidate_dependencies": workspace.candidate_dependencies,
                },
            ),
        )

    def _governed_repository_plans(
        self,
        target: m.Infra.RepositoryConformTarget,
        local_workspace: m.Infra.WorkspaceSpec,
        contract: m.Infra.CodegenConformSurfaceContract,
        inputs: m.Infra.CodegenInputs,
        *,
        scaffold: bool,
    ) -> p.Result[tuple[list[m.Infra.CodegenFilePlan], list[m.Infra.CodegenFilePlan]]]:
        """Plan governed files and retirements using the target's elected config.

        Args:
            target: Conform target of the repository being planned.
            local_workspace: The member's own local workspace specification.
            contract: Elected conform surface contract.
            inputs: Loaded codegen inputs of the repository.
            scaffold: Whether the repository is the declared workspace
                repository planning its initial scaffold.

        Returns:
            The resulting ``p.Result[tuple[list[m.Infra.CodegenFilePlan],
                list[m.Infra.CodegenFilePlan]]]``.

        """
        result_type = r[
            tuple[list[m.Infra.CodegenFilePlan], list[m.Infra.CodegenFilePlan]]
        ]
        config_spec = inputs.spec
        if scaffold:
            repository_plan = self._plan_scaffold_repository(
                target=target,
                workspace=local_workspace,
                codegen=config_spec,
                contract=contract,
            )
        else:
            repository_plan = self._plan_existing_repository(
                target=target,
                workspace=local_workspace,
                codegen=config_spec,
                contract=contract,
            )
        if repository_plan.failure:
            return result_type.from_failure(repository_plan)
        governed = self._complete_governed_plans(
            target,
            repository_plan.value,
            config_spec,
            contract,
        )
        if governed.failure:
            return result_type.from_failure(governed)
        governed_files = list(governed.value)
        retired_files: list[m.Infra.CodegenFilePlan] = []
        if contract.complete_governed:
            retired = self.retired_projection_plans(
                target.root,
                target.make_profile,
                inputs=inputs,
            )
            if retired.failure:
                return result_type.from_failure(retired)
            governed_paths = {item.path for item in governed.value}
            retired_files.extend(
                item for item in retired.value if item.path not in governed_paths
            )
        return result_type.ok((governed_files, retired_files))

    @staticmethod
    def _select_repositories(
        request: p.Infra.CodegenGenerateRequest,
        workspace: m.Infra.WorkspaceSpec,
        current_repository: m.Infra.RepositoryRef,
    ) -> p.Result[tuple[m.Infra.RepositoryRef, ...]]:
        """Resolve self/subprojects/all from the local read-only topology.

        Returns:
            The resulting ``p.Result[tuple[m.Infra.RepositoryRef, ...]]``.

        """
        scope = request.scope
        selected: tuple[m.Infra.RepositoryRef, ...]
        if scope is c.Infra.CodegenConformScope.SELF:
            selected = (current_repository,)
        elif scope is c.Infra.CodegenConformScope.DECLARED:
            if not workspace.subprojects:
                return r[tuple[m.Infra.RepositoryRef, ...]].fail(
                    "subprojects scope requires local .gitmodules entries",
                )
            selected = tuple(workspace.subprojects)
        else:
            selected = (workspace.repository, *workspace.subprojects)
        mutable = tuple(
            repository
            for repository in selected
            if repository.codegen is not c.Infra.CodegenKind.NONE
            and not repository.read_only
        )
        if not mutable:
            return r[tuple[m.Infra.RepositoryRef, ...]].fail(
                "selected repositories do not permit code generation",
            )
        return r[tuple[m.Infra.RepositoryRef, ...]].ok(mutable)

    @staticmethod
    def _repository_root(
        root: Path,
        workspace: p.Infra.WorkspaceSpec,
        repository: p.Infra.RepositoryRef,
    ) -> p.Result[Path]:
        """Resolve one declared checkout without escaping its workspace owner.

        Returns:
            The resulting ``p.Result[Path]``.

        """
        if repository.name == workspace.repository.name:
            return r[Path].ok(root)
        resolved_root = root.resolve()
        resolved: Path = (resolved_root / repository.path).resolve()
        if not resolved.is_relative_to(resolved_root):
            return r[Path].fail(
                "declared repository path escapes workspace root: "
                f"{repository.path.as_posix()}",
            )
        return r[Path].ok(resolved)


__all__: list[str] = ["FlextInfraCodegenConformPlan"]
