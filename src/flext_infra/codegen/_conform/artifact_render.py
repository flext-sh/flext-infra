"""Governed artifact rendering and project overlay composition.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path

from flext_infra import c, config, m, p, r, t, u
from flext_infra.codegen._conform import FlextInfraCodegenConformContextRender
from flext_infra.deps import FlextInfraPyprojectModernizer
from flext_infra.deps.phases import FlextInfraToolTablesPhase


class FlextInfraCodegenConformArtifactRender(FlextInfraCodegenConformContextRender):
    """Governed artifact rendering and project overlay composition."""

    @staticmethod
    def render_artifact_source(
        codegen: m.Infra.CodegenConfigSpec,
        entry: m.Infra.TemplateEntrySpec,
        context: p.Model,
    ) -> p.Result[m.Infra.CodegenArtifactComposition]:
        """Capture an explicit package resource or authenticate a Jinja render.

        Args:
            codegen: The code generation configuration.
            entry: The template entry specification.
            context: The rendering context for the template.

        Returns:
            A result containing the composed artifact or an error.

        """
        result_type = r[m.Infra.CodegenArtifactComposition]
        source = u.Infra.codegen_artifact_source(codegen, entry)
        if entry.source_kind == "resource":
            if entry.source_package is None:
                return result_type.fail(
                    f"resource has no explicit package owner: {entry.destination}",
                )
            sources: list[m.Cli.AtomicFileState] = []
            for declared_source in entry.source_closure:
                original = u.Infra.codegen_artifact_source(
                    codegen,
                    entry.model_copy(update={"source": declared_source}),
                )
                captured = u.Cli.atomic_read_binary_file_state(original, required=True)
                if captured.failure:
                    return result_type.from_failure(captured)
                sources.append(captured.value)
            primary = next(state for state in sources if state.path == source)
            content = primary.content
            if content is None:
                return result_type.fail(
                    f"required resource has no captured bytes: {source}",
                )
            return result_type.ok(
                m.Infra.CodegenArtifactComposition(
                    rendered=content.decode(c.DEFAULT_ENCODING),
                    source_states=tuple(sources),
                    validation_context=m.Infra.ArtifactResourceValidationContext(
                        source=primary,
                        source_package=entry.source_package,
                        source_states=tuple(sources),
                    ),
                ),
            )
        return u.Cli.template_render_authenticated(source, context).map(
            lambda rendered: m.Infra.CodegenArtifactComposition(
                rendered=rendered.rendered,
                source_states=rendered.source_states,
            ),
        )

    @staticmethod
    def _artifact_dependency_plans(
        codegen: m.Infra.CodegenConfigSpec,
        root: Path,
        planned: t.SequenceOf[m.Infra.CodegenFilePlan],
    ) -> p.Result[t.SequenceOf[m.Infra.CodegenFilePlan]]:
        """Keep each selected artifact and its required outputs in one publication.

        Args:
            codegen: The code generation configuration.
            root: The root path for the generated artifacts.
            planned: A sequence of planned file artifacts.

        Returns:
            File plans with connected publication dependencies resolved.

        """
        result_type = r[t.SequenceOf[m.Infra.CodegenFilePlan]]
        by_path = {plan.path: plan for plan in planned}
        existing: dict[str, set[Path]] = {}
        for plan in planned:
            if plan.dependency_group is not None:
                existing.setdefault(plan.dependency_group, set()).add(plan.path)
        groups = list(existing.values())
        for entry in codegen.templates.entries:
            path = root / entry.destination
            if path not in by_path or not entry.requires_artifacts:
                continue
            required = {
                root / destination
                for destination in codegen.templates.required_destinations(
                    frozenset({entry.destination}),
                )
            }
            missing = required.difference(by_path)
            if missing:
                return result_type.fail(
                    f"artifact {entry.destination} has unplanned dependencies: "
                    f"{', '.join(str(item) for item in sorted(missing))}",
                )
            groups.append(required)
        while groups:
            group = groups.pop().copy()
            while touching := [item for item in groups if item.intersection(group)]:
                for item in touching:
                    group.update(item)
                    groups.remove(item)
            identities = sorted(
                identity
                for identity, paths in existing.items()
                if paths.intersection(group)
            )
            identity = (
                identities[0]
                if identities
                else f"artifacts:{root}:{min(group).relative_to(root)}"
            )
            for path in group:
                by_path[path] = by_path[path].model_copy(
                    update={"dependency_group": identity},
                )
        return result_type.ok(tuple(by_path.values()))

    @staticmethod
    def planned_source_tooling(
        render_inputs: m.Infra.CodegenRenderInputs,
        planned: t.SequenceOf[m.Infra.CodegenFilePlan],
        *,
        source_project: p.Infra.RopeProject | None = None,
    ) -> m.Infra.ToolingRuntimeContext:
        """Derive tooling from the Python sources the transaction will publish.

        Returns:
            The original or finalized source-derived tooling context.

        Raises:
            ValueError: If Python source rendering has no resolved tooling context.

        """
        root = render_inputs.target.root
        python_plans = tuple(
            plan
            for plan in planned
            if plan.path.suffix == c.Infra.EXT_PYTHON
            and plan.desired_content is not None
        )
        sources = {
            plan.path: plan.desired_content.decode(c.DEFAULT_ENCODING)
            for plan in python_plans
            if plan.desired_content is not None
        }
        tooling = render_inputs.tooling_runtime
        if tooling is None:
            msg = "Python source rendering requires resolved tooling context"
            raise ValueError(msg)
        parsed = u.Cli.toml_mapping_from_text_result(tooling.configuration).unwrap()
        payload: t.MutableJsonMapping = dict(parsed)
        runtime = u.Cli.toml_mapping_ensure_path(
            payload,
            (c.Infra.TOOL, c.Infra.RUFF, c.Infra.LINT_SECTION, "flake8-type-checking"),
        )
        current_runtime = u.validate_value(
            t.Infra.STR_SEQ_ADAPTER,
            runtime.get("runtime-evaluated-base-classes", []),
            strict=True,
        ).unwrap()
        tool_config = tooling.document
        if tool_config is None:
            msg = "Python source rendering requires elected tooling inputs"
            raise ValueError(msg)
        policy = tool_config.tools.ruff.lint.flake8_type_checking
        runtime_bases = (
            tuple(current_runtime)
            if not any(
                u.Infra.codegen_file_requires_effect(plan) for plan in python_plans
            )
            else u.Infra.runtime_evaluated_base_classes(
                root,
                sources,
                policy.runtime_evaluated_roots,
                source_project=source_project,
            )
        )
        first_party: list[t.JsonValue] = list(
            FlextInfraToolTablesPhase.first_party_namespaces(
                path=root,
                planned_sources=tuple(sources),
            ),
        )
        isort = u.Cli.toml_mapping_ensure_path(
            payload, (c.Infra.TOOL, c.Infra.RUFF, c.Infra.LINT_SECTION, c.Infra.ISORT)
        )
        if first_party == isort.get(c.Infra.KNOWN_FIRST_PARTY_HYPHEN) and list(
            runtime_bases
        ) == list(current_runtime):
            return tooling
        isort[c.Infra.KNOWN_FIRST_PARTY_HYPHEN] = first_party
        runtime["runtime-evaluated-base-classes"] = list(runtime_bases)
        return FlextInfraPyprojectModernizer.tooling_context_from_payload(
            payload,
            project_kind=tooling.project_kind,
            tool_config=tool_config,
            sources=tooling.sources,
        ).unwrap()

    @staticmethod
    def direct_sources(
        render_inputs: m.Infra.CodegenRenderInputs,
        *,
        composed: str | None = None,
    ) -> p.Result[t.VariadicTuple[str]]:
        """Read direct references from composed, finalized, or committed metadata.

        Returns:
            The selected metadata's direct-reference names without advancing state.

        """
        if composed is not None:
            document = u.Cli.toml_parse_text(composed)
            if document is None:
                return r[t.VariadicTuple[str]].fail(
                    "planned pyproject is not valid TOML",
                )
            return u.Infra.direct_source_names(document)
        if render_inputs.planned_direct_sources is not None:
            return r[t.VariadicTuple[str]].ok(render_inputs.planned_direct_sources)
        document = u.Cli.toml_read_document(
            render_inputs.target.root / c.PYPROJECT_FILENAME,
        )
        if document.failure:
            return r[t.VariadicTuple[str]].from_failure(document)
        return u.Infra.direct_source_names(document.value)

    @classmethod
    def compose_project_artifact(
        cls,
        repository_root: Path,
        destination: str,
        rendered: str,
        *,
        render_inputs: m.Infra.CodegenRenderInputs | None = None,
        source_states: t.VariadicTuple[m.Cli.AtomicFileState] = (),
    ) -> p.Result[m.Infra.CodegenArtifactComposition]:
        """Apply typed project overlays after canonical template rendering.

        Python repairs require the complete planned policy and source context;
        the staging owner prepares those bytes after composition, never here.

        Without ``render_inputs`` the committed project catalog overlays the
        render and no pyproject conformance runs.

        Returns:
            The resulting ``p.Result[m.Infra.CodegenArtifactComposition]``.

        """
        if destination == c.Infra.GITIGNORE:
            overlay = cls._composed_gitignore_overlay(
                repository_root,
                rendered,
                render_inputs,
            )
            if overlay.failure:
                return r[m.Infra.CodegenArtifactComposition].from_failure(overlay)
            rendered = overlay.value
        composer = {
            c.PYPROJECT_FILENAME: cls._composed_pyproject_overlay,
            c.Infra.MISE_TOML_FILENAME: cls._composed_mise_overlay,
            f"config/{c.Infra.INFRA_CONFIG_FILENAME}": cls._composed_release_overlay,
        }.get(destination)
        composed = (
            composer(repository_root, rendered, render_inputs)
            if composer is not None
            else r[m.Infra.CodegenArtifactComposition].ok(
                m.Infra.CodegenArtifactComposition(rendered=rendered),
            )
        )
        if composed.failure:
            return r[m.Infra.CodegenArtifactComposition].from_failure(composed)
        tooling_sources = (
            ()
            if render_inputs is None or render_inputs.tooling_runtime is None
            else render_inputs.tooling_runtime.sources
        )
        captured = u.Infra.unique_states(
            (*source_states, *tooling_sources, *composed.value.source_states),
        )
        if captured.failure:
            return r[m.Infra.CodegenArtifactComposition].from_failure(captured)
        return r[m.Infra.CodegenArtifactComposition].ok(
            composed.value.model_copy(update={"source_states": captured.value}),
        )

    @classmethod
    def _composed_gitignore_overlay(
        cls,
        repository_root: Path,
        rendered: str,
        render_inputs: m.Infra.CodegenRenderInputs | None,
    ) -> p.Result[str]:
        """Preserve the live gitignore's owned blocks in the render.

        Returns:
            The resulting ``p.Result[str]``.

        """
        if render_inputs is None:
            resolved = u.Infra.load_project_managed_artifacts(repository_root)
            if resolved.failure:
                return r[str].from_failure(resolved)
            artifacts = resolved.value.artifacts
        else:
            artifacts = render_inputs.managed_artifacts.resolution.artifacts
        suffix = u.Infra.gitignore_runtime_suffix(config.Infra.codegen)
        if suffix.failure:
            return r[str].from_failure(suffix)
        return u.Infra.preserve_project_gitignore_blocks(
            rendered,
            repository_root,
            artifacts.Gitignore.preserved_blocks,
            runtime_suffix=suffix.value,
        )

    @classmethod
    def _live_pyproject_overlay(
        cls,
        live_path: Path,
        rendered: str,
    ) -> p.Result[t.Pair[str, m.Cli.AtomicFileState]]:
        """Read the live declaration and preserve its project-owned values.

        Returns:
            The preserved overlay or the original read or composition failure.

        """
        state = u.Cli.atomic_read_binary_file_state(live_path)
        if state.failure:
            return r[t.Pair[str, m.Cli.AtomicFileState]].from_failure(state)
        original = state.value
        if original.content is None:
            return u.Infra.overlay_preserved(rendered, None).map(
                lambda source: (source, original),
            )
        return (
            u.Infra
            .recover_live_pyproject_text(
                original.content.decode(c.DEFAULT_ENCODING),
            )
            .flat_map(u.Infra.pyproject_regeneration_source)
            .flat_map(lambda live_text: u.Infra.overlay_preserved(rendered, live_text))
            .map(lambda source: (source, original))
        )

    @classmethod
    def _composed_pyproject_overlay(
        cls,
        repository_root: Path,
        rendered: str,
        render_inputs: m.Infra.CodegenRenderInputs | None,
    ) -> p.Result[m.Infra.CodegenArtifactComposition]:
        """Overlay, conform, and format the pyproject render.

        Returns:
            The resulting ``p.Result[m.Infra.CodegenArtifactComposition]``.

        """
        result_type = r[m.Infra.CodegenArtifactComposition]
        tooling = u.Infra.load_tooling_inputs(repository_root)
        if tooling.failure:
            return result_type.from_failure(tooling)
        live_path = repository_root / c.PYPROJECT_FILENAME
        overlaid = cls._live_pyproject_overlay(live_path, rendered)
        if overlaid.failure:
            return result_type.from_failure(overlaid)
        composed_rendered, original = overlaid.value
        original_tooling_sources = (
            ()
            if render_inputs is None or render_inputs.tooling_runtime is None
            else render_inputs.tooling_runtime.sources
        )
        combined_sources = u.Infra.unique_states(
            (*original_tooling_sources, *tooling.value.sources, original),
        )
        if combined_sources.failure:
            return result_type.from_failure(combined_sources)
        source_states: list[m.Cli.AtomicFileState] = list(combined_sources.value)
        if render_inputs is not None:
            conformed = cls.conformed_pyproject_source(
                composed_rendered,
                render_inputs,
            )
            if conformed.failure:
                return result_type.from_failure(conformed)
            composed_rendered = conformed.value
        formatted = u.Infra.format_toml_source(
            composed_rendered,
            path=live_path,
            toolchain_root=(
                repository_root
                if render_inputs is None
                else render_inputs.target.toolchain_root
            ),
            taplo_version=config.Infra.codegen.toolchain.tool_versions["taplo"],
        )
        # The parse-merge-dump overlay drops every template comment, so
        # this composition owner publishes the one generated-file header
        # (owner, adjustment rule, regeneration verb) on the final bytes.
        # A re-run reads the live file as data, so it never accumulates.
        # The render-provenance line names the running generator's version:
        # drift reports can then state both sides (rendered-by vs consumed)
        # instead of a bare byte diff (aihub-l42it.11 consolidation postmortem).

        return formatted.map(
            lambda source: m.Infra.CodegenArtifactComposition(
                rendered=(
                    f"{c.Infra.BANNER}{cls.rendered_by_stamp()}\n{source.lstrip()}"
                ),
                source_states=tuple(source_states),
            ),
        )

    @classmethod
    def _composed_mise_overlay(
        cls,
        repository_root: Path,
        rendered: str,
        render_inputs: m.Infra.CodegenRenderInputs | None,
    ) -> p.Result[m.Infra.CodegenArtifactComposition]:
        """Compose the mise declaration from the resolved artifact catalog.

        Returns:
            The resulting ``p.Result[m.Infra.CodegenArtifactComposition]``.

        """
        result_type = r[m.Infra.CodegenArtifactComposition]
        if render_inputs is None:
            snapshot = u.Infra.snapshot_committed_project_managed_artifacts(
                repository_root,
                read_committed_directory=u.Infra.git_committed_directory_blobs,
            )
            if snapshot.failure:
                return result_type.from_failure(snapshot)
            resolved_artifacts = snapshot.value
        else:
            resolved_artifacts = render_inputs.managed_artifacts
        composed = (
            u.Infra.compose_mise_toml_from_snapshot(
                resolved_artifacts.sources,
                rendered,
            )
            if resolved_artifacts.sources
            else u.Infra.compose_mise_toml_from_resolution(
                resolved_artifacts.resolution,
                rendered,
            )
        )
        if composed.failure:
            return result_type.from_failure(composed)
        config_sources = u.Infra.snapshot_config_sources(repository_root)
        if config_sources.failure:
            return result_type.from_failure(config_sources)
        return result_type.ok(
            m.Infra.CodegenArtifactComposition(
                rendered=composed.value,
                source_states=config_sources.value,
            ),
        )

    @classmethod
    def _composed_release_overlay(
        cls,
        repository_root: Path,
        rendered: str,
        _render_inputs: m.Infra.CodegenRenderInputs | None,
    ) -> p.Result[m.Infra.CodegenArtifactComposition]:
        """Replace only the declared closure keys, retaining authored YAML.

        Returns:
            The comment-preserving document and its original file witness.

        """
        result_type = r[m.Infra.CodegenArtifactComposition]
        current = u.Cli.atomic_read_binary_file_state(
            repository_root / "config" / c.Infra.INFRA_CONFIG_FILENAME,
            required=False,
        )
        if current.failure:
            return result_type.from_failure(current)
        parsed = u.Cli.yaml_roundtrip_load_map_text(
            current.value.content.decode(c.DEFAULT_ENCODING)
            if current.value.content is not None
            else "{}",
        )
        if parsed.failure:
            return result_type.from_failure(parsed)
        declaration = cls._release_declaration(parsed.value)
        if declaration.failure:
            return result_type.from_failure(declaration)
        overlay = u.Cli.yaml_parse(rendered)
        if overlay.failure:
            return result_type.from_failure(overlay)
        u.Cli.yaml_overlay_preserving_order(parsed.value, overlay.value)
        return u.Cli.yaml_roundtrip_dump_text(parsed.value).map(
            lambda text: m.Infra.CodegenArtifactComposition(
                rendered=text,
                source_states=(current.value,),
            ),
        )

    @staticmethod
    def _release_declaration(
        document: t.MappingKV[str, t.Cli.YamlValue],
    ) -> p.Result[t.MappingKV[str, t.Cli.YamlValue]]:
        """Validate only owned namespace shapes without copying authored values.

        Returns:
            The declared release mapping by reference, or its original shape error.

        """
        result_type = r[t.MappingKV[str, t.Cli.YamlValue]]
        namespace = document.get("Infra", {})
        if not isinstance(namespace, Mapping):
            return result_type.fail("Infra must be a mapping")
        release = namespace.get("release", {})
        if not isinstance(release, Mapping):
            return result_type.fail("Infra.release must be a mapping")
        return result_type.ok(release)

    @classmethod
    def _release_policy_render_inputs(
        cls,
        root: Path,
    ) -> p.Result[
        t.Pair[m.Infra.ReleasePolicySpec, t.VariadicTuple[m.Cli.AtomicFileState]]
    ]:
        """Select committed closure declarations, never local/private policy.

        Returns:
            The existing typed release policy and exact declaration witnesses.

        """
        result_type = r[
            t.Pair[m.Infra.ReleasePolicySpec, t.VariadicTuple[m.Cli.AtomicFileState]]
        ]
        owner = u.Infra.git_repository_root(m.Infra.GitRepoRequest(repo_root=root))
        if owner.failure:
            return result_type.from_failure(owner)
        workspace = owner.value.repository_root.resolve()
        witnesses: list[m.Cli.AtomicFileState] = []
        if workspace != root.resolve():
            members = u.Infra.git_submodule_declarations(workspace)
            if members.failure:
                return result_type.from_failure(members)
            if not any(
                (workspace / member.path).resolve() == root.resolve()
                for member in members.value
            ):
                return result_type.fail(f"undeclared release policy member: {root}")
            membership = u.Cli.atomic_read_binary_file_state(
                workspace / ".gitmodules",
                required=True,
            )
            if membership.failure:
                return result_type.from_failure(membership)
            witnesses.append(membership.value)
        declaration = u.Cli.atomic_read_binary_file_state(
            workspace / "config" / c.Infra.INFRA_CONFIG_FILENAME,
            required=False,
        )
        if declaration.failure:
            return result_type.from_failure(declaration)
        witnesses.append(declaration.value)
        document = u.Cli.yaml_parse(
            declaration.value.content.decode(c.DEFAULT_ENCODING)
            if declaration.value.content is not None
            else "{}",
        )
        selected = document.flat_map(cls._release_declaration)
        return selected.flat_map(
            lambda section: r[m.Infra.ReleasePolicySpec].create_from_callable(
                lambda: m.Infra.ReleasePolicySpec.model_validate({
                    "build_constraints": config.Infra.release.build_constraints,
                    "maintenance_line": section.get("maintenance_line"),
                    "finalize_maintenance": section.get("finalize_maintenance", False),
                }),
            ),
        ).map(
            lambda policy: (policy, tuple(witnesses)),
        )

    def _rendered_artifact_source(
        self,
        render_inputs: m.Infra.CodegenRenderInputs,
        *,
        entry: m.Infra.TemplateEntrySpec,
        destination: str,
        failure_prefix: str,
        project_context: m.Infra.ProjectRenderContext | None,
    ) -> p.Result[m.Infra.CodegenArtifactComposition]:
        """Resolve one artifact render context and render its template source.

        ``failure_prefix`` carries the only difference between the scaffold and
        existing-repository planners: the stage banner the scaffold planner
        prepends to a render failure.

        Returns:
            Rendered content and the exact templates consumed by Jinja.

        Raises:
            ValueError: If the catalog entry has no renderable source.

        """
        if entry.source is None:
            msg = f"render entry has no source: {destination}"
            raise ValueError(msg)
        if entry.source_kind == "resource":
            return self.render_artifact_source(
                render_inputs.codegen,
                entry,
                m.Infra.StaticTextRenderSpec(),
            )
        policy_sources: t.VariadicTuple[m.Cli.AtomicFileState] = ()
        if destination == f"config/{c.Infra.INFRA_CONFIG_FILENAME}":
            policy = self._release_policy_render_inputs(render_inputs.target.root)
            if policy.failure:
                return r[m.Infra.CodegenArtifactComposition].from_failure(policy)
            artifact_context = r[p.Model].ok(policy.value[0])
            policy_sources = policy.value[1]
        else:
            artifact_context = self._artifact_render_context(
                render_inputs,
                destination=destination,
                project_context=project_context,
            )
        if artifact_context.failure:
            return r[m.Infra.CodegenArtifactComposition].from_failure(artifact_context)
        template_path = u.Infra.codegen_artifact_source(render_inputs.codegen, entry)
        rendered = self.render_artifact_source(
            render_inputs.codegen,
            entry,
            artifact_context.value,
        )
        if rendered.failure:
            return r[m.Infra.CodegenArtifactComposition].from_failure(rendered)
        primary = next(
            (
                source
                for source in rendered.value.source_states
                if source.path == template_path.expanduser().absolute()
            ),
            None,
        )
        if primary is None or primary.content is None:
            return r[m.Infra.CodegenArtifactComposition].fail(
                f"authenticated template has no captured primary source: "
                f"{template_path}",
            )
        return self._require_rendered_content(
            rendered.value.rendered,
            template_relpath=entry.source,
            destination=destination,
            failure_prefix=failure_prefix,
            template_source=primary.content.decode(c.DEFAULT_ENCODING),
        ).map(
            lambda content: m.Infra.CodegenArtifactComposition(
                rendered=content,
                source_states=(*policy_sources, *rendered.value.source_states),
            ),
        )

    @staticmethod
    def _require_rendered_content(
        content: str,
        *,
        template_relpath: Path,
        destination: str,
        failure_prefix: str = "",
        template_source: str | None = None,
    ) -> p.Result[str]:
        """Refuse to publish a successful render that produced no content.

        A template whose condition renders the whole body away (for example a
        workflow fragment gated on an undeclared capability layer) would
        otherwise surface as a 0-byte artifact — indistinguishable from a
        fragment with nothing to do, silently dropping the steps a consumer
        believes it selected. An empty render is a declaration error: the
        consumer must declare the layer or retire the selection, and the
        generator must fail loud instead of writing the empty file.

        A template that is empty at its source declares a static artifact with
        no content of its own (the PEP 561 ``py.typed`` marker); there is no
        condition to render away, so its empty render is the declared content.
        Only a non-empty source that rendered empty is the declaration error
        this guard exists to catch.

        Returns:
            The resulting ``p.Result[str]``.

        """
        if content.strip():
            return r[str].ok(content)
        if template_source is not None and not template_source.strip():
            return r[str].ok(content)
        return r[str].fail(
            f"{failure_prefix}"
            f"template={template_relpath}: destination={destination}: "
            "render produced no content: the template condition rendered "
            "empty, which is a consumer declaration error (a selected "
            "artifact whose data layer is undeclared); declare the missing "
            "layer or retire the selection — publishing a 0-byte artifact "
            "is forbidden",
        )

    def _artifact_render_context(
        self,
        render_inputs: m.Infra.CodegenRenderInputs,
        *,
        destination: str,
        project_context: m.Infra.ProjectRenderContext | None,
    ) -> p.Result[p.Model]:
        """Resolve one governed artifact to its canonical typed render input.

        Returns:
            The resulting ``p.Result[p.Model]``.

        """
        for resolver in (
            self._repo_config_context,
            self._static_spec_context,
            self._beads_context,
            self._github_context,
            self._makefile_group_context,
        ):
            context = resolver(render_inputs, destination)
            if context is not None:
                return context
        return self._project_or_pass_context(
            render_inputs,
            project_context,
            destination=destination,
        )

    def _repo_config_context(
        self,
        render_inputs: m.Infra.CodegenRenderInputs,
        destination: str,
    ) -> p.Result[p.Model] | None:
        """Resolve the repository-shaped config specs (gitignore/sonar/qlty/envrc).

        Returns:
            The resulting ``p.Result[p.Model] | None`` where None marks a
            destination outside this group.

        """
        target = render_inputs.target
        workspace = render_inputs.workspace
        codegen = render_inputs.codegen
        repository = target.repository
        if destination == c.Infra.GITIGNORE:
            project_patterns: t.StrSequence = (
                render_inputs.managed_artifacts.resolution.artifacts.Gitignore.patterns
            )
            return r[p.Model].ok(
                m.Infra.GitignoreRenderSpec(
                    gitignore_sections=u.Infra.gitignore_sections(
                        codegen,
                        profile=target.make_profile,
                        # The declared distribution is the project identity; a
                        # scaffold renders before its pyproject exists.
                        project_name=repository.distribution,
                        workspace=workspace,
                        project_patterns=project_patterns,
                    ),
                ),
            )
        if destination == c.Infra.SONARCLOUD_PROPERTIES_FILENAME:
            # Why: conform itself projects managed tests/fixtures/ci/docker files
            # into every profile, so the tests directory always exists and
            # sonar.tests never names an absent directory.
            return r[p.Model].ok(
                m.Infra.SonarcloudRenderSpec(
                    sonarcloud=codegen.sonarcloud,
                    tests_dir=c.Infra.DIR_TESTS,
                    # Why: a workspace root checks its members out in place, and
                    # each member is a separate repository analysed by its own
                    # SonarCloud project; scanning them again from the root
                    # double-counts their code as root duplication.
                    workspace_subprojects=(
                        tuple(item.path.as_posix() for item in workspace.subprojects)
                        if target.make_profile is c.Infra.MakeProfile.WORKSPACE
                        else ()
                    ),
                    generated_source_globs=codegen.generated_source_globs,
                ),
            )
        if destination == (
            f"{c.Infra.QLTY_CONFIG_DIRNAME}/{c.Infra.QLTY_CONFIG_FILENAME}"
        ):
            # Generated source trees are tracked, so Git ignore rules no
            # longer keep them out of the smells scan.
            return r[p.Model].ok(
                m.Infra.QltyRenderSpec(
                    generated_source_globs=codegen.generated_source_globs,
                ),
            )
        if destination == c.Infra.ENVRC_FILENAME:
            # The workspace declaration owns whether a Beads route exists.
            # A repository without one must not render ledger activation.
            return r[p.Model].ok(
                m.Infra.EnvrcRenderSpec(
                    native_environment_unset=codegen.make.native_environment_unset,
                    toolchain=codegen.toolchain,
                    repository_root_rel=self._repository_root_rel(workspace),
                    environment_path_prepends=(
                        codegen.toolchain.environment_path_prepends
                    ),
                ),
            )
        return None

    @classmethod
    def _static_spec_context(
        cls,
        render_inputs: m.Infra.CodegenRenderInputs,
        destination: str,
    ) -> p.Result[p.Model] | None:
        """Resolve the fleet-static and toolchain specs.

        Returns:
            The resulting ``p.Result[p.Model] | None`` where None marks a
            destination outside this group.

        """
        codegen = render_inputs.codegen
        dist = render_inputs.target.repository.distribution
        spec: p.Model
        if destination == c.Infra.PRE_COMMIT_CONFIG_FILENAME:
            spec = m.Infra.MakeWorkflowRenderSpec(dist=dist, make=codegen.make)
        elif destination in {
            c.Infra.MARKDOWNLINT_CONFIG_FILENAME,
            c.Infra.MARKDOWNLINT_IGNORE_FILENAME,
        }:
            tooling = render_inputs.tooling_runtime
            if tooling is None or tooling.document is None:
                return r[p.Model].fail(
                    "Markdown rendering requires elected tooling inputs"
                )
            markdown = tooling.document.tools.markdown
            spec = m.Infra.MarkdownLintRenderSpec(
                rules=u.Infra.configuration_pairs(markdown.rules),
                exclude=markdown.exclude,
            )
        elif destination in {
            c.Infra.MISE_TOML_FILENAME,
            c.Infra.PYTHON_VERSION_FILENAME,
        }:
            # Computed toolchain fields are projections, not inputs: filter the
            # dump to the render spec's declared fields before construction.
            toolchain_data = {
                field_name: value
                for field_name, value in codegen.toolchain.model_dump().items()
                if field_name in m.Infra.ToolchainSpec.model_fields
            }
            spec = m.Infra.ToolchainSpec(**toolchain_data)
        elif destination == c.Infra.RELEASE_GITLEAKS_CONFIG_PATH:
            # Why: the release build phase snapshots the gitleaks
            # policy from the repository; it is fleet policy owned by
            # config/infra.yaml, never scaffold-only project metadata.
            spec = m.Infra.ReleasePolicySpec(
                build_constraints=config.Infra.release.build_constraints,
            )
        else:
            destination_path = Path(destination)
            if (
                destination_path.parent.as_posix() != "tests/fixtures/ci/docker"
                or destination_path.suffix != ".Dockerfile"
            ):
                return None
            spec = m.Infra.DistroDockerRenderSpec(
                package_name=dist.replace("-", "_"),
                python_version=codegen.toolchain.python_version,
                make=codegen.make,
            )
        return r[p.Model].ok(spec)

    @classmethod
    def _beads_context(
        cls,
        render_inputs: m.Infra.CodegenRenderInputs,
        destination: str,
    ) -> p.Result[p.Model] | None:
        """Resolve the Beads config and identity-marker specs.

        Returns:
            The resulting ``p.Result[p.Model] | None`` where None marks a
            destination outside this group.

        """
        target = render_inputs.target
        codegen = render_inputs.codegen
        if destination == c.Infra.BEADS_CONFIG_RELPATH:
            if target.beads is None:
                return r[p.Model].fail(
                    "Beads rendering requires enabled Beads identity",
                )
            project_types = target.beads.custom_issue_types
            required_types = codegen.toolchain.beads.required_custom_types
            beads = codegen.toolchain.beads
            return r[p.Model].ok(
                m.Infra.BeadsConfigRenderSpec(
                    issue_prefix=target.beads.issue_prefix,
                    endpoint_origin=beads.endpoint_origin,
                    endpoint_status=beads.endpoint_status,
                    gascity_enabled=target.gascity_enabled,
                    custom_issue_types=tuple(
                        dict.fromkeys((*project_types, *required_types)),
                    ),
                    dolt_mode=beads.dolt_mode,
                    export_auto=beads.export_auto,
                    backup_enabled=beads.backup_enabled,
                    dolt_disable_event_flush=beads.dolt_disable_event_flush,
                ),
            )
        if destination == c.Infra.BEADS_METADATA_RELPATH:
            if target.beads is None:
                return r[p.Model].fail(
                    "Beads rendering requires enabled Beads identity",
                )
            # Why: this marker is regenerated on every `make gen`, but the
            # ledger identity inside it is owned by the checkout, not by the
            # fleet SSOT. Rendering without it stripped the key, and Beads then
            # minted a NEW identity on next access — a consumer rig lost its
            # identity that way. Read it back so a
            # regeneration is identity-preserving.
            return r[p.Model].ok(
                m.Infra.BeadsMetadataRenderSpec(
                    database=target.beads.database,
                    dolt_mode=codegen.toolchain.beads.dolt_mode,
                    project_id=cls._beads_project_id(render_inputs.target.root),
                ),
            )
        return None

    def _github_context(
        self,
        render_inputs: m.Infra.CodegenRenderInputs,
        destination: str,
    ) -> p.Result[p.Model] | None:
        """Resolve the GitHub workflow render spec for ``.github/`` targets.

        Returns:
            The resulting ``p.Result[p.Model] | None`` where None marks a
            destination outside this group.

        """
        if not destination.startswith(".github/"):
            return None
        target = render_inputs.target
        workspace = render_inputs.workspace
        codegen = render_inputs.codegen
        repository_root = target.root
        dist = target.repository.distribution
        workspace_repositories = (
            tuple(workspace.subprojects)
            if target.make_profile is c.Infra.MakeProfile.WORKSPACE
            else ()
        )
        # Why: ci.yml.j2 iterates this to build its push/pull_request branch
        # filters, so an unsupplied value fails the render outright. The
        # repository's own integration branch is the only branch this layer
        # can name from resolved data; a fleet-wide list hardcoded here would
        # make every repository trigger on branches it does not have.
        resolved_branch = self.render_integration_branch(render_inputs)
        if resolved_branch.failure:
            return r[p.Model].from_failure(resolved_branch)
        branch = resolved_branch.value
        # Forks and local projects never enter the cooldown: they are the
        # requirements this project takes by direct git reference.
        excluded = self.direct_sources(render_inputs)
        if excluded.failure:
            return r[p.Model].from_failure(excluded)
        return r[p.Model].ok(
            m.Infra.GithubWorkflowRenderSpec(
                publishes_release=target.repository.publishes_release,
                extra_verbs=self._elected_extra_verbs(
                    target.repository,
                    repository_root,
                    codegen,
                ),
                publish_index=config.Infra.release.publish_index,
                dist=dist,
                gate_original_receipt_filename=c.Infra.GATE_ORIGINAL_RECEIPT_FILENAME,
                setup_operations_report_directory=(
                    c.Infra.WORKSPACE_OPERATION_REPORT_DIRECTORY
                ),
                make_profile=target.make_profile,
                gascity_enabled=target.gascity_enabled,
                repository_branch=branch,
                ci_trigger_branches=tuple(
                    dict.fromkeys((
                        *codegen.branch_policy.ci_trigger_branches,
                        branch,
                    )),
                ),
                python_version=codegen.toolchain.python_version,
                github_actions=codegen.github_actions,
                toolchain=codegen.toolchain,
                make=codegen.make,
                workspace_repositories=workspace_repositories,
                # Why: dependabot.yml.j2 branches on this and the model
                # declares it, but the .github/ spec never supplied it, so
                # every render died with "'has_devcontainer' is undefined".
                # Dependabot rejects its ENTIRE config when an ecosystem
                # names a directory that is absent, so this is read from the
                # checkout rather than declared: a stale flag would silently
                # disable Dependabot for the repository.
                has_devcontainer=(repository_root / ".devcontainer").is_dir(),
                dependency_cooldown_days=codegen.toolchain.dependency_cooldown_days,
                cooldown_excluded_dependencies=excluded.value,
                checkout_submodules=codegen.checkout_submodules_overrides.get(
                    dist,
                    codegen.checkout_submodules,
                ),
                custom_steps=self._custom_ci_steps(repository_root),
                private_submodules=codegen.ci_private_submodules.get(dist),
                private_dependency_auth=codegen.ci_private_dependency_auth.get(
                    dist,
                ),
                system_packages=tuple(codegen.ci_system_packages.get(dist, ())),
                packages_read=dist in codegen.ci_package_registry_read,
            ),
        )

    def _makefile_group_context(
        self,
        render_inputs: m.Infra.CodegenRenderInputs,
        destination: str,
    ) -> p.Result[p.Model] | None:
        """Resolve the Makefile and custom-Make render specs.

        Returns:
            The resulting ``p.Result[p.Model] | None`` where None marks a
            destination outside this group.

        """
        if destination == c.Infra.MAKEFILE_FILENAME:
            makefile = self._makefile_render_spec(
                render_inputs.target,
                render_inputs.workspace,
                render_inputs.codegen,
            )
            if makefile.failure:
                return r[p.Model].from_failure(makefile)
            return r[p.Model].ok(makefile.value)
        if destination == c.Infra.CUSTOM_MAKE_FILENAME:
            # Existing repositories project custom routes from the same typed
            # Make contract as Makefile; they do not require scaffold-only
            # project metadata.
            make_context = self.make_render_context(render_inputs)
            if make_context.failure:
                return r[p.Model].from_failure(make_context)
            return r[p.Model].ok(make_context.value)
        return None

    def _project_or_pass_context(
        self,
        render_inputs: m.Infra.CodegenRenderInputs,
        project_context: m.Infra.ProjectRenderContext | None,
        *,
        destination: str,
    ) -> p.Result[p.Model]:
        """Pass a supplied project context through, or derive one on demand.

        Returns:
            The resulting ``p.Result[p.Model]``.

        """
        if project_context is not None:
            return r[p.Model].ok(project_context)
        context_result = self._project_render_context(
            render_inputs,
            scaffold_sources=destination != c.PYPROJECT_FILENAME,
        )
        if context_result.failure:
            return r[p.Model].from_failure(context_result)
        return r[p.Model].ok(context_result.value)

    def _makefile_render_spec(
        self,
        target: m.Infra.RepositoryConformTarget,
        workspace: m.Infra.WorkspaceSpec,
        codegen: m.Infra.CodegenConfigSpec,
    ) -> p.Result[m.Infra.MakefileRenderSpec]:
        """Resolve Makefile inputs directly from the declared repository topology.

        Returns:
            The resulting ``p.Result[m.Infra.MakefileRenderSpec]``.

        """
        pytest = config.Infra.tooling.tools.pytest
        order = (
            u.Infra.workspace_dependency_order(target.root, workspace.subprojects)
            if target.make_profile is c.Infra.MakeProfile.WORKSPACE
            else ()
        )
        return r[m.Infra.MakefileRenderSpec].ok(
            m.Infra.MakefileRenderSpec(
                bootstrap_report_shell_literal=(
                    u.Infra.bootstrap_operation_report_shell_literal()
                ),
                bootstrap_report_relative_path=(
                    c.Infra.WORKSPACE_BOOTSTRAP_REPORT_RELATIVE_PATH
                ),
                pytest=pytest,
                release_verbs=self._release_product_verbs(target.repository),
                dist=target.repository.distribution,
                infra_cli=config.Infra.name,
                examples_module=target.repository.examples_module,
                make_profile=target.make_profile,
                package=target.repository.package,
                analyzer_roots=tuple(
                    config.Infra.tooling.tools.pyright.path_rules.env_dirs,
                ),
                workspace_repositories=(
                    tuple(
                        sorted(
                            workspace.subprojects,
                            key=lambda repository: order.index(
                                repository.distribution,
                            ),
                        ),
                    )
                    if target.make_profile is c.Infra.MakeProfile.WORKSPACE
                    else ()
                ),
                environment_imports=self._declared_environment_imports(
                    target, workspace
                ),
                makefile_custom_include=c.Infra.MAKEFILE_CUSTOM_INCLUDE,
                repository_root_rel=self._repository_root_rel(workspace),
                workspace_subprojects=tuple(
                    item.path.as_posix() for item in workspace.subprojects
                ),
                uv_link_mode=self.link_mode(target.repository, codegen.toolchain),
                mise_selector=codegen.toolchain.mise_selector,
                mise_version=codegen.toolchain.mise_version,
                mise_install_tools=codegen.toolchain.mise_install_keys,
                toolchain=codegen.toolchain,
                python_version=codegen.toolchain.python_version,
                make=codegen.make,
                extra_verbs=self._elected_extra_verbs(
                    target.repository,
                    target.root,
                    codegen,
                ),
                script_dispatch=target.repository.script_dispatch,
                workspace_cli_group=c.Infra.CLI_GROUP_WORKSPACE,
                mypy_timeout_exit_code=c.Infra.PROCESS_TIMEOUT_EXIT_CODE,
                timeout_command=c.Infra.TIMEOUT_COMMAND,
                timeout_kill_after_seconds=c.Infra.TIMEOUT_KILL_AFTER_SECONDS,
            ),
        )

    @staticmethod
    def _custom_ci_steps(repository_root: Path) -> str:
        """Read the project-owned workflow steps, if the project declares any.

        This is the CI counterpart of ``custom.mk``: the generator injects the
        block verbatim and never interprets it, so a project extends its own
        pipeline without the generator learning that project's concerns.

        Returns:
            The resulting ``str``.

        """
        source: Path = repository_root / c.Infra.CUSTOM_CI_STEPS_FILENAME
        if not source.is_file():
            return ""
        return source.read_text(encoding=c.DEFAULT_ENCODING).rstrip("\n")


__all__: list[str] = ["FlextInfraCodegenConformArtifactRender"]
