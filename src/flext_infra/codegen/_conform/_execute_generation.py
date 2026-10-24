"""Locked publication of complete generation batches and staged validation.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from functools import partial
from pathlib import Path
from typing import TYPE_CHECKING

from flext_infra import c, m, p, r, t, u
from flext_infra.codegen import (
    FlextInfraCodegenLazyInit,
    FlextInfraCodegenMiseArtifacts,
    FlextInfraCodegenPreconditions,
    FlextInfraCodegenTransaction,
    FlextInfraMiseArtifactsVerification,
)


class FlextInfraCodegenConformExecuteGenerationMixin:
    """Publish managed generation in dependent batches through staged consumers."""

    if TYPE_CHECKING:
        generation_only: bool
        initial_workspace: m.Infra.WorkspaceSpec | None
        ports: m.Infra.CodegenConformPorts | None
        docs_planner: p.Infra.DocsArtifactPlanner | None

        @staticmethod
        def _observe_publication(
            request: m.Infra.CodegenConformRequest,
        ) -> p.Result[m.Infra.CodegenResult]: ...

        @staticmethod
        def mise_config_plans(
            plan: m.Infra.CodegenPlan,
        ) -> p.Result[t.VariadicTuple[m.Infra.CodegenFilePlan]]: ...

        def plan(
            self,
            request: m.Infra.CodegenConformRequest,
        ) -> p.Result[m.Infra.CodegenPlan]: ...

        def conform_workspace_beads_routes(
            self,
            request: m.Infra.CodegenConformRequest,
        ) -> p.Result[bool]: ...

        def _prepare_scaffold_directories(
            self,
            request: m.Infra.CodegenConformRequest,
        ) -> p.Result[t.VariadicTuple[m.Cli.AtomicDirectoryState]]: ...

    @staticmethod
    def _bootstrap_validation_paths(
        session: m.Infra.CodegenTransactionSession,
        publications: t.VariadicTuple[m.Infra.CodegenStagedFile],
        plans: t.VariadicTuple[m.Infra.CodegenFilePlan],
    ) -> p.Result[t.VariadicTuple[Path]]:
        """Authenticate the exact staged effects or unchanged physical plans.

        Returns:
            Paths admitted for consumption, or the first plan identity failure.

        """
        result_type = r[t.VariadicTuple[Path]]
        if not plans or len({plan.path for plan in plans}) != len(plans):
            return result_type.fail("bootstrap validation requires unique file plans")
        expected = {
            plan.path: (plan.project, plan.desired_content, plan.desired_mode)
            for plan in plans
            if u.Infra.codegen_file_requires_effect(plan)
        }
        actual = {
            publication.before.path: (
                publication.project,
                publication.replacement.content,
                publication.replacement.mode,
            )
            for publication in publications
            if publication.replacement is not None
        }
        if len(actual) != len(publications) or actual != expected:
            return result_type.fail("bootstrap replacements differ from file plans")
        current = FlextInfraMiseArtifactsVerification.plans_current(
            plans, journal=session.journal
        )
        if current.failure:
            return result_type.from_failure(current)
        staged_paths = {
            publication.before.path: publication.replacement.path
            for publication in publications
            if publication.replacement is not None
        }
        return result_type.ok(
            tuple(staged_paths.get(plan.path, plan.path) for plan in plans)
        )

    @classmethod
    def _validate_pyproject_stage(
        cls,
        session: m.Infra.CodegenTransactionSession,
        publications: t.VariadicTuple[m.Infra.CodegenStagedFile],
        *,
        plans: t.VariadicTuple[m.Infra.CodegenFilePlan],
    ) -> p.Result[m.Infra.CodegenTransactionSession]:
        """Parse every staged or retained plan through the real TOML consumer.

        Returns:
            The unchanged session or the native TOML parser failure.

        """
        result_type = r[m.Infra.CodegenTransactionSession]
        paths = cls._bootstrap_validation_paths(session, publications, plans)
        if paths.failure:
            return result_type.from_failure(paths)
        for path in paths.value:
            parsed = u.Cli.toml_read_document(path)
            if parsed.failure:
                return result_type.from_failure(parsed)
        current = FlextInfraMiseArtifactsVerification.plans_current(
            plans, journal=session.journal
        )
        if current.failure:
            return result_type.from_failure(current)
        u.Cli.info(
            f"stage=pyproject-staged-validation files={len(paths.value)} "
            "semantic-analysis=next-gen",
        )
        return result_type.ok(session)

    @classmethod
    def _validate_mise_stage(
        cls,
        session: m.Infra.CodegenTransactionSession,
        publications: t.VariadicTuple[m.Infra.CodegenStagedFile],
        *,
        plans: t.VariadicTuple[m.Infra.CodegenFilePlan],
    ) -> p.Result[m.Infra.CodegenTransactionSession]:
        """Validate staged or retained Mise TOML before completing its phase.

        Returns:
            The unchanged session or the exact declaration failure.

        """
        result_type = r[m.Infra.CodegenTransactionSession]
        if len(plans) != 1:
            return result_type.fail("mise-config requires one file plan")
        paths = cls._bootstrap_validation_paths(session, publications, plans)
        if paths.failure:
            return result_type.from_failure(paths)
        checked = FlextInfraCodegenMiseArtifacts.validate_config_file(
            paths.value[0],
        )
        if checked.failure:
            return result_type.from_failure(checked)
        current = FlextInfraMiseArtifactsVerification.plans_current(
            plans, journal=session.journal
        )
        if current.failure:
            return result_type.from_failure(current)
        u.Cli.info("stage=mise-config-staged-validation files=1 installs=0")
        return result_type.ok(session)

    def _seed_declared_beads_identity(self, root: Path) -> p.Result[bool]:
        """Materialize the scaffold's declared Beads identity before governance.

        The participant-policy snapshot resolves repository governance through
        the workspace detector, which reads the repository-local Beads
        identity. A fresh scaffold root has no local history for the detector
        to read yet, while the declared workspace already carries the derived
        identity: writing it first makes the repository self-consistent from
        the first governed effect. The template render of the same identity
        follows later in the cycle and is byte-identical.

        Returns:
            The resulting ``p.Result[bool]``.

        """
        workspace = self.initial_workspace
        if workspace is None or workspace.beads is None:
            return r[bool].ok(value=True)
        beads = workspace.beads
        destination = root / c.CONFIG_DIR_NAME / c.Infra.BEADS_CONFIG_FILENAME
        if destination.is_file():
            return r[bool].ok(value=True)
        quoted = tuple(
            u.Cli.json_dumps(value)
            for value in (beads.workspace, beads.database, beads.issue_prefix)
        )
        failed = next((item for item in quoted if item.failure), None)
        if failed is not None:
            return r[bool].from_failure(failed)
        workspace_name, database, issue_prefix = (item.value for item in quoted)
        payload = (
            f"version: {beads.version}\n"
            f"workspace: {workspace_name}\n"
            f"database: {database}\n"
            f"issue_prefix: {issue_prefix}\n"
        )
        written = u.Cli.atomic_write_text_file(destination, payload)
        if written.failure:
            return r[bool].from_failure(written)
        return r[bool].ok(value=True)

    def _execute_managed(
        self,
        request: m.Infra.CodegenConformRequest,
    ) -> p.Result[m.Infra.CodegenResult]:
        """Plan outside the lease and publish through locked generation phases.

        Returns:
            The resulting ``p.Result[m.Infra.CodegenResult]``.

        """
        if c.Infra.CodegenConformMode(request.mode) is c.Infra.CodegenConformMode.CHECK:
            return self._observe_publication(request)
        configured = self._managed_policy(request)
        if configured.failure:
            return r[m.Infra.CodegenResult].from_failure(configured)
        policy = configured.value
        transaction = FlextInfraCodegenTransaction(
            FlextInfraCodegenMiseArtifacts(repository_root=request.root),
            participant_policy=policy,
        )
        planned = transaction.run_locked(
            prepare=True,
            operation=lambda scope_root: self._execute_managed_locked(
                request,
                scope_root,
            ),
        ).flat_map(lambda _: self._prepare_managed_plan(request))
        cause = planned.exception
        if cause is not None:
            raise cause
        if planned.failure:
            return r[m.Infra.CodegenResult].from_failure(planned)
        operation = transaction.publish_operation_receipt(
            request,
            (),
            scope_roots=tuple(
                (request.root / repository.path).resolve()
                for repository in planned.value.repositories
            ),
        )
        if operation.failure:
            return r[m.Infra.CodegenResult].from_failure(operation)
        batches: list[m.Infra.CodegenPhaseOutcome] = []
        published = self._publish_generation_batches(
            request,
            self._managed_bootstrap_analysis(planned.value),
            policy,
            batches,
            operation.value,
        ).flat_map(
            lambda bootstrap: self._publish_lazy_batch(
                planned.value,
                policy,
                batches,
                operation.value,
            ).map(lambda lazy: (*bootstrap, *lazy)),
        )
        cause = published.exception
        if cause is not None:
            raise cause
        if published.failure:
            return r[m.Infra.CodegenResult].from_failure(published)
        written = published.value
        repaired = (
            r[bool].ok(value=True)
            if self.generation_only
            else self.conform_workspace_beads_routes(request).flat_map(
                lambda _: self._allow_direnv_after_apply(request, written)
            )
        )
        return repaired.flat_map(
            lambda _: self._publish_docs_batches(
                request,
                m.Infra.CodegenResult(plan=planned.value, written_files=written),
                tuple(batches),
                operation.value,
            ),
        )

    def _publish_lazy_batch(
        self,
        plan: m.Infra.CodegenPlan,
        policy: m.Infra.CodegenParticipantPolicy,
        batches: t.MutableSequenceOf[m.Infra.CodegenPhaseOutcome],
        operation: m.Infra.CodegenPhaseOutcome,
    ) -> p.Result[t.VariadicTuple[Path]]:
        """Plan after bootstrap and lease only the next publication batch.

        Returns:
            The written paths, or the original planning or publication failure.

        """
        result_type = r[t.VariadicTuple[Path]]
        lazy = self._lazy_phase(plan.request, plan)
        if lazy.failure:
            return result_type.from_failure(lazy)
        conform_paths = frozenset(file.path for file in plan.files)
        files = tuple(
            file for file in lazy.value.files if file.path not in conform_paths
        )
        if not files:
            current = FlextInfraMiseArtifactsVerification.states_current(
                lazy.value.inputs,
            )
            if current.failure:
                return result_type.from_failure(current)
            if lazy.value.issues or lazy.value.exception is not None:
                return result_type.fail(
                    "\n".join(issue.formatted for issue in lazy.value.issues)
                    or "lazy planning failed",
                    exception=lazy.value.exception,
                )
            return result_type.ok(())
        analysis = lazy.value.model_copy(
            update={"files": files, "inputs": ()},
        )
        return self._publish_generation_batches(
            plan.request,
            analysis,
            policy,
            batches,
            operation,
        )

    def _managed_policy(
        self,
        request: m.Infra.CodegenConformRequest,
    ) -> p.Result[m.Infra.CodegenParticipantPolicy]:
        """Authorize the declared physical generation participants.

        Returns:
            The policy, or its first prerequisite failure.

        """
        result = r[m.Infra.CodegenParticipantPolicy]
        ports = self.ports
        if ports is None:
            return result.fail(
                "complete generation requires the facade-wired docs and "
                "participant policy; "
                "run it through FlextInfra.codegen_conform",
            )
        if not self.generation_only:
            seeded = self._seed_declared_beads_identity(request.root)
            if seeded.failure:
                return result.from_failure(seeded)
        policy = ports.participant_policy(
            request.root,
            initial_workspace=self.initial_workspace,
        )
        if policy.failure:
            return result.from_failure(policy)
        return policy

    def _execute_managed_locked(
        self,
        request: m.Infra.CodegenConformRequest,
        scope_root: Path,
    ) -> p.Result[Path]:
        """Prepare scaffold parents after locked recovery, before source planning.

        Returns:
            The reconciled scope root, or the original preparation failure.

        """
        prepared = self._prepare_scaffold_directories(request)
        if prepared.failure:
            return r[Path].from_failure(prepared)
        return r[Path].ok(scope_root)

    @staticmethod
    def lazy_repository_task(root: Path) -> m.Infra.CodegenPhaseOutcome:
        """Analyze one repository's lazy-init surface in a fleet worker.

        Returns:
            The repository's lazy-init analysis, or its logical failure as data.

        """
        analysis = FlextInfraCodegenLazyInit(
            repository_root=root,
            project_scope_roots=(root,),
        ).plan_files()
        cause = analysis.exception
        if cause is not None:
            raise cause
        if analysis.failure:
            return m.Infra.CodegenPhaseOutcome(
                error=analysis.error or f"lazy-init analysis failed: {root}",
                exception=analysis.exception,
            )
        cause = analysis.value.exception
        if cause is not None:
            raise cause
        return m.Infra.CodegenPhaseOutcome(analysis=analysis.value)

    @staticmethod
    def _lazy_phase(
        request: m.Infra.CodegenConformRequest,
        plan: m.Infra.CodegenPlan,
    ) -> p.Result[m.Infra.CodegenPhaseAnalysis]:
        """Plan each selected repository through its own Rope boundary.

        APPLY captures this analysis before phase publication.
        ADR-014: lazy-init ownership stays inside conform's
        transaction. Lazy-init plans exactly the repositories conform
        rewrites: the selected mutable ``internal_flext`` repositories of
        ``plan``, never a scope-excluded root or a third-party checkout.

        Returns:
            The resulting ``p.Result[m.Infra.CodegenPhaseAnalysis]``.

        """
        files: list[m.Infra.CodegenFilePlan] = []
        inputs: t.MutableMappingKV[Path, m.Cli.AtomicFileState] = {}
        publications: list[m.Infra.LazyInitPlan] = []
        issues: list[m.Infra.Issue] = []
        first_exception: BaseException | None = None
        roots = tuple(
            (request.root / repository.path).resolve()
            for repository in plan.repositories
            if repository.kind is c.Infra.ProjectKind.INTERNAL_FLEXT
        )
        # Each repository analyzes through its own Rope boundary, read-only,
        # so the fleet runs them across worker processes in declaration order.
        outcomes = u.Infra.fleet_map(
            FlextInfraCodegenConformExecuteGenerationMixin.lazy_repository_task,
            roots,
        )
        for root, outcome in zip(roots, outcomes, strict=True):
            if first_exception is None:
                first_exception = outcome.exception
            issues.extend(outcome.issues)
            if outcome.analysis is None:
                if outcome.error:
                    issues.append(
                        m.Infra.Issue(
                            file=str(root),
                            line=0,
                            column=0,
                            code=c.Infra.ToolOutcome.ERROR.value,
                            message=outcome.error,
                        ),
                    )
                continue
            files.extend(outcome.analysis.files)
            if first_exception is None:
                first_exception = outcome.analysis.exception
            issues.extend(outcome.analysis.issues)
            publications.extend(outcome.analysis.publications)
            for state in outcome.analysis.inputs:
                inputs[state.path] = state
        return r[m.Infra.CodegenPhaseAnalysis].ok(
            m.Infra.CodegenPhaseAnalysis(
                phase=c.Infra.CodegenStagedFilePhase.LAZY_INIT,
                files=tuple(files),
                inputs=tuple(inputs[path] for path in sorted(inputs)),
                publications=tuple(publications),
                issues=tuple(issues),
                exception=first_exception,
            ),
        )

    def _prepare_managed_plan(
        self,
        request: m.Infra.CodegenConformRequest,
    ) -> p.Result[m.Infra.CodegenPlan]:
        """Plan consumed sources and retain the Docs planner outside the lease.

        Returns:
            The immutable plan, or the original planning failure.

        """
        u.Cli.header(
            "Code generation" if self.generation_only else "Project conformance"
        )
        u.Cli.info(
            f"stage=plan mode={request.mode} scope={request.scope} "
            f"what={request.what} root={request.root} lease=unheld",
        )
        planned = self.plan(request)
        cause = planned.exception
        if cause is not None:
            raise cause
        if planned.failure:
            return r[m.Infra.CodegenPlan].from_failure(planned)
        plan = planned.value
        if plan.exception is not None:
            raise plan.exception
        if not plan.files and (plan.issues or plan.exception is not None):
            return r[m.Infra.CodegenPlan].fail(
                "\n".join(issue.formatted for issue in plan.issues)
                or "generation planning failed",
                exception=plan.exception,
            )
        owned = tuple(
            repository.name
            for repository in plan.repositories
            if repository.path == Path()
        )
        self.docs_planner = None
        if owned:
            ports = self.ports
            if ports is None:
                return r[m.Infra.CodegenPlan].fail(
                    "docs planning requires the facade-wired planner before effects"
                )
            planner = ports.docs_planner(
                repository_root=request.root,
                projects=owned,
                include_root=True,
            )
            self.docs_planner = planner
        return planned

    @classmethod
    def _managed_bootstrap_analysis(
        cls,
        plan: m.Infra.CodegenPlan,
    ) -> m.Infra.CodegenPhaseAnalysis:
        """Retain completeness failures beside independently publishable plans.

        Returns:
            The batch candidates and first planning cause, before local admission.

        """
        configs = cls.mise_config_plans(plan)
        issues = plan.issues
        exception = plan.exception
        if configs.failure:
            issues = (
                *issues,
                m.Infra.Issue(
                    file=str(plan.request.root),
                    line=0,
                    column=0,
                    code=c.Infra.ToolOutcome.ERROR.value,
                    message=configs.error
                    or "generation configuration plan is incomplete",
                ),
            )
            if exception is None:
                exception = configs.exception
        return m.Infra.CodegenPhaseAnalysis(
            phase=c.Infra.CodegenStagedFilePhase.CONFORM_BOOTSTRAP,
            files=plan.files,
            inputs=(),
            issues=issues,
            exception=exception,
        )

    @classmethod
    def _generation_connections(
        cls,
        files: t.VariadicTuple[m.Infra.CodegenFilePlan],
    ) -> t.MutableMappingKV[Path, set[Path]]:
        """Connect only declared groups and consumed publication destinations.

        Returns:
            Dependency edges between the actual current plans.

        """
        connections = {file.path: set[Path]() for file in files}
        groups: dict[str, Path] = {}
        for file in files:
            dependencies = {source.path for source in file.source_states} | set(
                file.tracking_dependencies
            )
            if file.dependency_group is not None:
                dependencies.add(groups.setdefault(file.dependency_group, file.path))
            for dependency in dependencies & connections.keys():
                connections[file.path].add(dependency)
                connections[dependency].add(file.path)
        cls._generation_election_connections(files, connections)
        return connections

    @staticmethod
    def _generation_candidate_owners(
        files: t.VariadicTuple[m.Infra.CodegenFilePlan],
    ) -> t.MutableMappingKV[Path, set[Path]]:
        """Index only destinations and directory births declared by current plans.

        Returns:
            The output owners that can affect each consumed native candidate.

        """
        owners: dict[Path, set[Path]] = {}
        for file in files:
            directories = (
                file.before.directories
                if isinstance(file.before, m.Cli.AtomicDirectoryChainPlan)
                else ()
            )
            for candidate in (file.path, *directories):
                owners.setdefault(candidate, set()).add(file.path)
        return owners

    @classmethod
    def _generation_election_connections(
        cls,
        files: t.VariadicTuple[m.Infra.CodegenFilePlan],
        connections: t.MutableMappingKV[Path, set[Path]],
    ) -> None:
        """Keep publications affecting consumed native elections in one component."""
        candidates = cls._generation_candidate_owners(files)
        membership: dict[Path, set[Path]] = {}
        for candidate, owners in candidates.items():
            membership.setdefault(candidate.parent, set()).update(owners)
        for file in files:
            queried = {
                directory.root.path / name
                for directory in file.source_directories
                for name, _predicate in directory.queries
            }
            queried.update(
                directory
                for topology in file.source_query_topology
                for directory in topology.directories
            )
            queried.update(
                topology.target / name
                for topology in file.source_query_topology
                for name, _predicate in topology.queries
            )
            listed = {
                directory.root.path
                for directory in file.source_directories
                if directory.membership_queried
            }
            listed.update(
                topology.target
                for topology in file.source_query_topology
                if topology.membership_queried
            )
            dependencies = {
                owner for path in queried for owner in candidates.get(path, ())
            }
            dependencies.update(
                owner for path in listed for owner in membership.get(path, ())
            )
            for dependency in dependencies:
                connections[file.path].add(dependency)
                connections[dependency].add(file.path)

    @classmethod
    def _generation_batches(
        cls,
        files: t.VariadicTuple[m.Infra.CodegenFilePlan],
    ) -> t.VariadicTuple[t.VariadicTuple[m.Infra.CodegenFilePlan]]:
        """Publish dependent effects before one complete no-op observation.

        Returns:
            Whole effect components followed by the remaining no-op plans.

        """
        connections = cls._generation_connections(files)
        positions = {file.path: index for index, file in enumerate(files)}
        by_path = {file.path: file for file in files}
        batches: list[tuple[m.Infra.CodegenFilePlan, ...]] = []
        unchanged: list[m.Infra.CodegenFilePlan] = []
        visited: set[Path] = set()
        for file in files:
            if file.path in visited:
                continue
            component: set[Path] = set()
            pending = {file.path}
            while pending:
                path = pending.pop()
                component.add(path)
                pending.update(connections[path] - component)
            visited.update(component)
            batch = tuple(
                by_path[path] for path in sorted(component, key=positions.__getitem__)
            )
            if any(u.Infra.codegen_file_requires_effect(plan) for plan in batch):
                batches.append(batch)
            else:
                unchanged.extend(batch)
        if unchanged:
            batches.append(tuple(unchanged))
        return tuple(batches)

    def _publish_generation_batches(
        self,
        request: m.Infra.CodegenConformRequest,
        analysis: m.Infra.CodegenPhaseAnalysis,
        policy: m.Infra.CodegenParticipantPolicy,
        receipts: t.MutableSequenceOf[m.Infra.CodegenPhaseOutcome],
        operation: m.Infra.CodegenPhaseOutcome,
    ) -> p.Result[t.VariadicTuple[Path]]:
        """Lease and authenticate each independent batch, preserving first failure.

        Returns:
            Every written path or the first original failure after independent work.

        """
        result_type = r[t.VariadicTuple[Path]]
        if analysis.exception is not None:
            raise analysis.exception
        first_failure = (
            result_type.fail(
                "\n".join(issue.formatted for issue in analysis.issues)
                or "generation planning failed",
                exception=analysis.exception,
            )
            if analysis.issues or analysis.exception is not None
            else None
        )
        written: list[Path] = []
        for files in self._generation_batches(analysis.files):
            published = self._publish_generation_batch(
                request,
                analysis.model_copy(
                    update={"files": files, "issues": (), "exception": None},
                ),
                policy,
                receipts,
            )
            cause = published.exception
            if cause is not None:
                raise cause
            if published.failure:
                if first_failure is None:
                    first_failure = published
            else:
                written.extend(published.value)
        recorded = FlextInfraCodegenTransaction.publish_operation_receipt(
            request,
            tuple(receipts),
            scope_roots=operation.scope_roots,
            operation=operation,
        )
        cause = recorded.exception
        if cause is not None:
            raise cause
        if recorded.failure:
            if first_failure is not None:
                u.Cli.error(
                    f"generation receipt publication failed: {recorded.error}",
                )
                return result_type.from_failure(first_failure)
            return result_type.from_failure(recorded)
        if first_failure is not None:
            return result_type.from_failure(first_failure)
        return result_type.ok(tuple(written))

    def _publish_generation_batch(
        self,
        request: m.Infra.CodegenConformRequest,
        analysis: m.Infra.CodegenPhaseAnalysis,
        policy: m.Infra.CodegenParticipantPolicy,
        receipts: t.MutableSequenceOf[m.Infra.CodegenPhaseOutcome],
    ) -> p.Result[t.VariadicTuple[Path]]:
        """Use the shared journal publisher for one exact dependent component.

        Returns:
            Its published paths or the original admission or consumer failure.

        """
        result_type = r[t.VariadicTuple[Path]]
        inputs = FlextInfraCodegenPreconditions.unique_states(
            tuple(source for file in analysis.files for source in file.source_states),
        )
        if inputs.failure:
            return result_type.from_failure(inputs)
        files = analysis.files
        if len(files) > 1:
            group = f"{analysis.phase}:{files[0].path}"
            files = tuple(
                file.model_copy(update={"dependency_group": group}) for file in files
            )
        analysis = analysis.model_copy(
            update={
                "files": files,
                "inputs": inputs.value,
                "source_directories": tuple(
                    directory for file in files for directory in file.source_directories
                ),
                "source_query_topology": tuple(
                    topology
                    for file in files
                    for topology in file.source_query_topology
                ),
            },
        )
        transaction = FlextInfraCodegenTransaction(
            FlextInfraCodegenMiseArtifacts(repository_root=request.root),
            participant_policy=policy,
            prior_publications=tuple(receipts),
        )
        roots = transaction.capability_roots(
            analysis.phase,
            tuple(dict.fromkeys(file.project for file in analysis.files)),
        )
        changed = tuple(
            file
            for file in analysis.files
            if u.Infra.codegen_file_requires_effect(file)
        )
        validated = any(
            file.path.name
            in {
                c.Infra.MISE_TOML_FILENAME,
                c.Infra.PYPROJECT_FILENAME,
            }
            for file in analysis.files
        )
        publication = m.Infra.CodegenPhasePublicationPolicy(
            directories=tuple(
                sorted({
                    file.path.parent
                    for file in changed
                    if not file.path.parent.is_dir()
                })
            ),
            staged_validator=(
                partial(self._validate_generation_stage, plans=analysis.files)
                if validated
                else None
            ),
        )
        return transaction.run_files_locked(
            roots,
            lambda scope_root: transaction.publish_file_phase_locked(
                scope_root,
                roots,
                analysis,
                publication,
                publication_receipts=receipts,
            ),
        )

    @classmethod
    def _validate_generation_stage(
        cls,
        session: m.Infra.CodegenTransactionSession,
        publications: t.VariadicTuple[m.Infra.CodegenStagedFile],
        *,
        plans: t.VariadicTuple[m.Infra.CodegenFilePlan],
    ) -> p.Result[m.Infra.CodegenTransactionSession]:
        """Compose existing Mise and Pyproject consumers over exact staged subsets.

        Returns:
            The unchanged cursor or the first native consumer failure.

        """
        for plan in plans:
            if plan.path.name != c.Infra.MISE_TOML_FILENAME:
                continue
            checked = cls._validate_mise_stage(
                session,
                tuple(item for item in publications if item.before.path == plan.path),
                plans=(plan,),
            )
            if checked.failure:
                return checked
            session = checked.value
        pyprojects = tuple(
            plan for plan in plans if plan.path.name == c.Infra.PYPROJECT_FILENAME
        )
        if pyprojects:
            paths = {plan.path for plan in pyprojects}
            return cls._validate_pyproject_stage(
                session,
                tuple(item for item in publications if item.before.path in paths),
                plans=pyprojects,
            )
        return r[m.Infra.CodegenTransactionSession].ok(session)

    def _publish_docs_batches(
        self,
        request: m.Infra.CodegenConformRequest,
        result: m.Infra.CodegenResult,
        batches: t.VariadicTuple[m.Infra.CodegenPhaseOutcome],
        operation: m.Infra.CodegenPhaseOutcome,
    ) -> p.Result[m.Infra.CodegenResult]:
        """Publish only invocation-owned docs after the managed batch releases.

        Returns:
            The resulting ``p.Result[m.Infra.CodegenResult]``.

        """
        if result.plan is None:
            return r[m.Infra.CodegenResult].fail(
                "docs publication requires its actual generation plan",
            )
        owned = tuple(
            repository.name
            for repository in result.plan.repositories
            if repository.path == Path()
        )
        written = list(result.written_files)
        receipts = list(batches)
        if owned:
            docs_generator = self.docs_planner
            if docs_generator is None:
                return r[m.Infra.CodegenResult].fail(
                    "docs publication lacks its original planner"
                )
            for prepared in docs_generator.prepare_batches(
                publication_receipts=receipts,
            ):
                if prepared.failure:
                    return r[m.Infra.CodegenResult].from_failure(prepared)
                published = docs_generator.publish_batch(
                    prepared.value,
                    publication_receipts=receipts,
                )
                if published.failure:
                    return r[m.Infra.CodegenResult].from_failure(published)
                written.extend(
                    Path(item.path)
                    for report in published.value
                    for item in report.items
                    if item.written
                )
        qualified = FlextInfraCodegenTransaction.publish_operation_receipt(
            request,
            tuple(receipts),
            scope_roots=tuple(
                (request.root / repository.path).resolve()
                for repository in result.plan.repositories
            ),
            operation=operation,
            completed=True,
        )
        if qualified.failure:
            return r[m.Infra.CodegenResult].from_failure(qualified)
        return r[m.Infra.CodegenResult].ok(
            result.model_copy(
                update={
                    "written_files": tuple(written),
                    "publication_receipt": qualified.value,
                },
            ),
        )

    @staticmethod
    def _allow_direnv_after_apply(
        request: m.Infra.CodegenConformRequest,
        written_files: t.VariadicTuple[Path],
    ) -> p.Result[bool]:
        """Heal the direnv allow for every ``.envrc`` this apply published.

        ``make setup`` authorizes the rendered ``.envrc`` once; a later conform
        apply legitimately rewrites it (content-hash changes) and every
        subsequent command blocks on direnv's stale-allow warning. The
        generator owns the file it renders, so apply heals the allow itself
        instead of leaving every environment stale until the operator re-runs
        setup.

        Returns:
            The resulting ``p.Result[bool]``.

        """
        if (
            c.Infra.CodegenConformMode(request.mode)
            is not c.Infra.CodegenConformMode.APPLY
        ):
            return r[bool].ok(value=False)
        roots = {
            path.expanduser().resolve().parent
            for path in written_files
            if path.name == c.Infra.ENVRC_FILENAME
        }
        if not roots:
            return r[bool].ok(value=False)
        for root in sorted(roots):
            result = u.Cli.run_raw(
                (c.Infra.CLI_DIRENV, "allow", str(root)),
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
        return r[bool].ok(value=True)


__all__: list[str] = ["FlextInfraCodegenConformExecuteGenerationMixin"]
