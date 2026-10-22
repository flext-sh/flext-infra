"""Conformance plan selection and repository topology resolution.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import time
import traceback
from operator import itemgetter
from pathlib import Path
from typing import Literal

from flext_infra import c, m, p, r, t, u
from flext_infra.codegen import (
    FlextInfraCodegenLazyInit,
    FlextInfraMiseArtifactsVerification,
)
from flext_infra.codegen._conform import FlextInfraCodegenConformScaffoldPlan
from flext_infra.workspace import FlextInfraWorkspaceDetector


class FlextInfraCodegenConformPlan(FlextInfraCodegenConformScaffoldPlan):
    """Conformance planning across scaffold and existing repositories."""

    @staticmethod
    def continue_after_publication(
        receipts: t.VariadicTuple[m.Infra.CodegenPhaseOutcome],
    ) -> p.Result[bool]:
        """Continue planning through the invocation's authenticated live effects.

        Returns:
            Whether the actual publication inputs and outputs remain current.

        """
        if not receipts:
            return r[bool].fail(
                "generation continuation requires its publication receipts",
            )
        return FlextInfraMiseArtifactsVerification.publication_outputs_current(
            receipts,
        ).map(lambda _: True)

    def plan(
        self,
        request: m.Infra.CodegenConformRequest,
    ) -> p.Result[m.Infra.CodegenPlan]:
        """Build and validate the complete selection without writing.

        Returns:
            The resulting ``p.Result[m.Infra.CodegenPlan]``.

        """
        inputs = u.Infra.load_codegen_inputs(request.root.expanduser().resolve())
        if inputs.failure:
            return r[m.Infra.CodegenPlan].from_failure(inputs)
        return self.plan_repositories(request, inputs.value)

    def _plan_single_surface(
        self,
        request: m.Infra.CodegenConformRequest,
        *,
        inputs: m.Infra.CodegenInputs | None = None,
    ) -> p.Result[t.Pair[m.Infra.CodegenPlan, m.Infra.CodegenPhaseAnalysis]]:
        """Plan the declared facade or lazy-init surface of one repository.

        Returns:
            The public plan and its complete authenticated phase analysis.

        """
        if inputs is None:
            loaded = u.Infra.load_codegen_inputs(request.root.expanduser().resolve())
            if loaded.failure:
                return r[
                    t.Pair[m.Infra.CodegenPlan, m.Infra.CodegenPhaseAnalysis]
                ].from_failure(loaded)
            inputs = loaded.value
        if request.what == c.Infra.CodegenConformSurface.FACADES:
            return self._plan_facade(request, inputs)
        return self._plan_lazy_init(request, inputs)

    def plan_repositories(
        self,
        request: m.Infra.CodegenConformRequest,
        inputs: m.Infra.CodegenInputs,
    ) -> p.Result[m.Infra.CodegenPlan]:
        """Dispatch the declared surface using its captured repository inputs.

        Returns:
            The complete repository plan or its first planning failure.

        """
        if request.what in c.Infra.FILE_ONLY_SURFACES:
            return self._plan_single_surface(request, inputs=inputs).map(
                itemgetter(0),
            )
        config_spec = inputs.spec
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
            c.Infra.CodegenConformSurface(request.what),
            inputs,
        )
        if gathered.failure:
            return r[m.Infra.CodegenPlan].from_failure(gathered)
        files, environments, issues = gathered.value
        return r[m.Infra.CodegenPlan].ok(
            m.Infra.CodegenPlan(
                request=request,
                repositories=selected,
                workspace=workspace,
                make_spec=config_spec.make,
                uv_environments=tuple(environments),
                files=tuple(files),
                issues=tuple(issues),
                exception=self.state.planning_exception,
            ),
        )

    def _extended_pyproject_views(
        self,
        task: m.Infra.CodegenRepositoryPlanTask,
        tasks: t.SequenceOf[m.Infra.CodegenRepositoryPlanTask],
        inputs: m.Infra.CodegenInputs,
        files: t.SequenceOf[m.Infra.CodegenFilePlan],
    ) -> p.Result[list[m.Infra.CodegenFilePlan]]:
        """Resolve one repository's views without consulting failed selected metadata.

        Args:
            task: Captured repository and governing workspace planning inputs.
            tasks: Internal repository tasks admitted to this planning cohort.
            inputs: Loaded codegen inputs of the request root.
            files: Governed file plans planned so far.

        Returns:
            The native resolution views extending the planned files, or the
            first resolution failure.

        """
        result_type = r[list[m.Infra.CodegenFilePlan]]
        project_root = (task.root / task.repository.path).resolve()
        project_inputs = (
            r[m.Infra.CodegenInputs].ok(inputs)
            if project_root == task.root
            else u.Infra.load_codegen_inputs(project_root)
        )
        if project_inputs.failure:
            return result_type.from_failure(project_inputs)
        project_workspace = (
            r[m.Infra.WorkspaceSpec].ok(task.workspace)
            if project_root == task.root
            else FlextInfraWorkspaceDetector.load_workspace_spec(
                project_root,
                inputs=project_inputs.value,
            )
        )
        if project_workspace.failure:
            return result_type.from_failure(project_workspace)
        selected_roots = {
            (item.root / item.repository.path).resolve() for item in tasks
        }
        desired = {
            file.path: file.desired_content
            for file in files
            if file.desired_content is not None
        }
        repositories: list[m.Infra.RepositoryRef] = []
        for member in (
            project_workspace.value.repository,
            *project_workspace.value.subprojects,
        ):
            path = (project_root / member.path).resolve() / c.PYPROJECT_FILENAME
            if path in desired:
                projected = self._desired_resolution_repository(
                    member,
                    path,
                    desired[path],
                )
                if projected.failure:
                    return result_type.from_failure(projected)
                resolved = projected.value
            elif path.parent in selected_roots and (
                member is project_workspace.value.repository or member.package
            ):
                return result_type.fail(
                    f"native resolution input has no successful selected plan: {path}",
                )
            else:
                resolved = member
            repositories.append(resolved)
        return self.native_resolution_plans(
            project_root,
            project_workspace.value.model_copy(
                update={
                    "repository": repositories[0],
                    "subprojects": tuple(repositories[1:]),
                },
            ),
            project_inputs.value,
            files,
        ).map(list)

    @staticmethod
    def _desired_resolution_repository(
        repository: m.Infra.RepositoryRef,
        path: Path,
        content: bytes,
    ) -> p.Result[m.Infra.RepositoryRef]:
        """Derive native participation from the metadata being published.

        Returns:
            Repository identity with desired packaging facts, or its original failure.

        """
        result_type = r[m.Infra.RepositoryRef]
        payload = u.Cli.toml_mapping_from_text(content.decode(c.DEFAULT_ENCODING))
        if payload is None:
            return result_type.fail(
                f"native resolution input is not valid TOML: {path}"
            )
        try:
            declaration = m.Infra.ProjectPackagingDeclaration.model_validate(payload)
        except ValueError as exc:
            return result_type.fail(
                f"native resolution packaging is not valid: {path}: {exc}",
                exception=exc,
            )
        return result_type.ok(
            repository.model_copy(
                update={"package": u.Infra.project_package_participation(declaration)},
            ),
        )

    def _plan_facade(
        self,
        request: m.Infra.CodegenConformRequest,
        inputs: m.Infra.CodegenInputs,
    ) -> p.Result[t.Pair[m.Infra.CodegenPlan, m.Infra.CodegenPhaseAnalysis]]:
        """Plan one declared facade through its canonical family renderer.

        Args:
            request: The conform request containing the root and destination module.
            inputs: The effective codegen policy with its consulted input states.

        Returns:
            The plan and authenticated phase analysis, or the first failure.

        """
        result_type = r[t.Pair[m.Infra.CodegenPlan, m.Infra.CodegenPhaseAnalysis]]
        root = request.root.expanduser().resolve()
        topology = self._planning_workspace(request, root, inputs=inputs)
        if topology.failure:
            return result_type.from_failure(topology)
        workspace, _target, repository = topology.value
        destination_result = self._facade_destination(root, request.module)
        if destination_result.failure:
            return result_type.from_failure(destination_result)
        destination = destination_result.value
        analyzed = self._facade_analysis(root, destination)
        if analyzed.failure:
            return result_type.from_failure(analyzed)
        analysis = analyzed.value.model_copy(
            update={
                "files": self._bind_codegen_sources(analyzed.value.files, inputs),
                "inputs": (*analyzed.value.inputs, *inputs.sources),
                "issues": (*analyzed.value.issues, *self.state.planning_issues),
                "exception": analyzed.value.exception or self.state.planning_exception,
            },
        )
        plan = m.Infra.CodegenPlan(
            request=request,
            repositories=(repository,),
            workspace=workspace,
            make_spec=inputs.spec.make,
            uv_environments=(),
            files=analysis.files,
            issues=analysis.issues,
            exception=analysis.exception,
        )
        return result_type.ok((plan, analysis))

    @staticmethod
    def _facade_destination(root: Path, module: str | None) -> p.Result[Path]:
        """Validate a direct module destination in the existing package.

        Returns:
            The destination path or the original destination diagnostic.

        """
        layout = u.Infra.layout(root)
        if layout is None or module is None:
            return r[Path].fail(
                "facades requires an existing package and destination",
            )
        package_name, separator, module_name = module.partition(".")
        if (
            not separator
            or package_name != layout.package_dir.name
            or not package_name.isidentifier()
            or not module_name.isidentifier()
        ):
            return r[Path].fail(
                "facades --module must name a direct package module",
            )
        return r[Path].ok(layout.package_dir / f"{module_name}{c.Infra.EXT_PYTHON}")

    def _facade_analysis(
        self,
        root: Path,
        destination: Path,
    ) -> p.Result[m.Infra.CodegenPhaseAnalysis]:
        """Render and stage exactly one facade with its authenticated inputs.

        Returns:
            The selected file analysis or its first planning failure.

        """
        result_type = r[m.Infra.CodegenPhaseAnalysis]
        snapshots = self._facade_sources(root, destination)
        if snapshots.failure:
            return result_type.from_failure(snapshots)
        family, states, _sources = snapshots.value
        mode = states[0].mode
        if mode is None:
            return result_type.fail(
                f"facade input has no authenticated mode: {destination}",
            )
        with u.Infra.facade_source_project(root, source_states=tuple(states)) as (
            project,
            consumed_states,
            sources,
        ):
            rendered = self._render_facade(
                destination, family, sources, project=project
            )
            if rendered.failure:
                return result_type.from_failure(rendered)
            inputs, directories, topology = consumed_states()
        file = self.file_plan(
            root,
            destination.relative_to(root).as_posix(),
            rendered.value,
            mode=mode,
            source_states=inputs,
        )
        if file.failure:
            return result_type.from_failure(file)
        return result_type.ok(
            m.Infra.CodegenPhaseAnalysis(
                phase=c.Infra.CodegenStagedFilePhase.CONFORM,
                files=(
                    file.value.model_copy(
                        update={
                            "source_directories": directories,
                            "source_query_topology": topology,
                        }
                    ),
                ),
                inputs=inputs,
                source_directories=directories,
                source_query_topology=topology,
            ),
        )

    @staticmethod
    def _facade_family(
        source: str, destination: Path
    ) -> p.Result[Literal["c", "t", "u", "p", "m"]]:
        """Identify the selected renderer from the module's published declaration.

        Returns:
            The unique supported facade family or a declaration failure.

        """
        result_type = r[Literal["c", "t", "u", "p", "m"]]
        match tuple(
            sorted(
                u.Infra.facade_letter_names_source(source, filename=str(destination))
            )
        ):
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

    @classmethod
    def _facade_sources(
        cls,
        root: Path,
        destination: Path,
    ) -> p.Result[
        t.Triple[
            Literal["c", "t", "u", "p", "m"],
            list[m.Cli.AtomicFileState],
            t.MappingKV[Path, str],
        ]
    ]:
        """Authenticate owners and consumers before family rendering.

        Returns:
            The family, ordered source states and decoded source, or a failure.

        """
        result_type = r[
            t.Triple[
                Literal["c", "t", "u", "p", "m"],
                list[m.Cli.AtomicFileState],
                t.MappingKV[Path, str],
            ]
        ]
        selected = cls._facade_source_state(root, destination)
        if selected.failure:
            return result_type.from_failure(selected)
        state, source = selected.value
        declared = cls._facade_family(source, destination)
        if declared.failure:
            return result_type.from_failure(declared)
        family = declared.value
        states = [state]
        sources = {destination: source}
        # Type projection reads only its private family; the other renderers
        # also resolve executable consumers throughout the selected package.
        scan_root = destination.parent
        if family == "t":
            scan_root /= u.Infra.facade_families()[family].directory
        for path in sorted(scan_root.rglob(c.Infra.EXT_PYTHON_GLOB)):
            if path == destination:
                continue
            snapshot = cls._facade_source_state(root, path)
            if snapshot.failure:
                return result_type.from_failure(snapshot)
            state, source = snapshot.value
            states.append(state)
            sources[path] = source
        return result_type.ok((family, states, sources))

    @staticmethod
    def _facade_source_state(
        root: Path,
        path: Path,
    ) -> p.Result[t.Pair[m.Cli.AtomicFileState, str]]:
        """Read one required source without escaping the selected repository.

        Returns:
            Its authenticated state and decoded source, or the first failure.

        """
        result_type = r[t.Pair[m.Cli.AtomicFileState, str]]
        if not path.resolve().is_relative_to(root):
            return result_type.fail(f"facade input escapes repository: {path}")
        snapshot = u.Cli.atomic_read_binary_file_state(path, required=True)
        if snapshot.failure:
            return result_type.from_failure(snapshot)
        state = snapshot.value
        if state.content is None:
            return result_type.fail(f"facade input is absent: {path}")
        return result_type.ok((state, state.content.decode(c.DEFAULT_ENCODING)))

    @staticmethod
    def _render_facade(
        destination: Path,
        family: Literal["c", "t", "u", "p", "m"],
        sources: t.MappingKV[Path, str],
        *,
        project: p.Infra.RopeProject,
    ) -> p.Result[str]:
        """Reuse the canonical renderer without selecting a different destination.

        Returns:
            Rendered source for exactly the requested declaring module.

        """
        if family == "t":
            sources = {
                path: u.Infra.require_file_resource(
                    project.get_resource(
                        path.relative_to(Path(project.root.real_path)).as_posix()
                    ),
                    path,
                ).read()
                for path in sources
            }
            return r[str].ok(
                u.Infra.render_type_facade(
                    destination.parent, destination, sources, project=project
                ),
            )
        if (
            u.Infra.facade_module_path(
                destination.parent, family, project=project, sources=sources
            )
            != destination
        ):
            return r[str].fail("selected facade differs from its declaring module")
        rendered = u.Infra.render_utility_facade(
            destination.parent, family=family, project=project, sources=sources
        )
        if rendered is None:
            return r[str].fail(f"selected facade has no private {family} owners")
        return r[str].ok(rendered)

    def _plan_lazy_init(
        self,
        request: m.Infra.CodegenConformRequest,
        inputs: m.Infra.CodegenInputs,
    ) -> p.Result[t.Pair[m.Infra.CodegenPlan, m.Infra.CodegenPhaseAnalysis]]:
        """Plan only initializer destinations in one authenticated repository.

        Returns:
            The public plan and its complete authenticated lazy-init receipt.

        """
        result_type = r[t.Pair[m.Infra.CodegenPlan, m.Infra.CodegenPhaseAnalysis]]
        root = request.root.expanduser().resolve()
        topology = self._planning_workspace(request, root, inputs=inputs)
        if topology.failure:
            return result_type.from_failure(topology)
        workspace, _target, repository = topology.value
        selected = self._select_repositories(request, workspace, repository)
        if selected.failure:
            return result_type.from_failure(selected)
        planned = FlextInfraCodegenLazyInit(
            repository_root=root,
            project_scope_roots=tuple(
                (root / participant.path).resolve()
                for participant in selected.value
                if participant.kind is c.Infra.ProjectKind.INTERNAL_FLEXT
            ),
            target_module=request.module,
        ).plan_files()
        if planned.failure:
            return result_type.from_failure(planned)
        # Support-file retirement is not part of this initializer-only surface.
        analysis = planned.value.model_copy(
            update={
                "files": self._bind_codegen_sources(
                    tuple(
                        file
                        for file in planned.value.files
                        if file.path.name == c.Infra.INIT_PY
                    ),
                    inputs,
                ),
                "inputs": (*planned.value.inputs, *inputs.sources),
                "issues": (*planned.value.issues, *self.state.planning_issues),
                "exception": planned.value.exception or self.state.planning_exception,
            },
        )
        plan = m.Infra.CodegenPlan(
            request=request,
            repositories=selected.value,
            workspace=workspace,
            make_spec=inputs.spec.make,
            uv_environments=(),
            files=analysis.files,
            issues=analysis.issues,
            exception=analysis.exception,
        )
        return result_type.ok((plan, analysis))

    def _planning_workspace(
        self,
        request: m.Infra.CodegenConformRequest,
        root: Path,
        *,
        inputs: m.Infra.CodegenInputs,
    ) -> p.Result[
        t.Triple[
            m.Infra.WorkspaceSpec,
            m.Infra.RepositoryConformTarget,
            m.Infra.RepositoryRef,
        ]
    ]:
        """Load the planning workspace and its current conformance target.

        Returns:
            The resulting ``p.Result[t.Triple[m.Infra.WorkspaceSpec,
                m.Infra.RepositoryConformTarget, m.Infra.RepositoryRef]]``.

        """
        result_type = r[
            t.Triple[
                m.Infra.WorkspaceSpec,
                m.Infra.RepositoryConformTarget,
                m.Infra.RepositoryRef,
            ]
        ]
        workspace = self.state.initial_workspace
        if workspace is None:
            workspace_result = FlextInfraWorkspaceDetector.load_workspace_spec(
                root,
                inputs=inputs,
                allow_unprovisioned_members=(
                    request.what in c.Infra.ALLOW_UNPROVISIONED_SURFACES
                ),
            )
            if workspace_result.failure:
                return result_type.from_failure(workspace_result)
            workspace = workspace_result.value
        current_repository = workspace.repository
        if (
            self.state.initial_workspace is None
            and request.what not in c.Infra.DECLARED_TARGET_SURFACES
        ):
            current_target_result = FlextInfraWorkspaceDetector.conform_target(
                root,
                workspace,
                inputs=inputs,
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
                ci_enabled=True,
                publishes_release=current_repository.publishes_release,
                gascity_enabled=workspace.gascity_enabled,
                external_dependency_paths=workspace.external_dependency_paths,
            )
        return result_type.ok((workspace, current_target, current_repository))

    @staticmethod
    def _planning_report_evidence(
        root: Path,
        outcomes: t.SequenceOf[m.Infra.CodegenRepositoryPlanOutcome],
        repository_paths: t.MappingKV[str, Path],
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
            )
            if probe.failure:
                return r[m.Infra.CodegenPlanningReport].from_failure(probe)
            candidate_sha: str | None = None
            candidate_dirty: bool | None = None
            candidate_kind: Literal["git", "unversioned"] = "unversioned"
            if probe.value.value:
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
                    elapsed=outcome.elapsed,
                ),
            )
        return r[m.Infra.CodegenPlanningReport].ok(
            m.Infra.CodegenPlanningReport(root=root, outcomes=tuple(evidence)),
        )

    def _repository_plan_outcomes(
        self,
        tasks: t.SequenceOf[m.Infra.CodegenRepositoryPlanTask],
        surface: c.Infra.CodegenConformSurface,
        inputs: m.Infra.CodegenInputs,
    ) -> t.VariadicTuple[m.Infra.CodegenRepositoryPlanOutcome]:
        """Plan the read-only cohort before any serial evidence publication.

        Returns:
            Ordered outcomes retaining original failures and desired native metadata.

        """
        contract = self.surface_contract(surface, codegen=inputs.spec)
        selected_pyproject = contract.pyproject and (
            contract.destinations is None
            or c.PYPROJECT_FILENAME in contract.destinations
        )
        providers: t.VariadicTuple[m.Infra.CodegenFilePlan] = ()
        if contract.complete_governed and tasks:
            outcomes, providers = self._governed_plan_outcomes(
                tasks, selected_pyproject=selected_pyproject
            )
        else:
            outcomes = u.Infra.fleet_map(type(self).plan_repository_task, tasks)
        self._retain_diagnostics(*(outcome.exception for outcome in outcomes))
        metadata = tuple(
            file for outcome in outcomes if not outcome.failed for file in outcome.files
        )
        extended_outcomes: list[m.Infra.CodegenRepositoryPlanOutcome] = []
        for task, outcome in zip(tasks, outcomes, strict=True):
            if outcome.failed or not selected_pyproject:
                extended_outcomes.append(outcome)
                continue
            extended = self._extended_pyproject_views(task, tasks, inputs, metadata)
            extended_outcomes.append(
                outcome.model_copy(
                    update=(
                        {
                            "files": (),
                            "environment": None,
                            "error": (
                                extended.error or "native resolution planning failed"
                            ),
                            "exception": extended.exception,
                        }
                        if extended.failure
                        else {"files": (*outcome.files, *extended.value)}
                    ),
                ),
            )
        # A consumer may use a provider whose unrelated managed planning failed.
        # Keep only the successfully planned lazy inputs it actually consumed;
        # their own publication admission and dependency edges remain mandatory.
        consumed = {
            state.path
            for outcome in extended_outcomes
            for file in outcome.files
            for state in file.source_states
        }
        included = {
            file.path for outcome in extended_outcomes for file in outcome.files
        }
        paths = {
            (task.root / task.repository.path).resolve(): task.repository.name
            for task in tasks
        }
        additions: dict[str, list[m.Infra.CodegenFilePlan]] = {}
        for file in providers:
            if file.path in consumed and file.path not in included:
                additions.setdefault(paths[file.project.resolve()], []).append(file)
                included.add(file.path)
        return tuple(
            outcome.model_copy(
                update={
                    "files": (
                        *outcome.files,
                        *additions.get(outcome.repository, ()),
                    )
                }
            )
            for outcome in extended_outcomes
        )

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
        return m.Infra.CodegenRepositoryPlanOutcome(
            repository=repository,
            error=str(exception),
            error_type=f"{type(exception).__module__}.{type(exception).__qualname__}",
            error_traceback=traceback.format_exc(),
            exception=exception,
            elapsed=elapsed,
        )

    @staticmethod
    def _cohort_failure(
        failure: m.Infra.CodegenRepositoryPlanOutcome,
        outcomes: t.VariadicTuple[m.Infra.CodegenRepositoryPlanOutcome],
    ) -> t.VariadicTuple[m.Infra.CodegenRepositoryPlanOutcome]:
        """Fail every still-planned repository with one cohort-wide cause.

        Returns:
            The outcomes, each successful one carrying the shared failure.

        """
        return tuple(
            outcome
            if outcome.failed
            else outcome.model_copy(
                update={
                    "files": (),
                    "environment": None,
                    "error": failure.error,
                    "error_type": failure.error_type,
                    "error_traceback": failure.error_traceback,
                    "issues": failure.issues,
                    "exception": failure.exception,
                },
            )
            for outcome in outcomes
        )

    def _governed_plan_outcomes(
        self,
        tasks: t.SequenceOf[m.Infra.CodegenRepositoryPlanTask],
        *,
        selected_pyproject: bool,
    ) -> t.Pair[
        t.VariadicTuple[m.Infra.CodegenRepositoryPlanOutcome],
        t.VariadicTuple[m.Infra.CodegenFilePlan],
    ]:
        """Plan lazy providers in parallel, then managed surfaces in order.

        Each repository's lazy plan indexes only its own sources, so those
        read-only plans run across the fleet workers. Root metadata fixes the
        dependency order; the managed pass then stays serial. A cohort-wide
        failure fails every planned repository and keeps no provider.

        Returns:
            The ordered outcomes and the lazy provider plans they may consume.

        """
        plan = type(self).plan_repository_task
        lazy = u.Infra.fleet_map(
            plan,
            tuple(
                task.model_copy(
                    update={"surface": c.Infra.CodegenConformSurface.LAZY_INIT}
                )
                for task in tasks
            ),
        )
        self._retain_diagnostics(*(outcome.exception for outcome in lazy))
        providers = tuple(
            file for outcome in lazy if not outcome.failed for file in outcome.files
        )
        ready = {
            task.repository.distribution: task
            for task, outcome in zip(tasks, lazy, strict=True)
            if not outcome.failed
        }
        root_task = next(
            (
                task
                for task in ready.values()
                if selected_pyproject
                and task.initial_workspace is not None
                and task.repository.name == task.workspace.repository.name
            ),
            None,
        )
        manifests: t.VariadicTuple[m.Infra.CodegenFilePlan] = ()
        try:
            if root_task is not None:
                metadata = plan(
                    root_task.model_copy(
                        update={
                            "surface": c.Infra.CodegenConformSurface.PYPROJECT,
                            "provider_plans": providers,
                        },
                    ),
                )
                if metadata.failed:
                    self._retain_diagnostics(metadata.exception)
                    return self._cohort_failure(metadata, lazy), ()
                project = (root_task.root / root_task.repository.path).resolve()
                manifests = tuple(
                    file
                    for file in metadata.files
                    if file.project.resolve() == project
                    and file.path.resolve() == project / c.PYPROJECT_FILENAME
                    and file.desired_content is not None
                )
                if len(manifests) != 1:
                    msg = "root metadata requires exactly one owned pyproject plan"
                    raise ValueError(msg)
            order = u.Infra.workspace_dependency_order(
                tasks[0].root,
                tuple(task.repository for task in tasks),
                planned_manifests=manifests,
            )
        except (OSError, ValueError, TypeError) as exc:
            self._retain_diagnostics(exc)
            failure = self._failed_outcome(tasks[0].repository.name, exc)
            return self._cohort_failure(failure, lazy), ()
        planned, providers = self._managed_plan_outcomes(
            tuple(ready[name] for name in order if name in ready), providers
        )
        outcomes = tuple(
            outcome if outcome.failed else planned[outcome.repository]
            for outcome in lazy
        )
        try:
            for manifest in manifests:
                self._verify_root_manifest(manifest, outcomes, tasks)
        except (OSError, ValueError, TypeError, RuntimeError) as exc:
            self._retain_diagnostics(exc)
            failure = self._failed_outcome(tasks[0].repository.name, exc)
            return self._cohort_failure(failure, outcomes), providers
        return outcomes, providers

    def _managed_plan_outcomes(
        self,
        ordered: t.VariadicTuple[m.Infra.CodegenRepositoryPlanTask],
        providers: t.VariadicTuple[m.Infra.CodegenFilePlan],
    ) -> t.Pair[
        t.MappingKV[str, m.Infra.CodegenRepositoryPlanOutcome],
        t.VariadicTuple[m.Infra.CodegenFilePlan],
    ]:
        """Plan managed surfaces serially over the staged provider plans.

        A failed repository withdraws its own lazy providers. Only
        authenticated complete source output survives an unrelated managed
        failure, never incoming lazy inputs.

        Returns:
            The managed outcome per repository and the surviving providers.

        """
        planned: dict[str, m.Infra.CodegenRepositoryPlanOutcome] = {}
        staged = {file.path: file for file in providers}
        for task in ordered:
            outcome = type(self).plan_repository_task(
                task.model_copy(update={"provider_plans": tuple(staged.values())})
            )
            self._retain_diagnostics(outcome.exception)
            files = outcome.files
            if outcome.failed:
                project_root = (task.root / task.repository.path).resolve()
                staged = {
                    path: file
                    for path, file in staged.items()
                    if file.project != project_root
                }
                providers = tuple(
                    file for file in providers if file.project != project_root
                )
                if outcome.error:
                    providers = (*providers, *files)
                    outcome = outcome.model_copy(update={"files": ()})
                else:
                    files = ()
            staged.update((file.path, file) for file in files)
            planned[outcome.repository] = outcome
        return planned, providers

    @staticmethod
    def _verify_root_manifest(
        manifest: m.Infra.CodegenFilePlan,
        outcomes: t.VariadicTuple[m.Infra.CodegenRepositoryPlanOutcome],
        tasks: t.SequenceOf[m.Infra.CodegenRepositoryPlanTask],
    ) -> None:
        """Prove the planned root manifest stayed current and its graph stable.

        Raises:
            ValueError: When the final root metadata lost its single payload or
                its internal dependency edges changed after metadata planning.

        """
        FlextInfraMiseArtifactsVerification.plans_current((manifest,)).unwrap()
        FlextInfraMiseArtifactsVerification.states_current(
            manifest.source_states,
        ).unwrap()
        u.Cli.atomic_verify_directory_queries(
            manifest.source_directories,
            manifest.source_query_topology,
        ).unwrap()
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

    def _gathered_repository_plans(
        self,
        root: Path,
        planning: t.Triple[
            m.Infra.WorkspaceSpec,
            m.Infra.RepositoryConformTarget,
            m.Infra.RepositoryRef,
        ],
        selected: t.VariadicTuple[m.Infra.RepositoryRef],
        surface: c.Infra.CodegenConformSurface,
        inputs: m.Infra.CodegenInputs,
    ) -> p.Result[
        t.Triple[
            list[m.Infra.CodegenFilePlan],
            list[m.Infra.UvEnvironmentPlan],
            list[m.Infra.Issue],
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
            The resulting ``p.Result[t.Pair[list[m.Infra.CodegenFilePlan],
                list[m.Infra.UvEnvironmentPlan]]]``.

        """
        workspace, current_target, _current_repository = planning
        result_type = r[
            t.Triple[
                list[m.Infra.CodegenFilePlan],
                list[m.Infra.UvEnvironmentPlan],
                list[m.Infra.Issue],
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
            tasks.append(
                m.Infra.CodegenRepositoryPlanTask(
                    root=root,
                    workspace=workspace,
                    initial_workspace=self.state.initial_workspace,
                    current_target=current_target,
                    repository=repository,
                    surface=surface,
                    generation_only=self.state.generation_only,
                    selected_inputs=(
                        inputs
                        if repository.name == current_target.repository.name
                        else None
                    ),
                ),
            )
        # Every repository plans independently and read-only, so the fleet
        # plans them across worker processes; the results keep declaration
        # order, and publication stays serial under the generation lease.
        outcomes = self._repository_plan_outcomes(tasks, surface, inputs)
        repository_paths = {
            repository.name: root / repository.path for repository in selected
        }
        evidence = self._planning_report_evidence(root, outcomes, repository_paths)
        if evidence.failure:
            return result_type.from_failure(evidence)
        published = u.Infra.publish_refactor_report_evidence(
            root,
            evidence.value,
            relative_path=c.Infra.CODEGEN_PLAN_REPORT_RELATIVE_PATH,
        )
        if published.failure:
            return result_type.from_failure(published)
        files: list[m.Infra.CodegenFilePlan] = []
        environments: list[m.Infra.UvEnvironmentPlan] = []
        issues: list[m.Infra.Issue] = list(self.state.planning_issues)
        for index, outcome in enumerate(outcomes, start=1):
            issues.extend(outcome.issues)
            files.extend(outcome.files)
            self._retain_diagnostics(outcome.exception)
            u.Cli.progress(index, len(outcomes), outcome.repository, "conform")
            if (
                outcome.error
                or outcome.error_type
                or outcome.error_traceback
                or outcome.exception is not None
            ):
                u.Cli.status(
                    "conform",
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
                "conform",
                outcome.repository,
                result=not outcome.failed,
                elapsed=outcome.elapsed,
            )
        return result_type.ok((files, environments, issues))

    @classmethod
    def plan_repository_task(
        cls,
        task: m.Infra.CodegenRepositoryPlanTask,
    ) -> m.Infra.CodegenRepositoryPlanOutcome:
        """Preserve a planning failure as data without retry or publication.

        Returns:
            The outcome of the repository planning task, including any failure
            information.

        """
        started = time.monotonic()
        try:
            return cls._plan_repository_task(task)
        except (OSError, ValueError) as exc:
            return cls._failed_outcome(
                task.repository.name, exc, time.monotonic() - started
            )

    @classmethod
    def _plan_repository_task(
        cls,
        task: m.Infra.CodegenRepositoryPlanTask,
    ) -> m.Infra.CodegenRepositoryPlanOutcome:
        """Plan one repository from a self-contained task.

        The planner rebuilds from the task: no parent planner state crosses
        the boundary, each repository indexes only its own sources, and
        failures return as data instead of live results.

        Returns:
            The repository's file and environment plans, or its failure.

        """
        started = time.monotonic()
        repository = task.repository
        u.Cli.info(
            f"  stage=topology repository={repository.name} "
            f"role={repository.role.value} kind={repository.kind.value}",
        )
        planner = cls(
            repository_root=task.current_target.toolchain_root,
            state=m.Infra.CodegenConformState(
                repository_root=task.current_target.toolchain_root,
                initial_workspace=task.initial_workspace,
                generation_only=task.generation_only,
                provider_plans=task.provider_plans,
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
                error=resolved.error or f"checkout root failed: {repository.name}",
                exception=resolved.exception,
                elapsed=time.monotonic() - started,
            )
        inputs = task.selected_inputs
        if inputs is None:
            loaded = u.Infra.load_codegen_inputs(resolved.value)
            if loaded.failure:
                return m.Infra.CodegenRepositoryPlanOutcome(
                    repository=repository.name,
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
        if task.surface is c.Infra.CodegenConformSurface.LAZY_INIT:
            planned = (
                r[t.SequenceOf[m.Infra.CodegenFilePlan]].ok(())
                if task.initial_workspace is not None
                and task.initial_workspace.project is not None
                and repository.name == task.workspace.repository.name
                else planner._planned_lazy_init_files(repository_root)
            )
            return m.Infra.CodegenRepositoryPlanOutcome(
                repository=repository.name,
                files=() if planned.failure else tuple(planned.value),
                error=(
                    (planned.error or "lazy planning failed") if planned.failure else ""
                ),
                exception=(
                    planned.exception
                    if planned.failure
                    else planner.state.planning_exception
                ),
                issues=tuple(planner.state.planning_issues),
                elapsed=time.monotonic() - started,
            )
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
                and repository.name == task.workspace.repository.name
            ),
        )
        if planned.failure:
            return m.Infra.CodegenRepositoryPlanOutcome(
                repository=repository.name,
                files=tuple(
                    file
                    for file in planner.state.completed_source_plans or ()
                    if file.project == repository_root
                ),
                error=planned.error or f"planning failed: {repository.name}",
                exception=(
                    planned.exception
                    if planner.state.planning_exception is None
                    else planner.state.planning_exception
                ),
                issues=tuple(planner.state.planning_issues),
                elapsed=time.monotonic() - started,
            )
        governed_plans, retired_plans = planned.value
        return m.Infra.CodegenRepositoryPlanOutcome(
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
        )

    def _repository_planning_inputs(
        self,
        repository_root: Path,
        workspace: m.Infra.WorkspaceSpec,
        current_target: m.Infra.RepositoryConformTarget,
        repository: m.Infra.RepositoryRef,
        *,
        inputs: m.Infra.CodegenInputs,
    ) -> p.Result[
        t.Triple[
            Path,
            m.Infra.RepositoryConformTarget,
            m.Infra.WorkspaceSpec,
        ]
    ]:
        """Resolve one repository's checkout root, target, and local workspace.

        Returns:
            The resulting ``p.Result[t.Triple[Path,
                m.Infra.RepositoryConformTarget, m.Infra.WorkspaceSpec]]``.

        """
        result_type = r[
            t.Triple[
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
        target_result = FlextInfraWorkspaceDetector.conform_target(
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
        declared_member = FlextInfraWorkspaceDetector.load_workspace_spec(
            repository_root,
            inputs=inputs,
        )
        if declared_member.failure or repository.path == Path():
            return declared_member
        # The parent owns topology; the member owns its local project metadata.
        return r[m.Infra.WorkspaceSpec].ok(
            m.Infra.WorkspaceSpec(
                name=repository.name,
                docs_audit=declared_member.value.docs_audit,
                beads=workspace.beads,
                repository=repository.model_copy(update={"path": Path()}),
                project=declared_member.value.project,
                namespace_scan_dirs=declared_member.value.namespace_scan_dirs,
                candidate_dependencies=workspace.candidate_dependencies,
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
    ) -> p.Result[t.Pair[list[m.Infra.CodegenFilePlan], list[m.Infra.CodegenFilePlan]]]:
        """Plan governed files and retirements using the target's elected config.

        Args:
            target: Conform target of the repository being planned.
            local_workspace: The member's own local workspace specification.
            contract: Elected conform surface contract.
            inputs: Loaded codegen inputs of the repository.
            scaffold: Whether the repository is the declared workspace
                repository planning its initial scaffold.

        Returns:
            The resulting ``p.Result[t.Pair[list[m.Infra.CodegenFilePlan],
                list[m.Infra.CodegenFilePlan]]]``.

        """
        result_type = r[
            t.Pair[list[m.Infra.CodegenFilePlan], list[m.Infra.CodegenFilePlan]]
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
        return result_type.ok(
            (
                list(self._bind_codegen_sources(governed_files, inputs)),
                list(self._bind_codegen_sources(retired_files, inputs)),
            ),
        )

    def _bind_codegen_sources(
        self,
        files: t.SequenceOf[m.Infra.CodegenFilePlan],
        inputs: m.Infra.CodegenInputs,
    ) -> t.VariadicTuple[m.Infra.CodegenFilePlan]:
        """Bind each file to the same captured configuration without duplicate sources.

        Returns:
            Valid file plans; source conflicts retain their target issue and cause.

        """
        complete: list[m.Infra.CodegenFilePlan] = []
        for file in files:
            sources = u.Infra.unique_states(
                (*file.source_states, *inputs.sources),
            )
            if sources.failure:
                self._record_file_failure(
                    file.path,
                    sources.error or "configuration source identity conflicts",
                    exception=sources.exception,
                )
                continue
            complete.append(
                file.model_copy(
                    update={"source_states": sources.value},
                ),
            )
        return tuple(complete)

    @staticmethod
    def _select_repositories(
        request: m.Infra.CodegenConformRequest,
        workspace: m.Infra.WorkspaceSpec,
        current_repository: m.Infra.RepositoryRef,
    ) -> p.Result[t.VariadicTuple[m.Infra.RepositoryRef]]:
        """Resolve self/subprojects/all from the local read-only topology.

        Returns:
            The resulting ``p.Result[t.VariadicTuple[m.Infra.RepositoryRef]]``.

        """
        scope = c.Infra.CodegenConformScope(request.scope)
        selected: t.VariadicTuple[m.Infra.RepositoryRef]
        if scope is c.Infra.CodegenConformScope.SELF:
            selected = (current_repository,)
        elif scope is c.Infra.CodegenConformScope.DECLARED:
            if not workspace.subprojects:
                return r[t.VariadicTuple[m.Infra.RepositoryRef]].fail(
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
            return r[t.VariadicTuple[m.Infra.RepositoryRef]].fail(
                "selected repositories do not permit code generation",
            )
        return r[t.VariadicTuple[m.Infra.RepositoryRef]].ok(mutable)

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
