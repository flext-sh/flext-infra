"""Conformance planning for existing repositories and governed artifacts.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import time
import traceback
from collections.abc import Callable, Generator, MutableMapping
from contextlib import ExitStack, contextmanager
from functools import partial
from pathlib import Path

from flext_infra import c, m, p, r, t, u
from flext_infra.codegen import FlextInfraCodegenLazyInit
from flext_infra.codegen._conform.editor import FlextInfraCodegenConformEditor
from flext_infra.deps import FlextInfraPyprojectModernizer
from flext_infra.services._codegen import FlextInfraCodegenVscodeMixin
from flext_infra.workspace import FlextInfraWorkspaceEnvironmentContracts


class FlextInfraCodegenConformExistingPlan(FlextInfraCodegenConformEditor):
    """Conformance planning for existing repositories and governed artifacts."""

    _source_views: (
        t.Pair[
            ExitStack,
            t.MutableMappingKV[
                t.Pair[Path, frozenset[t.Pair[Path, bytes | None]]],
                tuple[
                    p.Infra.RopeProject,
                    Callable[
                        [],
                        t.Triple[
                            tuple[m.Cli.AtomicFileState, ...],
                            tuple[m.Cli.AtomicDirectoryInventory, ...],
                            tuple[m.Cli.AtomicDirectoryChainPlan, ...],
                        ],
                    ],
                    t.MappingKV[Path, str],
                    t.Pair[
                        list[t.Pair[Path, m.Infra.CodegenPhaseAnalysis]],
                        list[m.Infra.CodegenPhaseAnalysis],
                    ],
                ],
            ],
        ]
        | None
    ) = m.PrivateAttr(default=None)

    @contextmanager
    def shared_source_views(self) -> Generator[None]:
        """Keep each distinct source view of one repository plan open once.

        Every planning phase of the repository binds through this scope, so
        phases whose declared plans carry the same effects share one native
        Rope project and its inference instead of rebuilding it. Each view
        verifies its consumed sources when the scope closes.

        Yields:
            Nothing; the scope is active until the repository plan completes.

        """
        try:
            with ExitStack() as stack:
                self._source_views = (stack, {})
                yield
        finally:
            try:
                if self._source_views is not None:
                    for binding in self._source_views[1].values():
                        for failure in binding[3][1]:
                            self._retain_diagnostics(
                                failure.exception,
                                issues=failure.issues,
                                failed_targets=failure.failed_targets,
                            )
            finally:
                self._source_views = None

    @contextmanager
    def _source_view(
        self,
        root: Path,
        source_states: t.VariadicTuple[m.Cli.AtomicFileState] = (),
        declared_files: t.VariadicTuple[m.Infra.CodegenFilePlan] = (),
        source_publications: list[t.Pair[Path, m.Infra.CodegenPhaseAnalysis]]
        | None = None,
    ) -> Generator[
        t.Triple[
            p.Infra.RopeProject,
            Callable[
                [],
                t.Triple[
                    tuple[m.Cli.AtomicFileState, ...],
                    tuple[m.Cli.AtomicDirectoryInventory, ...],
                    tuple[m.Cli.AtomicDirectoryChainPlan, ...],
                ],
            ],
            t.MappingKV[Path, str],
        ]
    ]:
        """Bind the source view the declared effects determine, opening it once.

        Plans without an effect equal the physical tree, so only the effective
        declared payloads distinguish one view from another.

        Yields:
            The shared native project, original-state reader and planned sources.

        Raises:
            RuntimeError: If no repository planning scope is open.

        """
        if self._source_views is None:
            msg = "source views require an open repository planning scope"
            raise RuntimeError(msg)
        stack, opened = self._source_views
        key = (
            root,
            frozenset(
                (plan.path, plan.desired_content)
                for plan in declared_files
                if u.Infra.codegen_file_requires_effect(plan)
            ),
        )
        if key not in opened:
            publications: t.Pair[
                list[t.Pair[Path, m.Infra.CodegenPhaseAnalysis]],
                list[m.Infra.CodegenPhaseAnalysis],
            ] = ([], [])
            original_project = next(
                (
                    binding[0]
                    for (original_root, _effects), binding in opened.items()
                    if original_root == root
                ),
                None,
            )
            source_binding = stack.enter_context(
                u.Infra.facade_source_project(
                    root,
                    source_options=m.Infra.StageSourceOptions(
                        inputs=source_states, declared_files=declared_files
                    ),
                    source_publications=publications,
                    original_project=original_project,
                )
            )
            opened[key] = (*source_binding, publications)
        try:
            binding = opened[key]
            yield binding[0], binding[1], binding[2]
        finally:
            if source_publications is not None:
                opened[key][3][0].extend(source_publications)

    def _plan_existing_repository(
        self,
        *,
        target: m.Infra.RepositoryConformTarget,
        workspace: m.Infra.WorkspaceSpec,
        codegen: m.Infra.CodegenConfigSpec,
        contract: m.Infra.CodegenConformSurfaceContract,
    ) -> p.Result[t.SequenceOf[m.Infra.CodegenFilePlan]]:
        """Conform every declared managed surface in an existing repository.

        Returns:
            The resulting ``p.Result[t.SequenceOf[m.Infra.CodegenFilePlan]]``.

        """
        root = target.root
        repository = target.repository
        self.state.completed_source_plans = None
        surface_plans = self._plan_existing_contract_surface(
            target,
            workspace,
            codegen,
            contract,
        )
        if surface_plans is not None:
            return surface_plans
        u.Cli.info(f"  stage=pyproject repository={repository.name}")
        pyproject = root / c.PYPROJECT_FILENAME
        if not pyproject.is_file():
            return r[t.SequenceOf[m.Infra.CodegenFilePlan]].fail(
                f"existing repository has no pyproject.toml: {root}; "
                "scaffold templates are available only through codegen new",
            )
        identity = self._validated_existing_identity(target, workspace, codegen)
        if identity.failure:
            return r[t.SequenceOf[m.Infra.CodegenFilePlan]].from_failure(identity)
        docs_config = (Path(c.Infra.DIR_DOCS) / c.Infra.DOCS_CONFIG_FILENAME).as_posix()
        if contract.destinations == frozenset({docs_config}):
            return self._plan_existing_docs_config(
                target,
                workspace,
                codegen,
                docs_config,
            )
        return self._plan_existing_managed(
            target,
            workspace,
            codegen,
            contract,
            identity.value,
        )

    def _validated_existing_identity(
        self,
        target: m.Infra.RepositoryConformTarget,
        workspace: m.Infra.WorkspaceSpec,
        codegen: m.Infra.CodegenConfigSpec,
    ) -> p.Result[t.Pair[m.Infra.ProjectSpec, p.ProjectMetadata]]:
        """Resolve the project identity and prove it matches the live PEP 621.

        Existing checkouts declare no scaffold metadata: the tooling identity
        derives from live PEP 621 metadata (same rule as the render pass)
        instead of referencing an undefined name.

        Returns:
            The resulting ``p.Result[t.Pair[m.Infra.ProjectSpec,
                p.ProjectMetadata]]``.

        """
        result_type = r[t.Pair[m.Infra.ProjectSpec, p.ProjectMetadata]]
        root = target.root
        repository = target.repository
        u.Cli.info(f"  stage=pyproject repository={repository.name}")
        metadata = u.Infra.read_project_metadata_result(root)
        if metadata.failure:
            return result_type.from_failure(metadata)
        project = workspace.project
        if project is None:
            derived = self._project_spec_from_existing(repository, root, codegen)
            if derived.failure:
                return result_type.from_failure(derived)
            project = derived.value
        dist = metadata.value.project.name
        if dist != repository.distribution:
            return result_type.fail(
                "PEP 621 project name does not match catalog distribution: "
                f"{dist} != {repository.distribution}",
            )
        return result_type.ok((project, metadata.value))

    def _plan_existing_contract_surface(
        self,
        target: m.Infra.RepositoryConformTarget,
        workspace: m.Infra.WorkspaceSpec,
        codegen: m.Infra.CodegenConfigSpec,
        contract: m.Infra.CodegenConformSurfaceContract,
    ) -> p.Result[t.SequenceOf[m.Infra.CodegenFilePlan]] | None:
        """Plan recovery surfaces before consumers parse existing projections.

        Returns:
            The resulting plans for a single-artifact surface, or None when
            the contract does not select one.

        """
        if contract.destinations == self._editor_destinations(codegen):
            return self._plan_existing_editor(target, workspace, codegen)
        if contract.destinations == frozenset({c.Infra.ENVRC_FILENAME}):
            context = m.Infra.EnvrcRenderSpec(
                native_environment_unset=codegen.make.native_environment_unset,
                toolchain=codegen.toolchain,
                repository_root_rel=self._repository_root_rel(workspace),
                environment_path_prepends=codegen.toolchain.environment_path_prepends,
            )
            destination = c.Infra.ENVRC_FILENAME
        elif contract.destinations == frozenset({c.Infra.MISE_TOML_FILENAME}):
            context = m.Infra.ToolchainSpec(**{
                name: value
                for name, value in codegen.toolchain.model_dump().items()
                if name in m.Infra.ToolchainSpec.model_fields
            })
            destination = c.Infra.MISE_TOML_FILENAME
        elif contract.destinations == c.Infra.MAKEFILE_BOOTSTRAP_DESTINATIONS:
            return self._plan_existing_bootstrap(target, workspace, codegen)
        else:
            return None
        plans: list[m.Infra.CodegenFilePlan] = []
        for required in sorted(
            codegen.templates.required_destinations(frozenset({destination})),
        ):
            planned = self._bootstrap_destination_plan(
                target,
                codegen,
                context,
                required,
            )
            if planned.failure:
                return r[t.SequenceOf[m.Infra.CodegenFilePlan]].from_failure(planned)
            plans.append(planned.value)
        return self._artifact_dependency_plans(codegen, target.root, plans)

    def _plan_existing_managed(
        self,
        target: m.Infra.RepositoryConformTarget,
        workspace: m.Infra.WorkspaceSpec,
        codegen: m.Infra.CodegenConfigSpec,
        contract: m.Infra.CodegenConformSurfaceContract,
        identity: t.Pair[m.Infra.ProjectSpec, p.ProjectMetadata],
    ) -> p.Result[t.SequenceOf[m.Infra.CodegenFilePlan]]:
        """Plan the managed templates (and custom content) for an existing tree.

        One original source epoch serves the whole plan. Failures return as
        data; only a source cohort that passed verification is recorded as
        completed, so a later failure retains exactly that verified output.

        Returns:
            The resulting ``p.Result[t.SequenceOf[m.Infra.CodegenFilePlan]]``.

        """
        result_type = r[t.SequenceOf[m.Infra.CodegenFilePlan]]
        managed_started = time.monotonic()
        u.Cli.info(f"  stage=managed-artifacts repository={target.repository.name}")
        managed_artifacts = u.Infra.snapshot_committed_project_managed_artifacts(
            target.root,
            read_committed_directory=u.Infra.git_committed_directory_blobs,
        )
        if managed_artifacts.failure:
            return result_type.from_failure(managed_artifacts)
        u.Cli.info(
            f"  stage=managed-artifacts repository={target.repository.name} "
            f"elapsed={time.monotonic() - managed_started:.2f}s",
        )
        if not (contract.tooling or contract.custom):
            untooled_runtime = self._existing_untooled_runtime(
                target, codegen, contract, identity, managed_artifacts.value
            )
            return (
                result_type.from_failure(untooled_runtime)
                if untooled_runtime is not None and untooled_runtime.failure
                else self._plan_existing_templates(
                    render_inputs=self.resolve_render_inputs(
                        target=target,
                        workspace=workspace,
                        codegen=codegen,
                        tooling_runtime=(
                            None if untooled_runtime is None else untooled_runtime.value
                        ),
                        managed_artifacts=managed_artifacts.value,
                    ),
                    contract=contract,
                )
            )
        managed_started = time.monotonic()
        sources = self._existing_managed_sources(target, codegen, contract)
        if sources.failure:
            return result_type.from_failure(sources)
        custom, initializers = sources.value[1], sources.value[2]
        publications: list[t.Pair[Path, m.Infra.CodegenPhaseAnalysis]] = []
        with self._source_view(
            target.root,
            source_states=sources.value[3],
            declared_files=sources.value[0],
            source_publications=publications,
        ) as binding:
            with binding[0].source_consumption() as consumption:
                if contract.custom:
                    import_graph, _modules = u.Infra.snapshot_import_graph(binding[0])
                    cycles = u.Infra.project_import_cycles(import_graph)
                    if cycles:
                        return result_type.fail(
                            f"projected runtime import cycle: {sorted(cycles)}"
                        )
                if (
                    contract.custom
                    and self.state.planning_exception is None
                    and not self.state.planning_issues
                ):
                    self.state.completed_source_plans = sources.value[0]
                tooling_runtime = None
                if contract.tooling:
                    tooling_context = self._existing_tooling_context(
                        self._existing_tooling_request(
                            target, identity, codegen, (*initializers, *custom)
                        ),
                        managed_artifacts.value.resolution,
                        source_project=binding[0],
                    )
                    if tooling_context.failure:
                        return result_type.from_failure(tooling_context)
                    tooling_runtime = tooling_context.value
                    u.Cli.info(
                        f"  stage=tooling-context repository={target.repository.name} "
                        f"elapsed={time.monotonic() - managed_started:.2f}s",
                    )
                render_inputs = self.resolve_render_inputs(
                    target=target,
                    workspace=workspace,
                    codegen=codegen,
                    tooling_runtime=tooling_runtime,
                    managed_artifacts=managed_artifacts.value,
                )
                rendered = self._render_existing_managed(
                    render_inputs,
                    contract,
                    initializers,
                    custom,
                    source_project=binding[0],
                )
            return rendered.flat_map(
                lambda completed: self._qualified_existing_tooling(
                    render_inputs, contract, completed, consumption, publications
                )
            )

    def _existing_untooled_runtime(
        self,
        target: m.Infra.RepositoryConformTarget,
        codegen: m.Infra.CodegenConfigSpec,
        contract: m.Infra.CodegenConformSurfaceContract,
        identity: t.Pair[m.Infra.ProjectSpec, p.ProjectMetadata],
        managed_artifacts: m.Infra.ProjectManagedArtifactsSnapshot,
    ) -> p.Result[m.Infra.ToolingRuntimeContext] | None:
        """Resolve only the runtime consumed by an untooled template surface.

        Returns:
            The elected pyproject runtime, no runtime, or its original failure.

        """
        if contract.pyproject:
            return FlextInfraPyprojectModernizer(
                repository_root=target.root,
                skip_check=True,
                managed_artifacts=managed_artifacts.resolution,
            ).resolve_tooling_context(
                self._existing_tooling_request(target, identity, codegen, ()),
                derive_runtime=False,
            )
        return None

    def _existing_managed_sources(
        self,
        target: m.Infra.RepositoryConformTarget,
        codegen: m.Infra.CodegenConfigSpec,
        contract: m.Infra.CodegenConformSurfaceContract,
    ) -> p.Result[
        tuple[
            t.VariadicTuple[m.Infra.CodegenFilePlan],
            t.SequenceOf[m.Infra.CodegenFilePlan],
            t.VariadicTuple[m.Infra.CodegenFilePlan],
            t.VariadicTuple[m.Cli.AtomicFileState],
        ]
    ]:
        """Compose custom declarations and exports in their captured source epochs.

        Returns:
            Projected files, custom files, initializers and authenticated inputs.

        """
        result_type = r[
            tuple[
                t.VariadicTuple[m.Infra.CodegenFilePlan],
                t.SequenceOf[m.Infra.CodegenFilePlan],
                t.VariadicTuple[m.Infra.CodegenFilePlan],
                t.VariadicTuple[m.Cli.AtomicFileState],
            ]
        ]
        root = target.root
        metadata_only = (
            contract.destinations is not None
            and contract.destinations <= self._pyproject_destinations(codegen)
        )
        if metadata_only:
            # Metadata-only planning keeps managed projections and authenticated
            # source capture, but does not elect Python lazy initializers.
            lazy_result = r[
                t.Pair[
                    t.SequenceOf[m.Infra.CodegenFilePlan],
                    t.VariadicTuple[m.Cli.AtomicFileState],
                ]
            ].ok(((), ()))
        else:
            lazy_result = self._existing_lazy_sources(root)
        providers = self.state.provider_plans
        if providers is not None:
            lazy_result = lazy_result.map(
                lambda initial: (
                    (
                        *(plan for plan in providers if plan.project != root),
                        *initial[0],
                    ),
                    initial[1],
                )
            )
        if lazy_result.failure:
            return result_type.from_failure(lazy_result)
        cohort = tuple(
            {
                plan.path: plan
                for plan in (
                    *(plan for plan in providers or () if plan.project != root),
                    *lazy_result.value[0],
                )
            }.values()
        )
        if not contract.custom:
            return (
                self._projected_exports(root, lazy_result.value[1], cohort).map(
                    lambda projected: (
                        (*cohort, *projected[0]),
                        (),
                        tuple(projected[0]),
                        projected[1],
                    )
                )
                if metadata_only
                else result_type.ok((
                    cohort,
                    (),
                    tuple(lazy_result.value[0]),
                    lazy_result.value[1],
                ))
            )
        started = time.monotonic()
        publications: list[t.Pair[Path, m.Infra.CodegenPhaseAnalysis]] = []
        with self._source_view(
            root,
            source_states=lazy_result.value[1],
            declared_files=cohort,
            source_publications=publications,
        ) as binding:
            with binding[0].source_consumption() as consumption:
                custom_result = (
                    self._plan_existing_custom(
                        root,
                        codegen,
                        profile=target.make_profile.value,
                        binding=binding,
                        declared_files=cohort,
                    )
                    if contract.custom
                    else r[t.SequenceOf[m.Infra.CodegenFilePlan]].ok(())
                )
                if custom_result.failure:
                    return result_type.from_failure(custom_result)
            publications.extend(
                (plan.path, consumption.receipt()) for plan in custom_result.value
            )
            custom_inputs = u.Infra.unique_states((
                *lazy_result.value[1],
                *binding[1]()[0],
                *(
                    state
                    for plan in custom_result.value
                    for state in plan.source_states
                ),
            ))
            if custom_inputs.failure:
                return result_type.from_failure(custom_inputs)
        u.Cli.info(
            f"  stage=custom-facades repository={root.name} "
            f"elapsed={time.monotonic() - started:.2f}s"
        )
        projected_files = {plan.path: plan for plan in (*cohort, *custom_result.value)}
        exported: t.SequenceOf[m.Infra.CodegenFilePlan] = ()
        projected_inputs = custom_inputs.value
        # Exports re-derive only when this surface elected no initializer yet or
        # custom planning changed a Python source; otherwise the elected
        # initializers already describe these exact sources.
        if metadata_only or any(
            plan.path.suffix == c.Infra.EXT_PYTHON
            and u.Infra.codegen_file_requires_effect(plan)
            for plan in custom_result.value
        ):
            planned_exports = self._projected_exports(
                root, projected_inputs, tuple(projected_files.values())
            )
            if planned_exports.failure:
                return result_type.from_failure(planned_exports)
            exported, projected_inputs = planned_exports.value
        projected_files.update((plan.path, plan) for plan in exported)
        initializers = tuple(
            {
                plan.path: plan
                for plan in (*lazy_result.value[0], *exported)
                if plan.project == root
            }.values()
        )
        return result_type.ok((
            tuple(projected_files.values()),
            custom_result.value,
            initializers,
            projected_inputs,
        ))

    def _projected_exports(
        self,
        root: Path,
        inputs: t.VariadicTuple[m.Cli.AtomicFileState],
        declared: t.VariadicTuple[m.Infra.CodegenFilePlan],
    ) -> p.Result[
        t.Pair[
            t.SequenceOf[m.Infra.CodegenFilePlan],
            t.VariadicTuple[m.Cli.AtomicFileState],
        ]
    ]:
        """Re-plan initializers over one repository's projected sources.

        Returns:
            The export plans and the merged input witnesses they consumed.

        """
        result_type = r[
            t.Pair[
                t.SequenceOf[m.Infra.CodegenFilePlan],
                t.VariadicTuple[m.Cli.AtomicFileState],
            ]
        ]
        publications: list[t.Pair[Path, m.Infra.CodegenPhaseAnalysis]] = []
        with self._source_view(
            root,
            source_states=inputs,
            declared_files=declared,
            source_publications=publications,
        ) as projected:
            exports = FlextInfraCodegenLazyInit(
                repository_root=root, project_scope_roots=(root,)
            ).plan_files(source_project=projected[0], source_publications=publications)
            if exports.failure:
                return result_type.from_failure(exports)
            self._retain_diagnostics(
                exports.value.exception,
                issues=exports.value.issues,
                failed_targets=exports.value.failed_targets,
            )
            files = exports.value.files
            merged = u.Infra.unique_states((
                *inputs,
                *projected[1]()[0],
                *(state for plan in files for state in plan.source_states),
            ))
            if merged.failure:
                return result_type.from_failure(merged)
        return result_type.ok((files, merged.value))

    def _existing_lazy_sources(
        self,
        root: Path,
    ) -> p.Result[
        t.Pair[
            t.SequenceOf[m.Infra.CodegenFilePlan],
            t.VariadicTuple[m.Cli.AtomicFileState],
        ]
    ]:
        """Elect repository providers and retain their original source evidence.

        Returns:
            Planned initializers and their unique original source states.

        """
        result_type = r[
            t.Pair[
                t.SequenceOf[m.Infra.CodegenFilePlan],
                t.VariadicTuple[m.Cli.AtomicFileState],
            ]
        ]
        planned = (
            self._planned_lazy_init_files(root)
            if self.state.provider_plans is None
            else r[t.SequenceOf[m.Infra.CodegenFilePlan]].ok(
                tuple(
                    plan for plan in self.state.provider_plans if plan.project == root
                )
            )
        )
        if planned.failure:
            return result_type.from_failure(planned)
        sources = u.Infra.unique_states(
            tuple(state for plan in planned.value for state in plan.source_states)
        )
        if sources.failure:
            return result_type.from_failure(sources)
        return result_type.ok((planned.value, sources.value))

    def _render_existing_managed(
        self,
        render_inputs: m.Infra.CodegenRenderInputs,
        contract: m.Infra.CodegenConformSurfaceContract,
        initializers: t.SequenceOf[m.Infra.CodegenFilePlan],
        custom: t.SequenceOf[m.Infra.CodegenFilePlan],
        *,
        source_project: p.Infra.RopeProject,
    ) -> p.Result[t.SequenceOf[m.Infra.CodegenFilePlan]]:
        """Render both template passes through the same native source project.

        Returns:
            Final templates and their dependent facade publication groups.

        """
        managed = self._plan_existing_templates(
            render_inputs=render_inputs,
            contract=contract,
        )
        if managed.failure:
            return r[t.SequenceOf[m.Infra.CodegenFilePlan]].from_failure(managed)
        tooling = render_inputs.tooling_runtime
        if contract.pyproject:
            render_inputs.tooling_runtime = self.planned_source_tooling(
                render_inputs,
                [*initializers, *managed.value, *custom],
                source_project=source_project,
            )
        templates = (
            self._plan_existing_templates(
                render_inputs=render_inputs,
                contract=contract,
            )
            if render_inputs.tooling_runtime is not tooling
            else managed
        )
        if templates.failure:
            return r[t.SequenceOf[m.Infra.CodegenFilePlan]].from_failure(templates)
        return self._facade_runtime_plans(
            render_inputs.target.root,
            (*templates.value, *custom),
            custom,
            initializers,
            complete_governed=contract.complete_governed,
        )

    @staticmethod
    def _qualified_existing_tooling(
        render_inputs: m.Infra.CodegenRenderInputs,
        contract: m.Infra.CodegenConformSurfaceContract,
        planned: t.SequenceOf[m.Infra.CodegenFilePlan],
        consumption: p.Infra.RopeSourceConsumption,
        publications: list[t.Pair[Path, m.Infra.CodegenPhaseAnalysis]],
    ) -> p.Result[t.SequenceOf[m.Infra.CodegenFilePlan]]:
        """Bind consumed evidence to the pyproject output inside its source epoch.

        The consumption context must be closed while its source view remains
        open, so the receipt contains the completed native capture.

        Returns:
            File plans retaining their original and consumed native receipts.

        """
        receipt = consumption.receipt()
        states = receipt.inputs
        directories = receipt.source_directories
        topology = receipt.source_query_topology
        qualified: list[m.Infra.CodegenFilePlan] = []
        for file in planned:
            if (
                file.path != render_inputs.target.root / c.PYPROJECT_FILENAME
                or not contract.tooling
            ):
                qualified.append(file)
                continue
            publications.append((file.path, receipt))
            inputs = u.Infra.unique_states((
                *file.source_states,
                *states,
            ))
            if inputs.failure:
                return r[t.SequenceOf[m.Infra.CodegenFilePlan]].from_failure(inputs)
            queried, chains = u.Cli.atomic_merge_directory_query_receipts(
                (*file.source_directories, *directories),
                (*file.source_query_topology, *topology),
            )
            qualified.append(
                file.model_copy(
                    update={
                        "source_states": inputs.value,
                        "source_directories": queried,
                        "source_query_topology": chains,
                    }
                )
            )
        return r[t.SequenceOf[m.Infra.CodegenFilePlan]].ok(tuple(qualified))

    @staticmethod
    def _facade_runtime_plans(
        root: Path,
        planned: t.SequenceOf[m.Infra.CodegenFilePlan],
        custom: t.SequenceOf[m.Infra.CodegenFilePlan],
        initializers: t.SequenceOf[m.Infra.CodegenFilePlan],
        *,
        complete_governed: bool,
    ) -> p.Result[t.SequenceOf[m.Infra.CodegenFilePlan]]:
        """Compose the projections consumed by the publication's native checks.

        Complete generation retains every initializer. Facade consumers share
        their declared source group; other outputs retain their own native
        dependency and election receipts.

        Returns:
            Original plans grouped with the generated sources their checks consume.

        """
        result_type = r[t.SequenceOf[m.Infra.CodegenFilePlan]]
        facades = tuple(
            item for item in custom if item.path.suffix == c.Infra.EXT_PYTHON
        )
        packages = {item.path.parent for item in facades}
        if not packages and not complete_governed:
            return result_type.ok(tuple(planned))
        families = tuple(
            package / family.directory
            for package in packages
            for family in u.Infra.facade_families().values()
        )
        barrels = tuple(
            item
            for item in initializers
            if (
                complete_governed
                or item.path.name != c.Infra.INIT_PY
                or item.path.parent in packages
                or any(item.path.is_relative_to(family) for family in families)
            )
        )
        by_path = {item.path: item for item in planned}
        for barrel in barrels:
            existing = by_path.get(barrel.path)
            if existing is not None and existing != barrel:
                return result_type.fail(
                    f"runtime barrel has competing bootstrap plans: {barrel.path}"
                )
        if complete_governed:
            by_path.update((item.path, item) for item in barrels)
        grouped_paths = {
            item.path
            for item in (*barrels, *facades)
            if item.path.parent in packages
            or any(item.path.is_relative_to(family) for family in families)
        }
        if not complete_governed:
            by_path.update((item.path, item) for item in (*barrels, *facades))
        group = f"{c.Infra.CodegenConformSurface.FACADES.value}:{root}"
        return result_type.ok((
            *(
                item.model_copy(update={"dependency_group": group})
                if item.path in grouped_paths
                else item
                for item in by_path.values()
            ),
        ))

    def _planned_lazy_init_files(
        self,
        root: Path,
    ) -> p.Result[t.SequenceOf[m.Infra.CodegenFilePlan]]:
        """Plan the lazy-init projection the declarations determine, read-only.

        Facades import family owners in package form, which resolves only
        through the package initializer the declaring modules' ``__all__``
        project. Tooling derivations therefore read the planned initializers,
        never the previous projection on disk: a stale initializer otherwise
        blocks its own regeneration, on every conform surface (a partial
        surface such as ``dependencies`` derives tooling too). Required runtime
        barrels join their facade consumers in the bootstrap dependency group.
        Complete generation stages every initializer before its project-wide
        admission; narrower surfaces retain their declared publication scope.

        Returns:
            The repository's planned lazy-init file plans, or the planning failure.

        """
        planned = FlextInfraCodegenLazyInit(
            repository_root=root,
            project_scope_roots=(root,),
        ).plan_files()
        if planned.failure:
            return r[t.SequenceOf[m.Infra.CodegenFilePlan]].from_failure(planned)
        self._retain_diagnostics(
            planned.value.exception,
            issues=planned.value.issues,
            failed_targets=planned.value.failed_targets,
        )
        return r[t.SequenceOf[m.Infra.CodegenFilePlan]].ok(planned.value.files)

    @staticmethod
    def _existing_tooling_context(
        request: m.Infra.ToolingContextRequest,
        managed_resolution: m.Infra.ProjectManagedArtifactsResolution,
        *,
        source_project: p.Infra.RopeProject,
    ) -> p.Result[m.Infra.ToolingRuntimeContext]:
        """Resolve tooling through its canonical request and captured artifacts.

        Returns:
            The modernizer's tooling context or its original failure.

        """
        modernizer = FlextInfraPyprojectModernizer(
            repository_root=request.path.parent,
            skip_check=True,
            managed_artifacts=managed_resolution,
        )
        return modernizer.resolve_tooling_context(
            request,
            source_project=source_project,
        )

    def _existing_tooling_request(
        self,
        target: m.Infra.RepositoryConformTarget,
        identity: t.Pair[m.Infra.ProjectSpec, p.ProjectMetadata],
        codegen: m.Infra.CodegenConfigSpec,
        planned: t.SequenceOf[m.Infra.CodegenFilePlan],
    ) -> m.Infra.ToolingContextRequest:
        """Declare tooling inputs from the existing repository's native identity.

        Returns:
            The canonical request consumed by the modernizer.

        """
        root = target.root
        repository = target.repository
        project, metadata = identity
        return m.Infra.ToolingContextRequest(
            # Attached members resolve through the canonical workspace runtime
            # owner: runtime_environment_dir derives the superproject root when
            # the checkout is a submodule, and the checkout's own root otherwise.
            environment_dir=u.Infra.runtime_environment_dir(root),
            planned_sources={
                plan.path: plan.desired_content.decode(c.DEFAULT_ENCODING)
                for plan in planned
                if plan.path.suffix == c.Infra.EXT_PYTHON
                and plan.desired_content is not None
            },
            project_name=repository.distribution,
            package_name=metadata.package_name,
            path=root / c.PYPROJECT_FILENAME,
            scaffold_project=codegen.scaffold.project,
            runtime_dependency_overlay=project.runtime_dependency_overlay,
            declared_project_dependencies=metadata.project.dependencies,
            topology=m.Infra.PyprojectDeclaredTopology(
                root_modules=(
                    target.project.root_modules if target.project is not None else ()
                ),
                root_packages=(
                    target.project.root_packages if target.project is not None else ()
                ),
                repository_namespace_packages=(
                    target.project.repository_namespace_packages
                    if target.project is not None
                    else ()
                ),
                packaged_data_paths=(
                    target.project.packaged_data_paths
                    if target.project is not None
                    else ()
                ),
                packaged_data_excludes=(
                    target.project.packaged_data_excludes
                    if target.project is not None
                    else ()
                ),
                declared_python_dirs=tuple(
                    self._scaffold_python_dirs(
                        codegen.templates.entries,
                        target.make_profile,
                        package=repository.package,
                    ),
                ),
                analysis_exclusions=tuple(
                    path.as_posix() for path in target.external_dependency_paths
                ),
            ),
        )

    def _plan_existing_bootstrap(
        self,
        target: m.Infra.RepositoryConformTarget,
        workspace: m.Infra.WorkspaceSpec,
        codegen: m.Infra.CodegenConfigSpec,
    ) -> p.Result[t.SequenceOf[m.Infra.CodegenFilePlan]]:
        """Render the bootstrap Make surface before sibling checkouts exist.

        Every destination of the surface renders from the one Makefile spec:
        the lock publisher the bootstrap runs reads only its Mise contract.

        Returns:
            One file plan per bootstrap destination, in destination order.

        """
        context = self._makefile_render_spec(target, workspace, codegen)
        if context.failure:
            return r[t.SequenceOf[m.Infra.CodegenFilePlan]].from_failure(context)
        plans: list[m.Infra.CodegenFilePlan] = []
        for destination in sorted(
            codegen.templates.required_destinations(
                c.Infra.MAKEFILE_BOOTSTRAP_DESTINATIONS,
            ),
        ):
            planned = self._bootstrap_destination_plan(
                target,
                codegen,
                context.value,
                destination,
            )
            if planned.failure:
                return r[t.SequenceOf[m.Infra.CodegenFilePlan]].from_failure(planned)
            plans.append(planned.value)
        return self._artifact_dependency_plans(codegen, target.root, plans)

    def _bootstrap_destination_plan(
        self,
        target: m.Infra.RepositoryConformTarget,
        codegen: m.Infra.CodegenConfigSpec,
        context: p.Model,
        destination: str,
    ) -> p.Result[m.Infra.CodegenFilePlan]:
        """Render and plan exactly one bootstrap destination.

        Returns:
            The resulting ``p.Result[m.Infra.CodegenFilePlan]``.

        """
        result_type = r[m.Infra.CodegenFilePlan]
        binding = self._bootstrap_template_binding(target, codegen, destination)
        if binding.failure:
            return result_type.from_failure(binding)
        _template, managed_spec = binding.value
        entry = next(
            item
            for item in codegen.templates.entries
            if item.destination == destination
        )
        rendered = self.render_artifact_source(codegen, entry, context)
        if rendered.failure:
            return result_type.from_failure(rendered)
        content = rendered.value.rendered
        sources = rendered.value.source_states
        conflict_marker = u.Infra.first_merge_conflict_marker(content)
        if conflict_marker is not None:
            return result_type.fail(
                f"rendered {destination} contains a merge conflict marker: "
                f"{conflict_marker}",
            )
        if destination == c.Infra.MISE_TOML_FILENAME:
            composed = self._composed_mise_overlay(target.root, content, None)
            if composed.failure:
                return result_type.from_failure(composed)
            content = composed.value.rendered
            sources = (*sources, *composed.value.source_states)
        captured = u.Infra.unique_states(sources)
        if captured.failure:
            return result_type.from_failure(captured)
        return self.file_plan(
            target.root,
            destination,
            rendered.value.model_copy(update={"rendered": content}),
            mode=managed_spec.mode,
            source_states=captured.value,
        ).map(
            lambda plan: plan.model_copy(
                update={
                    "owner": managed_spec.owner,
                    "policy": managed_spec.policy,
                    "tracking": managed_spec.tracking,
                }
            ),
        )

    @classmethod
    def _bootstrap_template_binding(
        cls,
        target: m.Infra.RepositoryConformTarget,
        codegen: m.Infra.CodegenConfigSpec,
        destination: str,
    ) -> p.Result[t.Pair[Path, m.Infra.ManagedFileSpec]]:
        """Resolve the single render template and managed spec of a destination.

        Args:
            target: The conform target whose profile selects templates.
            codegen: The codegen configuration owning template entries.
            destination: The bootstrap destination being planned.

        Returns:
            The authenticated template path with its managed-file spec, or a
            failure when the destination lacks a unique binding.

        """
        result_type = r[t.Pair[Path, m.Infra.ManagedFileSpec]]
        entries = tuple(
            entry
            for entry in codegen.templates.entries
            if entry.destination == destination
            and entry.source is not None
            and target.make_profile in entry.profiles
        )
        if len(entries) != 1 or entries[0].source is None:
            return result_type.fail(
                f"{destination} requires exactly one render template for its profile",
            )
        managed = tuple(
            item
            for item in codegen.managed_file_specs
            if item.path == Path(destination)
        )
        if len(managed) != 1:
            return result_type.fail(
                f"{destination} requires exactly one managed-file declaration",
            )
        template = u.Infra.codegen_artifact_source(codegen, entries[0])
        return result_type.ok((template, managed[0]))

    def _plan_existing_docs_config(
        self,
        target: m.Infra.RepositoryConformTarget,
        workspace: m.Infra.WorkspaceSpec,
        codegen: m.Infra.CodegenConfigSpec,
        destination: str,
    ) -> p.Result[t.SequenceOf[m.Infra.CodegenFilePlan]]:
        """Render the declared docs policy before consumers parse its projection.

        Returns:
            The resulting ``p.Result[t.SequenceOf[m.Infra.CodegenFilePlan]]``.

        """
        entries = tuple(
            entry
            for entry in codegen.templates.entries
            if entry.destination == destination
            and entry.source is not None
            and target.make_profile in entry.profiles
        )
        managed = tuple(
            item
            for item in codegen.managed_file_specs
            if item.path == Path(destination)
        )
        if len(entries) != 1 or entries[0].source is None or len(managed) != 1:
            return r[t.SequenceOf[m.Infra.CodegenFilePlan]].fail(
                f"docs config requires one declared render template "
                f"and owner: {destination}",
            )
        template = u.Infra.codegen_templates_root(codegen) / entries[0].source
        rendered = u.Cli.template_render_authenticated(template, workspace)
        if rendered.failure:
            return r[t.SequenceOf[m.Infra.CodegenFilePlan]].from_failure(rendered)
        parsed = u.Cli.json_loads(rendered.value.rendered)
        if parsed.failure:
            return r[t.SequenceOf[m.Infra.CodegenFilePlan]].from_failure(parsed)
        plan = self.file_plan(
            target.root,
            destination,
            rendered.value.rendered,
            mode=managed[0].mode,
            source_states=rendered.value.source_states,
        )
        if plan.failure:
            return r[t.SequenceOf[m.Infra.CodegenFilePlan]].from_failure(plan)
        return r[t.SequenceOf[m.Infra.CodegenFilePlan]].ok((plan.value,))

    def _plan_existing_templates(
        self,
        *,
        render_inputs: m.Infra.CodegenRenderInputs,
        contract: m.Infra.CodegenConformSurfaceContract,
    ) -> p.Result[t.SequenceOf[m.Infra.CodegenFilePlan]]:
        """Render the managed-file templates for an existing tree.

        Returns:
            The resulting ``p.Result[t.SequenceOf[m.Infra.CodegenFilePlan]]``.

        """
        target = render_inputs.target
        workspace = render_inputs.workspace
        codegen = render_inputs.codegen
        root = target.root
        u.Cli.info(f"  stage=templates repository={target.repository.name}")
        profile = target.make_profile
        planned: list[m.Infra.CodegenFilePlan] = []
        # The pyproject plans first: renders that derive from its requirements
        # (the dependabot cooldown exclusion) read the planned bytes.
        for managed in sorted(
            codegen.managed_file_specs,
            key=lambda item: item.path != Path(c.PYPROJECT_FILENAME),
        ):
            if self._managed_file_skipped(
                render_inputs,
                contract,
                managed,
            ):
                continue
            resolved = self._managed_render_entry(codegen, workspace, root, managed)
            if resolved.failure:
                self._record_file_failure(
                    root / managed.path,
                    resolved.error or "managed file resolution failed",
                )
                continue
            (entry, path), present = resolved.value
            if not present or entry is None or path is None:
                continue
            if profile not in entry.profiles or (
                entry.requires_release_protocol and not target.publishes_release
            ):
                if managed.policy != c.Infra.MANAGED_FILE_POLICY_FULL:
                    continue
                # Profile- and capability-excluded workflows must not keep firing.
                # Conform, rather than a user, retires the generated orphan.
                orphan = self._retired_workflow_orphan(
                    render_inputs,
                    managed,
                    entry,
                    path,
                )
                if orphan.failure:
                    self._record_file_failure(
                        path,
                        orphan.error or "managed file retirement failed",
                    )
                    continue
                planned.extend(orphan.value)
                continue
            try:
                rendered = self._rendered_managed_plan(
                    render_inputs,
                    managed,
                    entry,
                    path,
                )
            except (OSError, ValueError) as exception:
                self._record_file_failure(
                    path,
                    traceback.format_exc(),
                    exception=exception,
                )
                continue
            if rendered.failure:
                self._record_file_failure(
                    path,
                    rendered.error or "managed file rendering failed",
                )
                continue
            planned.append(rendered.value)
        return self._artifact_dependency_plans(codegen, root, planned)

    @staticmethod
    def _managed_file_skipped(
        render_inputs: m.Infra.CodegenRenderInputs,
        contract: m.Infra.CodegenConformSurfaceContract,
        managed: m.Infra.ManagedFileSpec,
    ) -> bool:
        """Whether this managed file is out of scope for the current surface.

        Returns:
            True when the file is skipped before any template resolution.

        """
        target = render_inputs.target
        codegen = render_inputs.codegen
        if target.beads is None and managed.path.parts[:1] == (".beads",):
            return True
        if not target.ci_enabled and managed.path.parts[:2] == (
            ".github",
            "workflows",
        ):
            return True
        if (
            contract.destinations is not None
            and managed.path.as_posix()
            not in codegen.templates.required_destinations(
                contract.destinations,
            )
        ):
            return True
        return managed.path == Path(c.PYPROJECT_FILENAME) and not contract.pyproject

    @staticmethod
    def _managed_render_entry(
        codegen: m.Infra.CodegenConfigSpec,
        workspace: m.Infra.WorkspaceSpec,
        root: Path,
        managed: m.Infra.ManagedFileSpec,
    ) -> p.Result[t.Pair[t.Pair[m.Infra.TemplateEntrySpec | None, Path | None], bool]]:
        """Resolve the single render template entry and its physical target path.

        Returns:
            The resulting ``p.Result[t.Pair[t.Pair[m.Infra.TemplateEntrySpec |
            None, Path | None], bool]]`` where the boolean selects template
            rendering rather than an absent capability or specialized owner.

        """
        result_type = r[
            t.Pair[t.Pair[m.Infra.TemplateEntrySpec | None, Path | None], bool]
        ]
        entries = tuple(
            entry
            for entry in codegen.templates.entries
            if entry.destination == managed.path.as_posix()
        )
        if not entries:
            return result_type.fail(
                f"managed file has no artifact declaration: {managed.path}",
            )
        if len(entries) != 1:
            return result_type.fail(
                f"managed file requires exactly one render template: {managed.path}",
            )
        entry = entries[0]
        if entry.requires_beads and workspace.beads is None:
            return result_type.ok(((None, None), False))
        path = FlextInfraCodegenConformExistingPlan._managed_entry_path(root, entry)
        if path.failure:
            return result_type.from_failure(path)
        return result_type.ok(((entry, path.value), entry.source is not None))

    @staticmethod
    def _managed_entry_path(
        root: Path,
        entry: m.Infra.TemplateEntrySpec,
    ) -> p.Result[Path]:
        """Resolve and confine one managed destination inside the repository root.

        Returns:
            The resulting ``p.Result[Path]``.

        """
        relative = Path(entry.destination)
        if relative.is_absolute() or ".." in relative.parts:
            return r[Path].fail(
                f"managed destination escapes repository root: {entry.destination}",
            )
        path = (root / relative).resolve()
        if not path.is_relative_to(root.resolve()):
            return r[Path].fail(
                f"managed destination escapes repository root: {entry.destination}",
            )
        return r[Path].ok(path)

    def _retired_workflow_orphan(
        self,
        render_inputs: m.Infra.CodegenRenderInputs,
        managed: m.Infra.ManagedFileSpec,
        entry: m.Infra.TemplateEntrySpec,
        path: Path,
    ) -> p.Result[t.VariadicTuple[m.Infra.CodegenFilePlan]]:
        """Retire one inapplicable full-owned artifact through its catalog owner.

        The same declaration authorizes updates and retirement. Native snapshots
        bind the original destination and current template inputs; historical
        machine-local receipts and file headers are not ownership inputs.

        Returns:
            The owned retirement plan, or no effects for an absent destination.

        """
        result_type = r[t.VariadicTuple[m.Infra.CodegenFilePlan]]
        if (
            entry.ownership is None
            or entry.ownership.policy != c.Infra.MANAGED_FILE_POLICY_FULL
            or managed.policy != c.Infra.MANAGED_FILE_POLICY_FULL
            or entry.source is None
        ):
            return result_type.fail(
                f"artifact retirement requires full template ownership: {path}",
            )
        target = render_inputs.target
        if target.make_profile in entry.profiles and (
            not entry.requires_release_protocol or target.publishes_release
        ):
            return result_type.fail(
                f"applicable catalog artifact cannot be retired: {path}",
            )
        if not path.exists() and not path.is_symlink():
            return result_type.ok(())
        templates = u.Cli.template_capture_sources((
            u.Infra.codegen_templates_root(render_inputs.codegen) / entry.source,
        ))
        if templates.failure:
            return result_type.from_failure(templates)
        orphan = self._absent_file_plan(render_inputs.target.root, path)
        if orphan.failure:
            return result_type.from_failure(orphan)
        sources = u.Infra.unique_states((
            *orphan.value.source_states,
            *templates.value,
        ))
        return sources.map(
            lambda captured: (
                orphan.value.model_copy(
                    update={
                        "source_states": captured,
                        "owner": managed.owner,
                        "policy": managed.policy,
                    },
                ),
            ),
        )

    def _rendered_managed_plan(
        self,
        render_inputs: m.Infra.CodegenRenderInputs,
        managed: m.Infra.ManagedFileSpec,
        entry: m.Infra.TemplateEntrySpec,
        path: Path,
    ) -> p.Result[m.Infra.CodegenFilePlan]:
        """Render, compose, record, and plan one managed artifact.

        Returns:
            The finalized file plan using this operation's existing render state.

        """
        result_type = r[m.Infra.CodegenFilePlan]
        root = render_inputs.target.root
        rendered = (
            r[m.Infra.CodegenArtifactComposition].fail(
                f"managed render entry has no template source: {entry.destination}",
            )
            if entry.source is None
            else self._rendered_artifact_source(
                render_inputs,
                entry=entry,
                destination=entry.destination,
                failure_prefix="",
                project_context=None,
            )
        )
        if rendered.failure:
            u.Cli.error(
                f"artifact render failed: {entry.destination}: {rendered.error}"
            )
            return result_type.from_failure(rendered)
        composed = (
            rendered
            if entry.source_kind == "resource"
            else self.compose_project_artifact(
                root,
                entry.destination,
                rendered.value.rendered,
                render_inputs=render_inputs,
                source_states=rendered.value.source_states,
            )
        )
        if composed.failure:
            u.Cli.error(
                f"artifact composition failed: {entry.destination}: {composed.error}"
            )
            return result_type.from_failure(composed)
        rendered_content = composed.value.rendered
        names = None
        if entry.destination == c.PYPROJECT_FILENAME:
            names = self.direct_sources(render_inputs, composed=rendered_content)
            if names.failure:
                return result_type.from_failure(names)
        conflict_marker = u.Infra.first_merge_conflict_marker(rendered_content)
        if conflict_marker is not None:
            return result_type.fail(
                "rendered template contains a merge conflict marker: "
                f"source={entry.source}; target={path}; root={root}; "
                f"marker={conflict_marker}",
            )
        planned = self.file_plan(
            root,
            entry.destination,
            composed.value,
            mode=managed.mode,
        )
        if planned.success and names is not None:
            render_inputs.planned_direct_sources = names.value
        return planned.map(
            lambda file: file.model_copy(
                update={
                    "owner": managed.owner,
                    "policy": managed.policy,
                    "tracking": managed.tracking,
                }
            ),
        )

    def _plan_existing_custom(
        self,
        root: Path,
        config: m.Infra.CodegenConfigSpec,
        *,
        profile: str | None = None,
        binding: t.Triple[
            p.Infra.RopeProject,
            Callable[
                [],
                t.Triple[
                    tuple[m.Cli.AtomicFileState, ...],
                    tuple[m.Cli.AtomicDirectoryInventory, ...],
                    tuple[m.Cli.AtomicDirectoryChainPlan, ...],
                ],
            ],
            t.MappingKV[Path, str],
        ],
        declared_files: t.VariadicTuple[m.Infra.CodegenFilePlan] = (),
    ) -> p.Result[t.SequenceOf[m.Infra.CodegenFilePlan]]:
        """Validate custom Make content and stage dependency-ordered family facades.

        Existing handwritten Make content is validated against the selected
        profile policy. The canonical source inventory contributes declared
        facade families from every owned package, including internal test and
        auxiliary namespaces. Each subsequent family binds the prior candidate,
        while its receipts continue to authenticate the original source epoch.
        This method returns file plans; it does not publish their contents.

        Returns:
            The custom Make and facade plans, or a typed validation failure.

        """
        policy = config.make.custom_handler_policies.get(
            profile or "",
            config.make.custom_handler_policy,
        )
        plans: list[m.Infra.CodegenFilePlan] = []
        make_plan = self._validated_custom_make_plan(root, policy)
        if make_plan.failure:
            self._record_file_failure(
                root / policy.filename,
                make_plan.error or "custom Make planning failed",
            )
        else:
            make_plan_value, make_plan_present = make_plan.value
            if make_plan_present and make_plan_value is not None:
                plans.append(make_plan_value)
        if root.is_dir():
            layout = u.Infra.layout(root)
            project, consumed, sources = binding
            package_dirs = {
                path.parent
                for path in sources
                if path.is_relative_to(root)
                and path.suffix == c.Infra.EXT_PYTHON
                and path.parent / c.Infra.INIT_PY in sources
            }
            if layout is not None and layout.class_stem:
                package_dirs.add(layout.package_dir)
            staged = {plan.path: plan for plan in declared_files}
            inputs = consumed()[0]
            for declared_family in u.Infra.facade_families().values():
                family = c.Infra.FacadeFamily(declared_family.letter)
                for package_dir in sorted(package_dirs):
                    if (
                        layout is None or package_dir != layout.package_dir
                    ) and u.Infra.facade_module_path(
                        package_dir,
                        family,
                        project=project,
                        sources=sources,
                    ) is None:
                        continue
                    projected = self._captured_facade_plan(
                        root, package_dir, family, staged, inputs
                    )
                    if projected.failure:
                        return r[t.SequenceOf[m.Infra.CodegenFilePlan]].from_failure(
                            projected
                        )
                    plans.extend(projected.value[0])
                    inputs = projected.value[1]
        return r[t.SequenceOf[m.Infra.CodegenFilePlan]].ok(tuple(plans))

    def _captured_facade_plan(
        self,
        root: Path,
        package_dir: Path,
        family: c.Infra.FacadeFamily,
        staged: t.MutableMappingKV[Path, m.Infra.CodegenFilePlan],
        inputs: t.VariadicTuple[m.Cli.AtomicFileState],
    ) -> p.Result[
        t.Pair[
            t.SequenceOf[m.Infra.CodegenFilePlan],
            t.VariadicTuple[m.Cli.AtomicFileState],
        ]
    ]:
        """Plan one family facade over the staged candidate.

        The staged plan map is updated in place; the original input witnesses
        are recaptured while the candidate binding is still consumed.

        Returns:
            The facade plans and the merged input witnesses, or the first
            planning failure.

        """
        result_type = r[
            t.Pair[
                t.SequenceOf[m.Infra.CodegenFilePlan],
                t.VariadicTuple[m.Cli.AtomicFileState],
            ]
        ]
        publications: list[t.Pair[Path, m.Infra.CodegenPhaseAnalysis]] = []
        with self._source_view(
            root,
            source_states=inputs,
            declared_files=tuple(staged.values()),
            source_publications=publications,
        ) as current:
            with current[0].source_consumption() as consumption:
                planned = self._utility_facade_plan(root, package_dir, family, current)
            receipt = consumption.receipt()
            if planned.failure:
                return result_type.from_failure(planned)
            publications.extend((plan.path, receipt) for plan in planned.value)
            files = tuple(
                plan.model_copy(
                    update={
                        "source_states": receipt.inputs,
                        "source_directories": receipt.source_directories,
                        "source_query_topology": receipt.source_query_topology,
                    }
                )
                for plan in planned.value
            )
            staged.update((plan.path, plan) for plan in files)
            captured = u.Infra.unique_states((
                *inputs,
                *current[1]()[0],
            ))
            if captured.failure:
                return result_type.from_failure(captured)
        return result_type.ok((files, captured.value))

    def _validated_custom_make_plan(
        self,
        root: Path,
        policy: m.Infra.CustomHandlerPolicy,
    ) -> p.Result[t.Pair[m.Infra.CodegenFilePlan | None, bool]]:
        """Validate and plan the existing custom Make content under its policy.

        Returns:
            The resulting ``p.Result[t.Pair[m.Infra.CodegenFilePlan | None,
            bool]]`` where the boolean marks plan presence (False: an absent
            custom Make file).

        """
        result_type = r[t.Pair[m.Infra.CodegenFilePlan | None, bool]]
        path = root / policy.filename
        if path.exists() and not path.is_file():
            return result_type.fail(
                f"custom Make destination is not a regular file: {path}",
            )
        if not path.is_file():
            return result_type.ok((None, False))
        read = u.Cli.files_read_text(path)
        if read.failure:
            return result_type.from_failure(read)
        validation = self.validate_custom_make(read.value, policy)
        if validation.failure:
            return result_type.from_failure(validation)
        planned = self.file_plan(root, policy.filename, read.value)
        if planned.failure:
            return result_type.from_failure(planned)
        return result_type.ok((planned.value, True))

    def _utility_facade_plan(
        self,
        root: Path,
        package_dir: Path,
        family: c.Infra.FacadeFamily,
        binding: t.Triple[
            p.Infra.RopeProject,
            Callable[
                [],
                t.Triple[
                    tuple[m.Cli.AtomicFileState, ...],
                    tuple[m.Cli.AtomicDirectoryInventory, ...],
                    tuple[m.Cli.AtomicDirectoryChainPlan, ...],
                ],
            ],
            t.MappingKV[Path, str],
        ],
    ) -> p.Result[t.SequenceOf[m.Infra.CodegenFilePlan]]:
        """Plan one projected facade for the discovered package layout.

        Returns:
            The owned facade file plan, or no plans for a family with no owners.

        Raises:
            ValueError: If a rendered facade has no declaring package module.

        """
        project, consumed_states, sources = binding
        result_type = r[t.SequenceOf[m.Infra.CodegenFilePlan]]
        facade_path = u.Infra.facade_module_path(
            package_dir, family, project=project, sources=sources
        )
        match family:
            case c.Infra.FacadeFamily.T:
                if facade_path is None or not project.source_query(
                    package_dir / u.Infra.facade_families()[family].directory, "isdir"
                ):
                    return result_type.ok(())
                rendered = u.Infra.render_type_facade(
                    package_dir,
                    facade_path,
                    {
                        path: u.Infra.require_file_resource(
                            project.get_resource(path.relative_to(root).as_posix()),
                            path,
                        ).read()
                        for path in sources
                    },
                    project=project,
                )
            case (
                c.Infra.FacadeFamily.C
                | c.Infra.FacadeFamily.U
                | c.Infra.FacadeFamily.P
                | c.Infra.FacadeFamily.M
            ):
                rendered = u.Infra.render_utility_facade(
                    package_dir,
                    family=family,
                    project=project,
                    sources=sources,
                )
        if rendered is None:
            return result_type.ok(())
        if facade_path is None:
            msg = f"rendered {family} facade has no declaring module"
            raise ValueError(msg)
        relative = facade_path.relative_to(root)
        utility_plan = self.file_plan(root, relative.as_posix(), rendered)
        if utility_plan.failure:
            return result_type.from_failure(utility_plan)
        states, directories, topology = consumed_states()
        inputs = u.Infra.unique_states((
            *utility_plan.value.source_states,
            *states,
        ))
        if inputs.failure:
            return result_type.from_failure(inputs)
        return result_type.ok((
            utility_plan.value.model_copy(
                update={
                    "source_states": inputs.value,
                    "source_directories": directories,
                    "source_query_topology": topology,
                }
            ),
        ))

    def _complete_governed_plans(
        self,
        target: m.Infra.RepositoryConformTarget,
        planned: t.SequenceOf[m.Infra.CodegenFilePlan],
        codegen: m.Infra.CodegenConfigSpec,
        contract: m.Infra.CodegenConformSurfaceContract,
    ) -> p.Result[t.SequenceOf[m.Infra.CodegenFilePlan]]:
        """Attach ownership metadata and represent every governed root artifact.

        Only the ``ALL`` surface completes the full governed set; the
        pyproject-scoped surfaces (``DEPENDENCIES``/``PYPROJECT``) keep the plan
        restricted to what their own planners already produced.

        Returns:
            The resulting ``p.Result[t.SequenceOf[m.Infra.CodegenFilePlan]]``.

        """
        root = target.root
        governed_by_path = {
            item.path: item
            for item in codegen.managed_file_specs
            if target.beads is not None or item.path.parts[:1] != (".beads",)
        }
        bound = self._bind_governed_ownership(root, planned, governed_by_path)
        if bound.failure:
            return r[t.SequenceOf[m.Infra.CodegenFilePlan]].from_failure(bound)
        completed, represented = bound.value
        if not contract.complete_governed:
            return r[t.SequenceOf[m.Infra.CodegenFilePlan]].ok(tuple(completed))
        pending_artifacts = {
            path: item
            for path, item in governed_by_path.items()
            if path not in represented
        }
        represented_set = self._represent_ungoverned_artifacts(
            target,
            codegen,
            pending_artifacts,
        )
        if represented_set.failure:
            return r[t.SequenceOf[m.Infra.CodegenFilePlan]].from_failure(
                represented_set,
            )
        completed.extend(represented_set.value)
        return r[t.SequenceOf[m.Infra.CodegenFilePlan]].ok(tuple(completed))

    @staticmethod
    def _bind_governed_ownership(
        root: Path,
        planned: t.SequenceOf[m.Infra.CodegenFilePlan],
        governed_by_path: t.MappingKV[Path, m.Infra.ManagedFileSpec],
    ) -> p.Result[t.Pair[list[m.Infra.CodegenFilePlan], set[Path]]]:
        """Stamp governed ownership onto the planned files, first plan wins.

        Returns:
            The resulting ``p.Result[t.Pair[list[m.Infra.CodegenFilePlan],
                set[Path]]]`` with the bound plans and the represented paths.

        """
        completed: list[m.Infra.CodegenFilePlan] = []
        represented: set[Path] = set()
        represented_indexes: MutableMapping[Path, int] = {}
        for file in planned:
            relative = file.path.relative_to(root)
            governed = governed_by_path.get(relative)
            if governed is None:
                completed.append(file)
                continue
            represented.add(relative)
            governed_file = file.model_copy(
                update={
                    "owner": governed.owner,
                    "policy": governed.policy,
                    "desired_mode": (
                        governed.mode if file.desired_content is not None else None
                    ),
                },
            )
            if relative in represented_indexes:
                completed[represented_indexes[relative]] = governed_file
            else:
                represented_indexes[relative] = len(completed)
                completed.append(governed_file)
        return r[t.Pair[list[m.Infra.CodegenFilePlan], set[Path]]].ok(
            (completed, represented),
        )

    def _represent_ungoverned_artifacts(
        self,
        target: m.Infra.RepositoryConformTarget,
        codegen: m.Infra.CodegenConfigSpec,
        governed_by_path: t.MappingKV[Path, m.Infra.ManagedFileSpec],
    ) -> p.Result[t.VariadicTuple[m.Infra.CodegenFilePlan]]:
        """Plan every unrepresented governed artifact in the mapping.

        Args:
            target: The conform target whose root owns the artifacts.
            codegen: The codegen configuration governing the artifacts.
            governed_by_path: Governed artifacts keyed by repository-relative
                path.

        Returns:
            The resulting ``p.Result[t.VariadicTuple[m.Infra.CodegenFilePlan]]``
            carrying one plan per represented artifact; per-artifact failures
            are recorded and skipped.

        """
        plans: list[m.Infra.CodegenFilePlan] = []
        root = target.root
        vscode_spec = target.vscode_spec
        for relative, governed in governed_by_path.items():
            path = root / relative
            if path.exists() and not path.is_file():
                error = ValueError(f"governed artifact is not a regular file: {path}")
                self._record_file_failure(
                    path,
                    str(error),
                    exception=error,
                )
                continue
            if not self._governed_entry_reachable(codegen, target, relative):
                continue
            if not path.exists() and governed.policy != "merge":
                continue
            current = self._governed_current_text(path)
            if current.failure:
                self._record_file_failure(
                    path,
                    current.error or "cannot read governed artifact",
                    exception=current.exception,
                )
                continue
            request = m.Infra.CodegenGovernedPlanRequest(
                root=root,
                relative=relative,
                governed=governed,
                current=current.value,
                vscode_spec=vscode_spec,
                source_states=target.vscode_sources,
            )
            decided = self._decide_governed_plan(request)
            if decided.failure:
                self._record_file_failure(
                    path,
                    decided.error or "cannot plan governed artifact",
                    exception=decided.exception,
                )
                continue
            decided_value, decided_present = decided.value
            if decided_present and decided_value is not None:
                plans.append(decided_value)
        return r[t.VariadicTuple[m.Infra.CodegenFilePlan]].ok(tuple(plans))

    @staticmethod
    def _governed_entry_reachable(
        codegen: m.Infra.CodegenConfigSpec,
        target: m.Infra.RepositoryConformTarget,
        relative: Path,
    ) -> bool:
        """Whether the artifact admits this profile and its selected capabilities.

        Returns:
            True only for a declared artifact applicable to this target.

        """
        if (
            not target.ci_enabled and relative.parts[:2] == (".github", "workflows")
        ) or (
            relative == Path(c.PYPROJECT_FILENAME)
            and target.make_profile is c.Infra.MakeProfile.WORKSPACE
            and target.project is None
        ):
            return False
        return any(
            entry.destination == relative.as_posix()
            and target.make_profile in entry.profiles
            and (not entry.requires_beads or target.beads is not None)
            and (not entry.requires_release_protocol or target.publishes_release)
            for entry in codegen.templates.entries
        )

    @staticmethod
    def _governed_current_text(path: Path) -> p.Result[str]:
        """Read the current bytes of an existing governed artifact.

        Returns:
            The resulting ``p.Result[str]``, empty for a non-file path.

        """
        if not path.is_file():
            return r[str].ok("")
        read = u.Cli.atomic_read_binary_file_state(path, required=True)
        if read.failure:
            return r[str].from_failure(read)
        content = read.value.content
        if content is None:
            error = ValueError(f"governed artifact has no captured bytes: {path}")
            return r[str].fail(str(error), exception=error)
        return r[str].create_from_callable(partial(content.decode, c.DEFAULT_ENCODING))

    @classmethod
    def _decide_governed_plan(
        cls,
        request: m.Infra.CodegenGovernedPlanRequest,
    ) -> p.Result[t.Pair[m.Infra.CodegenFilePlan | None, bool]]:
        """Require the existing specialized planner for an unrendered artifact.

        Returns:
            The resulting ``p.Result[t.Pair[m.Infra.CodegenFilePlan | None,
            bool]]`` with its presence flag.

        """
        special = cls._special_governed_plan(request)
        if special.failure:
            return special
        if special.value[0] is not None:
            return special
        return r[t.Pair[m.Infra.CodegenFilePlan | None, bool]].fail(
            "managed artifact has no specialized projection owner: "
            f"{request.relative} (owner={request.governed.owner})",
        )

    @classmethod
    def _special_governed_plan(
        cls,
        request: m.Infra.CodegenGovernedPlanRequest,
    ) -> p.Result[t.Pair[m.Infra.CodegenFilePlan | None, bool]]:
        """Plan owner-specific merge behavior for special governed artifacts.

        Returns:
            The resulting ``p.Result[t.Pair[m.Infra.CodegenFilePlan | None,
            bool]]`` where the boolean identifies a declared rendering owner.

        """
        vscode_merge = request.governed.policy == "merge" and (
            request.governed.owner == c.Infra.CODEGEN_OWNER_VSCODE
        )
        if vscode_merge:
            # Owner-merge dispatch: owners with a canonical document merge
            # (vscode settings today) produce their rendered content here.
            return cls._vscode_merged_plan(request)
        if request.governed.policy == "merge" and request.relative.as_posix() == (
            c.Infra.ENVRC_LOCAL_RELPATH
        ):
            # Local overrides never carry generated content: the merge strips
            # stale generated sections and deletes the file when nothing
            # custom remains, so `.envrc` stays the single beads owner.
            return cls._envrc_local_plan(request)
        return r[t.Pair[m.Infra.CodegenFilePlan, bool]].ok((None, False))

    @classmethod
    def _vscode_merged_plan(
        cls,
        request: m.Infra.CodegenGovernedPlanRequest,
    ) -> p.Result[t.Pair[m.Infra.CodegenFilePlan | None, bool]]:
        """Render the canonical vscode settings merge when it diverges.

        Returns:
            The resulting ``p.Result[t.Pair[m.Infra.CodegenFilePlan | None,
            bool]]`` with its presence flag.

        """
        result_type = r[t.Pair[m.Infra.CodegenFilePlan | None, bool]]
        spec = request.vscode_spec
        sources = request.source_states
        if spec is None:
            loaded = u.Infra.load_codegen_inputs(request.root)
            if loaded.failure:
                return result_type.from_failure(loaded)
            spec = loaded.value.spec.vscode
            sources = loaded.value.sources
        merged = FlextInfraCodegenVscodeMixin.render_vscode_settings(
            request.root,
            spec=spec,
        )
        if merged.failure:
            return result_type.from_failure(merged)
        merged_plan = cls.file_plan(
            request.root,
            request.relative.as_posix(),
            merged.value,
            mode=request.governed.mode,
            source_states=sources,
        )
        if merged_plan.failure:
            return result_type.from_failure(merged_plan)
        before = merged_plan.value.before
        if isinstance(before, m.Cli.AtomicFileState) and before.content != (
            request.current.encode(c.DEFAULT_ENCODING)
            if request.current
            else (b"" if before.content is not None else None)
        ):
            error = ValueError(
                f"editor settings changed during planning: {merged_plan.value.path}",
            )
            return result_type.fail(str(error), exception=error)
        return result_type.ok(
            (
                merged_plan.value.model_copy(
                    update={
                        "owner": request.governed.owner,
                        "policy": request.governed.policy,
                        "tracking": request.governed.tracking,
                    },
                ),
                True,
            ),
        )

    @classmethod
    def _envrc_local_plan(
        cls,
        request: m.Infra.CodegenGovernedPlanRequest,
    ) -> p.Result[t.Pair[m.Infra.CodegenFilePlan | None, bool]]:
        """Normalize the local envrc overrides or plan the file's deletion.

        Returns:
            The resulting ``p.Result[t.Pair[m.Infra.CodegenFilePlan | None,
            bool]]`` with its presence flag.

        """
        result_type = r[t.Pair[m.Infra.CodegenFilePlan | None, bool]]
        root = request.root
        relative = request.relative
        path = root / relative
        normalized = FlextInfraWorkspaceEnvironmentContracts.envrc_local_normalized(
            request.current,
        )
        if normalized and normalized == request.current:
            current_plan = cls.file_plan(
                root,
                relative.as_posix(),
                request.current,
                mode=request.governed.mode,
            )
            if current_plan.failure:
                return result_type.from_failure(current_plan)
            return result_type.ok(
                (
                    current_plan.value.model_copy(
                        update={
                            "owner": request.governed.owner,
                            "policy": request.governed.policy,
                        },
                    ),
                    True,
                ),
            )
        if not normalized:
            before = u.Cli.atomic_read_binary_file_state(path, required=False)
            if before.failure:
                return result_type.from_failure(before)
            return result_type.ok(
                (
                    m.Infra.CodegenFilePlan(
                        project=root,
                        path=path,
                        before=before.value,
                        desired_content=None,
                        desired_mode=None,
                        owner=request.governed.owner,
                        policy=request.governed.policy,
                    ),
                    True,
                ),
            )
        merged_plan = cls.file_plan(
            root,
            relative.as_posix(),
            normalized,
            mode=request.governed.mode,
        )
        if merged_plan.failure:
            return result_type.from_failure(merged_plan)
        return result_type.ok(
            (
                merged_plan.value.model_copy(
                    update={
                        "owner": request.governed.owner,
                        "policy": request.governed.policy,
                    },
                ),
                True,
            ),
        )


__all__: list[str] = ["FlextInfraCodegenConformExistingPlan"]
