"""Transactional execution of conformance plans.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from functools import partial
from pathlib import Path
from typing import Self, override

from flext_infra import FlextInfraConfig, c, config, m, p, r, t, u
from flext_infra.codegen import (
    FlextInfraCodegenMiseArtifacts,
    FlextInfraCodegenPreconditions,
    FlextInfraCodegenTransaction,
)
from flext_infra.codegen._conform import FlextInfraCodegenConformExecuteDirected
from flext_infra.codegen._conform._execute_generation import (
    FlextInfraCodegenConformExecuteGenerationMixin,
)
from flext_infra.workspace.native_reference import FlextInfraWorkspaceNativeReference


class FlextInfraCodegenConformExecute(
    FlextInfraCodegenConformExecuteDirected,
    FlextInfraCodegenConformExecuteGenerationMixin,
):
    """Transactional execution of conformance plans.

    The chain is linear in dependency order, so execution statically inherits
    everything it calls: bootstrap (service root, request state) <- gitignore
    <- docs ownership <- beads routes <- file plans <- pyproject policy <-
    context render <- artifact render <- existing plan <- scaffold plan <- plan
    <- execute scaffold <- directed file publication <- execute. Existing plan,
    plan and execute compose their own responsibility mixins (recovery and
    governed artifacts, repository topology, generation batch publication)
    without deepening the chain.
    """

    @classmethod
    def generate_request(
        cls: type[Self],
        request: m.Infra.CodegenGenerateRequest,
        *,
        ports: m.Infra.CodegenConformPorts,
    ) -> p.Result[m.Infra.CodegenResult]:
        """Publish declared projections through the shared planner and publisher.

        Returns:
            The generation result without repairing authored declarations.

        """
        return cls.execute_request(
            m.Infra.CodegenConformRequest.model_validate(
                request.model_dump() | {"mode": c.Infra.CodegenConformMode.APPLY},
            ),
            ports=ports,
            generation_only=True,
        )

    @classmethod
    def execute_request(
        cls: type[Self],
        request: m.Infra.CodegenConformRequest,
        initial_workspace: m.Infra.WorkspaceSpec | None = None,
        *,
        ports: m.Infra.CodegenConformPorts | None,
        generation_only: bool = False,
    ) -> p.Result[m.Infra.CodegenResult]:
        """Execute one already validated request with the facade-wired ports.

        ``ports`` is required at every call: the complete surface consumes it,
        and a single-file surface declares its absence explicitly with ``None``.

        Returns:
            The resulting ``p.Result[m.Infra.CodegenResult]``.

        """
        if c.Infra.CodegenConformMode(request.mode) is c.Infra.CodegenConformMode.CHECK:
            with FlextInfraWorkspaceNativeReference.compilation_scope():
                return cls._observe_publication(request)
        if request.what is c.Infra.CodegenConformSurface.DEPENDENCIES:
            return cls(
                repository_root=request.root,
                ports=ports,
                generation_only=generation_only,
            ).execute_plan(request)
        root = request.root.expanduser().resolve()
        operation = "generate" if generation_only else "conform"
        u.Cli.info(
            f"operation={operation} stage=inputs root={root} "
            f"scope={request.scope} surface={request.what}"
        )
        prelude = cls._validated_request_prelude(root, initial_workspace)
        if prelude.failure:
            return r[m.Infra.CodegenResult].from_failure(prelude)
        if initial_workspace is not None and not root.is_dir():
            created = cls._bootstrap_request_root(root)
            if created.failure:
                return r[m.Infra.CodegenResult].from_failure(created)
        if initial_workspace is not None and not (root / c.Infra.GIT_DIR).exists():
            initialized = cls._initialize_request_git(root, initial_workspace)
            if initialized.failure:
                return r[m.Infra.CodegenResult].from_failure(initialized)
        service = cls(
            repository_root=root,
            request=request,
            initial_workspace=initial_workspace,
            ports=ports,
            generation_only=generation_only,
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
    def execute(self) -> p.Result[m.Infra.CodegenResult]:
        """Run check or apply and require a verified fixed point.

        Returns:
            The resulting ``p.Result[m.Infra.CodegenResult]``.

        """
        request = self.request or m.Infra.CodegenConformRequest(
            root=self.repository_root,
        )
        if c.Infra.CodegenConformMode(request.mode) is c.Infra.CodegenConformMode.CHECK:
            return self._observe_publication(request)
        inputs = u.Infra.load_codegen_inputs(request.root.expanduser().resolve())
        if inputs.failure:
            return r[m.Infra.CodegenResult].from_failure(inputs)
        if not self.generation_only:
            blocked = self._migrate_declarations_for_apply(request, inputs.value.spec)
            if blocked is not None:
                return blocked
        return self._dispatch_conform_surface(request)

    def _migrate_declarations_for_apply(
        self,
        request: m.Infra.CodegenConformRequest,
        spec: m.Infra.CodegenConfigSpec,
    ) -> p.Result[m.Infra.CodegenResult] | None:
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
            or not self.planning_issues
        ):
            return r[m.Infra.CodegenResult].from_failure(migrated)
        return None

    def _dispatch_conform_surface(
        self,
        request: m.Infra.CodegenConformRequest,
    ) -> p.Result[m.Infra.CodegenResult]:
        """Dispatch the request's conform surface to its owning executor.

        Returns:
            The resulting ``p.Result[m.Infra.CodegenResult]``.

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
        self.planning_issues.extend(parsed.value)
        if self.planning_exception is None:
            self.planning_exception = published.exception
        return r[bool].ok(value=True)

    def execute_plan(
        self,
        request: m.Infra.CodegenConformRequest,
    ) -> p.Result[m.Infra.CodegenResult]:
        """Execute a non-toolchain conform surface without widening its scope.

        Returns:
            The resulting ``p.Result[m.Infra.CodegenResult]``.

        """
        if c.Infra.CodegenConformMode(request.mode) is c.Infra.CodegenConformMode.CHECK:
            return self._observe_publication(request)
        if request.what is c.Infra.CodegenConformSurface.DEPENDENCIES:
            return r[m.Infra.CodegenResult].fail(
                "partial codegen apply is prohibited; use the complete all surface",
            )
        u.Cli.header(
            "Code generation" if self.generation_only else "Project conformance"
        )
        u.Cli.info(
            f"stage=plan mode={request.mode} scope={request.scope} "
            f"what={request.what} root={request.root}",
        )
        planned = self.plan(request)
        if planned.failure:
            return r[m.Infra.CodegenResult].from_failure(planned)
        plan = planned.value
        if not plan.files and (plan.issues or plan.exception is not None):
            return r[m.Infra.CodegenResult].fail(
                "\n".join(issue.formatted for issue in plan.issues)
                or "generation planning failed",
                exception=plan.exception,
            )
        surface = c.Infra.CodegenConformSurface(request.what)
        if surface not in c.Infra.PARTIAL_PLAN_SURFACES:
            return r[m.Infra.CodegenResult].fail(
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

        def publish(scope_root: Path) -> p.Result[m.Infra.CodegenResult]:
            written = self._publish_bootstrap_phase(
                request,
                plan,
                transaction,
                (scope_root, roots),
                publication_receipts=receipts,
            )
            if written.failure:
                return r[m.Infra.CodegenResult].from_failure(written)
            return r[m.Infra.CodegenResult].ok(
                m.Infra.CodegenResult(plan=plan, written_files=written.value),
            )

        return transaction.run_files_locked(roots, publish).flat_map(
            lambda result: transaction.publish_operation_receipt(
                request,
                tuple(receipts),
                scope_roots=tuple(roots.values()),
                completed=True,
            ).map(
                lambda receipt: result.model_copy(
                    update={"publication_receipt": receipt},
                ),
            ),
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

        Returns:
            The expected destination paths paired with each path's owning
            repository root.

        """
        result_type = r[t.Pair[set[Path], t.MutableMappingKV[Path, Path]]]
        expected_owners: t.MutableMappingKV[Path, Path] = {}
        for repository in plan.repositories:
            repository_root = (
                request.root.expanduser().resolve() / repository.path
            ).resolve()
            inputs = u.Infra.load_codegen_inputs(repository_root)
            if inputs.failure:
                return result_type.from_failure(inputs)
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


__all__: list[str] = ["FlextInfraCodegenConformExecute"]
