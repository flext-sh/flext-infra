"""Conformance planning of bootstrap recovery surfaces in existing repositories.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from flext_infra import c, m, p, r, t, u
from flext_infra.codegen.codegen_preconditions import FlextInfraCodegenPreconditions
from flext_infra.deps import FlextInfraPyprojectModernizer


class FlextInfraCodegenConformExistingPlanRecoveryMixin:
    """Plan recovery surfaces that publish before consumers parse projections."""

    if TYPE_CHECKING:

        @staticmethod
        def file_plan(
            root: Path,
            relative_path: str,
            rendered: str,
            *,
            mode: int = 0o644,
            source_states: t.VariadicTuple[m.Cli.AtomicFileState] = (),
        ) -> p.Result[m.Infra.CodegenFilePlan]: ...

        @staticmethod
        def _repository_root_rel(workspace: m.Infra.WorkspaceSpec) -> str: ...

        @classmethod
        def conformed_pyproject_source(
            cls,
            source: str,
            *,
            target: m.Infra.RepositoryConformTarget,
            workspace: m.Infra.WorkspaceSpec,
            codegen: m.Infra.CodegenConfigSpec,
            member_declarations: t.VariadicTuple[m.Cli.AtomicFileState] | None = None,
        ) -> p.Result[str]: ...

        @classmethod
        def _member_declaration_states(
            cls,
            repository_root: Path,
            workspace: m.Infra.WorkspaceSpec,
        ) -> p.Result[
            t.Pair[
                t.VariadicTuple[m.Cli.AtomicFileState],
                t.VariadicTuple[m.Cli.AtomicFileState],
            ]
        ]: ...

        def _makefile_render_spec(
            self,
            target: m.Infra.RepositoryConformTarget,
            workspace: m.Infra.WorkspaceSpec,
            codegen: m.Infra.CodegenConfigSpec,
        ) -> p.Result[m.Infra.MakefileRenderSpec]: ...

        @classmethod
        def _composed_mise_overlay(
            cls,
            repository_root: Path,
            rendered: str,
            render_inputs: m.Infra.CodegenRenderInputs | None,
        ) -> p.Result[m.Infra.CodegenArtifactComposition]: ...

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
        elif (
            contract.destinations is not None
            and c.PYPROJECT_FILENAME in contract.destinations
            and not contract.templates
        ):
            return self._plan_existing_pyproject_bootstrap(target, workspace, codegen)
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
        workspace: m.Infra.WorkspaceSpec,
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
        artifacts = u.Infra.snapshot_committed_project_managed_artifacts(target.root)
        if artifacts.failure:
            return result_type.from_failure(artifacts)
        captured = cls._bootstrap_member_sources(
            target.root,
            workspace,
            artifacts.value.sources,
        )
        if captured.failure:
            return result_type.from_failure(captured)
        sources, declarations = captured.value
        modernizer = FlextInfraPyprojectModernizer(
            repository_root=target.root,
            skip_check=True,
            managed_artifacts=artifacts.value.resolution,
        )
        conformed = cls.conformed_pyproject_source(
            source,
            target=target,
            workspace=workspace,
            codegen=codegen,
            member_declarations=declarations,
        )
        if conformed.failure:
            return result_type.from_failure(conformed)
        rendered = modernizer.conform_source(
            conformed.value,
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
        return cls._bootstrap_file_plan(
            target,
            codegen,
            (before, rendered.value, sources),
        )

    @classmethod
    def _bootstrap_member_sources(
        cls,
        root: Path,
        workspace: m.Infra.WorkspaceSpec,
        artifact_sources: t.VariadicTuple[m.Cli.AtomicFileState],
    ) -> p.Result[
        t.Pair[
            t.VariadicTuple[m.Cli.AtomicFileState],
            t.VariadicTuple[m.Cli.AtomicFileState],
        ]
    ]:
        """Combine the authenticated artifact and actual member declarations.

        Returns:
            The complete source evidence and original member declarations.

        """
        result = r[
            t.Pair[
                t.VariadicTuple[m.Cli.AtomicFileState],
                t.VariadicTuple[m.Cli.AtomicFileState],
            ]
        ]
        collected = cls._member_declaration_states(root, workspace)
        if collected.failure:
            return result.from_failure(collected)
        sources = FlextInfraCodegenPreconditions.unique_states((
            *artifact_sources,
            *collected.value[0],
        ))
        if sources.failure:
            return result.from_failure(sources)
        return result.ok((sources.value, collected.value[1]))

    @staticmethod
    def _bootstrap_file_plan(
        target: m.Infra.RepositoryConformTarget,
        codegen: m.Infra.CodegenConfigSpec,
        material: t.Triple[
            m.Cli.AtomicFileState,
            str,
            t.VariadicTuple[m.Cli.AtomicFileState],
        ],
    ) -> p.Result[t.SequenceOf[m.Infra.CodegenFilePlan]]:
        """Bind the conformed bytes and evidence to their declared managed owner.

        Returns:
            The complete bootstrap file plan, or an ambiguous-owner failure.

        """
        result_type = r[t.SequenceOf[m.Infra.CodegenFilePlan]]
        before, source, sources = material
        managed = tuple(
            item
            for item in codegen.managed_file_specs
            if item.path == Path(c.PYPROJECT_FILENAME)
        )
        if len(managed) != 1:
            return result_type.fail("pyproject bootstrap requires one managed owner")
        planned = m.Infra.CodegenFilePlan(
            project=target.root,
            path=target.root / c.PYPROJECT_FILENAME,
            before=before,
            desired_content=source.encode(c.DEFAULT_ENCODING),
            desired_mode=managed[0].mode,
            source_states=sources,
        )
        return result_type.ok((planned,))


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
        binding = self._bootstrap_template_binding(target, codegen, destination)
        if binding.failure:
            return r[t.SequenceOf[m.Infra.CodegenFilePlan]].from_failure(binding)
        template, managed_spec = binding.value
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
            mode=managed_spec.mode,
            source_states=rendered.value.source_states,
        )
        if plan.failure:
            return r[t.SequenceOf[m.Infra.CodegenFilePlan]].from_failure(plan)
        return r[t.SequenceOf[m.Infra.CodegenFilePlan]].ok((plan.value,))


__all__: list[str] = ["FlextInfraCodegenConformExistingPlanRecoveryMixin"]
