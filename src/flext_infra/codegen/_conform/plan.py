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
    FlextInfraCodegenPreconditions,
    FlextInfraMiseArtifactsJournal,
    FlextInfraMiseArtifactsVerification,
)
from flext_infra.codegen._conform import FlextInfraCodegenConformScaffoldPlan
from flext_infra.workspace import FlextInfraWorkspaceDetector


class FlextInfraCodegenConformPlan(FlextInfraCodegenConformScaffoldPlan):
    """Conformance planning across scaffold and existing repositories."""

    def continue_after_publication(
        self,
        receipts: t.VariadicTuple[m.Infra.CodegenPhaseOutcome],
    ) -> p.Result[bool]:
        """Advance producer capture only through this producer's live effect proof.

        Returns:
            Whether the recaptured producer still owns the published receipts.

        """
        if self.producer is None or not receipts:
            return r[bool].fail(
                "producer continuation requires its captured publication receipts",
            )
        producer = self.producer
        expected = self._expected_producer_sources(producer)
        if expected.failure:
            return r[bool].from_failure(expected)
        matched = self._matched_producer_receipts(receipts, producer, expected.value)
        if matched.failure:
            return matched
        verified = self._verified_receipt_states(receipts)
        if verified.failure:
            return verified
        return self._advanced_producer_capture(receipts)

    @staticmethod
    def _expected_producer_sources(
        producer: m.Infra.CodegenPhaseAnalysis,
    ) -> p.Result[t.MappingKV[Path, m.Infra.CodegenJournalSource]]:
        """Encode the captured producer's inputs as expected journal sources.

        Args:
            producer: The captured producer analysis.

        Returns:
            The expected generator sources keyed by path, or the first
            encoding failure.

        """
        expected_sources: t.MutableMappingKV[Path, m.Infra.CodegenJournalSource] = {}
        for state in producer.inputs:
            encoded = FlextInfraMiseArtifactsJournal.source_record("generator", state)
            if encoded.failure:
                return r[t.MappingKV[Path, m.Infra.CodegenJournalSource]].from_failure(
                    encoded
                )
            expected_sources[state.path] = encoded.value
        return r[t.MappingKV[Path, m.Infra.CodegenJournalSource]].ok(expected_sources)

    @staticmethod
    def _matched_producer_receipts(
        receipts: t.VariadicTuple[m.Infra.CodegenPhaseOutcome],
        producer: m.Infra.CodegenPhaseAnalysis,
        expected_sources: t.MappingKV[Path, m.Infra.CodegenJournalSource],
    ) -> p.Result[bool]:
        """Reject publication receipts captured by a different producer.

        Args:
            receipts: Publication receipts of this producer's live effects.
            producer: The captured producer analysis.
            expected_sources: Expected generator sources keyed by path.

        Returns:
            Whether every receipt belongs to the captured producer, or the
            first mismatch failure.

        """
        expected_trees = {tree.root.path: tree for tree in producer.generator_trees}
        for receipt in receipts:
            if (
                {
                    source.path: source.model_copy(update={"role": None})
                    for source in receipt.generator_sources
                }
                != expected_sources
                or {tree.root.path: tree for tree in receipt.generator_trees}
                != expected_trees
                or receipt.generator_modules != producer.generator_modules
            ):
                return r[bool].fail(
                    "publication receipt belongs to a different captured producer",
                )
        return r[bool].ok(value=True)

    @staticmethod
    def _verified_receipt_states(
        receipts: t.VariadicTuple[m.Infra.CodegenPhaseOutcome],
    ) -> p.Result[bool]:
        """Verify every publication receipt's source states remain current.

        Args:
            receipts: Publication receipts of this producer's live effects.

        Returns:
            Whether every receipt's states remain current, or the first
            verification failure.

        """
        for receipt in receipts:
            verified = FlextInfraMiseArtifactsVerification.publication_states_current(
                receipt,
            )
            if verified.failure:
                return verified
        return r[bool].ok(value=True)

    def _advanced_producer_capture(
        self,
        receipts: t.VariadicTuple[m.Infra.CodegenPhaseOutcome],
    ) -> p.Result[bool]:
        """Recapture the producer and prove it still owns its live effects.

        Args:
            receipts: Publication receipts of this producer's live effects.

        Returns:
            Whether the recaptured producer is current, or the first capture,
            verification or currency failure.

        """
        captured = FlextInfraCodegenPreconditions.capture_producer(
            self.repository_root,
            entrypoint=self.plan,
        )
        if captured.failure:
            return r[bool].from_failure(captured)
        reverified = self._verified_receipt_states(receipts)
        if reverified.failure:
            return reverified
        current = FlextInfraCodegenPreconditions.producer_current(captured.value)
        if current.failure:
            return current
        self.producer = captured.value
        return r[bool].ok(value=True)

    def plan(
        self,
        request: m.Infra.CodegenConformRequest,
    ) -> p.Result[m.Infra.CodegenPlan]:
        """Build and validate the complete selection without writing.

        Returns:
            The resulting ``p.Result[m.Infra.CodegenPlan]``.

        """
        producer = self._required_producer()
        if producer.failure:
            return r[m.Infra.CodegenPlan].from_failure(producer)
        inputs = u.Infra.load_codegen_inputs(request.root.expanduser().resolve())
        if inputs.failure:
            return r[m.Infra.CodegenPlan].from_failure(inputs)
        return self.plan_repositories(request, inputs.value)

    def _required_producer(self) -> p.Result[m.Infra.CodegenPhaseAnalysis]:
        """Return the current captured producer, capturing one when absent.

        Returns:
            The current captured producer, or the first capture or currency
            failure.

        """
        if self.producer is None:
            captured = FlextInfraCodegenPreconditions.capture_producer(
                self.repository_root,
                entrypoint=self.plan,
            )
            if captured.failure:
                return r[m.Infra.CodegenPhaseAnalysis].from_failure(captured)
            self.producer = captured.value
        verified = FlextInfraCodegenPreconditions.producer_current(self.producer)
        if verified.failure:
            return r[m.Infra.CodegenPhaseAnalysis].from_failure(verified)
        return r[m.Infra.CodegenPhaseAnalysis].ok(self.producer)

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
        if request.what in {
            c.Infra.CodegenConformSurface.LAZY_INIT,
            c.Infra.CodegenConformSurface.FACADES,
        }:
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
        contract = self.surface_contract(
            c.Infra.CodegenConformSurface(request.what),
            codegen=config_spec,
        )
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
        if (
            not issues
            and contract.pyproject
            and (
                contract.destinations is None
                or c.PYPROJECT_FILENAME in contract.destinations
            )
        ):
            extended = self._extended_pyproject_views(
                root,
                selected,
                workspace,
                inputs,
                files,
            )
            if extended.failure:
                return r[m.Infra.CodegenPlan].from_failure(extended)
            files.extend(extended.value)
        return r[m.Infra.CodegenPlan].ok(
            m.Infra.CodegenPlan(
                request=request,
                repositories=selected,
                workspace=workspace,
                make_spec=config_spec.make,
                uv_environments=tuple(environments),
                files=tuple(files),
                issues=tuple(issues),
                exception=self.planning_exception,
            ),
        )

    def _extended_pyproject_views(
        self,
        root: Path,
        selected: t.VariadicTuple[m.Infra.RepositoryRef],
        workspace: m.Infra.WorkspaceSpec,
        inputs: m.Infra.CodegenInputs,
        files: t.SequenceOf[m.Infra.CodegenFilePlan],
    ) -> p.Result[list[m.Infra.CodegenFilePlan]]:
        """Resolve native topology views when the surface plans pyproject.

        Args:
            root: Resolved repository root of the request.
            selected: Repository references selected for planning.
            workspace: Loaded workspace specification of the request root.
            inputs: Loaded codegen inputs of the request root.
            files: Governed file plans planned so far.

        Returns:
            The native resolution views extending the planned files, or the
            first resolution failure.

        """
        views: list[m.Infra.CodegenFilePlan] = []
        for repository in selected:
            if repository.kind is not c.Infra.ProjectKind.INTERNAL_FLEXT:
                continue
            project_root = (root / repository.path).resolve()
            project_inputs = (
                r[m.Infra.CodegenInputs].ok(inputs)
                if project_root == root
                else u.Infra.load_codegen_inputs(project_root)
            )
            if project_inputs.failure:
                return r[list[m.Infra.CodegenFilePlan]].from_failure(project_inputs)
            project_workspace = (
                r[m.Infra.WorkspaceSpec].ok(workspace)
                if project_root == root
                else FlextInfraWorkspaceDetector.load_workspace_spec(
                    project_root,
                    inputs=project_inputs.value,
                )
            )
            if project_workspace.failure:
                return r[list[m.Infra.CodegenFilePlan]].from_failure(
                    project_workspace,
                )
            resolved = self.native_resolution_plans(
                project_root,
                project_workspace.value,
                project_inputs.value,
                files,
                rendered_by=self.rendered_by_stamp(),
            )
            if resolved.failure:
                return r[list[m.Infra.CodegenFilePlan]].from_failure(resolved)
            views.extend(resolved.value)
        return r[list[m.Infra.CodegenFilePlan]].ok(views)

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
            },
        )
        analysis = analysis.model_copy(
            update={
                "issues": (*analysis.issues, *self.planning_issues),
                "exception": analysis.exception or self.planning_exception,
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
        family, states, sources = snapshots.value
        rendered = self._render_facade(destination, family, sources)
        if rendered.failure:
            return result_type.from_failure(rendered)
        mode = states[0].mode
        if mode is None:
            return result_type.fail(
                f"facade input has no authenticated mode: {destination}",
            )
        file = self.file_plan(
            root,
            destination.relative_to(root).as_posix(),
            rendered.value,
            mode=mode,
            source_states=tuple(states),
        )
        if file.failure:
            return result_type.from_failure(file)
        return result_type.ok(
            m.Infra.CodegenPhaseAnalysis(
                phase=c.Infra.CodegenStagedFilePhase.CONFORM,
                files=(file.value,),
                inputs=tuple(states),
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
    ) -> p.Result[str]:
        """Reuse the canonical renderer without selecting a different destination.

        Returns:
            Rendered source for exactly the requested declaring module.

        """
        if family == "t":
            return r[str].ok(
                u.Infra.render_type_facade(destination.parent, destination, sources),
            )
        if u.Infra.facade_module_path(destination.parent, family) != destination:
            return r[str].fail("selected facade differs from its declaring module")
        rendered = u.Infra.render_utility_facade(destination.parent, family=family)
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
            },
        )
        analysis = analysis.model_copy(
            update={
                "issues": (*analysis.issues, *self.planning_issues),
                "exception": analysis.exception or self.planning_exception,
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
        workspace = self.initial_workspace
        if workspace is None:
            workspace_result = FlextInfraWorkspaceDetector.load_workspace_spec(
                root,
                inputs=inputs,
                allow_unprovisioned_members=(
                    request.what
                    in {
                        c.Infra.CodegenConformSurface.MAKEFILE,
                        c.Infra.CodegenConformSurface.DOCS_CONFIG,
                        c.Infra.CodegenConformSurface.ENVRC,
                        c.Infra.CodegenConformSurface.PYPROJECT,
                        c.Infra.CodegenConformSurface.MISE_CONFIG,
                    }
                ),
            )
            if workspace_result.failure:
                return result_type.from_failure(workspace_result)
            workspace = workspace_result.value
        current_repository = workspace.repository
        if self.initial_workspace is None and request.what not in {
            c.Infra.CodegenConformSurface.MAKEFILE,
            c.Infra.CodegenConformSurface.ENVRC,
            c.Infra.CodegenConformSurface.PYPROJECT,
            c.Infra.CodegenConformSurface.MISE_CONFIG,
        }:
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
                toolchain_root=root,
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
                    error=outcome.error,
                    error_type=outcome.error_type,
                    elapsed=outcome.elapsed,
                ),
            )
        return r[m.Infra.CodegenPlanningReport].ok(
            m.Infra.CodegenPlanningReport(root=root, outcomes=tuple(evidence)),
        )

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
                    initial_workspace=self.initial_workspace,
                    current_target=current_target,
                    repository=repository,
                    surface=surface,
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
        outcomes = u.Infra.fleet_map(type(self).plan_repository_task, tasks)
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
        issues: list[m.Infra.Issue] = list(self.planning_issues)
        for index, outcome in enumerate(outcomes, start=1):
            issues.extend(outcome.issues)
            if self.planning_exception is None:
                self.planning_exception = outcome.exception
            u.Cli.progress(index, len(outcomes), outcome.repository, "conform")
            if outcome.error or outcome.error_type:
                u.Cli.status(
                    "conform",
                    outcome.repository,
                    result=False,
                    elapsed=outcome.elapsed,
                )
                u.Cli.error(
                    f"{outcome.repository}: {outcome.error_type}: {outcome.error}",
                )
                issues.append(
                    m.Infra.Issue(
                        file=str(repository_paths[outcome.repository]),
                        line=0,
                        column=0,
                        code=c.Infra.ToolOutcome.ERROR.value,
                        message=outcome.error_traceback or outcome.error,
                    ),
                )
                continue
            files.extend(outcome.files)
            if outcome.environment is not None:
                environments.append(outcome.environment)
            for issue in outcome.issues:
                u.Cli.error(issue.formatted)
            u.Cli.status(
                "conform",
                outcome.repository,
                result=not outcome.issues,
                elapsed=outcome.elapsed,
            )
        return result_type.ok((files, environments, issues))

    @classmethod
    def plan_repository_task(
        cls,
        task: m.Infra.CodegenRepositoryPlanTask,
    ) -> m.Infra.CodegenRepositoryPlanOutcome:
        """Preserve a worker's failure as data without retry or publication.

        Args:
            task: The repository planning task to be executed.

        Returns:
            The outcome of the repository planning task, including any failure
            information.

        """
        started = time.monotonic()
        try:
            return cls._plan_repository_task(task)
        except (OSError, ValueError) as exc:
            return m.Infra.CodegenRepositoryPlanOutcome(
                repository=task.repository.name,
                error=str(exc),
                error_type=f"{type(exc).__module__}.{type(exc).__qualname__}",
                error_traceback=traceback.format_exc(),
                exception=exc,
                elapsed=time.monotonic() - started,
            )

    @classmethod
    def _plan_repository_task(
        cls,
        task: m.Infra.CodegenRepositoryPlanTask,
    ) -> m.Infra.CodegenRepositoryPlanOutcome:
        """Plan one repository from a self-contained, picklable task.

        A fleet worker runs this in its own process: it rebuilds the planner
        from the task, so no parent state, lease, or collaborator crosses the
        boundary, and returns a failure as data instead of a live result.

        Returns:
            The repository's file and environment plans, or its failure.

        """
        started = time.monotonic()
        repository = task.repository
        u.Cli.info(
            f"  stage=topology repository={repository.name} "
            f"role={repository.role.value} kind={repository.kind.value}",
        )
        planner = cls(initial_workspace=task.initial_workspace)
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
                and repository.name == task.workspace.repository.name
            ),
        )
        if planned.failure:
            return m.Infra.CodegenRepositoryPlanOutcome(
                repository=repository.name,
                error=planned.error or f"planning failed: {repository.name}",
                exception=planned.exception,
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
            issues=tuple(planner.planning_issues),
            exception=planner.planning_exception,
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
        if not repository_root.is_dir() and self.initial_workspace is None:
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
        if repository.path != Path():
            declared_member = FlextInfraWorkspaceDetector.load_workspace_spec(
                repository_root,
                inputs=inputs,
            )
            if declared_member.failure:
                return r[m.Infra.WorkspaceSpec].from_failure(declared_member)
            local_repository = repository.model_copy(update={"path": Path()})
            # The parent owns topology and selection; the member owns its
            # project metadata, including the runtime dependency profile
            # and the namespace production scope it declares.
            return r[m.Infra.WorkspaceSpec].ok(
                m.Infra.WorkspaceSpec(
                    name=repository.name,
                    docs_audit=declared_member.value.docs_audit,
                    beads=workspace.beads,
                    repository=local_repository,
                    project=declared_member.value.project,
                    namespace_scan_dirs=(declared_member.value.namespace_scan_dirs),
                    candidate_dependencies=workspace.candidate_dependencies,
                ),
            )
        local_workspace_result = FlextInfraWorkspaceDetector.load_workspace_spec(
            repository_root,
            inputs=inputs,
        )
        if local_workspace_result.failure:
            return r[m.Infra.WorkspaceSpec].from_failure(local_workspace_result)
        return r[m.Infra.WorkspaceSpec].ok(local_workspace_result.value)

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
        if contract.runtime_bindings:
            repository_plan = self.plan_runtime_bindings(
                target,
                config_spec,
                codegen_inputs=inputs,
            )
        elif scaffold:
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
            declared = file.model_copy(
                update={"source_states": (*file.source_states, *inputs.sources)},
            )
            sources = FlextInfraCodegenPreconditions.phase_sources(
                c.Infra.CodegenStagedFilePhase.CONFORM_BOOTSTRAP,
                (declared,),
            )
            if sources.failure:
                self._record_file_failure(
                    file.path,
                    sources.error or "configuration source identity conflicts",
                    exception=sources.exception,
                )
                continue
            complete.append(
                declared.model_copy(
                    update={
                        "source_states": tuple(
                            state for _phase, state in sources.value
                        ),
                    },
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

    @staticmethod
    def _repository_provider(
        repository: m.Infra.RepositoryRef,
    ) -> p.Result[m.Infra.ProviderIdentitySpec]:
        """Resolve one repository to its self-declared provider identity.

        Returns:
            The resulting ``p.Result[m.Infra.ProviderIdentitySpec]``.

        """
        return u.Infra.repository_provider(repository)


__all__: list[str] = ["FlextInfraCodegenConformPlan"]
