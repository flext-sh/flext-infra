"""Complete scaffold planning for ``codegen new``.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

from flext_infra import c, m, p, r, t, u
from flext_infra.codegen import FlextInfraCodegenLazyInit
from flext_infra.codegen._conform import FlextInfraCodegenConformExistingPlan
from flext_infra.deps import FlextInfraPyprojectModernizer


class FlextInfraCodegenConformScaffoldPlan(FlextInfraCodegenConformExistingPlan):
    """Complete scaffold planning for ``codegen new``."""

    def _plan_scaffold_repository(
        self,
        *,
        target: m.Infra.RepositoryConformTarget,
        workspace: m.Infra.WorkspaceSpec,
        codegen: m.Infra.CodegenConfigSpec,
        contract: m.Infra.CodegenConformSurfaceContract,
    ) -> p.Result[t.SequenceOf[m.Infra.CodegenFilePlan]]:
        """Render the complete scaffold for ``codegen new`` only.

        Returns:
            The resulting ``p.Result[t.SequenceOf[m.Infra.CodegenFilePlan]]``.

        """
        project = workspace.project
        if project is None:
            return r[t.SequenceOf[m.Infra.CodegenFilePlan]].fail(
                f"scaffold workspace has no project metadata: {workspace.name}",
            )
        root = target.root
        required_data_destinations = frozenset(
            entry.destination
            for entry in codegen.templates.entries
            if any(
                Path(entry.destination).is_relative_to(Path(path))
                for path in project.packaged_data_paths
            )
        )
        selected_destinations = (
            None
            if contract.destinations is None
            else codegen.templates.required_destinations(contract.destinations)
        )
        # New and existing repositories share the exact same
        # root-scoped modernizer pipeline, so first generation is a fixed point.
        # A declared subproject consumes the workspace root
        # tooling profile even before the atomic scaffold creates files on disk.
        scaffold_entries = tuple(
            (
                entry,
                entry.destination.format(
                    package_name=project.package_name,
                    ns=project.namespace,
                    **u.Infra.runtime_module_names(
                        project_name=target.repository.distribution,
                        codegen=codegen,
                    ),
                ),
            )
            for entry in codegen.templates.entries
            if entry.source is not None
            and target.make_profile in entry.profiles
            and (entry.destination != c.PYPROJECT_FILENAME or contract.pyproject)
            and (
                contract.delegates
                or entry.destination == c.PYPROJECT_FILENAME
                or entry.destination in required_data_destinations
                or (
                    selected_destinations is not None
                    and entry.destination in selected_destinations
                )
            )
            and (not entry.requires_release_protocol or target.publishes_release)
            and (not entry.requires_beads or workspace.beads is not None)
            and (
                selected_destinations is None
                or entry.destination in selected_destinations
                or entry.destination in required_data_destinations
            )
        )
        modernizer = FlextInfraPyprojectModernizer(
            repository_root=root,
            skip_check=True,
            managed_artifacts=u.Infra.empty_snapshot().resolution,
        )
        # Why: a scaffold's declared roots are the complete
        # future topology only for a subproject/standalone target; a workspace
        # root aggregates subproject trees it has not declared here.
        lazy_sources = self._existing_lazy_sources(root)
        if lazy_sources.failure:
            return r[t.SequenceOf[m.Infra.CodegenFilePlan]].from_failure(lazy_sources)
        tooling_request = m.Infra.ToolingContextRequest(
            # A future scaffold owns its declared runtime (standalone), so the
            # runtime root is pinned to the scaffold root itself.
            environment_dir=u.Infra.runtime_environment_dir(root, runtime_root=root),
            planned_sources={
                plan.path: plan.desired_content.decode(c.DEFAULT_ENCODING)
                for plan in lazy_sources.value[0]
                if plan.path.suffix == c.Infra.EXT_PYTHON
                and plan.desired_content is not None
            },
            project_name=target.repository.distribution,
            package_name=project.package_name,
            path=root / c.PYPROJECT_FILENAME,
            scaffold_project=codegen.scaffold.project,
            runtime_dependency_overlay=project.runtime_dependency_overlay,
            declared_project_dependencies=(),
            topology=m.Infra.PyprojectDeclaredTopology(
                root_modules=project.root_modules,
                root_packages=project.root_packages,
                repository_namespace_packages=project.repository_namespace_packages,
                packaged_data_paths=project.packaged_data_paths,
                planned_data_files=tuple(
                    destination for _, destination in scaffold_entries
                ),
                declared_python_dirs=tuple(
                    self._scaffold_python_dirs(
                        codegen.templates.entries, target.make_profile
                    ),
                ),
                declared_python_dirs_are_complete=(
                    target.make_profile is not c.Infra.MakeProfile.WORKSPACE
                ),
                analysis_exclusions=tuple(
                    path.as_posix()
                    for path in (
                        *target.external_dependency_paths,
                        *workspace.external_dependency_paths,
                    )
                ),
            ),
        )
        publications: list[t.Pair[Path, m.Infra.CodegenPhaseAnalysis]] = []
        with self._source_view(
            root,
            source_states=lazy_sources.value[1],
            declared_files=tuple(lazy_sources.value[0]),
            source_publications=publications,
        ) as binding:
            with binding[0].source_consumption() as consumption:
                tooling_result = modernizer.resolve_tooling_context(
                    tooling_request, source_project=binding[0]
                )
                if tooling_result.failure:
                    return r[t.SequenceOf[m.Infra.CodegenFilePlan]].from_failure(
                        tooling_result
                    )
                render_inputs = self.resolve_render_inputs(
                    target=target,
                    workspace=workspace,
                    codegen=codegen,
                    tooling_runtime=tooling_result.value,
                    managed_artifacts=u.Infra.empty_snapshot(),
                )
                context = self._project_render_context(
                    render_inputs,
                    planned_data_files=tuple(
                        destination for _, destination in scaffold_entries
                    ),
                )
                if context.failure:
                    return r[t.SequenceOf[m.Infra.CodegenFilePlan]].from_failure(
                        context
                    )
                targets = self._validated_scaffold_targets(
                    codegen, root, scaffold_entries
                )
                planned = targets.flat_map(
                    lambda _validated: self._scaffold_planned_entries(
                        render_inputs, context.value, scaffold_entries
                    )
                )
                if planned.failure:
                    return r[t.SequenceOf[m.Infra.CodegenFilePlan]].from_failure(
                        planned
                    )
                files = planned.value
            return self._qualified_existing_tooling(
                render_inputs, contract, files, consumption, publications
            ).flat_map(
                lambda qualified: self._with_planned_facade_rebinds(
                    planned=tuple(qualified),
                    scaffold_entries=scaffold_entries,
                    render_inputs=render_inputs,
                    contract=contract,
                )
            )

    def _scaffold_planned_entries(
        self,
        render_inputs: m.Infra.CodegenRenderInputs,
        context: m.Infra.ProjectRenderContext,
        scaffold_entries: t.VariadicTuple[t.Pair[m.Infra.TemplateEntrySpec, str]],
    ) -> p.Result[t.SequenceOf[m.Infra.CodegenFilePlan]]:
        """Plan scaffold entries in dependency order using the owned render state.

        Returns:
            The ordered plans, or the first entry failure.

        """
        result_type = r[t.SequenceOf[m.Infra.CodegenFilePlan]]
        planned: list[m.Infra.CodegenFilePlan] = []
        # The pyproject plans first: renders that derive from its requirements
        # (the dependabot cooldown exclusion) read the planned bytes.
        for entry, destination in sorted(
            scaffold_entries,
            key=lambda item: item[1] != c.PYPROJECT_FILENAME,
        ):
            entry_plan = self._scaffold_entry_plan(
                entry=entry,
                destination=destination,
                render_inputs=render_inputs,
                context=context,
            )
            if entry_plan.failure:
                return result_type.from_failure(entry_plan)
            file_plan = entry_plan.value
            metadata = render_inputs.target.root / c.PYPROJECT_FILENAME
            if file_plan.path != metadata and any(
                item.path == metadata for item in planned
            ):
                file_plan = file_plan.model_copy(
                    update={
                        "tracking_dependencies": tuple(
                            dict.fromkeys((*file_plan.tracking_dependencies, metadata))
                        ),
                    },
                )
            planned.append(file_plan)
        return self._artifact_dependency_plans(
            render_inputs.codegen,
            render_inputs.target.root,
            planned,
        )

    def _validated_scaffold_targets(
        self,
        codegen: m.Infra.CodegenConfigSpec,
        root: Path,
        scaffold_entries: t.VariadicTuple[t.Pair[m.Infra.TemplateEntrySpec, str]],
    ) -> p.Result[bool]:
        """Validate every scaffold template source and destination path.

        One selection and one formatted path govern validation and planning.

        Returns:
            The resulting ``p.Result[bool]``.

        """
        result_type = r[bool]
        seen_destinations: set[str] = set()
        for entry, destination in scaffold_entries:
            source = self._validated_template_source(
                codegen,
                entry,
                destination,
            )
            if source.failure:
                return result_type.from_failure(source)
            destination_check = self._validated_destination(
                root,
                destination,
                seen_destinations,
            )
            if destination_check.failure:
                return result_type.from_failure(destination_check)
            seen_destinations.add(destination)
        return result_type.ok(value=True)

    @staticmethod
    def _validated_template_source(
        codegen: m.Infra.CodegenConfigSpec,
        entry: m.Infra.TemplateEntrySpec,
        destination: str,
    ) -> p.Result[bool]:
        """Prove a render entry's template source exists inside its root.

        Returns:
            The resulting ``p.Result[bool]``.

        """
        result_type = r[bool]
        if entry.source is None:
            return result_type.fail(
                f"render entry has no template source: {destination}",
            )
        source = u.Infra.codegen_artifact_source(codegen, entry)
        if not source.is_file():
            return result_type.fail(
                f"artifact source is missing: {entry.source}",
            )
        return result_type.ok(value=True)

    @staticmethod
    def _validated_destination(
        root: Path,
        destination: str,
        seen_destinations: set[str],
    ) -> p.Result[bool]:
        """Confine one template destination inside the root, without duplicates.

        Returns:
            The resulting ``p.Result[bool]``.

        """
        result_type = r[bool]
        relative = Path(destination)
        if relative.is_absolute() or ".." in relative.parts:
            return result_type.fail(
                f"template destination escapes repository root: {destination}",
            )
        if destination in seen_destinations:
            return result_type.fail(
                f"duplicate template destination: {destination}",
            )
        path = root / relative
        if path.exists() and not path.is_file():
            return result_type.fail(
                f"template destination is not a regular file: {path}",
            )
        for parent in path.parents:
            if parent == root:
                break
            if parent.exists() and not parent.is_dir():
                return result_type.fail(
                    f"template destination parent is not a directory: {parent}",
                )
        return result_type.ok(value=True)

    def _with_planned_facade_rebinds(
        self,
        *,
        planned: t.VariadicTuple[m.Infra.CodegenFilePlan],
        scaffold_entries: t.VariadicTuple[t.Pair[m.Infra.TemplateEntrySpec, str]],
        render_inputs: m.Infra.CodegenRenderInputs,
        contract: m.Infra.CodegenConformSurfaceContract,
    ) -> p.Result[t.SequenceOf[m.Infra.CodegenFilePlan]]:
        """Render the final pyproject over the sources the scaffold plans.

        The pyproject renders before the sources, but its facade-rebind Mypy
        scope and its first-party namespaces are facts of those sources:
        derived from the tree before publication it omits every facade the
        scaffold creates, and the next
        generation adds them. Once every source is planned, the scope is
        derived from the planned bytes and the pyproject is rendered once more
        with it; nothing rendered earlier reads that scope.

        Returns:
            The resulting ``p.Result[t.SequenceOf[m.Infra.CodegenFilePlan]]``.

        """
        result_type = r[t.SequenceOf[m.Infra.CodegenFilePlan]]
        pyproject_entry = next(
            (
                entry
                for entry, destination in scaffold_entries
                if destination == c.PYPROJECT_FILENAME
            ),
            None,
        )
        if pyproject_entry is None:
            return result_type.ok(planned)
        root = render_inputs.target.root
        projected = {plan.path: plan for plan in planned}
        export_publications: list[t.Pair[Path, m.Infra.CodegenPhaseAnalysis]] = []
        with self._source_view(
            root,
            declared_files=tuple(projected.values()),
            source_publications=export_publications,
        ) as binding:
            exports = FlextInfraCodegenLazyInit(
                repository_root=root, project_scope_roots=(root,)
            ).plan_files(
                source_project=binding[0], source_publications=export_publications
            )
            if exports.failure:
                return result_type.from_failure(exports)
            self.retain_diagnostics(
                exports.value.exception, issues=exports.value.issues
            )
            inputs = u.Infra.unique_states((
                *binding[1]()[0],
                *(
                    state
                    for plan in exports.value.files
                    for state in plan.source_states
                ),
            ))
            if inputs.failure:
                return result_type.from_failure(inputs)
        projected.update((plan.path, plan) for plan in exports.value.files)
        source_states = inputs.value
        planned = tuple(projected.values())
        publications: list[t.Pair[Path, m.Infra.CodegenPhaseAnalysis]] = []
        with self._source_view(
            root,
            source_states=source_states,
            declared_files=planned,
            source_publications=publications,
        ) as binding:
            tooling = render_inputs.tooling_runtime
            with binding[0].source_consumption() as consumption:
                render_inputs.tooling_runtime = self.planned_source_tooling(
                    render_inputs, planned, source_project=binding[0]
                )
            if render_inputs.tooling_runtime is tooling:
                return self._qualified_existing_tooling(
                    render_inputs, contract, planned, consumption, publications
                )
            context = self._project_render_context(
                render_inputs,
                planned_data_files=tuple(
                    destination for _, destination in scaffold_entries
                ),
            )
            if context.failure:
                return result_type.from_failure(context)
            final = self._scaffold_entry_plan(
                entry=pyproject_entry,
                destination=c.PYPROJECT_FILENAME,
                render_inputs=render_inputs,
                context=context.value,
            )
            return final.flat_map(
                lambda rendered: self._qualified_existing_tooling(
                    render_inputs,
                    contract,
                    tuple(
                        rendered if plan.path == rendered.path else plan
                        for plan in planned
                    ),
                    consumption,
                    publications,
                )
            )

    def _scaffold_entry_plan(
        self,
        *,
        entry: m.Infra.TemplateEntrySpec,
        destination: str,
        render_inputs: m.Infra.CodegenRenderInputs,
        context: m.Infra.ProjectRenderContext,
    ) -> p.Result[m.Infra.CodegenFilePlan]:
        """Render one scaffold entry into its file plan.

        A rendered pyproject advances this operation's existing render state.

        Returns:
            The finalized entry's file plan.

        """
        result_type = r[m.Infra.CodegenFilePlan]
        root = render_inputs.target.root
        if entry.source is None:
            return result_type.fail(
                f"render entry has no template source: {destination}",
            )
        rendered = self._rendered_artifact_source(
            render_inputs,
            destination=destination,
            failure_prefix=(
                f"stage=templates repository={render_inputs.target.repository.name} "
            ),
            project_context=context,
            entry=entry,
        )
        if rendered.failure:
            return result_type.from_failure(rendered)
        rendered_content = (
            rendered
            if entry.source_kind == "resource"
            else self.compose_project_artifact(
                root,
                destination,
                rendered.value.rendered,
                render_inputs=render_inputs,
                source_states=rendered.value.source_states,
            )
        )
        if rendered_content.failure:
            return result_type.from_failure(rendered_content)
        names = None
        if destination == c.PYPROJECT_FILENAME:
            names = self.direct_sources(
                render_inputs,
                composed=rendered_content.value.rendered,
            )
            if names.failure:
                return result_type.from_failure(names)
        planned = self.file_plan(
            root,
            destination,
            rendered_content.value,
            mode=(
                entry.ownership.mode
                if entry.ownership is not None
                else render_inputs.codegen.modes.file_default
            ),
        )
        if planned.failure:
            return planned
        file = planned.value
        if entry.ownership is not None:
            file = file.model_copy(
                update={
                    "owner": entry.ownership.owner,
                    "policy": entry.ownership.policy,
                    "tracking": entry.ownership.tracking,
                }
            )
        if names is not None:
            render_inputs.planned_direct_sources = names.value
        return result_type.ok(file)


__all__: list[str] = ["FlextInfraCodegenConformScaffoldPlan"]
