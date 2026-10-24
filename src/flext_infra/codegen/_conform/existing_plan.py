"""Conformance planning for existing repositories.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import time
import traceback
from collections.abc import Callable
from pathlib import Path
from typing import Literal

from flext_infra import c, m, p, r, t, u
from flext_infra.codegen import FlextInfraCodegenLazyInit
from flext_infra.codegen._conform import FlextInfraCodegenConformArtifactRender
from flext_infra.codegen._conform._existing_plan_governed import (
    FlextInfraCodegenConformExistingPlanGovernedMixin,
)
from flext_infra.codegen._conform._existing_plan_recovery import (
    FlextInfraCodegenConformExistingPlanRecoveryMixin,
)
from flext_infra.codegen.codegen_preconditions import FlextInfraCodegenPreconditions
from flext_infra.deps import FlextInfraPyprojectModernizer


class FlextInfraCodegenConformExistingPlan(
    FlextInfraCodegenConformArtifactRender,
    FlextInfraCodegenConformExistingPlanRecoveryMixin,
    FlextInfraCodegenConformExistingPlanGovernedMixin,
):
    """Conformance planning of managed and custom content in existing repositories."""

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
        if managed_artifacts.failure:
            return result_type.from_failure(managed_artifacts)
        u.Cli.info(
            f"  stage=managed-artifacts repository={repository.name} "
            f"elapsed={time.monotonic() - managed_started:.2f}s",
        )
        tooling_started = time.monotonic()
        lazy_result = (
            self._planned_lazy_init_files(root)
            if contract.tooling or contract.custom
            else r[t.SequenceOf[m.Infra.CodegenFilePlan]].ok(())
        )
        if lazy_result.failure:
            return result_type.from_failure(lazy_result)
        custom_result = (
            self._plan_existing_custom(
                root,
                codegen,
                profile=target.make_profile.value,
                lazy_plans=tuple(lazy_result.value),
            )
            if contract.custom
            else r[t.SequenceOf[m.Infra.CodegenFilePlan]].ok(())
        )
        if custom_result.failure:
            return result_type.from_failure(custom_result)
        tooling_runtime: m.Infra.ToolingRuntimeContext | None = None
        if contract.tooling:
            tooling_context = self._existing_tooling_context(
                target,
                identity,
                codegen,
                managed_artifacts.value.resolution,
                (*lazy_result.value, *custom_result.value),
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
        managed_result = self._plan_existing_templates(
            render_inputs=render_inputs,
            contract=contract,
        )
        if managed_result.failure:
            return result_type.from_failure(managed_result)
        final_inputs = (
            self.planned_source_render_inputs(
                render_inputs,
                [*lazy_result.value, *managed_result.value, *custom_result.value],
            )
            if contract.pyproject
            else render_inputs
        )
        final_templates = (
            self._plan_existing_templates(
                render_inputs=final_inputs,
                contract=contract,
            )
            if contract.pyproject and final_inputs is not render_inputs
            else managed_result
        )
        return final_templates.flat_map(
            lambda templates: self._facade_runtime_plans(
                root,
                (*templates, *custom_result.value),
                custom_result.value,
                lazy_result.value,
            ),
        )

    @staticmethod
    def _facade_runtime_plans(
        root: Path,
        planned: t.SequenceOf[m.Infra.CodegenFilePlan],
        custom: t.SequenceOf[m.Infra.CodegenFilePlan],
        initializers: t.SequenceOf[m.Infra.CodegenFilePlan],
    ) -> p.Result[t.SequenceOf[m.Infra.CodegenFilePlan]]:
        """Publish facade consumers together with their declared family barrels.

        Returns:
            Independent plans followed by the original dependent runtime plans.

        """
        result_type = r[t.SequenceOf[m.Infra.CodegenFilePlan]]
        facades = tuple(
            item for item in custom if item.path.suffix == c.Infra.EXT_PYTHON
        )
        packages = {item.path.parent for item in facades}
        if not packages:
            return result_type.ok(tuple(planned))
        families = tuple(
            package / family.directory
            for package in packages
            for family in u.Infra.facade_families().values()
        )
        barrels = tuple(
            item
            for item in initializers
            if item.path.name == c.Infra.INIT_PY
            and (
                item.path.parent in packages
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
        grouped_paths = {item.path for item in (*barrels, *facades)}
        group = f"{c.Infra.CodegenConformSurface.FACADES.value}:{root}"
        return result_type.ok((
            *(item for item in planned if item.path not in grouped_paths),
            *(
                item.model_copy(update={"dependency_group": group})
                for item in (*barrels, *facades)
            ),
        ))

    @staticmethod
    def _planned_lazy_init_files(
        root: Path,
    ) -> p.Result[t.SequenceOf[m.Infra.CodegenFilePlan]]:
        """Plan the lazy-init projection the declarations determine, read-only.

        Facades import family owners in package form, which resolves only
        through the package initializer the declaring modules' ``__all__``
        project. Tooling derivations therefore read the planned initializers,
        never the previous projection on disk: a stale initializer otherwise
        blocks its own regeneration, on every conform surface (a partial
        surface such as ``dependencies`` derives tooling too). Required runtime
        barrels join their facade consumers in the bootstrap dependency group;
        the later lazy-init phase publishes the remaining initializer plans.

        Returns:
            The repository's planned lazy-init file plans, or the planning failure.

        """
        planned = FlextInfraCodegenLazyInit(
            repository_root=root,
            project_scope_roots=(root,),
        ).plan_files()
        if planned.failure:
            return r[t.SequenceOf[m.Infra.CodegenFilePlan]].from_failure(planned)
        return r[t.SequenceOf[m.Infra.CodegenFilePlan]].ok(planned.value.files)

    def _existing_tooling_context(
        self,
        target: m.Infra.RepositoryConformTarget,
        identity: t.Pair[m.Infra.ProjectSpec, p.ProjectMetadata],
        codegen: m.Infra.CodegenConfigSpec,
        managed_resolution: m.Infra.ProjectManagedArtifactsResolution,
        planned: t.SequenceOf[m.Infra.CodegenFilePlan] = (),
    ) -> p.Result[m.Infra.ToolingRuntimeContext]:
        """Resolve the modernizer tooling context for one existing repository.

        Returns:
            The resulting ``p.Result[m.Infra.ToolingRuntimeContext]``.

        """
        root = target.root
        repository = target.repository
        project, metadata = identity
        modernizer = FlextInfraPyprojectModernizer(
            repository_root=root,
            skip_check=True,
            managed_artifacts=managed_resolution,
        )
        return modernizer.resolve_tooling_context(
            m.Infra.ToolingContextRequest(
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
                        target.project.root_modules
                        if target.project is not None
                        else ()
                    ),
                    root_packages=(
                        target.project.root_packages
                        if target.project is not None
                        else ()
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
            ),
        )

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
            or (workspace.project is None and profile is c.Infra.MakeProfile.WORKSPACE)
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
        lazy_plans: tuple[m.Infra.CodegenFilePlan, ...] = (),
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
            states = FlextInfraCodegenPreconditions.unique_states(
                tuple(state for plan in lazy_plans for state in plan.source_states)
            )
            if states.failure:
                return r[t.SequenceOf[m.Infra.CodegenFilePlan]].from_failure(states)
            families: t.VariadicTuple[Literal["u", "p", "m"]] = ("u", "p", "m")
            layout = u.Infra.layout(root)
            with u.Infra.facade_source_project(
                root, source_states=states.value, declared_files=lazy_plans
            ) as binding:
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
                            self._captured_facade_plan(
                                root, package_dir, family, binding
                            )
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


__all__: list[str] = ["FlextInfraCodegenConformExistingPlan"]
