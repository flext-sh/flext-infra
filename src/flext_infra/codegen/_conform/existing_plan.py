"""Conformance planning for existing repositories and governed artifacts.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import time
import traceback
from collections.abc import Callable, MutableMapping
from functools import partial
from pathlib import Path
from typing import Literal

from flext_infra import FlextInfraConfig, c, m, p, r, t, u
from flext_infra.codegen import (
    FlextInfraCodegenLazyInit,
    FlextInfraCodegenProtocolModels,
)
from flext_infra.codegen._conform import FlextInfraCodegenConformArtifactRender
from flext_infra.codegen.codegen_preconditions import FlextInfraCodegenPreconditions
from flext_infra.deps import FlextInfraPyprojectModernizer
from flext_infra.services._codegen import FlextInfraCodegenVscodeMixin
from flext_infra.workspace import (
    FlextInfraRopeWorkspace,
    FlextInfraWorkspaceEnvironmentContracts,
)


class FlextInfraCodegenConformExistingPlan(FlextInfraCodegenConformArtifactRender):
    """Conformance planning for existing repositories and governed artifacts."""

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
        if contract.destinations == frozenset({c.Infra.ENVRC_FILENAME}):
            context = m.Infra.EnvrcRenderSpec(
                toolchain=codegen.toolchain,
                uv_resolution=codegen.make.uv_resolution,
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
        planned = self._bootstrap_destination_plan(
            target, codegen, context, destination
        )
        if planned.failure:
            return r[t.SequenceOf[m.Infra.CodegenFilePlan]].from_failure(planned)
        return r[t.SequenceOf[m.Infra.CodegenFilePlan]].ok((planned.value,))

    def _plan_existing_managed(
        self,
        target: m.Infra.RepositoryConformTarget,
        workspace: m.Infra.WorkspaceSpec,
        codegen: m.Infra.CodegenConfigSpec,
        contract: m.Infra.CodegenConformSurfaceContract,
        identity: t.Pair[m.Infra.ProjectSpec, p.ProjectMetadata],
    ) -> p.Result[t.SequenceOf[m.Infra.CodegenFilePlan]]:
        """Plan the managed templates (and custom content) for an existing tree.

        Returns:
            The resulting ``p.Result[t.SequenceOf[m.Infra.CodegenFilePlan]]``.

        """
        result_type = r[t.SequenceOf[m.Infra.CodegenFilePlan]]
        root = target.root
        repository = target.repository
        managed_started = time.monotonic()
        u.Cli.info(f"  stage=managed-artifacts repository={repository.name}")
        managed_artifacts = u.Infra.snapshot_committed_project_managed_artifacts(root)
        if managed_artifacts.success:
            u.Cli.info(
                f"  stage=managed-artifacts repository={repository.name} "
                f"elapsed={time.monotonic() - managed_started:.2f}s",
            )
        if managed_artifacts.failure or not (contract.tooling or contract.custom):
            return (
                result_type.from_failure(managed_artifacts)
                if managed_artifacts.failure
                else self._plan_existing_templates(
                    render_inputs=self.resolve_render_inputs(
                        target=target,
                        workspace=workspace,
                        codegen=codegen,
                        tooling_runtime=None,
                        managed_artifacts=managed_artifacts.value,
                    ),
                    contract=contract,
                )
            )
        tooling_started = time.monotonic()
        sources = self._existing_managed_sources(target, codegen, contract, identity[0])
        if sources.failure:
            return result_type.from_failure(sources)
        custom, initializers = sources.value[1], sources.value[2]
        with u.Infra.facade_source_project(
            root,
            source_states=sources.value[3],
            declared_files=sources.value[0],
        ) as binding:
            if contract.custom:
                import_graph, _modules = u.Infra.snapshot_import_graph(binding[0])
                cycles = u.Infra.project_import_cycles(import_graph)
                if cycles:
                    return result_type.fail(
                        f"projected runtime import cycle: {sorted(cycles)}"
                    )
            tooling_runtime: m.Infra.ToolingRuntimeContext | None = None
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
                    f"  stage=tooling-context repository={repository.name} "
                    f"elapsed={time.monotonic() - tooling_started:.2f}s",
                )
            render_inputs = self.resolve_render_inputs(
                target=target,
                workspace=workspace,
                codegen=codegen,
                tooling_runtime=tooling_runtime,
                managed_artifacts=managed_artifacts.value,
            )
            return self._render_existing_managed(
                render_inputs,
                contract,
                initializers,
                custom,
                source_project=binding[0],
            ).flat_map(
                lambda completed: self._qualified_existing_tooling(
                    render_inputs, contract, completed, binding[1]()
                )
            )

    def _existing_managed_sources(
        self,
        target: m.Infra.RepositoryConformTarget,
        codegen: m.Infra.CodegenConfigSpec,
        contract: m.Infra.CodegenConformSurfaceContract,
        project: p.Infra.ProjectSpec,
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
        lazy_result = self._existing_lazy_sources(root)
        if contract.custom:
            lazy_result = lazy_result.flat_map(
                lambda initial: self._existing_protocol_sources(root, project, initial)
            )
        if lazy_result.failure:
            return result_type.from_failure(lazy_result)
        cohort = (
            tuple(lazy_result.value[0])
            if self.state.provider_plans is None
            else (
                *(plan for plan in self.state.provider_plans if plan.project != root),
                *lazy_result.value[0],
            )
        )
        with u.Infra.facade_source_project(
            root, source_states=lazy_result.value[1], declared_files=cohort
        ) as binding:
            custom_result = (
                self._plan_existing_custom(
                    root,
                    codegen,
                    profile=target.make_profile.value,
                    binding=binding,
                )
                if contract.custom
                else r[t.SequenceOf[m.Infra.CodegenFilePlan]].ok(())
            )
            if custom_result.failure:
                return result_type.from_failure(custom_result)
            custom_inputs = FlextInfraCodegenPreconditions.unique_states((
                *lazy_result.value[1],
                *binding[1]()[0],
            ))
            if custom_inputs.failure:
                return result_type.from_failure(custom_inputs)
        projected_files = {plan.path: plan for plan in (*cohort, *custom_result.value)}
        with u.Infra.facade_source_project(
            root,
            source_states=custom_inputs.value,
            declared_files=tuple(projected_files.values()),
        ) as projected:
            exports = FlextInfraCodegenLazyInit(
                repository_root=root, project_scope_roots=(root,)
            ).plan_files(source_project=projected[0])
            if exports.failure:
                return result_type.from_failure(exports)
            self.state.planning_issues.extend(exports.value.issues)
            if self.state.planning_exception is None:
                self.state.planning_exception = exports.value.exception
            projected_inputs = FlextInfraCodegenPreconditions.unique_states((
                *custom_inputs.value,
                *projected[1]()[0],
                *(
                    state
                    for plan in exports.value.files
                    for state in plan.source_states
                ),
            ))
            if projected_inputs.failure:
                return result_type.from_failure(projected_inputs)
        projected_files.update((plan.path, plan) for plan in exports.value.files)
        initializers = tuple(
            {
                plan.path: plan
                for plan in (*lazy_result.value[0], *exports.value.files)
            }.values()
        )
        return result_type.ok((
            tuple(projected_files.values()),
            custom_result.value,
            initializers,
            projected_inputs.value,
        ))

    def _render_existing_protocol_plans(
        self,
        root: Path,
        project: p.Infra.ProjectSpec,
        initial: t.Pair[
            t.SequenceOf[m.Infra.CodegenFilePlan],
            t.VariadicTuple[m.Cli.AtomicFileState],
        ],
    ) -> p.Result[
        t.Pair[
            t.SequenceOf[m.Infra.CodegenFilePlan],
            t.MappingKV[str, str],
        ]
    ]:
        """Project model contracts and exports inside the original source epoch.

        Returns:
            Authenticated protocol and initializer plans, without publishing files.

        """
        result_type = r[
            t.Pair[
                t.SequenceOf[m.Infra.CodegenFilePlan],
                t.MappingKV[str, str],
            ]
        ]
        with u.Infra.facade_source_project(
            root, source_states=initial[1], declared_files=tuple(initial[0])
        ) as binding:
            with FlextInfraRopeWorkspace.open_workspace(
                root,
                rope_repository_root=Path(binding[0].root.real_path),
                source_project=binding[0],
            ) as workspace:
                rendered = FlextInfraCodegenProtocolModels.render_modules(
                    project, workspace
                )
            if rendered.failure:
                return result_type.from_failure(rendered)
            states, directories, topology = binding[1]()
            protocols: list[m.Infra.CodegenFilePlan] = []
            for path, content in rendered.value[0].items():
                planned = self.file_plan(
                    root, path.as_posix(), content, source_states=states
                )
                if planned.failure:
                    return result_type.from_failure(planned)
                protocols.append(
                    planned.value.model_copy(
                        update={
                            "source_directories": directories,
                            "source_query_topology": topology,
                        }
                    )
                )
            for path, content in binding[2].items():
                if (
                    path not in {root / path for path in rendered.value[0]}
                    and path.parent.name == u.Infra.facade_families()["p"].directory
                    and path.name.startswith("generated_models")
                    and content.startswith(c.Infra.AUTOGEN_HEADERS)
                ):
                    retired = self._absent_file_plan(root, path)
                    if retired.failure:
                        return result_type.from_failure(retired)
                    protocols.append(
                        retired.value.model_copy(
                            update={
                                "source_states": (
                                    *retired.value.source_states,
                                    *states,
                                ),
                                "source_directories": directories,
                                "source_query_topology": topology,
                            }
                        )
                    )
        return result_type.ok((tuple(protocols), rendered.value[1]))

    @staticmethod
    def _skip_redundant_exports_pass(
        operation: str, operation_index: int, *, produced_new_files: bool
    ) -> bool:
        """Whether a repeated exports pass has no new plans to process.

        Returns:
            True when the exports pass is redundant.

        """
        return (
            operation == "exports"
            and operation_index > 0
            and not produced_new_files
        )

    def _existing_protocol_sources(
        self,
        root: Path,
        project: p.Infra.ProjectSpec,
        initial: t.Pair[
            t.SequenceOf[m.Infra.CodegenFilePlan],
            t.VariadicTuple[m.Cli.AtomicFileState],
        ],
    ) -> p.Result[
        t.Pair[
            t.SequenceOf[m.Infra.CodegenFilePlan],
            t.VariadicTuple[m.Cli.AtomicFileState],
        ]
    ]:
        """Compose protocol owners and exports before and after model transfer.

        Returns:
            The complete changed plan set and its original input witnesses.

        """
        result_type = r[
            t.Pair[
                t.SequenceOf[m.Infra.CodegenFilePlan],
                t.VariadicTuple[m.Cli.AtomicFileState],
            ]
        ]
        rendered = self._render_existing_protocol_plans(root, project, initial)
        if rendered.failure:
            return result_type.from_failure(rendered)
        protocols, identities = rendered.value
        if not protocols:
            return result_type.ok(initial)
        changed = {plan.path: plan for plan in protocols}
        staged = {plan.path: plan for plan in (*initial[0], *protocols)}
        inputs = initial[1]
        for transfer in (True, False):
            # The same export/facade owners run before transfer and again after
            # retirement. Neither stage publishes or replaces the input epoch.
            pass_produced_new_files = False
            for operation_index, operation in enumerate(("exports", "facade", "exports")):
                # Skip a redundant exports pass when the previous pass in this
                # transfer iteration produced no new plans.
                if self._skip_redundant_exports_pass(
                    operation, operation_index, pass_produced_new_files
                ):
                    continue
                with u.Infra.facade_source_project(
                    root, source_states=inputs, declared_files=tuple(staged.values())
                ) as binding:
                    files = self._protocol_projection_pass(root, operation, binding)
                    if files.failure:
                        return result_type.from_failure(files)
                    _new_files = bool(files.value)
                    changed.update((plan.path, plan) for plan in files.value)
                    staged.update((plan.path, plan) for plan in files.value)
                    captured_inputs = FlextInfraCodegenPreconditions.unique_states((
                        *inputs,
                        *binding[1]()[0],
                        *(
                            state
                            for plan in changed.values()
                            for state in plan.source_states
                        ),
                    ))
                    if captured_inputs.failure:
                        return result_type.from_failure(captured_inputs)
                    inputs = captured_inputs.value
                    pass_produced_new_files = _new_files
            if not transfer:
                continue
            transferred = self._protocol_transfer_plans(
                root, project, identities, (tuple(staged.values()), inputs)
            )
            if transferred.failure:
                return result_type.from_failure(transferred)
            for plan in transferred.value[0]:
                staged[plan.path] = changed[plan.path] = plan
            inputs = transferred.value[1]
        return result_type.ok((tuple(changed.values()), inputs))

    def _protocol_transfer_plans(
        self,
        root: Path,
        project: p.Infra.ProjectSpec,
        identities: t.MappingKV[str, str],
        initial: t.Pair[
            t.SequenceOf[m.Infra.CodegenFilePlan],
            t.VariadicTuple[m.Cli.AtomicFileState],
        ],
    ) -> p.Result[
        t.Pair[
            t.SequenceOf[m.Infra.CodegenFilePlan],
            t.VariadicTuple[m.Cli.AtomicFileState],
        ]
    ]:
        """Plan authenticated ownership transfers without publishing sources.

        Returns:
            Transferred plans and the merged original source witnesses.

        """
        result_type = r[
            t.Pair[
                t.SequenceOf[m.Infra.CodegenFilePlan],
                t.VariadicTuple[m.Cli.AtomicFileState],
            ]
        ]
        with u.Infra.facade_source_project(
            root, source_states=initial[1], declared_files=tuple(initial[0])
        ) as binding:
            with FlextInfraRopeWorkspace.open_workspace(
                root,
                rope_repository_root=Path(binding[0].root.real_path),
                source_project=binding[0],
            ) as workspace:
                tuple(workspace.modules())
                captured = u.Infra.codemod_source_epoch(
                    m.Infra.CodemodBindingSnapshot(states=binding[1]()[0])
                )
                transfers = FlextInfraCodegenProtocolModels.plan_transfers(
                    project, workspace, dict(binding[2]), captured, identities
                )
            if transfers.failure:
                return result_type.from_failure(transfers)
            states, directories, topology = binding[1]()
            plans: list[m.Infra.CodegenFilePlan] = []
            for edit in transfers.value:
                planned = (
                    self._absent_file_plan(root, edit.file_path)
                    if edit.retire_file
                    else self.file_plan(
                        root,
                        edit.file_path.relative_to(root).as_posix(),
                        edit.updated_source,
                        source_states=states,
                    )
                )
                if planned.failure:
                    return result_type.from_failure(planned)
                plans.append(
                    planned.value.model_copy(
                        update={
                            "source_states": states,
                            "source_directories": directories,
                            "source_query_topology": topology,
                        }
                    )
                )
            return FlextInfraCodegenPreconditions.unique_states((
                *initial[1],
                *states,
            )).map(lambda inputs: (tuple(plans), inputs))

    def _protocol_projection_pass(
        self,
        root: Path,
        operation: str,
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
        """Run one export or facade pass inside its original source binding.

        Returns:
            The owner's plans, or the first planning/layout failure.

        """
        result_type = r[t.SequenceOf[m.Infra.CodegenFilePlan]]
        if operation == "exports":
            refreshed = FlextInfraCodegenLazyInit(
                repository_root=root, project_scope_roots=(root,)
            ).plan_files(source_project=binding[0])
            if refreshed.failure:
                return result_type.from_failure(refreshed)
            self.state.planning_issues.extend(refreshed.value.issues)
            if self.state.planning_exception is None:
                self.state.planning_exception = refreshed.value.exception
            return result_type.ok(refreshed.value.files)
        layout = u.Infra.layout(root, rope_project=binding[0])
        if layout is None:
            return result_type.fail("protocol projection has no native package layout")
        return self._utility_facade_plan(root, layout.package_dir, "p", binding)

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
        sources = FlextInfraCodegenPreconditions.unique_states(
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
        final_inputs = (
            self.planned_source_render_inputs(
                render_inputs,
                [*initializers, *managed.value, *custom],
                source_project=source_project,
            )
            if contract.pyproject
            else render_inputs
        )
        templates = (
            self._plan_existing_templates(
                render_inputs=final_inputs,
                contract=contract,
            )
            if contract.pyproject and final_inputs is not render_inputs
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
        evidence: t.Triple[
            t.VariadicTuple[m.Cli.AtomicFileState],
            t.VariadicTuple[m.Cli.AtomicDirectoryInventory],
            t.VariadicTuple[m.Cli.AtomicDirectoryChainPlan],
        ],
    ) -> p.Result[t.SequenceOf[m.Infra.CodegenFilePlan]]:
        """Bind consumed evidence to the pyproject output inside its source epoch.

        Returns:
            File plans retaining their original and consumed native receipts.

        """
        states, directories, topology = evidence
        qualified: list[m.Infra.CodegenFilePlan] = []
        for file in planned:
            if (
                file.path != render_inputs.target.root / c.PYPROJECT_FILENAME
                or not contract.tooling
            ):
                qualified.append(file)
                continue
            inputs = FlextInfraCodegenPreconditions.unique_states((
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

        Complete generation checks the whole project before publication, so its
        bootstrap must stage every planned initializer, even without a facade.

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
            group = f"{c.Infra.CodegenConformSurface.ALL.value}:{root}"
            return result_type.ok(
                tuple(
                    item.model_copy(update={"dependency_group": group})
                    for item in by_path.values()
                )
            )
        grouped_paths = {item.path for item in (*barrels, *facades)}
        group = f"{c.Infra.CodegenConformSurface.FACADES.value}:{root}"
        return result_type.ok((
            *(item for item in planned if item.path not in grouped_paths),
            *(
                item.model_copy(update={"dependency_group": group})
                for item in (*barrels, *facades)
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
        self.state.planning_issues.extend(planned.value.issues)
        if self.state.planning_exception is None:
            self.state.planning_exception = planned.value.exception
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
        for destination in sorted(c.Infra.MAKEFILE_BOOTSTRAP_DESTINATIONS):
            planned = self._bootstrap_destination_plan(
                target,
                codegen,
                context.value,
                destination,
            )
            if planned.failure:
                return r[t.SequenceOf[m.Infra.CodegenFilePlan]].from_failure(planned)
            plans.append(planned.value)
        return r[t.SequenceOf[m.Infra.CodegenFilePlan]].ok(tuple(plans))

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
        template, managed_spec = binding.value
        rendered = u.Cli.template_render_authenticated(template, context)
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
        captured = FlextInfraCodegenPreconditions.unique_states(sources)
        if captured.failure:
            return result_type.from_failure(captured)
        return self.file_plan(
            target.root,
            destination,
            content,
            mode=managed_spec.mode,
            source_states=captured.value,
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
            and entry.delegate == c.Infra.TemplateDelegate.RENDER
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
        template = u.Infra.codegen_templates_root(codegen) / entries[0].source
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
            and entry.delegate == c.Infra.TemplateDelegate.RENDER
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
                target,
                workspace,
                contract,
                profile,
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
                # Profile- and capability-excluded workflows must not keep firing.
                # Conform, rather than a user, retires the generated orphan.
                orphan = self._retired_workflow_orphan(render_inputs, managed, path)
                if orphan.failure:
                    self._record_file_failure(
                        path,
                        orphan.error or "managed file retirement failed",
                    )
                    continue
                orphan_plan = orphan.value[0]
                if orphan.value[1] and orphan_plan is not None:
                    planned.append(
                        orphan_plan.model_copy(
                            update={"owner": managed.owner, "policy": managed.policy},
                        ),
                    )
                continue
            try:
                rendered = self._rendered_managed_plan(
                    render_inputs,
                    managed,
                    entry,
                    path,
                )
            except (OSError, ValueError):
                self._record_file_failure(path, traceback.format_exc())
                continue
            if rendered.failure:
                self._record_file_failure(
                    path,
                    rendered.error or "managed file rendering failed",
                )
                continue
            render_inputs, planned_file = rendered.value
            planned.append(planned_file)
        return r[t.SequenceOf[m.Infra.CodegenFilePlan]].ok(tuple(planned))

    @staticmethod
    def _managed_file_skipped(
        target: m.Infra.RepositoryConformTarget,
        workspace: m.Infra.WorkspaceSpec,
        contract: m.Infra.CodegenConformSurfaceContract,
        profile: c.Infra.MakeProfile,
        managed: m.Infra.ManagedFileSpec,
    ) -> bool:
        """Whether this managed file is out of scope for the current surface.

        Returns:
            True when the file is skipped before any template resolution.

        """
        if target.beads is None and managed.path.parts[:1] == (".beads",):
            return True
        if not target.ci_enabled and managed.path.parts[:2] == (
            ".github",
            "workflows",
        ):
            return True
        if (
            contract.destinations is not None
            and managed.path.as_posix() not in contract.destinations
        ):
            return True
        return managed.path == Path(c.PYPROJECT_FILENAME) and (
            not contract.pyproject
            or (
                workspace.project is None
                and profile is c.Infra.MakeProfile.WORKSPACE
                and contract.destinations is None
            )
        )

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
            None, Path | None], bool]]`` where the boolean marks entry
            presence (False: the managed file declares no render entry for
            this topology).

        """
        result_type = r[
            t.Pair[t.Pair[m.Infra.TemplateEntrySpec | None, Path | None], bool]
        ]
        entries = tuple(
            entry
            for entry in codegen.templates.entries
            if entry.destination == managed.path.as_posix()
            and entry.delegate == c.Infra.TemplateDelegate.RENDER
        )
        if not entries:
            return result_type.ok(((None, None), False))
        if len(entries) != 1:
            return result_type.fail(
                f"managed file requires exactly one render template: {managed.path}",
            )
        entry = entries[0]
        if entry.source is None:
            return result_type.fail(
                f"managed render entry has no template source: {managed.path}",
            )
        if entry.requires_beads and workspace.beads is None:
            return result_type.ok(((None, None), False))
        path = FlextInfraCodegenConformExistingPlan._managed_entry_path(root, entry)
        if path.failure:
            return result_type.from_failure(path)
        return result_type.ok(((entry, path.value), True))

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
        path: Path,
    ) -> p.Result[t.Pair[m.Infra.CodegenFilePlan | None, bool]]:
        """Plan retirement of a profile-excluded generated workflow orphan.

        A managed destination does not establish authorship of its current
        bytes. Retire generated projections only; repository-owned workflows
        survive profile changes.

        Returns:
            The resulting ``p.Result[t.Pair[m.Infra.CodegenFilePlan | None,
            bool]]`` where the boolean marks orphan presence (False: a
            repository-owned workflow survives).

        """
        result_type = r[t.Pair[m.Infra.CodegenFilePlan | None, bool]]
        if not (managed.path.parts[:2] == (".github", "workflows") and path.is_file()):
            return result_type.ok((None, False))
        # Keep the typed read result distinct from its string payload.
        orphan_read = u.Cli.files_read_text(path)
        if orphan_read.failure:
            return result_type.from_failure(orphan_read)
        if not any(
            marker in orphan_read.value for marker in c.Infra.TEMPLATE_GENERATED_MARKERS
        ):
            return result_type.ok((None, False))
        orphan = self._absent_file_plan(render_inputs.target.root, path)
        if orphan.failure:
            return result_type.from_failure(orphan)
        return result_type.ok((orphan.value, True))

    def _rendered_managed_plan(
        self,
        render_inputs: m.Infra.CodegenRenderInputs,
        managed: m.Infra.ManagedFileSpec,
        entry: m.Infra.TemplateEntrySpec,
        path: Path,
    ) -> p.Result[t.Pair[m.Infra.CodegenRenderInputs, m.Infra.CodegenFilePlan]]:
        """Render, compose, record, and plan one managed artifact.

        Returns:
            The resulting ``p.Result[t.Pair[m.Infra.CodegenRenderInputs,
                m.Infra.CodegenFilePlan]]`` where the inputs carry the planned
            pyproject when this artifact is the pyproject itself.

        """
        result_type = r[t.Pair[m.Infra.CodegenRenderInputs, m.Infra.CodegenFilePlan]]
        root = render_inputs.target.root
        rendered = (
            r[m.Infra.CodegenArtifactComposition].fail(
                f"managed render entry has no template source: {entry.destination}",
            )
            if entry.source is None
            else self._rendered_artifact_source(
                render_inputs,
                template_relpath=entry.source,
                destination=entry.destination,
                failure_prefix="",
                project_context=None,
            )
        )
        if rendered.failure:
            return result_type.from_failure(rendered)
        composed = self.compose_project_artifact(
            root,
            entry.destination,
            rendered.value.rendered,
            render_inputs=render_inputs,
            source_states=rendered.value.source_states,
        )
        if composed.failure:
            return result_type.from_failure(composed)
        rendered_content = composed.value.rendered
        if entry.destination == c.PYPROJECT_FILENAME:
            recorded = self.with_planned_pyproject(render_inputs, rendered_content)
            if recorded.failure:
                return result_type.from_failure(recorded)
            render_inputs = recorded.value
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
            rendered_content,
            mode=managed.mode,
            source_states=composed.value.source_states,
        )
        if planned.failure:
            return result_type.from_failure(planned)
        return result_type.ok((render_inputs, planned.value))

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
    ) -> p.Result[t.SequenceOf[m.Infra.CodegenFilePlan]]:
        """Validate custom Make content and plan utility, protocol and model facades.

        Existing handwritten Make content is validated against the selected
        profile policy. The canonical source inventory contributes declared
        ``u``, ``p`` and ``m`` facades from every owned package, including
        auxiliary packages, through consumer-driven owner projection.
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
            families: t.VariadicTuple[Literal["u", "p", "m"]] = ("u", "p", "m")
            layout = u.Infra.layout(root)
            project, _, sources = binding
            package_dirs = {
                path.parent
                for path in sources
                if path.is_relative_to(root)
                and path.suffix == c.Infra.EXT_PYTHON
                and path.parent / c.Infra.INIT_PY in sources
            }
            if layout is not None and layout.class_stem:
                package_dirs.add(layout.package_dir)
            for package_dir in sorted(package_dirs):
                for family in families:
                    if (
                        layout is None or package_dir != layout.package_dir
                    ) and u.Infra.facade_module_path(
                        package_dir,
                        family,
                        project=project,
                        sources=sources,
                    ) is None:
                        continue
                    plans.extend(
                        self._captured_facade_plan(root, package_dir, family, binding)
                    )
        return r[t.SequenceOf[m.Infra.CodegenFilePlan]].ok(tuple(plans))

    def _captured_facade_plan(
        self,
        root: Path,
        package_dir: Path,
        family: Literal["u", "p", "m"],
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
    ) -> t.SequenceOf[m.Infra.CodegenFilePlan]:
        """Retain the original diagnostic while collecting independent plans.

        Returns:
            The declared facade plans, or no effects for a recorded failure.

        """
        project, _, sources = binding
        facade_path = u.Infra.facade_module_path(
            package_dir, family, project=project, sources=sources
        )
        failure_path = facade_path if facade_path is not None else package_dir
        try:
            planned = self._utility_facade_plan(root, package_dir, family, binding)
        except (OSError, ValueError) as exception:
            self._record_file_failure(
                failure_path, traceback.format_exc(), exception=exception
            )
            return ()
        if planned.failure:
            self._record_file_failure(
                failure_path,
                planned.error or "facade planning failed",
                exception=planned.exception,
            )
            return ()
        return planned.value

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
        family: Literal["u", "p", "m"],
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
        rendered = u.Infra.render_utility_facade(
            package_dir,
            family=family,
            project=project,
            sources=sources,
        )
        if rendered is None:
            return result_type.ok(())
        facade_path = u.Infra.facade_module_path(
            package_dir, family, project=project, sources=sources
        )
        if facade_path is None:
            msg = f"rendered {family} facade has no declaring module"
            raise ValueError(msg)
        relative = facade_path.relative_to(root)
        utility_plan = self.file_plan(root, relative.as_posix(), rendered)
        if utility_plan.failure:
            return result_type.from_failure(utility_plan)
        states, directories, topology = consumed_states()
        inputs = FlextInfraCodegenPreconditions.unique_states((
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
        # Native views render after collection from every project's desired metadata.
        pending_artifacts = {
            path: item
            for path, item in governed_by_path.items()
            if path not in represented and path not in codegen.uv_resolution_pyprojects
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

    def plan_runtime_bindings(
        self,
        target: m.Infra.RepositoryConformTarget,
        codegen: m.Infra.CodegenConfigSpec,
        *,
        vscode_spec: m.Infra.CodegenVscodeSpec | None = None,
        codegen_inputs: m.Infra.CodegenInputs | None = None,
    ) -> p.Result[t.SequenceOf[m.Infra.CodegenFilePlan]]:
        """Plan only bindings selected by their declared artifact policy.

        Returns:
            Runtime-local file plans, including missing declared bindings.

        """
        planned = self._represent_ungoverned_artifacts(
            target
            if vscode_spec is None
            else target.model_copy(
                update={"vscode_spec": vscode_spec},
            ),
            codegen,
            {
                item.path: item
                for item in codegen.managed_file_specs
                if item.runtime_binding
            },
            codegen_inputs=codegen_inputs,
            migrate_tracking=not self.state.generation_only,
        )
        if planned.failure:
            return r[t.SequenceOf[m.Infra.CodegenFilePlan]].from_failure(planned)
        return r[t.SequenceOf[m.Infra.CodegenFilePlan]].ok(planned.value)

    def _represent_ungoverned_artifacts(
        self,
        target: m.Infra.RepositoryConformTarget,
        codegen: m.Infra.CodegenConfigSpec,
        governed_by_path: t.MappingKV[Path, m.Infra.ManagedFileSpec],
        *,
        migrate_tracking: bool = False,
        codegen_inputs: m.Infra.CodegenInputs | None = None,
    ) -> p.Result[t.VariadicTuple[m.Infra.CodegenFilePlan]]:
        """Plan every unrepresented governed artifact in the mapping.

        Args:
            target: The conform target whose root owns the artifacts.
            codegen: The codegen configuration governing the artifacts.
            governed_by_path: Governed artifacts keyed by repository-relative
                path.
            migrate_tracking: Whether runtime-local editor tracking migrates.
            codegen_inputs: Captured codegen inputs for migration planning.

        Returns:
            The resulting ``p.Result[t.VariadicTuple[m.Infra.CodegenFilePlan]]``
            carrying one plan per represented artifact; per-artifact failures
            are recorded and skipped.

        """
        plans: list[m.Infra.CodegenFilePlan] = []
        root = target.root
        profile = target.make_profile
        vscode_spec = target.vscode_spec
        runtime_root = (
            root
            if self.state.initial_workspace is not None
            and target.repository.name == self.state.initial_workspace.repository.name
            else None
        )
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
            if not self._governed_entry_reachable(codegen, profile, relative):
                continue
            if (
                not path.exists()
                and not governed.runtime_binding
                and governed.policy != "merge"
            ):
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
                runtime_root=runtime_root,
                vscode_spec=vscode_spec,
                source_states=target.vscode_sources,
            )
            if (
                migrate_tracking
                and governed.tracking == "runtime-local"
                and governed.owner == c.Infra.CODEGEN_OWNER_VSCODE
                and runtime_root is None
            ):
                migrated = self._vscode_tracking_plans(
                    request,
                    codegen_inputs=codegen_inputs,
                )
                if migrated.failure:
                    self._record_file_failure(
                        path,
                        migrated.error or "cannot plan runtime tracking migration",
                        exception=migrated.exception,
                    )
                    continue
                plans.extend(migrated.value)
                continue
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

    @classmethod
    def _vscode_tracking_plans(
        cls,
        request: m.Infra.CodegenGovernedPlanRequest,
        *,
        codegen_inputs: m.Infra.CodegenInputs | None = None,
    ) -> p.Result[t.VariadicTuple[m.Infra.CodegenFilePlan]]:
        """Plan portable declarations before the captured editor index retirement.

        Returns:
            Source declaration plans followed by the runtime-local binding plan.

        """
        result_type = r[t.VariadicTuple[m.Infra.CodegenFilePlan]]
        captured = u.Infra.git_capture_index_file(
            m.Infra.GitRelativePathRequest(
                repo_root=request.root,
                relative_path=request.relative.as_posix(),
            ),
        )
        if captured.failure:
            return result_type.from_failure(captured)
        state = captured.value
        if state.entry is None:
            binding = cls._vscode_merged_plan(request)
            if binding.failure:
                return result_type.from_failure(binding)
            return result_type.ok(
                () if binding.value[0] is None else (binding.value[0],),
            )
        settings = cls._vscode_tracking_settings(request, state)
        if settings.failure:
            return result_type.from_failure(settings)
        projected = cls._vscode_tracking_projection(
            request, *settings.value, codegen_inputs=codegen_inputs
        )
        if projected.failure:
            return result_type.from_failure(projected)
        effective, declarations = projected.value
        return cls._vscode_tracking_binding(request, state, effective, declarations)

    @staticmethod
    def _vscode_tracking_settings(
        request: m.Infra.CodegenGovernedPlanRequest,
        state: m.Infra.GitIndexFileState,
    ) -> p.Result[t.Pair[t.JsonMapping, t.JsonMapping]]:
        """Parse the captured index blob and live editor content independently.

        Returns:
            Indexed and live settings with their original parse failures.

        """
        result_type = r[t.Pair[t.JsonMapping, t.JsonMapping]]
        content = state.content
        if content is None:
            error = ValueError(
                f"captured editor index blob is absent: {request.relative}"
            )
            return result_type.fail(str(error), exception=error)
        decoded = r[str].create_from_callable(
            lambda: content.decode(c.DEFAULT_ENCODING),
        )
        if decoded.failure:
            return result_type.from_failure(decoded)
        indexed = FlextInfraCodegenVscodeMixin.parse_vscode_settings(decoded.value)
        live = FlextInfraCodegenVscodeMixin.parse_vscode_settings(request.current)
        if indexed.failure:
            return result_type.from_failure(indexed)
        if live.failure:
            return result_type.from_failure(live)
        return result_type.ok((indexed.value, live.value))

    @classmethod
    def _vscode_tracking_projection(
        cls,
        request: m.Infra.CodegenGovernedPlanRequest,
        indexed: t.JsonMapping,
        live: t.JsonMapping,
        *,
        codegen_inputs: m.Infra.CodegenInputs | None = None,
    ) -> p.Result[
        t.Pair[m.Infra.CodegenInputs, t.VariadicTuple[m.Infra.CodegenFilePlan]]
    ]:
        """Compose project and local overrides through captured config layers.

        Returns:
            Effective inputs and guarded source declaration plans.

        """
        result_type = r[
            t.Pair[m.Infra.CodegenInputs, t.VariadicTuple[m.Infra.CodegenFilePlan]]
        ]
        if codegen_inputs is None:
            loaded = u.Infra.load_codegen_inputs(request.root)
            if loaded.failure:
                return result_type.from_failure(loaded)
            codegen_inputs = loaded.value
        project = cls._vscode_project_projection(request.root, codegen_inputs, indexed)
        if project.failure:
            return result_type.from_failure(project)
        projections = project.value
        composed = u.Infra.project_codegen_inputs(
            request.root,
            codegen_inputs,
            projections=projections,
        )
        if composed.failure:
            return result_type.from_failure(composed)
        local = FlextInfraCodegenVscodeMixin.vscode_local_declaration_delta(
            request.root,
            indexed,
            live,
            spec=composed.value.spec.vscode,
        )
        if local.failure:
            return result_type.from_failure(local)
        if local.value.values:
            layers = FlextInfraConfig.config_layer_paths_for_repository(
                request.root,
                filename=c.Infra.CODEGEN_CONFIG_FILENAME,
            )
            projections = (
                *projections,
                m.Infra.CodegenLayerProjection(
                    path=layers[2],
                    values={"Infra": {"codegen": {"vscode": dict(local.value.values)}}},
                ),
            )
        effective = u.Infra.project_codegen_inputs(
            request.root,
            codegen_inputs,
            projections=projections,
        )
        if effective.failure:
            return result_type.from_failure(effective)
        return cls._vscode_declaration_plans(
            request.root,
            codegen_inputs,
            projections,
        ).map(lambda declarations: (effective.value, declarations))

    @staticmethod
    def _vscode_project_projection(
        root: Path,
        inputs: m.Infra.CodegenInputs,
        indexed: t.JsonMapping,
    ) -> p.Result[t.VariadicTuple[m.Infra.CodegenLayerProjection]]:
        """Extract a portable project delta without promoting local configuration.

        Returns:
            A project-layer projection only when indexed settings differ.

        """
        result_type = r[t.VariadicTuple[m.Infra.CodegenLayerProjection]]
        baseline = u.Infra.project_codegen_inputs(
            root,
            inputs,
            include_local=False,
        )
        if baseline.failure:
            return result_type.from_failure(baseline)
        project = FlextInfraCodegenVscodeMixin.vscode_declaration_delta(
            root,
            indexed,
            spec=baseline.value.spec.vscode,
        )
        if project.failure:
            return result_type.from_failure(project)
        layers = FlextInfraConfig.config_layer_paths_for_repository(
            root,
            filename=c.Infra.CODEGEN_CONFIG_FILENAME,
        )
        if project.value.values and layers[1].resolve() == layers[0].resolve():
            error = ValueError(
                "project editor declarations share the distributed defaults: "
                f"{layers[1]}",
            )
            return result_type.fail(str(error), exception=error)
        return result_type.ok(
            (
                m.Infra.CodegenLayerProjection(
                    path=layers[1],
                    values={
                        "Infra": {"codegen": {"vscode": dict(project.value.values)}}
                    },
                ),
            )
            if project.value.values
            else ()
        )

    @classmethod
    def _vscode_declaration_plans(
        cls,
        root: Path,
        inputs: m.Infra.CodegenInputs,
        projections: t.VariadicTuple[m.Infra.CodegenLayerProjection],
    ) -> p.Result[t.VariadicTuple[m.Infra.CodegenFilePlan]]:
        """Bind each projected delta to its captured source without touching defaults.

        Returns:
            Guarded project and local configuration plans in dependency order.

        """
        result_type = r[t.VariadicTuple[m.Infra.CodegenFilePlan]]
        library = FlextInfraConfig.config_layer_paths_for_repository(
            root,
            filename=c.Infra.CODEGEN_CONFIG_FILENAME,
        )[0]
        declarations: list[m.Infra.CodegenFilePlan] = []
        for projection in projections:
            path = projection.path
            if path.resolve() == library.resolve():
                error = ValueError(
                    "project editor declarations share the distributed defaults: "
                    f"{path}",
                )
                return result_type.fail(str(error), exception=error)
            values = u.Cli.json_walk_path(projection.values, ("Infra", "codegen"))
            validated = u.validate_value(u.json_mapping_adapter(), values)
            if validated.failure:
                return result_type.from_failure(validated)
            planned = cls._codegen_declaration_plan(
                root,
                path,
                validated.value,
                sources=inputs.sources,
            )
            if planned.failure:
                return result_type.from_failure(planned)
            declarations.append(planned.value)
        return result_type.ok(tuple(declarations))

    @classmethod
    def _vscode_tracking_binding(
        cls,
        request: m.Infra.CodegenGovernedPlanRequest,
        state: m.Infra.GitIndexFileState,
        effective: m.Infra.CodegenInputs,
        declarations: t.VariadicTuple[m.Infra.CodegenFilePlan],
    ) -> p.Result[t.VariadicTuple[m.Infra.CodegenFilePlan]]:
        """Retire captured tracking only after its portable declarations are written.

        Returns:
            Source declarations followed by their guarded editor binding.

        """
        result_type = r[t.VariadicTuple[m.Infra.CodegenFilePlan]]
        binding = cls._vscode_merged_plan(
            request.model_copy(
                update={
                    "vscode_spec": effective.spec.vscode,
                    "source_states": effective.sources,
                },
            ),
        )
        if binding.failure:
            return result_type.from_failure(binding)
        if binding.value[0] is None:
            error = ValueError(f"runtime binding plan is absent: {request.relative}")
            return result_type.fail(str(error), exception=error)
        return result_type.ok(
            (
                *declarations,
                binding.value[0].model_copy(
                    update={
                        "tracking": request.governed.tracking,
                        "index_before": state.entry,
                        "tracking_dependencies": tuple(
                            plan.path for plan in declarations
                        ),
                    },
                ),
            ),
        )

    @classmethod
    def _governed_entry_reachable(
        cls,
        codegen: m.Infra.CodegenConfigSpec,
        profile: c.Infra.MakeProfile,
        relative: Path,
    ) -> bool:
        """Whether any template entry for this destination admits the profile.

        Returns:
            True when no entry restricts the destination or the profile is
            among the admitted ones.

        """
        entry_profiles = tuple(
            entry.profiles
            for entry in codegen.templates.entries
            if entry.destination == relative.as_posix()
        )
        if not entry_profiles:
            return True
        allowed = {item for profiles in entry_profiles for item in profiles}
        return profile in allowed

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
        """Decide the representing plan: owner merge first, plain content next.

        Returns:
            The resulting ``p.Result[t.Pair[m.Infra.CodegenFilePlan | None,
            bool]]`` with its presence flag.

        """
        special = cls._special_governed_plan(request)
        if special.failure:
            return special
        if special.value[0] is not None:
            return special
        if request.governed.runtime_binding and not special.value[1]:
            return r[t.Pair[m.Infra.CodegenFilePlan | None, bool]].fail(
                "runtime binding has no declared renderer: "
                f"{request.governed.owner} {request.relative}",
            )
        result_type = r[t.Pair[m.Infra.CodegenFilePlan | None, bool]]
        current_plan = cls.file_plan(
            request.root,
            request.relative.as_posix(),
            request.current,
            mode=request.governed.mode,
        )
        if current_plan.failure:
            return result_type.from_failure(current_plan)
        return r[t.Pair[m.Infra.CodegenFilePlan, bool]].ok(
            (
                current_plan.value.model_copy(
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
        if normalized == request.current:
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
