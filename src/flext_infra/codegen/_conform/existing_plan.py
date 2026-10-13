"""Conformance planning for existing repositories and governed artifacts.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import time
import traceback
from collections.abc import MutableMapping
from functools import partial
from pathlib import Path
from typing import Literal

from flext_core import FlextStrictYamlConfigSource
from flext_infra import FlextInfraConfig, c, config, m, p, r, t, u
from flext_infra.codegen._conform import FlextInfraCodegenConformArtifactRender
from flext_infra.deps import FlextInfraPyprojectModernizer
from flext_infra.services import FlextInfraCodegenVscodeMixin
from flext_infra.workspace import FlextInfraWorkspaceEnvironmentContracts


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
        elif (
            contract.destinations == frozenset({c.PYPROJECT_FILENAME})
            and not contract.templates
        ):
            return self._plan_existing_pyproject_bootstrap(target, codegen)
        else:
            return None
        planned = self._bootstrap_destination_plan(
            target, codegen, context, destination
        )
        if planned.failure:
            return r[t.SequenceOf[m.Infra.CodegenFilePlan]].from_failure(planned)
        return r[t.SequenceOf[m.Infra.CodegenFilePlan]].ok((planned.value,))

    @staticmethod
    def _bootstrap_pyproject_source(
        path: Path,
    ) -> p.Result[t.Pair[m.Cli.AtomicFileState, str]]:
        """Recover owned TOML while retaining the exact authenticated before state.

        Returns:
            The original file identity and its recovered regeneration source.
        """
        result_type = r[t.Pair[m.Cli.AtomicFileState, str]]
        before = u.Cli.atomic_read_binary_file_state(path, required=True)
        if before.failure:
            return result_type.from_failure(before)
        if before.value.content is None:
            return result_type.fail(f"pyproject is absent: {path}")
        recovered = u.Infra.recover_live_pyproject_text(
            before.value.content.decode(c.DEFAULT_ENCODING),
        )
        if recovered.failure:
            return result_type.from_failure(recovered)
        source = u.Infra.pyproject_regeneration_source(recovered.value)
        if source.failure:
            return result_type.from_failure(source)
        return result_type.ok((before.value, source.value))

    @classmethod
    def _plan_existing_pyproject_bootstrap(
        cls,
        target: m.Infra.RepositoryConformTarget,
        codegen: m.Infra.CodegenConfigSpec,
    ) -> p.Result[t.SequenceOf[m.Infra.CodegenFilePlan]]:
        """Publish owned TOML policy before native semantic consumers open it.

        This recovery surface uses the ordinary dependency conformance phases,
        not the full template context whose runtime-base discovery opens Rope.
        Complete generation still derives that context after bootstrap.

        Returns:
            One authenticated pyproject plan, preserving live unowned content.

        """
        result_type = r[t.SequenceOf[m.Infra.CodegenFilePlan]]
        path = target.root / c.PYPROJECT_FILENAME
        prepared = cls._bootstrap_pyproject_source(path)
        if prepared.failure:
            return result_type.from_failure(prepared)
        before, source = prepared.value
        owners = u.Infra.snapshot_config_sources(config.ssot_config_dir().parent)
        if owners.failure:
            return result_type.from_failure(owners)
        artifacts = u.Infra.snapshot_committed_project_managed_artifacts(target.root)
        if artifacts.failure:
            return result_type.from_failure(artifacts)
        modernizer = FlextInfraPyprojectModernizer(
            repository_root=target.root,
            skip_check=True,
            managed_artifacts=artifacts.value.resolution,
        )
        rendered = modernizer.conform_source(
            source,
            path=path,
            format_source=False,
            topology=m.Infra.PyprojectDeclaredTopology(
                analysis_exclusions=tuple(
                    item.as_posix() for item in target.external_dependency_paths
                ),
            ),
        )
        if rendered.failure:
            return result_type.from_failure(rendered)
        managed = tuple(
            item
            for item in codegen.managed_files
            if item.path == Path(c.PYPROJECT_FILENAME)
        )
        if len(managed) != 1:
            return result_type.fail("pyproject bootstrap requires one managed owner")
        planned = m.Infra.CodegenFilePlan(
            project=target.root,
            path=path,
            before=before,
            desired_content=rendered.value.encode(c.DEFAULT_ENCODING),
            desired_mode=managed[0].mode,
            source_states=(*owners.value, *artifacts.value.sources),
        )
        return result_type.ok((planned,))

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
        _project, _metadata = identity
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
        custom_result = (
            self._plan_existing_custom(root, codegen, profile=target.make_profile.value)
            if contract.custom
            else r[t.SequenceOf[m.Infra.CodegenFilePlan]].ok(())
        )
        if custom_result.failure:
            return result_type.from_failure(custom_result)
        tooling_context = self._existing_tooling_context(
            target,
            identity,
            codegen,
            managed_artifacts.value.resolution,
            custom_result.value,
        )
        if tooling_context.failure:
            return result_type.from_failure(tooling_context)
        u.Cli.info(
            f"  stage=tooling-context repository={repository.name} "
            f"elapsed={time.monotonic() - tooling_started:.2f}s",
        )
        render_inputs = self.resolve_render_inputs(
            target=target,
            workspace=workspace,
            codegen=codegen,
            tooling_runtime=tooling_context.value,
            managed_artifacts=managed_artifacts.value,
        )
        managed_result = self._plan_existing_templates(
            render_inputs=render_inputs,
            contract=contract,
        )
        if managed_result.failure:
            return result_type.from_failure(managed_result)
        planned = list(managed_result.value)
        planned.extend(custom_result.value)
        final_inputs = self.planned_source_render_inputs(render_inputs, planned)
        if contract.pyproject and final_inputs is not render_inputs:
            final_templates = self._plan_existing_templates(
                render_inputs=final_inputs,
                contract=contract,
            )
            if final_templates.failure:
                return result_type.from_failure(final_templates)
            planned = [*final_templates.value, *planned[len(managed_result.value) :]]
        return result_type.ok(tuple(planned))

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
                upstream=project.upstream,
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
            item for item in codegen.managed_files if item.path == Path(destination)
        )
        if len(managed) != 1:
            return result_type.fail(
                f"{destination} requires exactly one managed-file declaration",
            )
        template = u.Infra.codegen_templates_root(codegen) / entries[0].source
        sources: t.VariadicTuple[m.Cli.AtomicFileState] = ()
        if destination in {c.Infra.MISE_TOML_FILENAME, c.Infra.ENVRC_FILENAME}:
            owner_sources = u.Infra.snapshot_config_sources(
                config.ssot_config_dir().parent
            )
            if owner_sources.failure:
                return result_type.from_failure(owner_sources)
            authenticated = u.Cli.template_render_authenticated(template, context)
            rendered = authenticated.map(lambda value: value.rendered)
            if authenticated.success:
                sources = (*owner_sources.value, *authenticated.value.source_states)
        else:
            rendered = u.Cli.template_render(template, context)
        if rendered.failure:
            return result_type.from_failure(rendered)
        conflict_marker = u.Infra.first_merge_conflict_marker(rendered.value)
        if conflict_marker is not None:
            return result_type.fail(
                f"rendered {destination} contains a merge conflict marker: "
                f"{conflict_marker}",
            )
        if destination == c.Infra.MISE_TOML_FILENAME:
            composed = self._composed_mise_overlay(target.root, rendered.value, None)
            rendered = composed.map(lambda value: value.rendered)
            if composed.success:
                sources = (*sources, *composed.value.source_states)
        return (
            result_type.from_failure(rendered)
            if rendered.failure
            else self.file_plan(
                target.root,
                destination,
                rendered.value,
                mode=managed[0].mode,
                source_states=sources,
            )
        )

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
            item for item in codegen.managed_files if item.path == Path(destination)
        )
        if len(entries) != 1 or entries[0].source is None or len(managed) != 1:
            return r[t.SequenceOf[m.Infra.CodegenFilePlan]].fail(
                f"docs config requires one declared render template "
                f"and owner: {destination}",
            )
        template = u.Infra.codegen_templates_root(codegen) / entries[0].source
        source = u.Cli.atomic_read_binary_file_state(template, required=True)
        if source.failure:
            return r[t.SequenceOf[m.Infra.CodegenFilePlan]].from_failure(source)
        rendered = u.Cli.template_render(template, workspace)
        if rendered.failure:
            return r[t.SequenceOf[m.Infra.CodegenFilePlan]].from_failure(rendered)
        parsed = u.Cli.json_loads(rendered.value)
        if parsed.failure:
            return r[t.SequenceOf[m.Infra.CodegenFilePlan]].from_failure(parsed)
        plan = self.file_plan(
            target.root,
            destination,
            rendered.value,
            mode=managed[0].mode,
            source_states=(source.value,),
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
            codegen.managed_files,
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
            r[str].fail(
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
            rendered.value,
            render_inputs=render_inputs,
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
            sources = u.Infra.iter_python_files(
                m.Infra.SourceScanRequest(project_roots=(root,)),
            )
            if sources.failure:
                return r[t.SequenceOf[m.Infra.CodegenFilePlan]].from_failure(sources)
            families: t.VariadicTuple[Literal["u", "p", "m"]] = ("u", "p", "m")
            layout = u.Infra.layout(root)
            package_dirs = {
                path.parent
                for path in sources.value
                if (path.parent / c.Infra.INIT_PY).is_file()
            }
            if layout is not None and layout.class_stem:
                package_dirs.add(layout.package_dir)
            for package_dir in sorted(package_dirs):
                for family in families:
                    if (
                        layout is None or package_dir != layout.package_dir
                    ) and u.Infra.facade_module_path(package_dir, family) is None:
                        continue
                    plans.extend(self._captured_facade_plan(root, package_dir, family))
        return r[t.SequenceOf[m.Infra.CodegenFilePlan]].ok(tuple(plans))

    def _captured_facade_plan(
        self,
        root: Path,
        package_dir: Path,
        family: Literal["u", "p", "m"],
    ) -> t.SequenceOf[m.Infra.CodegenFilePlan]:
        """Retain the original diagnostic while collecting independent plans.

        Returns:
            The declared facade plans, or no effects for a recorded failure.
        """
        facade_path = u.Infra.facade_module_path(package_dir, family)
        failure_path = facade_path if facade_path is not None else package_dir
        try:
            planned = self._utility_facade_plan(root, package_dir, family)
        except (OSError, ValueError):
            self._record_file_failure(failure_path, traceback.format_exc())
            return ()
        if planned.failure:
            self._record_file_failure(
                failure_path, planned.error or "facade planning failed"
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
    ) -> p.Result[t.SequenceOf[m.Infra.CodegenFilePlan]]:
        """Plan one projected facade for the discovered package layout.

        Returns:
            The owned facade file plan, or no plans for a family with no owners.

        Raises:
            ValueError: If a rendered facade has no declaring package module.

        """
        result_type = r[t.SequenceOf[m.Infra.CodegenFilePlan]]
        rendered = u.Infra.render_utility_facade(
            package_dir,
            family=family,
        )
        if rendered is None:
            return result_type.ok(())
        facade_path = u.Infra.facade_module_path(package_dir, family)
        if facade_path is None:
            msg = f"rendered {family} facade has no declaring module"
            raise ValueError(msg)
        relative = facade_path.relative_to(root)
        utility_plan = self.file_plan(root, relative.as_posix(), rendered)
        if utility_plan.failure:
            return result_type.from_failure(utility_plan)
        return result_type.ok((utility_plan.value,))

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
            for item in codegen.managed_files
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
            completed,
        )
        if represented_set.failure:
            return r[t.SequenceOf[m.Infra.CodegenFilePlan]].from_failure(
                represented_set,
            )
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
    ) -> p.Result[t.SequenceOf[m.Infra.CodegenFilePlan]]:
        """Plan only bindings selected by their declared artifact policy.

        Returns:
            Runtime-local file plans, including missing declared bindings.
        """
        completed: list[m.Infra.CodegenFilePlan] = []
        planned = self._represent_ungoverned_artifacts(
            target,
            codegen,
            {item.path: item for item in codegen.managed_files if item.runtime_binding},
            completed,
            vscode_spec=vscode_spec,
            migrate_tracking=True,
        )
        if planned.failure:
            return r[t.SequenceOf[m.Infra.CodegenFilePlan]].from_failure(planned)
        return r[t.SequenceOf[m.Infra.CodegenFilePlan]].ok(tuple(completed))

    def _represent_ungoverned_artifacts(
        self,
        target: m.Infra.RepositoryConformTarget,
        codegen: m.Infra.CodegenConfigSpec,
        governed_by_path: t.MappingKV[Path, m.Infra.ManagedFileSpec],
        completed: list[m.Infra.CodegenFilePlan],
        *,
        vscode_spec: m.Infra.CodegenVscodeSpec | None = None,
        migrate_tracking: bool = False,
    ) -> p.Result[bool]:
        """Append a plan for every unrepresented governed artifact in the mapping.

        Returns:
            The resulting ``p.Result[bool]``.

        """
        root = target.root
        profile = target.make_profile
        vscode_spec = target.vscode_spec if vscode_spec is None else vscode_spec
        runtime_root = (
            root
            if self.initial_workspace is not None
            and target.repository.name == self.initial_workspace.repository.name
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
            if not path.exists() and not governed.runtime_binding:
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
                migrated = self._vscode_tracking_plans(request)
                if migrated.failure:
                    self._record_file_failure(
                        path,
                        migrated.error or "cannot plan runtime tracking migration",
                        exception=migrated.exception,
                    )
                    continue
                completed.extend(migrated.value)
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
                completed.append(decided_value)
        return r[bool].ok(value=True)

    @classmethod
    def _vscode_tracking_plans(
        cls,
        request: m.Infra.CodegenGovernedPlanRequest,
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
        if state.content is None:
            error = ValueError(
                f"captured editor index blob is absent: {request.relative}"
            )
            return result_type.fail(str(error), exception=error)
        decoded = r[str].create_from_callable(
            lambda: state.content.decode(c.DEFAULT_ENCODING),
        )
        if decoded.failure:
            return result_type.from_failure(decoded)
        indexed = FlextInfraCodegenVscodeMixin.parse_vscode_settings(decoded.value)
        live = FlextInfraCodegenVscodeMixin.parse_vscode_settings(request.current)
        if indexed.failure:
            return result_type.from_failure(indexed)
        if live.failure:
            return result_type.from_failure(live)
        loaded = u.Infra.load_codegen_inputs(request.root)
        if loaded.failure:
            return result_type.from_failure(loaded)
        baseline = u.Infra.project_codegen_inputs(
            request.root,
            loaded.value,
            include_local=False,
        )
        if baseline.failure:
            return result_type.from_failure(baseline)
        project = FlextInfraCodegenVscodeMixin.vscode_declaration_delta(
            request.root,
            indexed.value,
            spec=baseline.value.spec.vscode,
        )
        if project.failure:
            return result_type.from_failure(project)
        layers = FlextInfraConfig.config_layer_paths_for_repository(
            request.root,
            filename=c.Infra.CODEGEN_CONFIG_FILENAME,
        )
        if project.value.values and layers[1].resolve() == layers[0].resolve():
            error = ValueError(
                "project editor declarations share the distributed defaults: "
                f"{layers[1]}",
            )
            return result_type.fail(str(error), exception=error)
        projections = (
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
        composed = u.Infra.project_codegen_inputs(
            request.root,
            loaded.value,
            projections=projections,
        )
        if composed.failure:
            return result_type.from_failure(composed)
        local = FlextInfraCodegenVscodeMixin.vscode_local_declaration_delta(
            request.root,
            indexed.value,
            live.value,
            spec=composed.value.spec.vscode,
        )
        if local.failure:
            return result_type.from_failure(local)
        if local.value.values:
            projections = (
                *projections,
                m.Infra.CodegenLayerProjection(
                    path=layers[2],
                    values={"Infra": {"codegen": {"vscode": dict(local.value.values)}}},
                ),
            )
        effective = u.Infra.project_codegen_inputs(
            request.root,
            loaded.value,
            projections=projections,
        )
        if effective.failure:
            return result_type.from_failure(effective)
        declarations: list[m.Infra.CodegenFilePlan] = []
        for path, delta in zip(layers[1:], (project.value, local.value), strict=True):
            if not delta.values:
                continue
            if path.resolve() == layers[0].resolve():
                error = ValueError(
                    "project editor declarations share the distributed defaults: "
                    f"{path}",
                )
                return result_type.fail(str(error), exception=error)
            planned = cls._vscode_declaration_plan(
                request.root,
                path,
                delta,
                sources=loaded.value.sources,
            )
            if planned.failure:
                return result_type.from_failure(planned)
            declarations.append(planned.value)
        binding = cls._vscode_merged_plan(
            request.model_copy(
                update={
                    "vscode_spec": effective.value.spec.vscode,
                    "source_states": loaded.value.sources,
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
    def _vscode_declaration_plan(
        cls,
        root: Path,
        path: Path,
        delta: m.Infra.CodegenVscodeDeclarationDelta,
        *,
        sources: t.VariadicTuple[m.Cli.AtomicFileState],
    ) -> p.Result[m.Infra.CodegenFilePlan]:
        """Merge captured project YAML through its canonical config primitive.

        Returns:
            A guarded source plan preserving all unrelated configuration values.
        """
        result_type = r[m.Infra.CodegenFilePlan]
        captured = cls.file_plan(root, path.relative_to(root).as_posix(), "")
        if captured.failure:
            return result_type.from_failure(captured)
        before = captured.value.before
        original = next((state for state in sources if state.path == path), None)
        if original is not None and before != original:
            error = ValueError(
                f"editor declaration changed after input capture: {path}"
            )
            return result_type.fail(str(error), exception=error)
        if (
            original is None
            and isinstance(before, m.Cli.AtomicFileState)
            and before.content is not None
        ):
            error = ValueError(
                f"editor declaration appeared after input capture: {path}"
            )
            return result_type.fail(str(error), exception=error)
        payload: t.JsonMapping = {}
        if isinstance(before, m.Cli.AtomicFileState) and before.content is not None:
            parsed = u.Infra.read_codegen_config_document(before.content)
            if parsed.failure:
                return result_type.from_failure(parsed)
            payload = parsed.value
        merged = FlextStrictYamlConfigSource.merge_values(
            dict(payload),
            {"Infra": {"codegen": {"vscode": dict(delta.values)}}},
        )
        serialized = u.Cli.yaml_dump_str(merged)
        if serialized.failure:
            return result_type.from_failure(serialized)
        return result_type.ok(
            captured.value.model_copy(
                update={"desired_content": serialized.value.encode(c.DEFAULT_ENCODING)},
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
            runtime_root=request.runtime_root,
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
