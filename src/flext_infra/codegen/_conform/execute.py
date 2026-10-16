"""Transactional execution of conformance plans.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import traceback
from functools import partial
from pathlib import Path
from typing import Self, override

from flext_infra import FlextInfraConfig, c, config, m, p, r, t, u
from flext_infra.codegen import (
    FlextInfraCodegenLazyInit,
    FlextInfraCodegenMiseArtifacts,
    FlextInfraCodegenPreconditions,
    FlextInfraCodegenTransaction,
    FlextInfraMiseArtifactsVerification,
)
from flext_infra.codegen._conform import FlextInfraCodegenConformExecuteDirected
from flext_infra.workspace.native_reference import FlextInfraWorkspaceNativeReference

# The surfaces a partial apply plan may publish; every other non-ALL surface is
# prohibited outside the complete managed run.
_PARTIAL_PLAN_SURFACES: frozenset[c.Infra.CodegenConformSurface] = frozenset((
    c.Infra.CodegenConformSurface.MAKEFILE,
    c.Infra.CodegenConformSurface.DOCS_CONFIG,
    c.Infra.CodegenConformSurface.ENVRC,
    c.Infra.CodegenConformSurface.PYPROJECT,
    c.Infra.CodegenConformSurface.MISE_CONFIG,
    c.Infra.CodegenConformSurface.RUNTIME_BINDINGS,
    c.Infra.CodegenConformSurface.WORKFLOWS,
))


class FlextInfraCodegenConformExecute(FlextInfraCodegenConformExecuteDirected):
    """Transactional execution of conformance plans.

    The chain is linear in dependency order, so execution statically inherits
    everything it calls: bootstrap (service root, request state) <- gitignore
    <- docs ownership <- beads routes <- file plans <- pyproject policy <-
    context render <- artifact render <- existing plan <- scaffold plan <- plan
    <- execute scaffold <- directed file publication <- execute.
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
            m.Infra.CodegenConformRequest(
                root=request.root,
                what=request.what,
                scope=request.scope,
                mode=c.Infra.CodegenConformMode.APPLY,
                module=request.module,
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
        if surface in {
            c.Infra.CodegenConformSurface.LAZY_INIT,
            c.Infra.CodegenConformSurface.FACADES,
        }:
            return self._execute_lazy_init(request)
        if surface is c.Infra.CodegenConformSurface.ALL:
            return self._execute_managed(request)
        if c.Infra.CodegenConformMode(request.mode) is c.Infra.CodegenConformMode.APPLY:
            if surface in _PARTIAL_PLAN_SURFACES:
                return self._execute_plan(request)
            mise_owner = FlextInfraCodegenMiseArtifacts(repository_root=request.root)
            transaction = FlextInfraCodegenTransaction(mise_owner)
            return transaction.run_locked(
                prepare=False,
                operation=lambda _scope_root: self._execute_plan(request),
            )
        return self._execute_plan(request)

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

    def _execute_plan(
        self,
        request: m.Infra.CodegenConformRequest,
    ) -> p.Result[m.Infra.CodegenResult]:
        """Execute a non-toolchain conform surface without widening its scope.

        Returns:
            The resulting ``p.Result[m.Infra.CodegenResult]``.

        """
        if c.Infra.CodegenConformMode(request.mode) is c.Infra.CodegenConformMode.CHECK:
            return self._observe_publication(request)
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
        if surface not in _PARTIAL_PLAN_SURFACES:
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
                )
                if changed
                else None,
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
        if planned.failure:
            return r[m.Infra.CodegenResult].from_failure(planned)
        batches: list[m.Infra.CodegenPhaseOutcome] = []
        published = transaction.run_locked(
            prepare=True,
            operation=lambda scope_root: self._execute_managed_locked_prepared(
                planned.value,
                scope_root,
                transaction,
                batches,
            ),
        )
        if published.failure:
            return published
        lazy_published = self._publish_lazy_batch(
            planned.value,
            policy,
            batches,
        )
        if lazy_published.failure:
            return r[m.Infra.CodegenResult].from_failure(lazy_published)
        written = (*published.value.written_files, *lazy_published.value)
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
                published.value.model_copy(update={"written_files": written}),
                tuple(batches),
            ),
        )

    def _publish_lazy_batch(
        self,
        plan: m.Infra.CodegenPlan,
        policy: m.Infra.CodegenParticipantPolicy,
        batches: t.MutableSequenceOf[m.Infra.CodegenPhaseOutcome],
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
        inputs = FlextInfraCodegenPreconditions.unique_states(
            tuple(source for file in files for source in file.source_states),
        )
        if inputs.failure:
            return result_type.from_failure(inputs)
        analysis = lazy.value.model_copy(
            update={"files": files, "inputs": inputs.value},
        )
        transaction = FlextInfraCodegenTransaction(
            FlextInfraCodegenMiseArtifacts(repository_root=plan.request.root),
            participant_policy=policy,
            prior_publications=tuple(batches),
        )
        projects = frozenset(file.project for file in files)
        roots = transaction.capability_roots(
            "lazy-init",
            tuple(
                project
                for project in (
                    (plan.request.root / repository.path).resolve()
                    for repository in plan.repositories
                )
                if project in projects
            ),
        )
        return transaction.run_files_locked(
            roots,
            lambda scope_root: transaction.publish_file_phase_locked(
                scope_root,
                roots,
                analysis,
                m.Infra.CodegenPhasePublicationPolicy(directories=()),
                publication_receipts=batches,
            ),
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
            The repository's lazy-init analysis, or its failure as data.

        """
        try:
            analysis = FlextInfraCodegenLazyInit(
                repository_root=root,
                project_scope_roots=(root,),
            ).plan_files()
        except (OSError, SyntaxError, ValueError) as exc:
            path = (
                exc.filename
                if isinstance(exc, SyntaxError) and exc.filename is not None
                else str(root)
            )
            return m.Infra.CodegenPhaseOutcome(
                exception=exc,
                issues=(
                    m.Infra.Issue(
                        file=path,
                        line=exc.lineno or 0 if isinstance(exc, SyntaxError) else 0,
                        column=exc.offset or 0 if isinstance(exc, SyntaxError) else 0,
                        code=c.Infra.ToolOutcome.ERROR.value,
                        message=traceback.format_exc(),
                    ),
                ),
            )
        if analysis.failure:
            return m.Infra.CodegenPhaseOutcome(
                error=analysis.error or f"lazy-init analysis failed: {root}",
                exception=analysis.exception,
            )
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
            FlextInfraCodegenConformExecute.lazy_repository_task,
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

    def _execute_managed_locked_prepared(
        self,
        plan: m.Infra.CodegenPlan,
        scope_root: Path,
        transaction: FlextInfraCodegenTransaction,
        publication_receipts: t.MutableSequenceOf[m.Infra.CodegenPhaseOutcome],
    ) -> p.Result[m.Infra.CodegenResult]:
        """Reauthenticate the captured plan and publish one locked generation cycle.

        Returns:
            The resulting ``p.Result[m.Infra.CodegenResult]``.

        """
        config_plans = self.mise_config_plans(plan)
        if config_plans.failure:
            return r[m.Infra.CodegenResult].from_failure(config_plans)
        session = transaction.begin_locked(scope_root, config_plans.value, plan.files)
        if session.failure:
            return r[m.Infra.CodegenResult].from_failure(session)
        recorded = transaction.record_publication(
            session.value.model_copy(
                update={
                    "issues": (*session.value.issues, *plan.issues),
                    "exception": session.value.exception or plan.exception,
                },
            ),
            phase=c.Infra.CodegenStagedFilePhase.CONFORM,
        )
        if recorded.failure:
            return r[m.Infra.CodegenResult].from_failure(recorded)
        return transaction.publish_prepared_locked(
            recorded.value,
            lambda current: self._publish_managed_locked(
                plan,
                transaction=transaction,
                session=current,
                publication_receipts=publication_receipts,
            ),
        )

    @staticmethod
    def _publish_managed_locked(
        plan: m.Infra.CodegenPlan,
        transaction: FlextInfraCodegenTransaction,
        session: m.Infra.CodegenTransactionSession,
        publication_receipts: t.MutableSequenceOf[m.Infra.CodegenPhaseOutcome],
    ) -> p.Result[m.Infra.CodegenResult]:
        """Settle bootstrap publication before planning the lazy phase.

        Returns:
            The resulting ``p.Result[m.Infra.CodegenResult]``.

        """
        published = transaction.commit_locked(
            session,
            publication_receipts=publication_receipts,
        )
        if published.failure:
            return r[m.Infra.CodegenResult].from_failure(published)
        return r[m.Infra.CodegenResult].ok(
            m.Infra.CodegenResult(plan=plan, written_files=published.value),
        )

    def _publish_docs_batches(
        self,
        request: m.Infra.CodegenConformRequest,
        result: m.Infra.CodegenResult,
        batches: t.VariadicTuple[m.Infra.CodegenPhaseOutcome],
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


__all__: list[str] = ["FlextInfraCodegenConformExecute"]
