"""Conformance plan selection and repository topology resolution.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import operator
import time
from collections.abc import Mapping, MutableMapping, Sequence
from contextlib import ExitStack
from pathlib import Path
from typing import Literal, cast

from flext_infra import c, m, p, r, u, workspace as workspace_services
from flext_infra.codegen import FlextInfraCodegenLazyInit
from flext_infra.codegen._conform.scaffold_plan import (
    FlextInfraCodegenConformScaffoldPlan,
)


class FlextInfraCodegenConformPlan(FlextInfraCodegenConformScaffoldPlan):
    """Conformance planning across scaffold and existing repositories."""

    _planning_topology: (
        tuple[
            p.Infra.WorkspaceSpec,
            p.Infra.RepositoryConformTarget,
            p.Infra.RepositoryRef,
        ]
        | None
    ) = m.PrivateAttr(default=None)
    (
        "The invocation's authenticated topology, loaded once from Git and its "
        "declarations; every planning phase of this invocation reuses it."
    )

    def plan(
        self,
        request: p.Infra.CodegenGenerateRequest,
    ) -> p.Result[p.Infra.CodegenPlan]:
        """Build and validate the complete selection without writing.

        Returns:
            The resulting ``p.Result[p.Infra.CodegenPlan]``.

        """
        return self._plan_request(request)

    def _plan_request(
        self,
        request: p.Infra.CodegenGenerateRequest,
    ) -> p.Result[p.Infra.CodegenPlan]:
        """Plan the active invocation.

        Returns:
            The resulting ``p.Result[p.Infra.CodegenPlan]``.

        """
        inputs = u.Infra.load_codegen_inputs(request.root.expanduser().resolve())
        if inputs.failure:
            return r[p.Infra.CodegenPlan].from_failure(inputs)
        return self._plan_repositories(request, inputs.value)

    def _plan_single_surface(
        self,
        request: p.Infra.CodegenGenerateRequest,
        *,
        inputs: p.Infra.CodegenInputs | None = None,
    ) -> p.Result[p.Infra.CodegenPlan]:
        """Plan the declared facade or lazy-init surface of one repository.

        Returns:
            The surface plan, or its first planning failure.

        """
        if inputs is None:
            loaded = u.Infra.load_codegen_inputs(request.root.expanduser().resolve())
            if loaded.failure:
                return r[p.Infra.CodegenPlan].from_failure(loaded)
            inputs = loaded.value
        if request.what == c.Infra.CodegenConformSurface.FACADES:
            return self.plan_facade(request, inputs)
        return self._plan_lazy_init(request, inputs)

    def plan_repositories(
        self,
        request: p.Infra.CodegenGenerateRequest,
        inputs: p.Infra.CodegenInputs,
    ) -> p.Result[p.Infra.CodegenPlan]:
        """Dispatch the declared surface using its captured repository inputs.

        Returns:
            The complete repository plan or its first planning failure.

        """
        return self._plan_repositories(request, inputs)

    def _plan_repositories(
        self,
        request: p.Infra.CodegenGenerateRequest,
        inputs: p.Infra.CodegenInputs,
    ) -> p.Result[p.Infra.CodegenPlan]:
        """Compose repository phases within the active planning invocation.

        Returns:
            The resulting ``p.Result[p.Infra.CodegenPlan]``.

        """
        if request.what in c.Infra.FILE_ONLY_SURFACES:
            return self._plan_single_surface(request, inputs=inputs)
        root = request.root.expanduser().resolve()
        targets = self._planning_workspace(request, root, inputs=inputs)
        if targets.failure:
            return r[p.Infra.CodegenPlan].from_failure(targets)
        workspace, _current_target, current_repository = targets.value
        selected_result = self._select_repositories(
            request,
            workspace,
            current_repository,
        )
        if selected_result.failure:
            return r[p.Infra.CodegenPlan].from_failure(selected_result)
        selected = selected_result.value
        gathered = self._gathered_repository_plans(
            root,
            targets.value,
            selected,
            request.what,
            inputs,
        )
        if gathered.failure:
            return r[p.Infra.CodegenPlan].from_failure(gathered)
        files, environments, outcomes = gathered.value
        return r[p.Infra.CodegenPlan].ok(
            m.Infra.CodegenPlan(
                request=request,
                repositories=selected,
                workspace=workspace,
                uv_environments=tuple(environments),
                files=tuple(files),
                outcomes=outcomes,
            ),
        )

    def plan_facade(
        self,
        request: p.Infra.CodegenGenerateRequest,
        inputs: p.Infra.CodegenInputs,
    ) -> p.Result[p.Infra.CodegenPlan]:
        """Admit a destination and close its recursive family dependency cohort.

        The selected facade, native component moves, dependent initializers and
        consumer imports share the existing fixed point and publication owner.

        Args:
            request: The conform request containing the root and destination module.
            inputs: The effective codegen policy.

        Returns:
            The facade plan, or the first failure.

        """
        result_type = r[p.Infra.CodegenPlan]
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
            )
        )

    def _facade_file_plans(
        self,
        root: Path,
        module: str | None,
        codegen: p.Infra.CodegenConfigSpec,
        *,
        profile: str,
    ) -> p.Result[tuple[p.Infra.CodegenFilePlan, ...]]:
        """Authenticate one facade and use the existing source convergence owner.

        The current module elects the family; directory spelling never elects a
        namespace identity. The caller's snapshot authority is restored on exit.

        Returns:
            The dependency-complete selected cohort, or its planning failure.

        """
        result_type = r[tuple[p.Infra.CodegenFilePlan, ...]]
        previous_snapshot = self.state.snapshot
        with ExitStack() as source_scope, self.shared_source_views():
            snapshot = self.state.snapshot
            if snapshot is None:
                snapshot = source_scope.enter_context(
                    u.Infra.workspace_snapshot(root, (root,))
                )
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
                projected = self._projected_custom_sources(
                    root,
                    (codegen, profile),
                    cohort=cohort,
                    selection=(destination, c.Infra.FacadeFamily(family.value)),
                )
                if projected.success:
                    self._retain_source_facts(snapshot, root)
                return projected.map(operator.itemgetter(0))
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
        inputs: p.Infra.CodegenInputs,
    ) -> p.Result[p.Infra.CodegenPlan]:
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
        result_type = r[p.Infra.CodegenPlan]
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
                            u.Infra.workspace_snapshot(project, (project,))
                        )
                    )
                    project_inputs = (
                        r[p.Infra.CodegenInputs].ok(inputs)
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
                    projected = self._projected_custom_sources(
                        project,
                        (project_inputs.value.spec, participant.role.value),
                        cohort=tuple(files.values()),
                        selection=selection,
                    )
                    if projected.failure:
                        return result_type.from_failure(projected)
                    cast(MutableMapping[Path, object], files).update({
                        file.path: file for file in projected.value[0]
                    })
                    self._retain_source_facts(self.state.snapshot, project)
            finally:
                self.state.snapshot, self.state.provider_plans = previous
        return result_type.ok(
            m.Infra.CodegenPlan(
                request=request,
                repositories=repositories,
                workspace=workspace,
                uv_environments=(),
                files=tuple(files[path] for path in sorted(files)),
            )
        )

    def _lazy_init_repositories(
        self,
        request: p.Infra.CodegenGenerateRequest,
        root: Path,
        inputs: p.Infra.CodegenInputs,
    ) -> p.Result[tuple[p.Infra.WorkspaceSpec, tuple[p.Infra.RepositoryRef, ...]]]:
        """Resolve initializer participants through the existing topology owner.

        Returns:
            The workspace and its selected repositories, or the original failure.

        """
        result_type = r[tuple[p.Infra.WorkspaceSpec, tuple[p.Infra.RepositoryRef, ...]]]
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
        inputs: p.Infra.CodegenInputs,
    ) -> p.Result[
        tuple[
            p.Infra.WorkspaceSpec,
            p.Infra.RepositoryConformTarget,
            p.Infra.RepositoryRef,
        ]
    ]:
        """Load the planning workspace and its current conformance target.

        Returns:
            The resulting ``p.Result[tuple[p.Infra.WorkspaceSpec,
                m.Infra.RepositoryConformTarget, m.Infra.RepositoryRef]]``.

        """
        result_type = r[
            tuple[
                m.Infra.WorkspaceSpec,
                m.Infra.RepositoryConformTarget,
                m.Infra.RepositoryRef,
            ]
        ]
        cached = self._planning_topology
        if cached is not None:
            return result_type.ok(cached)
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
            current_target = current_target_result.value.model_copy(
                update={"toolchain_root": self.state.repository_root},
            )
            current_repository = current_target.repository
        else:
            rendered = (
                workspace_services.FlextInfraWorkspaceDetector.conform_repository(
                    root, current_repository
                )
            )
            if rendered.failure:
                return result_type.from_failure(rendered)
            current_target = m.Infra.RepositoryConformTarget.model_validate({
                "repository": rendered.value,
                "root": root,
                "toolchain_root": self.state.repository_root,
                "make_profile": current_repository.role,
                "beads": (
                    m.Infra.BeadsProjectSpec.model_validate(workspace.beads)
                    if workspace.beads is not None
                    else None
                ),
                "project": (
                    m.Infra.ProjectSpec.model_validate(workspace.project)
                    if workspace.project is not None
                    else None
                ),
                "canonical_project_name": current_repository.distribution,
                "ci_enabled": inputs.spec.repository.ci_enabled,
                "publishes_release": current_repository.publishes_release,
                "gascity_enabled": workspace.gascity_enabled,
                "external_dependency_paths": workspace.external_dependency_paths,
            })
        topology = (workspace, current_target, current_repository)
        self._planning_topology = topology
        return result_type.ok(topology)

    @staticmethod
    def _planning_report_evidence(
        root: Path,
        outcomes: Sequence[p.Infra.CodegenRepositoryPlanOutcome],
        repository_paths: Mapping[str, Path],
    ) -> p.Result[p.Infra.CodegenPlanningReport]:
        """Project original planning outcomes into payload-free publication evidence.

        Returns:
            Candidate and target evidence, or the original Git identity failure.

        """
        evidence: list[p.Infra.CodegenPlanningRepositoryEvidence] = []
        for outcome in outcomes:
            project_root = repository_paths[outcome.repository].resolve()
            probe = u.Infra.git_is_inside_work_tree(
                m.Infra.GitRepoRequest(repo_root=project_root),
                search_parent_directories=False,
            )
            if probe.failure:
                return r[p.Infra.CodegenPlanningReport].from_failure(probe)
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
                    return r[p.Infra.CodegenPlanningReport].from_failure(identity)
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
                    elapsed=outcome.elapsed,
                ),
            )
        return r[p.Infra.CodegenPlanningReport].ok(
            m.Infra.CodegenPlanningReport.model_validate({
                "root": (root),
                "outcomes": (tuple(evidence)),
            }),
        )

    def _repository_plan_outcomes(
        self,
        tasks: Sequence[p.Infra.CodegenRepositoryPlanTask],
        surface: c.Infra.CodegenConformSurface,
        inputs: p.Infra.CodegenInputs,
        snapshots: Mapping[str, p.Infra.WorkspaceSnapshot],
    ) -> tuple[p.Infra.CodegenRepositoryPlanOutcome, ...]:
        """Plan the read-only cohort before any serial evidence publication.

        Returns:
            Ordered outcomes with their desired native metadata.

        """
        contract = self.surface_contract(surface, codegen=inputs.spec)
        selected_pyproject = contract.pyproject and (
            contract.destinations is None
            or c.PYPROJECT_FILENAME in contract.destinations
        )
        if contract.complete_governed and tasks:
            return self._governed_plan_outcomes(
                tasks, snapshots, selected_pyproject=selected_pyproject
            )
        return tuple(
            type(self).plan_repository_task(task, snapshots[task.repository.name])
            for task in tasks
        )

    def _governed_plan_outcomes(
        self,
        tasks: Sequence[p.Infra.CodegenRepositoryPlanTask],
        snapshots: Mapping[str, p.Infra.WorkspaceSnapshot],
        *,
        selected_pyproject: bool,
    ) -> tuple[p.Infra.CodegenRepositoryPlanOutcome, ...]:
        """Plan lazy providers, then managed surfaces in dependency order.

        One process loops over the repositories: every lazy plan first, then
        root metadata fixes the runtime dependency order, and each managed
        plan reads the plans staged by the repositories before it. The first
        planning failure of any repository stops the cohort with its cause.

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
        providers = tuple(file for outcome in lazy for file in outcome.files)
        ready = {task.repository.distribution: task for task in tasks}
        scaffold_tasks = tuple(
            task
            for task in tasks
            if selected_pyproject
            and task.initial_workspace is not None
            and task.repository.name == task.initial_workspace.repository.name
        )
        metadata_files = tuple(
            file
            for task in scaffold_tasks
            for file in plan(
                task.model_copy(
                    update={
                        "surface": c.Infra.CodegenConformSurface.PYPROJECT,
                        "provider_plans": providers,
                    },
                ),
                snapshots[task.repository.name],
            ).files
        )
        manifests, _dependencies, waves = self._planned_dependency_waves(
            tasks, scaffold_tasks, metadata_files
        )
        planned = self._managed_plan_outcomes(
            tuple(
                tuple(ready[name] for name in wave if name in ready) for wave in waves
            ),
            providers,
            snapshots,
        )
        outcomes = tuple(
            self._merged_repository_outcome(outcome, planned[outcome.repository])
            if outcome.repository in planned
            else outcome
            for outcome in lazy
        )
        for manifest in manifests:
            self._verify_root_manifest(manifest, outcomes, tasks)
        return outcomes

    @staticmethod
    def _merged_repository_outcome(
        lazy: p.Infra.CodegenRepositoryPlanOutcome,
        managed: p.Infra.CodegenRepositoryPlanOutcome,
    ) -> p.Infra.CodegenRepositoryPlanOutcome:
        """Compose ordered projections of one repository's planning phases.

        Managed planning may rederive an initializer after facade projection.
        Its final desired bytes supersede the lazy candidate only for the same
        physical original and owner.

        Returns:
            Every final candidate in execution order.

        Raises:
            ValueError: If phases disagree about a destination's original owner.

        """
        if lazy.repository != managed.repository:
            msg = "repository planning phases have different owners"
            raise ValueError(msg)
        managed = m.Infra.CodegenRepositoryPlanOutcome.model_validate(managed)
        managed.files = tuple(
            m.Infra.CodegenFilePlan.model_validate(file)
            for file in u.Infra.codegen_compose_file_plans(
                (*lazy.files, *managed.files),
                ordered=True,
            )
        )
        managed.elapsed += lazy.elapsed
        return managed

    @staticmethod
    def _planned_dependency_waves(
        tasks: Sequence[p.Infra.CodegenRepositoryPlanTask],
        scaffold_tasks: Sequence[p.Infra.CodegenRepositoryPlanTask],
        metadata_files: tuple[p.Infra.CodegenFilePlan, ...],
    ) -> tuple[
        tuple[p.Infra.CodegenFilePlan, ...],
        Mapping[str, tuple[str, ...]],
        Sequence[Sequence[str]],
    ]:
        """Select each declared scaffold manifest and derive dependency waves.

        Returns:
            The single owned manifest per scaffold, and the shared waves.

        Raises:
            ValueError: If a scaffold has no single owned pyproject plan.

        """
        manifests: list[p.Infra.CodegenFilePlan] = []
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
            u.Infra.distribution_identity(
                task.repository.distribution
            ): task.repository.distribution
            for task in tasks
        }
        return (
            tuple(manifests),
            graph,
            tuple(tuple(distributions[name] for name in wave) for wave in waves.value),
        )

    def _managed_plan_outcomes(
        self,
        waves: Sequence[tuple[p.Infra.CodegenRepositoryPlanTask, ...]],
        providers: tuple[p.Infra.CodegenFilePlan, ...],
        snapshots: Mapping[str, p.Infra.WorkspaceSnapshot],
    ) -> Mapping[str, p.Infra.CodegenRepositoryPlanOutcome]:
        """Plan managed surfaces in dependency order over the staged plans.

        Each repository plans in the one loop over the plans staged by the
        repositories before it.

        Returns:
            The managed outcome per repository.

        """
        planned: MutableMapping[str, p.Infra.CodegenRepositoryPlanOutcome] = {}
        staged = {file.path: file for file in providers}
        for wave in waves:
            for task in wave:
                outcome = type(self).plan_repository_task(
                    task.model_copy(update={"provider_plans": tuple(staged.values())}),
                    snapshots[task.repository.name],
                )
                staged.update((file.path, file) for file in outcome.files)
                planned[outcome.repository] = outcome
        return planned

    @staticmethod
    def _verify_root_manifest(
        manifest: p.Infra.CodegenFilePlan,
        outcomes: tuple[p.Infra.CodegenRepositoryPlanOutcome, ...],
        tasks: Sequence[p.Infra.CodegenRepositoryPlanTask],
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
        selected = tuple(file for file in final.files if file.path == manifest.path)
        if len(selected) != 1 or selected[0].desired_content is None:
            msg = "final root metadata has no single pyproject payload"
            raise ValueError(msg)
        names = {
            u.Infra.distribution_identity(task.repository.distribution)
            for task in tasks
        }
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

    def _gathered_repository_plans(
        self,
        root: Path,
        planning: tuple[
            p.Infra.WorkspaceSpec,
            p.Infra.RepositoryConformTarget,
            p.Infra.RepositoryRef,
        ],
        selected: tuple[p.Infra.RepositoryRef, ...],
        surface: c.Infra.CodegenConformSurface,
        inputs: p.Infra.CodegenInputs,
    ) -> p.Result[
        tuple[
            list[p.Infra.CodegenFilePlan],
            list[p.Infra.UvEnvironmentPlan],
            tuple[p.Infra.CodegenRepositoryPlanOutcome, ...],
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
            The planned files, environments and repository outcomes, or the
            first task-selection failure.

        """
        result_type = r[
            tuple[
                list[p.Infra.CodegenFilePlan],
                list[p.Infra.UvEnvironmentPlan],
                tuple[p.Infra.CodegenRepositoryPlanOutcome, ...],
            ]
        ]
        u.Cli.info(f"stage=plan repositories={len(selected)}")
        planned_tasks = self._repository_plan_tasks(
            root, planning, selected, surface, inputs
        )
        if planned_tasks.failure:
            return result_type.from_failure(planned_tasks)
        tasks = planned_tasks.value
        # Each repository retains its own native election through the lazy
        # provider and managed passes. Inventory membership identifies nested
        # checkouts without merging their internal package names into one engine.
        roots = {
            task.repository.name: (root / task.repository.path).resolve()
            for task in tasks
        }
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
            }
            outcomes = self._repository_plan_outcomes(tasks, surface, inputs, snapshots)
            for name, snapshot in snapshots.items():
                self._retain_source_facts(snapshot, roots[name])
            self._verify_snapshot_outcomes(snapshots)
        return self._reported_repository_plans(root, selected, outcomes)

    def _retain_source_facts(
        self, snapshot: p.Infra.WorkspaceSnapshot, member: Path
    ) -> None:
        """Carry original source states and import facts beyond native planning.

        Raises:
            ValueError: If planning observes conflicting source states or imports.

        """
        for path in u.Infra.workspace_python_files(snapshot, member):
            source = u.Infra.workspace_source(snapshot, path)
            previous = self.state.source_inputs.setdefault(path, source.state)
            if previous.content != source.state.content:
                message = f"generation has conflicting source witnesses: {path}"
                raise ValueError(message)
            imports = u.Infra.workspace_module_imports(snapshot, path)
            known = self.state.source_imports.setdefault(path, imports)
            if known != imports:
                message = f"generation has conflicting source import facts: {path}"
                raise ValueError(message)

    def _repository_plan_tasks(
        self,
        root: Path,
        planning: tuple[
            p.Infra.WorkspaceSpec,
            p.Infra.RepositoryConformTarget,
            p.Infra.RepositoryRef,
        ],
        selected: tuple[p.Infra.RepositoryRef, ...],
        surface: c.Infra.CodegenConformSurface,
        inputs: p.Infra.CodegenInputs,
    ) -> p.Result[tuple[p.Infra.CodegenRepositoryPlanTask, ...]]:
        """Build one planning task per selected internal FLEXT repository.

        Returns:
            The ordered planning tasks, or the first member configuration
            failure.

        """
        current_target = planning[1]
        result_type = r[tuple[p.Infra.CodegenRepositoryPlanTask, ...]]
        tasks: list[p.Infra.CodegenRepositoryPlanTask] = []
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
                    r[p.Infra.WorkspaceSpec].from_failure(captured)
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
                m.Infra.CodegenRepositoryPlanTask.model_validate({
                    "ports": (self.state.ports),
                    "root": (root),
                    "workspace": (planning[0]),
                    "initial_workspace": (initial_workspace),
                    "current_target": (current_target),
                    "repository": (repository),
                    "surface": (surface),
                    "selected_inputs": (selected_inputs),
                }),
            )
        return result_type.ok(tuple(tasks))

    @staticmethod
    def _verify_snapshot_outcomes(
        snapshots: Mapping[str, p.Infra.WorkspaceSnapshot],
    ) -> None:
        """Stop planning when a source observation changed while planning."""
        for snapshot in snapshots.values():
            verified = u.Infra.workspace_snapshot_verify(
                snapshot, tuple(snapshot.sources)
            )
            if verified.failure:
                u.Infra.codegen_raise_failure(snapshot.workspace_root, verified)

    def _reported_repository_plans(
        self,
        root: Path,
        selected: tuple[p.Infra.RepositoryRef, ...],
        outcomes: tuple[p.Infra.CodegenRepositoryPlanOutcome, ...],
    ) -> p.Result[
        tuple[
            list[p.Infra.CodegenFilePlan],
            list[p.Infra.UvEnvironmentPlan],
            tuple[p.Infra.CodegenRepositoryPlanOutcome, ...],
        ]
    ]:
        """Publish planning evidence and collect the same observed outcomes.

        Returns:
            Planned files and environments, or the evidence failure.

        """
        result_type = r[
            tuple[
                list[p.Infra.CodegenFilePlan],
                list[p.Infra.UvEnvironmentPlan],
                tuple[p.Infra.CodegenRepositoryPlanOutcome, ...],
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
        files: list[p.Infra.CodegenFilePlan] = []
        environments: list[p.Infra.UvEnvironmentPlan] = []
        for index, outcome in enumerate(outcomes, start=1):
            files.extend(outcome.files)
            u.Cli.progress(index, len(outcomes), outcome.repository, "plan")
            if outcome.environment is not None:
                environments.append(outcome.environment)
            u.Cli.status(
                "plan",
                outcome.repository,
                result=True,
                elapsed=outcome.elapsed,
            )
        return result_type.ok((files, environments, outcomes))

    @classmethod
    def plan_repository_task(
        cls,
        task: p.Infra.CodegenRepositoryPlanTask,
        snapshot: p.Infra.WorkspaceSnapshot,
    ) -> p.Infra.CodegenRepositoryPlanOutcome:
        """Plan one repository; its first failure propagates with its traceback.

        Returns:
            The outcome of the repository planning task.

        """
        started = time.monotonic()
        u.Cli.info(
            f"stage=repository state=start repository={task.repository.name} "
            f"root={(task.root / task.repository.path).resolve()} "
            f"source_root={snapshot.engine.root.real_path} "
            f"surface={task.surface} role={task.repository.role.value}"
        )
        outcome = cls._plan_repository_task(task, snapshot)
        u.Cli.info(
            f"stage=repository state=end repository={task.repository.name} "
            f"surface={task.surface} elapsed={time.monotonic() - started:.3f}s "
            f"files={len(outcome.files)}"
        )
        return outcome

    @classmethod
    def _plan_repository_task(
        cls,
        task: p.Infra.CodegenRepositoryPlanTask,
        snapshot: p.Infra.WorkspaceSnapshot,
    ) -> p.Infra.CodegenRepositoryPlanOutcome:
        """Plan one repository from its task over the run's one snapshot.

        The repository planner is built from the task and reads the run's
        workspace snapshot.

        Returns:
            The repository's file and environment plans.

        """
        started = time.monotonic()
        repository = task.repository
        project_root = (task.root / repository.path).resolve()
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
            u.Infra.codegen_raise_failure(project_root, resolved)
        if task.surface is c.Infra.CodegenConformSurface.LAZY_INIT:
            return planner._lazy_init_outcome(task, resolved.value, started)
        inputs = task.selected_inputs
        if inputs is None:
            loaded = u.Infra.load_codegen_inputs(resolved.value)
            if loaded.failure:
                u.Infra.codegen_raise_failure(resolved.value, loaded)
            inputs = loaded.value
        planned_inputs = planner._repository_planning_inputs(
            resolved.value,
            task.workspace,
            task.current_target,
            repository,
            inputs=inputs,
        )
        if planned_inputs.failure:
            u.Infra.codegen_raise_failure(resolved.value, planned_inputs)
        return planner._governed_repository_outcome(
            task, inputs, planned_inputs.value, started
        )

    def _lazy_init_outcome(
        self,
        task: p.Infra.CodegenRepositoryPlanTask,
        repository_root: Path,
        started: float,
    ) -> p.Infra.CodegenRepositoryPlanOutcome:
        """Plan the lazy-init surface of one resolved repository.

        Returns:
            The lazy-init file plans of the repository.

        """
        planned = (
            r[Sequence[p.Infra.CodegenFilePlan]].ok(())
            if task.initial_workspace is not None
            and task.initial_workspace.project is not None
            and task.repository.name == task.initial_workspace.repository.name
            else self._planned_lazy_init_files(repository_root)
        )
        if planned.failure:
            u.Infra.codegen_raise_failure(repository_root, planned)
        return m.Infra.CodegenRepositoryPlanOutcome(
            repository=task.repository.name,
            files=tuple(planned.value),
            elapsed=time.monotonic() - started,
        )

    def _governed_repository_outcome(
        self,
        task: p.Infra.CodegenRepositoryPlanTask,
        inputs: p.Infra.CodegenInputs,
        planned_inputs: tuple[
            Path,
            p.Infra.RepositoryConformTarget,
            p.Infra.WorkspaceSpec,
        ],
        started: float,
    ) -> p.Infra.CodegenRepositoryPlanOutcome:
        """Plan the governed files of one repository from its resolved inputs.

        Returns:
            The repository's governed file and environment plans.

        """
        repository_root, target, local_workspace = planned_inputs
        target = target.model_copy(
            update={
                "vscode_spec": inputs.spec.vscode,
                "vscode_sources": inputs.sources,
            },
        )
        scaffold = (
            task.initial_workspace is not None
            and task.initial_workspace.project is not None
            and task.repository.name == task.initial_workspace.repository.name
        )
        with self.shared_source_views():
            planned = self._governed_repository_plans(
                target,
                local_workspace,
                self.surface_contract(
                    c.Infra.CodegenConformSurface(task.surface),
                    codegen=inputs.spec,
                ),
                inputs,
                scaffold=scaffold,
            )
        if planned.failure:
            u.Infra.codegen_raise_failure(repository_root, planned)
        governed_plans, retired_plans = planned.value
        return m.Infra.CodegenRepositoryPlanOutcome(
            repository=task.repository.name,
            files=(*governed_plans, *retired_plans),
            environment=self.uv_environment_plan(
                root=repository_root,
                target=target,
                workspace=local_workspace,
                config=inputs.spec,
            ),
            elapsed=time.monotonic() - started,
        )

    def _repository_planning_inputs(
        self,
        repository_root: Path,
        workspace: p.Infra.WorkspaceSpec,
        current_target: p.Infra.RepositoryConformTarget,
        repository: p.Infra.RepositoryRef,
        *,
        inputs: p.Infra.CodegenInputs,
    ) -> p.Result[
        tuple[
            Path,
            p.Infra.RepositoryConformTarget,
            p.Infra.WorkspaceSpec,
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
            rendered = self._rendered_members(repository_root, workspace)
            if rendered.failure:
                return result_type.from_failure(rendered)
            return result_type.ok(
                (repository_root, current_target, rendered.value),
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
            # Only the parent-relative path differs; participation stays rendered.
            target = target.model_copy(
                update={
                    "repository": target.repository.model_copy(
                        update={"path": repository.path},
                    ),
                },
            )
        return result_type.ok((repository_root, target, local_workspace))

    @staticmethod
    def _rendered_members(
        root: Path,
        workspace: p.Infra.WorkspaceSpec,
    ) -> p.Result[m.Infra.WorkspaceSpec]:
        """Give root projections each member's rendered package participation.

        The same generation writes every member's ``[build-system]``, so root
        projections that filter members on ``package`` read the rendered value,
        never the pre-render one.

        Returns:
            The render workspace whose members carry rendered participation.

        """
        result_type = r[m.Infra.WorkspaceSpec]
        detector = workspace_services.FlextInfraWorkspaceDetector
        members: list[p.Infra.RepositoryRef] = []
        for member in workspace.subprojects:
            rendered = detector.conform_repository(root / member.path, member)
            if rendered.failure:
                return result_type.from_failure(rendered)
            members.append(rendered.value)
        return result_type.ok(
            m.Infra.WorkspaceSpec.model_validate(workspace).model_copy(
                update={"subprojects": tuple(members)},
            ),
        )

    def _resolved_repository_root(
        self,
        root: Path,
        workspace: p.Infra.WorkspaceSpec,
        current_target: p.Infra.RepositoryConformTarget,
        repository: p.Infra.RepositoryRef,
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
        workspace: p.Infra.WorkspaceSpec,
        repository: p.Infra.RepositoryRef,
        repository_root: Path,
        *,
        inputs: p.Infra.CodegenInputs,
    ) -> p.Result[p.Infra.WorkspaceSpec]:
        """Load the local workspace a declared member plans from.

        Returns:
            The resulting ``p.Result[p.Infra.WorkspaceSpec]``.

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
        return r[p.Infra.WorkspaceSpec].ok(
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
        target: p.Infra.RepositoryConformTarget,
        local_workspace: p.Infra.WorkspaceSpec,
        contract: p.Infra.CodegenConformSurfaceContract,
        inputs: p.Infra.CodegenInputs,
        *,
        scaffold: bool,
    ) -> p.Result[tuple[list[p.Infra.CodegenFilePlan], list[p.Infra.CodegenFilePlan]]]:
        """Plan governed files and retirements using the target's elected config.

        Args:
            target: Conform target of the repository being planned.
            local_workspace: The member's own local workspace specification.
            contract: Elected conform surface contract.
            inputs: Loaded codegen inputs of the repository.
            scaffold: Whether the repository is the declared workspace
                repository planning its initial scaffold.

        Returns:
            The resulting ``p.Result[tuple[list[p.Infra.CodegenFilePlan],
                list[p.Infra.CodegenFilePlan]]]``.

        """
        result_type = r[
            tuple[list[p.Infra.CodegenFilePlan], list[p.Infra.CodegenFilePlan]]
        ]
        config_spec = inputs.spec
        planner = (
            self._plan_scaffold_repository
            if scaffold
            else self._plan_existing_repository
        )
        repository_plan = planner(
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
        retired_files: list[p.Infra.CodegenFilePlan] = []
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
        workspace: p.Infra.WorkspaceSpec,
        current_repository: p.Infra.RepositoryRef,
    ) -> p.Result[tuple[p.Infra.RepositoryRef, ...]]:
        """Resolve self/subprojects/all from the local read-only topology.

        Returns:
            The resulting ``p.Result[tuple[p.Infra.RepositoryRef, ...]]``.

        """
        scope = request.scope
        selected: tuple[p.Infra.RepositoryRef, ...]
        if scope is c.Infra.CodegenConformScope.SELF:
            selected = (current_repository,)
        elif scope is c.Infra.CodegenConformScope.DECLARED:
            if not workspace.subprojects:
                return r[tuple[p.Infra.RepositoryRef, ...]].fail(
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
            return r[tuple[p.Infra.RepositoryRef, ...]].fail(
                "selected repositories do not permit code generation",
            )
        return r[tuple[p.Infra.RepositoryRef, ...]].ok(mutable)

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
