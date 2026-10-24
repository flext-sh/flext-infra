"""Transactional publication of declared projection plans.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import os
from collections.abc import Callable
from functools import partial
from pathlib import Path
from typing import Self, override

from flext_infra import c, m, p, r, t, u

from flext_infra.codegen._conform.execute_directed import (
    FlextInfraCodegenConformExecuteDirected,
)
from flext_infra.workspace import FlextInfraWorkspaceDetector


class FlextInfraCodegenConformExecute(FlextInfraCodegenConformExecuteDirected):
    """Transactional publication of declared projection plans.

    The chain is linear in dependency order, so execution statically inherits
    everything it calls: bootstrap (service root, request state) <- gitignore
    <- docs ownership <- file plans <- pyproject policy <-
    context render <- artifact render <- existing plan <- scaffold plan <- plan
    <- execute scaffold <- directed file publication <- execute.
    """

    _generation_issues: t.MutableSequenceOf[m.Infra.Issue] = m.PrivateAttr(
        default_factory=list[m.Infra.Issue],
    )

    @classmethod
    def from_request(
        cls: type[Self],
        request: m.Infra.CodegenGenerateRequest,
        *,
        execution_context: p.Infra.CodegenExecutionContext | None,
        repository_root: t.Infra.Path | None = None,
    ) -> p.Result[FlextInfraCodegenConformExecute]:
        """Bind one validated request to the native projection executor.

        The request is retained by reference. The caller supplies runtime seeds
        and ports; the destination owns its physical identity and scaffold facts.

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
            observed = FlextInfraWorkspaceDetector.load_workspace_spec(
                root, inputs=inputs.value
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
        """Admit the public request once, then publish its native instance.

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
        """Publish only the projections selected by the bound request.

        Returns:
            The native projection outcome.

        Raises:
            ValueError: The planner has no bound execution request.

        """
        request = self.state.request
        if request is None:
            msg = "projection execution requires a bound generation request"
            raise ValueError(msg)
        u.Cli.info(
            f"operation=generate stage=inputs root={request.root} "
            f"scope={request.scope} surface={request.what} pid={os.getpid()}"
        )
        if request.what in c.Infra.FILE_ONLY_SURFACES:
            return self._execute_lazy_init(request)
        if request.what is c.Infra.CodegenConformSurface.ALL:
            return self.execute_managed(request)
        return self.execute_plan(request)

    def _plan_or_report(
        self,
        request: p.Infra.CodegenGenerateRequest,
    ) -> p.Result[m.Infra.CodegenPlan]:
        """Plan the surface, reporting an empty plan with planning failures.

        Returns:
            The resulting plan, or a failure carrying any planning issues and
            the original planning exception by identity.

        """
        planned = self.plan(request)
        if planned.failure:
            return r[m.Infra.CodegenPlan].from_failure(planned)
        plan = planned.value
        if not plan.files and (plan.issues or plan.exception is not None):
            return r[m.Infra.CodegenPlan].fail(
                "\n".join(issue.formatted for issue in plan.issues)
                or "generation planning failed",
                exception=plan.exception,
            )
        return planned

    def execute_plan(
        self,
        request: p.Infra.CodegenGenerateRequest,
    ) -> p.Result[p.Infra.CodegenResult]:
        """Execute a non-toolchain projection without widening its scope.

        Returns:
            The resulting ``p.Result[p.Infra.CodegenResult]``.

        """
        if request.what is c.Infra.CodegenConformSurface.DEPENDENCIES:
            return r[p.Infra.CodegenResult].fail(
                "partial codegen apply is prohibited; use the complete all surface",
            )
        u.Cli.header("Code generation")
        u.Cli.info(
            f"stage=plan scope={request.scope} what={request.what} root={request.root}",
        )
        planned = self._plan_or_report(request)
        if planned.failure:
            return r[p.Infra.CodegenResult].from_failure(planned)
        plan = planned.value
        surface = request.what
        if surface not in c.Infra.PARTIAL_PLAN_SURFACES:
            return r[p.Infra.CodegenResult].fail(
                "partial codegen apply is prohibited; use the complete all surface",
            )
        mise_owner = FlextInfraCodegenMiseArtifacts(repository_root=request.root)
        transaction = FlextInfraCodegenTransaction(mise_owner)
        root = request.root.expanduser().resolve()
        roots = transaction.capability_roots(
            "bootstrap",
            tuple(
                (root / repository.path).resolve() for repository in plan.repositories
            ),
        )
        receipts: list[m.Infra.CodegenPhaseOutcome] = []

        def publish(scope_root: Path) -> p.Result[t.VariadicTuple[Path]]:
            return self._publish_bootstrap_phase(
                request,
                plan,
                transaction,
                (scope_root, roots),
            )

        def complete(
            written_files: t.VariadicTuple[Path],
        ) -> p.Result[p.Infra.CodegenResult]:
            receipt = transaction.publish_operation_receipt(
                request,
                tuple(receipts),
                publication=m.Infra.CodegenPhaseOutcome(
                    scope_roots=tuple(roots.values()),
                    completed=True,
                ),
            )
            if receipt.failure:
                return r[p.Infra.CodegenResult].from_failure(receipt)
            aggregate_failure = self._aggregate_planning_failure(plan)
            if aggregate_failure is not None:
                return aggregate_failure
            payload: p.Infra.CodegenResult = m.Infra.CodegenResult(
                plan=plan,
                written_files=written_files,
                publication_receipt=receipt.value,
            )
            return r[p.Infra.CodegenResult].ok(payload)

        return transaction.run_files_locked(roots, publish).flat_map(complete)

    @staticmethod
    def _aggregate_planning_failure(
        plan: m.Infra.CodegenPlan,
    ) -> p.Result[p.Infra.CodegenResult] | None:
        """Fail the aggregate carrying the first member's original exception.

        Published valid siblings keep their effects; the aggregate still
        fails carrying the original planning exception by identity, never a
        re-wrapped cause.

        Returns:
            The aggregate failure result, or ``None`` when every member
            conformed.

        """
        if plan.exception is None:
            return None
        return r[p.Infra.CodegenResult].fail(
            "\n".join(issue.formatted for issue in plan.issues)
            or "generation planning failed",
            exception=plan.exception,
        )

    def _publish_bootstrap_phase(
        self,
        request: p.Infra.CodegenGenerateRequest,
        plan: m.Infra.CodegenPlan,
        transaction: FlextInfraCodegenTransaction,
        publication_scope: t.Pair[Path, t.MappingKV[str, Path]],
    ) -> p.Result[t.VariadicTuple[Path]]:
        """Authorize the surface contract, then publish its changed files.

        Returns:
            The resulting ``p.Result[t.VariadicTuple[Path]]`` with the written
            bootstrap files.

        """
        scope_root, roots = publication_scope
        surface = request.what
        expected = self._bootstrap_expected_surface(request, plan, surface)
        if expected.failure:
            return r[t.VariadicTuple[Path]].from_failure(expected)
        expected_paths, expected_owners = expected.value
        planned_paths = {file.path for file in plan.files}
        failed_paths = {Path(issue.file).resolve() for issue in plan.issues}
        unaccounted = {
            path
            for path in expected_paths - planned_paths - failed_paths
            if expected_owners[path] not in failed_paths
        }
        if unaccounted or planned_paths - expected_paths:
            return r[t.VariadicTuple[Path]].fail(
                f"bootstrap plan does not own the declared destinations for {surface}: "
                f"missing={sorted(map(str, unaccounted))}; "
                f"unexpected={sorted(map(str, planned_paths - expected_paths))}",
            )
        changed = tuple(
            file for file in plan.files if u.Infra.codegen_file_requires_effect(file)
        )
        if any(
            file.desired_content is None or file.desired_mode is None
            for file in changed
        ):
            return r[t.VariadicTuple[Path]].fail(
                f"bootstrap cannot delete a declared destination for {surface}",
            )
        inputs = {
            state.path: state for file in plan.files for state in file.source_states
        }
        analysis = m.Infra.CodegenPhaseAnalysis(
            phase=c.Infra.CodegenStagedFilePhase.CONFORM_BOOTSTRAP,
            files=plan.files,
            inputs=tuple(inputs.values()),
            issues=plan.issues,
            exception=plan.exception,
        )
        return transaction.publish_file_phase_locked(
            scope_root,
            roots,
            analysis,
            m.Infra.CodegenPhasePublicationPolicy(
                directories=tuple(
                    sorted({
                        file.path.parent
                        for file in changed
                        if not file.path.parent.is_dir()
                    }),
                ),
                staged_validator=(
                    partial(self._validate_mise_stage, plans=plan.files)
                    if surface is c.Infra.CodegenConformSurface.MISE_CONFIG
                    else partial(self._validate_pyproject_stage, plans=plan.files)
                    if surface is c.Infra.CodegenConformSurface.PYPROJECT
                    else None
                ),
            ),
        )

    def _bootstrap_expected_surface(
        self,
        request: p.Infra.CodegenGenerateRequest,
        plan: m.Infra.CodegenPlan,
        surface: c.Infra.CodegenConformSurface,
    ) -> p.Result[t.Pair[set[Path], t.MutableMappingKV[Path, Path]]]:
        """Resolve the bootstrap surface's expected paths and their owning roots.

        A repository whose codegen inputs were already rejected during
        planning owns no expected destinations: its failure is recorded in
        the plan's issues, and aborting here would discard the valid
        siblings' publication instead of letting the aggregate carry the
        original cause.

        Returns:
            The expected destination paths paired with each path's owning
            repository root.

        """
        result_type = r[t.Pair[set[Path], t.MutableMappingKV[Path, Path]]]
        rejected_roots = {Path(issue.file).resolve() for issue in plan.issues}
        expected_owners: t.MutableMappingKV[Path, Path] = {}
        for repository in plan.repositories:
            repository_root = (
                request.root.expanduser().resolve() / repository.path
            ).resolve()
            inputs = u.Infra.load_codegen_inputs(repository_root)
            if inputs.failure:
                if repository_root not in rejected_roots:
                    return result_type.from_failure(inputs)
                continue
            spec = inputs.value.spec
            declared = self.surface_contract(surface, codegen=spec).destinations
            destinations = (
                spec.templates.required_destinations(declared)
                if declared is not None
                else frozenset[str]()
            )
            if not destinations:
                return result_type.fail(
                    f"bootstrap requires declared destinations for {surface}",
                )
            expected_owners.update(
                {
                    (repository_root / path).resolve(): repository_root
                    for path in destinations
                },
            )
        expected_paths = set(expected_owners)
        return result_type.ok(
            (expected_paths, expected_owners),
        )

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

    def _publish_documents_stage(
        self,
        request: p.Infra.CodegenGenerateRequest,
        planned: m.Infra.CodegenPlan,
        batches: t.MutableSequenceOf[m.Infra.CodegenPhaseOutcome],
        *,
        published: p.Result[t.VariadicTuple[Path]],
        written: t.VariadicTuple[Path],
    ) -> p.Result[bool]:
        """Publish documents unless a new scaffold failed before its metadata.

        Returns:
            The document stage outcome, or the original publication failure when
            the scaffold never wrote its project metadata.

        """
        if (
            self.state.initial_workspace is not None
            and published.failure
            and request.root.expanduser().resolve() / c.PYPROJECT_FILENAME
            not in written
        ):
            return r[bool].from_failure(published)
        return self._settle_generation_stage(
            lambda: self._publish_docs_batches(planned, batches),
        )

    def execute_managed(
        self,
        request: p.Infra.CodegenGenerateRequest,
        *,
        after_publication: tuple[
            Callable[[t.VariadicTuple[Path]], p.Result[bool]], ...
        ] = (),
    ) -> p.Result[p.Infra.CodegenResult]:
        """Plan outside the lease and publish through locked generation phases.

        Returns:
            The resulting ``p.Result[p.Infra.CodegenResult]``.

        """
        configured = self._managed_policy(request)
        if configured.failure:
            return r[p.Infra.CodegenResult].from_failure(configured)
        transaction = FlextInfraCodegenTransaction(
            FlextInfraCodegenMiseArtifacts(repository_root=request.root),
            participant_policy=configured.value,
        )
        planned = (
            transaction
            .prepare_source_controlplanes(
                tuple(root.target for root in configured.value.roots),
            )
            .flat_map(
                lambda _: transaction.run_locked(
                    prepare=True,
                    operation=lambda scope_root: self._execute_managed_locked(
                        request,
                        scope_root,
                    ),
                ),
            )
            .flat_map(lambda _: self._prepare_managed_plan(request))
        )
        cause = planned.exception
        if cause is not None:
            raise cause
        if planned.failure:
            return r[p.Infra.CodegenResult].from_failure(planned)
        operation = transaction.publish_operation_receipt(
            request,
            (),
            publication=m.Infra.CodegenPhaseOutcome(
                scope_roots=tuple(
                    (request.root / repository.path).resolve()
                    for repository in planned.value.repositories
                ),
            ),
        )
        if operation.failure:
            return r[p.Infra.CodegenResult].from_failure(operation)
        batches: list[m.Infra.CodegenPhaseOutcome] = []
        self._generation_issues = list(planned.value.issues)
        published = self._settle_generation_stage(
            lambda: self._publish_generation_batches(
                request,
                self._managed_bootstrap_analysis(planned.value),
                configured.value,
                batches,
                operation.value,
            ),
        )
        written = tuple(path for batch in batches for path in batch.written_files)
        repaired = tuple(
            self._settle_generation_stage(partial(operation, written))
            for operation in after_publication
        )
        documents = self._publish_documents_stage(
            request, planned.value, batches, published=published, written=written
        )
        failures: list[p.FailureLike] = [
            item for item in (published, *repaired, documents) if item.failure
        ]
        self._generation_issues.extend(
            m.Infra.Issue(
                file=str(request.root),
                line=0,
                column=0,
                code=c.Infra.ToolOutcome.ERROR.value,
                message=item.error or "generation phase failed",
            )
            for item in failures
        )
        first_exception = planned.value.exception or (
            failures[0].exception if failures else None
        )
        completed = self._settle_generation_stage(
            lambda: FlextInfraCodegenTransaction.publish_operation_receipt(
                request,
                tuple(batches),
                publication=m.Infra.CodegenPhaseOutcome(
                    scope_roots=operation.value.scope_roots,
                    completed=not failures,
                    issues=tuple(self._generation_issues),
                    exception=first_exception,
                ),
                operation=operation.value,
            ),
        )
        if completed.failure:
            u.Cli.error(f"generation receipt publication failed: {completed.error}")
            had_failure = bool(failures)
            failures.append(completed)
            if first_exception is None and not had_failure:
                first_exception = completed.exception
            elif first_exception is not None:
                first_exception.add_note(
                    f"generation receipt publication also failed: {completed.error}"
                )
        if first_exception is not None:
            raise first_exception
        if failures:
            return r[p.Infra.CodegenResult].from_failure(failures[0])
        payload: p.Infra.CodegenResult = m.Infra.CodegenResult(
            plan=planned.value,
            # Managed projection delta is distinct from the final evidence
            # phase; the native receipt retains every physical effect.
            written_files=tuple(
                path for batch in batches for path in batch.written_files
            ),
            publication_receipt=completed.value,
        )
        return r[p.Infra.CodegenResult].ok(payload)

    @staticmethod
    def _settle_generation_stage[T](
        operation: Callable[[], p.Result[T]],
    ) -> p.Result[T]:
        """Retain a native cause until all independent publications settle.

        Returns:
            The original result or a failure retaining the native exception.

        """
        runtime_errors: tuple[type[Exception], ...] = (OSError, *c.EXC_BROAD_RUNTIME)
        try:
            return operation()
        except runtime_errors as exc:
            return r[T].fail(str(exc), exception=exc)

    def _managed_policy(
        self,
        request: p.Infra.CodegenGenerateRequest,
    ) -> p.Result[p.Infra.CodegenParticipantPolicy]:
        """Authorize the declared physical generation participants.

        Returns:
            The policy, or its first prerequisite failure.

        """
        result = r[p.Infra.CodegenParticipantPolicy]
        ports = self.state.ports
        if ports is None:
            return result.fail(
                "complete generation requires the facade-wired docs and "
                "participant policy; "
                "run it through FlextInfra.codegen_generate",
            )
        policy = ports.participant_policy(
            request.root,
            initial_workspace=self.state.initial_workspace,
        )
        if policy.failure:
            return result.from_failure(policy)
        return policy

    def _execute_managed_locked(
        self,
        request: p.Infra.CodegenGenerateRequest,
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

    def _prepare_managed_plan(
        self,
        request: p.Infra.CodegenGenerateRequest,
    ) -> p.Result[m.Infra.CodegenPlan]:
        """Plan consumed sources and retain the Docs planner outside the lease.

        Returns:
            The immutable plan, or the original planning failure.

        """
        u.Cli.header("Code generation")
        u.Cli.info(
            f"stage=plan scope={request.scope} "
            f"what={request.what} root={request.root} lease=unheld",
        )
        planned = self.plan(request)
        cause = planned.exception
        if cause is not None:
            raise cause
        if planned.failure:
            return r[m.Infra.CodegenPlan].from_failure(planned)
        plan = planned.value
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
        self.state.docs_planner = None
        if owned:
            ports = self.state.ports
            if ports is None:
                return r[m.Infra.CodegenPlan].fail(
                    "docs planning requires the facade-wired planner before effects"
                )
            planner = ports.docs_planner(
                repository_root=request.root,
                projects=owned,
                include_root=True,
            )
            self.state.docs_planner = planner
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
            failed_targets=plan.failed_targets,
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
        effects = {
            file.path for file in files if u.Infra.codegen_file_requires_effect(file)
        }
        groups: t.MutableMappingKV[str, Path] = {}
        for file in files:
            dependencies = {source.path for source in file.source_states} & effects
            dependencies.update(set(file.tracking_dependencies) & connections.keys())
            if file.dependency_group is not None:
                dependencies.add(groups.setdefault(file.dependency_group, file.path))
            for dependency in dependencies:
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
        owners: t.MutableMappingKV[Path, set[Path]] = {}
        for file in files:
            if not u.Infra.codegen_file_requires_effect(file):
                continue
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
        membership: t.MutableMappingKV[Path, set[Path]] = {}
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
                if directory.membership_queried or directory.membership_queries
            }
            listed.update(
                topology.target
                for topology in file.source_query_topology
                if topology.membership_queried or topology.membership_queries
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
        """Publish effect components before their independent no-op observations.

        Returns:
            Whole effect components followed by the unchanged components.

        """
        connections = cls._generation_connections(files)
        positions = {file.path: index for index, file in enumerate(files)}
        by_path = {file.path: file for file in files}
        batches: list[tuple[m.Infra.CodegenFilePlan, ...]] = []
        unchanged: list[t.VariadicTuple[m.Infra.CodegenFilePlan]] = []
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
                unchanged.append(batch)
        batches.extend(unchanged)
        return tuple(batches)

    def _publish_generation_batches(
        self,
        request: p.Infra.CodegenGenerateRequest,
        analysis: m.Infra.CodegenPhaseAnalysis,
        policy: p.Infra.CodegenParticipantPolicy,
        receipts: t.MutableSequenceOf[m.Infra.CodegenPhaseOutcome],
        operation: m.Infra.CodegenPhaseOutcome,
    ) -> p.Result[t.VariadicTuple[Path]]:
        """Lease and authenticate each independent batch, preserving first failure.

        Returns:
            Every written path or the first original failure after independent work.

        """
        result_type = r[t.VariadicTuple[Path]]
        failures = (
            [
                result_type.fail(
                    "\n".join(issue.formatted for issue in analysis.issues)
                    or "generation planning failed",
                    exception=analysis.exception,
                ),
            ]
            if analysis.issues or analysis.exception is not None
            else []
        )
        written: list[Path] = []
        issues = list(analysis.issues)
        for files in self._generation_batches(analysis.files):
            published = self._settle_generation_stage(
                partial(
                    self._publish_generation_batch,
                    request,
                    analysis.model_copy(
                        update={"files": files, "issues": (), "exception": None},
                    ),
                    policy,
                    receipts,
                ),
            )
            if published.failure:
                failures.append(published)
                issues.extend(
                    m.Infra.Issue(
                        file=str(file.path),
                        line=0,
                        column=0,
                        code=c.Infra.ToolOutcome.ERROR.value,
                        message=published.error or "generation publication failed",
                    )
                    for file in files
                )
            else:
                written.extend(published.value)
        self._generation_issues.extend(
            issue for issue in issues if issue not in self._generation_issues
        )
        first_exception = next(
            (item.exception for item in failures if item.exception is not None),
            None,
        )
        recorded = self._settle_generation_stage(
            partial(
                FlextInfraCodegenTransaction.publish_operation_receipt,
                request,
                tuple(receipts),
                publication=m.Infra.CodegenPhaseOutcome(
                    scope_roots=operation.scope_roots,
                    issues=tuple(self._generation_issues),
                    exception=first_exception,
                ),
                operation=operation,
            ),
        )
        if recorded.failure:
            if failures:
                u.Cli.error(
                    f"generation receipt publication failed: {recorded.error}",
                )
            failures.append(result_type.from_failure(recorded))
            if first_exception is None:
                first_exception = recorded.exception
        first_failure = next(iter(failures), None)
        if first_failure is not None:
            return result_type.fail(
                first_failure.error,
                error_code=first_failure.error_code,
                error_data=first_failure.error_data,
                exception=first_exception,
            )
        return result_type.ok(tuple(written))

    def _publish_generation_batch(
        self,
        request: p.Infra.CodegenGenerateRequest,
        analysis: m.Infra.CodegenPhaseAnalysis,
        policy: p.Infra.CodegenParticipantPolicy,
        receipts: t.MutableSequenceOf[m.Infra.CodegenPhaseOutcome],
    ) -> p.Result[t.VariadicTuple[Path]]:
        """Use the shared journal publisher for one exact dependent component.

        Returns:
            Its published paths or the original admission or consumer failure.

        """
        result_type = r[t.VariadicTuple[Path]]
        current_inputs = FlextInfraMiseArtifactsVerification.publication_input_states(
            tuple(source for file in analysis.files for source in file.source_states),
            tuple(receipts),
        )
        if current_inputs.failure:
            return result_type.from_failure(current_inputs)
        by_path = {state.path: state for state in current_inputs.value}
        prepared = FlextInfraCodegenStaging.prepare_python_plans(
            request.root,
            tuple(file for file in analysis.files),
            prepare=u.Infra.normalize_source_plan,
        )
        if prepared.failure:
            return result_type.from_failure(prepared)
        analysis = analysis.model_copy(update={"files": prepared.value})
        inputs = u.Infra.unique_states(
            tuple(source for file in analysis.files for source in file.source_states),
        )
        if inputs.failure:
            return result_type.from_failure(inputs)
        files = analysis.files
        if len(files) > 1:
            group = f"{analysis.phase}:{files[0].path}"
            files = tuple(file for file in files)
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
        publication = m.Infra.CodegenPhasePublicationPolicy(
            directories=tuple(
                sorted({
                    file.path.parent
                    for file in changed
                    if not file.path.parent.is_dir()
                })
            ),
            staged_validator=partial(
                self._validate_generation_stage,
                plans=analysis.files,
                workspace=request.root,
                runtime_root=(
                    u.Infra.runtime_environment_dir(self.state.repository_root).parent
                    if self.state.initial_workspace is not None
                    else None
                ),
            ),
        )
        return inputs.flat_map(
            lambda _: transaction.run_files_locked(
                roots,
                lambda scope_root: transaction.publish_file_phase_locked(
                    scope_root,
                    roots,
                    analysis,
                    publication,
                ),
            ),
        )

    @classmethod
    def _validate_generation_stage(
        cls,
        session: m.Infra.CodegenTransactionSession,
        publications: t.VariadicTuple[m.Infra.CodegenStagedFile],
        *,
        plans: t.VariadicTuple[m.Infra.CodegenFilePlan],
        workspace: Path,
        runtime_root: Path | None = None,
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
            checked = cls._validate_pyproject_stage(
                session,
                tuple(item for item in publications if item.before.path in paths),
                plans=pyprojects,
            )
            if checked.failure:
                return checked
            session = checked.value
        return FlextInfraCodegenStaging.validate_python_plans(
            session,
            publications,
            plans=plans,
            runtime=m.Infra.CodegenSourceRuntime(
                workspace=workspace,
                runtime_root=runtime_root,
            ),
        )

    def _publish_docs_batches(
        self,
        plan: m.Infra.CodegenPlan,
        receipts: t.MutableSequenceOf[m.Infra.CodegenPhaseOutcome],
    ) -> p.Result[bool]:
        """Publish only invocation-owned docs after the managed batch releases.

        Returns:
            Whether every documentation component settled successfully.

        """
        if not any(repository.path == Path() for repository in plan.repositories):
            return r[bool].ok(value=True)
        docs_generator = self.state.docs_planner
        if docs_generator is None:
            return r[bool].fail("docs publication lacks its original planner")
        failures: list[p.FailureLike] = []
        runtime_errors: tuple[type[Exception], ...] = (OSError, *c.EXC_BROAD_RUNTIME)
        try:
            for prepared in docs_generator.prepare_batches():
                published = prepared.flat_map(
                    lambda bundle: self._settle_generation_stage(
                        partial(
                            docs_generator.publish_batch,
                            bundle,
                        ),
                    ),
                )
                if published.failure:
                    failures.append(published)
        except runtime_errors as exc:
            failures.append(r[bool].fail(str(exc), exception=exc))
        self._generation_issues.extend(
            m.Infra.Issue(
                file=str(plan.request.root),
                line=0,
                column=0,
                code=c.Infra.ToolOutcome.ERROR.value,
                message=item.error or "documentation publication failed",
            )
            for item in failures
        )
        first_failure = next(iter(failures), None)
        first_exception = next(
            (item.exception for item in failures if item.exception is not None),
            None,
        )
        if first_failure is not None:
            return r[bool].fail(
                first_failure.error,
                error_code=first_failure.error_code,
                error_data=first_failure.error_data,
                exception=first_exception,
            )
        return r[bool].ok(value=True)


__all__: list[str] = ["FlextInfraCodegenConformExecute"]
