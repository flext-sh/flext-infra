"""Transactional execution of conformance plans.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Callable
from functools import partial
from pathlib import Path
from typing import Self, override

from flext_infra import FlextInfraConfig, c, config, m, p, r, t, u
from flext_infra.codegen import (
    FlextInfraCodegenLazyInit,
    FlextInfraCodegenMiseArtifacts,
    FlextInfraCodegenPreconditions,
    FlextInfraCodegenStaging,
    FlextInfraCodegenTransaction,
    FlextInfraMiseArtifactsVerification,
)
from flext_infra.codegen._conform import FlextInfraCodegenConformExecuteDirected
from flext_infra.workspace import FlextInfraWorkspaceNativeReference


class FlextInfraCodegenConformExecute(FlextInfraCodegenConformExecuteDirected):
    """Transactional execution of conformance plans.

    The chain is linear in dependency order, so execution statically inherits
    everything it calls: bootstrap (service root, request state) <- gitignore
    <- docs ownership <- beads routes <- file plans <- pyproject policy <-
    context render <- artifact render <- existing plan <- scaffold plan <- plan
    <- execute scaffold <- directed file publication <- execute.
    """

    _generation_issues: t.MutableSequenceOf[m.Infra.Issue] = m.PrivateAttr(
        default_factory=list,
    )

    @classmethod
    def generate_request(
        cls: type[Self],
        request: p.Infra.CodegenGenerateRequest,
        *,
        execution_context: p.Infra.CodegenExecutionContext,
    ) -> p.Result[p.Infra.CodegenResult]:
        """Publish declared projections through the shared planner and publisher.

        Returns:
            The generation result without repairing authored declarations.

        """
        return cls.execute_request(
            m.Infra.CodegenConformRequest(
                root=request.root,
                what=request.what,
                scope=request.scope,
                module=request.module,
                mode=c.Infra.CodegenConformMode.APPLY,
            ),
            execution_context=execution_context,
            generation_only=True,
        )

    @classmethod
    def execute_request(
        cls: type[Self],
        request: p.Infra.CodegenConformRequest,
        initial_workspace: p.Infra.WorkspaceSpec | None = None,
        *,
        execution_context: p.Infra.CodegenExecutionContext | None,
        generation_only: bool = False,
        repository_root: t.Infra.Path | None = None,
    ) -> p.Result[p.Infra.CodegenResult]:
        """Validate structural inputs once and execute with the facade-wired ports.

        ``execution_context`` is required at every call: the complete surface
        consumes its bound ports, while a direct single-file invocation declares
        the absence of caller runtime seeds and ports explicitly with ``None``.
        An explicit ``repository_root`` owns generation tools while
        ``request.root`` remains the destination of every planned effect.
        The caller's actual settings and context are constructor seeds, not a
        copied private runtime or a promise to inherit its container.

        Returns:
            The generation or verified observation outcome.

        """
        validated_request = m.Infra.CodegenConformRequest.model_validate(
            request,
            from_attributes=True,
        )
        validated_workspace = (
            None
            if initial_workspace is None
            else m.Infra.WorkspaceSpec.model_validate(
                initial_workspace,
                from_attributes=True,
            )
        )
        if validated_request.mode is c.Infra.CodegenConformMode.CHECK:
            with FlextInfraWorkspaceNativeReference.compilation_scope():
                return cls._observe_publication(validated_request)
        ports = (
            None
            if execution_context is None
            else execution_context.codegen_conform_collaborators()
        )
        runtime_settings = (
            None if execution_context is None else execution_context.settings
        )
        initial_context = (
            None if execution_context is None else execution_context.context
        )
        if validated_request.what is c.Infra.CodegenConformSurface.DEPENDENCIES:
            return cls(
                repository_root=validated_request.root,
                state=m.Infra.CodegenConformState(
                    repository_root=validated_request.root,
                    ports=ports,
                    generation_only=generation_only,
                ),
                runtime_settings=runtime_settings,
                initial_context=initial_context,
            ).execute_plan(validated_request)
        root = validated_request.root.expanduser().resolve()
        operation = "generate" if generation_only else "conform"
        u.Cli.info(
            f"operation={operation} stage=inputs root={root} "
            f"scope={validated_request.scope} surface={validated_request.what}"
        )
        prelude = cls._validated_request_prelude(root, validated_workspace)
        if prelude.failure:
            return r[p.Infra.CodegenResult].from_failure(prelude)
        if validated_workspace is not None and not root.is_dir():
            created = cls._bootstrap_request_root(root)
            if created.failure:
                return r[p.Infra.CodegenResult].from_failure(created)
        if validated_workspace is not None and not (root / c.Infra.GIT_DIR).exists():
            initialized = cls._initialize_request_git(root, validated_workspace)
            if initialized.failure:
                return r[p.Infra.CodegenResult].from_failure(initialized)
        generation_root = (
            root if repository_root is None else repository_root.expanduser().resolve()
        )
        service = cls(
            repository_root=generation_root,
            state=m.Infra.CodegenConformState(
                repository_root=generation_root,
                request=validated_request,
                initial_workspace=validated_workspace,
                ports=ports,
                generation_only=generation_only,
            ),
            runtime_settings=runtime_settings,
            initial_context=initial_context,
        )
        return service.execute()

    @staticmethod
    def _validated_request_prelude(
        root: Path,
        initial_workspace: m.Infra.WorkspaceSpec | None,
    ) -> p.Result[bool]:
        """Validate the scaffold provenance and the declared integration branch.

        The project's declared scaffold source is validated before any
        filesystem effect: a silent acceptance would materialize a whole tree
        whose declared provenance was never a direct Git requirement, and the
        declaration is the scaffold's provenance input, not decoration. The
        supplied WorkspaceSpec already owns the declared integration branch;
        require it before materialization instead of a second divergent input.

        Returns:
            The resulting ``p.Result[bool]``.

        """
        if initial_workspace is None:
            return r[bool].ok(value=True)
        if not (root / c.PYPROJECT_FILENAME).exists():
            source = FlextInfraCodegenConformExecute._validated_scaffold_source(
                root,
                initial_workspace,
            )
            if source.failure:
                return r[bool].from_failure(source)
        if (
            not (root / c.Infra.GIT_DIR).exists()
            and initial_workspace.integration is None
        ):
            return r[bool].fail(
                "initial integration is required to initialize repository Git: "
                "declare --repository-branch",
            )
        return r[bool].ok(value=True)

    @staticmethod
    def _validated_scaffold_source(
        root: Path,
        initial_workspace: m.Infra.WorkspaceSpec,
    ) -> p.Result[bool]:
        """Validate the declared scaffold provenance before any filesystem effect.

        A silent acceptance would materialize a whole tree whose declared
        provenance was never a direct Git requirement, and the declaration is
        the scaffold's provenance input, not decoration.

        Returns:
            The resulting ``p.Result[bool]``.

        """
        source = u.Infra.flext_integration_line(
            codegen=config.Infra.codegen,
            repository_root=root,
            bootstrap_source=initial_workspace.flext_source,
        )
        if source.failure:
            return r[bool].from_failure(source)
        declared = (
            initial_workspace.project.flext_source
            if initial_workspace.project is not None
            else None
        )
        if declared is None:
            return r[bool].ok(value=True)
        distribution = config.Infra.codegen.infra_repository.distribution
        if u.Infra.dep_name(declared) != distribution:
            return r[bool].fail(
                f"scaffold source must declare {distribution}: {declared}",
            )
        parsed = u.Infra.declared_git_source(declared)
        if parsed.failure:
            return r[bool].from_failure(parsed)
        requirement_url, requirement_ref = parsed.value
        if (
            not requirement_url.startswith("https://")
            or not requirement_ref
            or u.Infra.ref_is_commit(requirement_ref)
        ):
            return r[bool].fail(
                "infrastructure source must declare an HTTPS Git URL "
                f"and integration line (never a commit): {declared}",
            )
        return r[bool].ok(value=True)

    @staticmethod
    def _bootstrap_request_root(
        root: Path,
    ) -> p.Result[t.VariadicTuple[m.Cli.AtomicDirectoryState]]:
        """Plan and create the guarded root directory chain for a new project.

        Returns:
            The resulting ``p.Result[t.VariadicTuple[m.Cli.AtomicDirectoryState]]
            ``.

        """
        planned = u.Cli.atomic_plan_directory_chain(root)
        if planned.failure:
            return r[t.VariadicTuple[m.Cli.AtomicDirectoryState]].from_failure(planned)
        created = u.Cli.atomic_create_directory_chain_guarded(
            planned.value,
            permission_mode=config.Infra.codegen.modes.directory_generated,
        )
        if created.failure:
            return r[t.VariadicTuple[m.Cli.AtomicDirectoryState]].from_failure(created)
        return r[t.VariadicTuple[m.Cli.AtomicDirectoryState]].ok(tuple(created.value))

    @staticmethod
    def _initialize_request_git(
        root: Path,
        initial_workspace: m.Infra.WorkspaceSpec,
    ) -> p.Result[bool]:
        """Initialize the unborn repository Git from its declared integration.

        Git owns no answer for an unborn repository: the caller declares the
        integration branch and a missing declaration fails loudly.

        Returns:
            The resulting ``p.Result[bool]``.

        """
        if initial_workspace.integration is None:
            return r[bool].fail(
                "initial branch is required to initialize the repository "
                "Git: declare --repository-branch",
            )
        commands: t.SequenceOf[t.StrSequence] = (
            (
                c.Infra.GIT,
                "init",
                "--initial-branch",
                initial_workspace.integration.branch,
                str(root),
            ),
            (
                c.Infra.GIT,
                "-C",
                str(root),
                "remote",
                "add",
                c.Infra.GIT_DEFAULT_REMOTE,
                initial_workspace.repository.url,
            ),
            (
                c.Infra.GIT,
                "-C",
                str(root),
                "commit",
                "--allow-empty",
                "-m",
                "chore: initialize generated project",
            ),
        )
        for command in commands:
            executed = u.Cli.run_checked(command)
            if executed.failure:
                return r[bool].from_failure(executed)
        return r[bool].ok(value=True)

    @override
    def execute(self) -> p.Result[p.Infra.CodegenResult]:
        """Run check or apply and require a verified fixed point.

        Returns:
            The resulting generation or observation outcome.

        """
        request = self.state.request or m.Infra.CodegenConformRequest(
            root=self.state.repository_root,
        )
        if c.Infra.CodegenConformMode(request.mode) is c.Infra.CodegenConformMode.CHECK:
            return self._observe_publication(request)
        inputs = u.Infra.load_codegen_inputs(request.root.expanduser().resolve())
        if inputs.failure:
            return r[p.Infra.CodegenResult].from_failure(inputs)
        if not self.state.generation_only:
            blocked = self._migrate_declarations_for_apply(request, inputs.value.spec)
            if blocked is not None:
                return blocked
        return self._dispatch_conform_surface(request)

    def _migrate_declarations_for_apply(
        self,
        request: m.Infra.CodegenConformRequest,
        spec: m.Infra.CodegenConfigSpec,
    ) -> p.Result[p.Infra.CodegenResult] | None:
        """Migrate repository declarations on governed apply surfaces.

        Returns:
            The failing conform result when a migration fails without a
            retained planning receipt, or ``None`` to continue the run.

        """
        if (
            c.Infra.CodegenConformMode(request.mode)
            is not c.Infra.CodegenConformMode.APPLY
        ):
            return None
        if not (
            self.surface_contract(
                c.Infra.CodegenConformSurface(request.what),
                codegen=spec,
            ).complete_governed
            or request.declaration_kind is not None
        ):
            return None
        migrated = self._migrate_repository_declarations(request)
        if migrated.failure and (
            migrated.error_code != c.Infra.ToolOutcome.ERROR.value
            or not self.state.planning_issues
        ):
            return r[p.Infra.CodegenResult].from_failure(migrated)
        return None

    def _dispatch_conform_surface(
        self,
        request: m.Infra.CodegenConformRequest,
    ) -> p.Result[p.Infra.CodegenResult]:
        """Dispatch the request's conform surface to its owning executor.

        Returns:
            The resulting ``p.Result[p.Infra.CodegenResult]``.

        """
        surface = c.Infra.CodegenConformSurface(request.what)
        if surface in c.Infra.FILE_ONLY_SURFACES:
            return self._execute_lazy_init(request)
        if surface is c.Infra.CodegenConformSurface.ALL:
            return self._execute_managed(request)
        if c.Infra.CodegenConformMode(request.mode) is c.Infra.CodegenConformMode.APPLY:
            if surface in c.Infra.PARTIAL_PLAN_SURFACES:
                return self.execute_plan(request)
            mise_owner = FlextInfraCodegenMiseArtifacts(repository_root=request.root)
            transaction = FlextInfraCodegenTransaction(mise_owner)
            return transaction.run_locked(
                prepare=False,
                operation=lambda _scope_root: self.execute_plan(request),
            )
        return self.execute_plan(request)

    def _migrate_repository_declarations(
        self,
        request: m.Infra.CodegenConformRequest,
    ) -> p.Result[bool]:
        """Publish explicit input migration before any runtime detector read.

        Returns:
            A complete migration receipt, retaining per-file failures and gains.

        """
        targets = u.Infra.repository_operation_targets(
            request.root,
            c.Infra.CodegenConformScope(request.scope),
        )
        if targets.failure:
            return r[bool].from_failure(targets)
        selected = tuple(
            target
            for target in targets.value
            if target.managed is not False
            and (
                u.Infra.workspace_manifest_path(target.root).is_file()
                or (
                    request.declaration_kind is not None
                    and target.root.resolve() == request.root.resolve()
                )
            )
        )
        if not selected:
            return r[bool].ok(value=True)
        roots = FlextInfraCodegenTransaction.capability_roots(
            "repository-declaration",
            tuple(target.root for target in selected),
        )
        transaction = FlextInfraCodegenTransaction(
            FlextInfraCodegenMiseArtifacts(repository_root=request.root),
        )

        def publish(scope_root: Path) -> p.Result[bool]:
            analysis = self._collect_declaration_migration_plans(request, selected)
            if analysis.failure:
                return r[bool].from_failure(analysis)
            if (
                not analysis.value.files
                and not analysis.value.issues
                and analysis.value.exception is None
            ):
                return r[bool].ok(value=True)
            published = transaction.publish_file_phase_locked(
                scope_root,
                roots,
                analysis.value,
                m.Infra.CodegenPhasePublicationPolicy(
                    directories=tuple(
                        sorted({
                            file.path.parent
                            for file in analysis.value.files
                            if not file.path.parent.is_dir()
                        }),
                    ),
                ),
            )
            if published.failure:
                if published.error_code == c.Infra.ToolOutcome.ERROR.value:
                    retained = self._retain_completed_migration_issues(published)
                    if retained.failure:
                        return retained
                return r[bool].from_failure(published)
            return r[bool].ok(value=True)

        return transaction.run_files_locked(roots, publish)

    def _collect_declaration_migration_plans(
        self,
        request: m.Infra.CodegenConformRequest,
        selected: t.SequenceOf[m.Infra.WorkspaceOperationTarget],
    ) -> p.Result[m.Infra.CodegenPhaseAnalysis]:
        """Plan every selected target's declaration migration into one analysis.

        Returns:
            The combined bootstrap-phase analysis, retaining per-file
            failures and gains.

        """
        files: list[m.Infra.CodegenFilePlan] = []
        inputs: list[m.Cli.AtomicFileState] = []
        issues: list[m.Infra.Issue] = []
        first_exception: BaseException | None = None
        for target in selected:
            captured = u.Infra.load_codegen_inputs(target.root)
            if captured.failure:
                planned: p.Result[m.Infra.CodegenPhaseAnalysis] = r[
                    m.Infra.CodegenPhaseAnalysis
                ].from_failure(captured)
            elif request.declaration_kind is not None:
                planned = self.repository_kind_declaration_plans(
                    target.root,
                    captured.value,
                    request.declaration_kind,
                )
            else:
                planned = self.repository_declaration_migration_plans(
                    target.root,
                    captured.value,
                )
            if planned.failure:
                issues.append(
                    m.Infra.Issue(
                        file=str(u.Infra.workspace_manifest_path(target.root)),
                        line=0,
                        column=0,
                        code=c.Infra.ToolOutcome.ERROR.value,
                        message=planned.error
                        or "repository declaration migration failed",
                    ),
                )
                if first_exception is None:
                    first_exception = planned.exception
                continue
            files.extend(planned.value.files)
            inputs.extend(planned.value.inputs)
            issues.extend(planned.value.issues)
            if first_exception is None:
                first_exception = planned.value.exception
        snapshots = FlextInfraCodegenPreconditions.unique_states(tuple(inputs))
        if snapshots.failure:
            return r[m.Infra.CodegenPhaseAnalysis].from_failure(snapshots)
        return r[m.Infra.CodegenPhaseAnalysis].ok(
            m.Infra.CodegenPhaseAnalysis(
                phase=c.Infra.CodegenStagedFilePhase.CONFORM_BOOTSTRAP,
                files=tuple(files),
                inputs=snapshots.value,
                issues=tuple(issues),
                exception=first_exception,
            ),
        )

    def _retain_completed_migration_issues(
        self,
        published: p.Result[t.VariadicTuple[Path]],
    ) -> p.Result[bool]:
        """Carry a settled red publication into the existing final plan report.

        Returns:
            Typed residual issues retained with their original first cause.

        """
        metadata = published.error_data
        if metadata is None:
            return r[bool].fail(
                "completed migration failure has no structured publication receipt",
                exception=published.exception,
            )

        def parse() -> t.VariadicTuple[m.Infra.Issue]:
            serialized = u.Cli.json_dumps(metadata["issues"]).unwrap()
            wire = u.type_adapter(tuple[t.JsonMapping, ...]).validate_json(serialized)
            return tuple(
                m.Infra.Issue.model_validate_json(
                    u.Cli.json_dumps(
                        {
                            key: value
                            for key, value in issue.items()
                            if key not in m.Infra.Issue.model_computed_fields
                        },
                    ).unwrap(),
                )
                for issue in wire
            )

        parsed = r[t.VariadicTuple[m.Infra.Issue]].create_from_callable(parse)
        if parsed.failure:
            return r[bool].fail(
                parsed.error or "invalid completed migration issue receipt",
                exception=published.exception or parsed.exception,
            )
        if not parsed.value:
            return r[bool].fail(
                "completed migration failure has no residual issue",
                exception=published.exception,
            )
        self.state.planning_issues.extend(parsed.value)
        if self.state.planning_exception is None:
            self.state.planning_exception = published.exception
        return r[bool].ok(value=True)

    def _plan_or_report(
        self,
        request: m.Infra.CodegenConformRequest,
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
        request: m.Infra.CodegenConformRequest,
    ) -> p.Result[p.Infra.CodegenResult]:
        """Execute a non-toolchain conform surface without widening its scope.

        Returns:
            The resulting ``p.Result[p.Infra.CodegenResult]``.

        """
        if c.Infra.CodegenConformMode(request.mode) is c.Infra.CodegenConformMode.CHECK:
            return self._observe_publication(request)
        if request.what is c.Infra.CodegenConformSurface.DEPENDENCIES:
            return r[p.Infra.CodegenResult].fail(
                "partial codegen apply is prohibited; use the complete all surface",
            )
        u.Cli.header(
            "Code generation" if self.state.generation_only else "Project conformance"
        )
        u.Cli.info(
            f"stage=plan mode={request.mode} scope={request.scope} "
            f"what={request.what} root={request.root}",
        )
        planned = self._plan_or_report(request)
        if planned.failure:
            return r[p.Infra.CodegenResult].from_failure(planned)
        plan = planned.value
        surface = c.Infra.CodegenConformSurface(request.what)
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

        def publish(scope_root: Path) -> p.Result[p.Infra.CodegenResult]:
            written = self._publish_bootstrap_phase(
                request,
                plan,
                transaction,
                (scope_root, roots),
                publication_receipts=receipts,
            )
            if written.failure:
                return r[p.Infra.CodegenResult].from_failure(written)
            payload: p.Infra.CodegenResult = m.Infra.CodegenResult(
                plan=plan,
                written_files=written.value,
            )
            return r[p.Infra.CodegenResult].ok(payload)

        def complete(result: p.Infra.CodegenResult) -> p.Result[p.Infra.CodegenResult]:
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
            payload: p.Infra.CodegenResult = m.Infra.CodegenResult.model_validate(
                result,
                from_attributes=True,
            ).model_copy(update={"publication_receipt": receipt.value})
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
        request: m.Infra.CodegenConformRequest,
        plan: m.Infra.CodegenPlan,
        transaction: FlextInfraCodegenTransaction,
        publication_scope: t.Pair[Path, t.MappingKV[str, Path]],
        *,
        publication_receipts: t.MutableSequenceOf[m.Infra.CodegenPhaseOutcome],
    ) -> p.Result[t.VariadicTuple[Path]]:
        """Authorize the surface contract, then publish its changed files.

        Returns:
            The resulting ``p.Result[t.VariadicTuple[Path]]`` with the written
            bootstrap files.

        """
        scope_root, roots = publication_scope
        surface = c.Infra.CodegenConformSurface(request.what)
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
            source_directories=tuple(
                directory
                for file in plan.files
                for directory in file.source_directories
            ),
            source_query_topology=tuple(
                topology
                for file in plan.files
                for topology in file.source_query_topology
            ),
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
            publication_receipts=publication_receipts,
        )

    def _bootstrap_expected_surface(
        self,
        request: m.Infra.CodegenConformRequest,
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
            destinations = self.surface_contract(
                surface,
                codegen=inputs.value.spec,
            ).destinations
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
        dependencies = {
            path
            for file in plan.files
            if file.index_before is not None
            for path in file.tracking_dependencies
        }
        if dependencies:
            permitted = {
                path
                for repository in plan.repositories
                for path in FlextInfraConfig.config_layer_paths_for_repository(
                    (request.root.expanduser().resolve() / repository.path).resolve(),
                    filename=c.Infra.CODEGEN_CONFIG_FILENAME,
                )[1:]
            }
            if (
                surface is not c.Infra.CodegenConformSurface.RUNTIME_BINDINGS
                or not dependencies.issubset(permitted)
            ):
                error = ValueError(
                    "runtime tracking dependencies escape declared config layers"
                )
                return result_type.fail(str(error), exception=error)
            expected_paths.update(dependencies)
            expected_owners.update(
                {
                    dependency: file.project
                    for file in plan.files
                    for dependency in file.tracking_dependencies
                },
            )
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
        workspace = self.state.initial_workspace
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
    ) -> p.Result[p.Infra.CodegenResult]:
        """Plan outside the lease and publish through locked generation phases.

        Returns:
            The resulting ``p.Result[p.Infra.CodegenResult]``.

        """
        if c.Infra.CodegenConformMode(request.mode) is c.Infra.CodegenConformMode.CHECK:
            return self._observe_publication(request)
        configured = self._managed_policy(request)
        if configured.failure:
            return r[p.Infra.CodegenResult].from_failure(configured)
        transaction = FlextInfraCodegenTransaction(
            FlextInfraCodegenMiseArtifacts(repository_root=request.root),
            participant_policy=configured.value,
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
        # Each phase authenticates its own consumed inputs. An unrelated failed
        # target is not a prerequisite of every later publication.
        lazy = self._settle_generation_stage(
            lambda: self._publish_lazy_batch(
                planned.value,
                configured.value,
                batches,
                operation.value,
            ),
        )
        written = tuple(path for batch in batches for path in batch.written_files)
        repaired = (
            r[bool].ok(value=True)
            if self.state.generation_only
            else self._settle_generation_stage(
                lambda: self.conform_workspace_beads_routes(request).flat_map(
                    lambda _: self._allow_direnv_after_apply(request, written)
                ),
            )
        )
        documents = self._settle_generation_stage(
            lambda: self._publish_docs_batches(
                planned.value,
                batches,
            ),
        )
        failures: list[p.FailureLike] = [
            item for item in (published, lazy, repaired, documents) if item.failure
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
        first_exception = next(
            (
                item.exception
                for item in (planned.value, *failures)
                if item.exception is not None
            ),
            None,
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
            failures.append(completed)
            if first_exception is None:
                first_exception = completed.exception
        if first_exception is not None:
            raise first_exception
        if failures:
            return r[p.Infra.CodegenResult].from_failure(failures[0])
        payload: p.Infra.CodegenResult = m.Infra.CodegenResult(
            plan=planned.value,
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
        try:
            return operation()
        except (OSError, *c.EXC_BROAD_RUNTIME) as exc:
            return r[T].fail(str(exc), exception=exc)

    def _publish_lazy_batch(
        self,
        plan: m.Infra.CodegenPlan,
        policy: p.Infra.CodegenParticipantPolicy,
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
        if not files and not (lazy.value.issues or lazy.value.exception is not None):
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
                "run it through FlextInfra.codegen_conform",
            )
        if not self.state.generation_only:
            seeded = self._seed_declared_beads_identity(request.root)
            if seeded.failure:
                return result.from_failure(seeded)
        policy = ports.participant_policy(
            request.root,
            initial_workspace=self.state.initial_workspace,
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
    def _lazy_phase(
        request: m.Infra.CodegenConformRequest,
        plan: m.Infra.CodegenPlan,
    ) -> p.Result[m.Infra.CodegenPhaseAnalysis]:
        """Compose selected repositories in one authenticated source epoch.

        APPLY captures this analysis before phase publication.
        ADR-014: lazy-init ownership stays inside conform's
        transaction. Lazy-init plans exactly the repositories conform
        rewrites: the selected mutable ``internal_flext`` repositories of
        ``plan``, never a scope-excluded root or a third-party checkout.

        Returns:
            The resulting ``p.Result[m.Infra.CodegenPhaseAnalysis]``.

        """
        roots = tuple(
            (request.root / repository.path).resolve()
            for repository in plan.repositories
            if repository.kind is c.Infra.ProjectKind.INTERNAL_FLEXT
        )
        return FlextInfraCodegenLazyInit(
            repository_root=request.root,
            project_scope_roots=roots,
        ).plan_files()

    def _prepare_managed_plan(
        self,
        request: m.Infra.CodegenConformRequest,
    ) -> p.Result[m.Infra.CodegenPlan]:
        """Plan consumed sources and retain the Docs planner outside the lease.

        Returns:
            The immutable plan, or the original planning failure.

        """
        u.Cli.header(
            "Code generation" if self.state.generation_only else "Project conformance"
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
        request: m.Infra.CodegenConformRequest,
        analysis: m.Infra.CodegenPhaseAnalysis,
        policy: p.Infra.CodegenParticipantPolicy,
        receipts: t.MutableSequenceOf[m.Infra.CodegenPhaseOutcome],
    ) -> p.Result[t.VariadicTuple[Path]]:
        """Use the shared journal publisher for one exact dependent component.

        Returns:
            Its published paths or the original admission or consumer failure.

        """
        result_type = r[t.VariadicTuple[Path]]
        prepared = FlextInfraCodegenStaging.prepare_python_plans(
            request.root,
            analysis.files,
        )
        if prepared.failure:
            return result_type.from_failure(prepared)
        analysis = analysis.model_copy(update={"files": prepared.value})
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
                    publication_receipts=receipts,
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
            workspace=workspace,
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
        try:
            for prepared in docs_generator.prepare_batches(
                publication_receipts=receipts,
            ):
                published = prepared.flat_map(
                    lambda bundle: self._settle_generation_stage(
                        partial(
                            docs_generator.publish_batch,
                            bundle,
                            publication_receipts=receipts,
                        ),
                    ),
                )
                if published.failure:
                    failures.append(published)
        except (OSError, *c.EXC_BROAD_RUNTIME) as exc:
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


__all__: list[str] = ["FlextInfraCodegenConformExecute"]
