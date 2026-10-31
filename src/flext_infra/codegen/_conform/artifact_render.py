"""Governed artifact rendering and project overlay composition.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Generator, Mapping, Sequence
from contextlib import contextmanager
from pathlib import Path

from flext_infra import c, config, deps as dependency_services, m, p, r, t, u
from flext_infra.codegen._conform.context_render import (
    FlextInfraCodegenConformContextRender,
)
from flext_infra.deps.phases import FlextInfraToolTablesPhase


class FlextInfraCodegenConformArtifactRender(FlextInfraCodegenConformContextRender):
    """Governed artifact rendering and project overlay composition."""

    _project_contexts: dict[bool, m.Infra.ProjectRenderContext] | None = m.PrivateAttr(
        default=None
    )

    @contextmanager
    def project_render_scope(self) -> Generator[None]:
        """Derive each project render context once per repository templates pass.

        Every artifact of one pass renders from the same repository inputs, so
        its project context is the same derivation; the pass keeps it.

        Yields:
            Nothing; the scope is active until the pass completes.

        """
        try:
            self._project_contexts = {}
            yield
        finally:
            self._project_contexts = None

    @staticmethod
    def render_artifact_source(
        codegen: m.Infra.CodegenConfigSpec,
        entry: m.Infra.TemplateEntrySpec,
        context: p.Model,
    ) -> p.Result[str]:
        """Read an explicit package resource or render a Jinja template.

        Args:
            codegen: The code generation configuration.
            entry: The template entry specification.
            context: The rendering context for the template.

        Returns:
            A result containing the rendered artifact or an error.

        """
        return FlextInfraCodegenConformArtifactRender._render_artifact_authenticated(
            codegen, entry, context
        ).map(lambda rendered: rendered.rendered)

    @staticmethod
    def _render_artifact_authenticated(
        codegen: m.Infra.CodegenConfigSpec,
        entry: m.Infra.TemplateEntrySpec,
        context: p.Model,
    ) -> p.Result[m.Cli.AuthenticatedTemplateRender]:
        """Retain the original resource or Jinja observations with its text.

        Returns:
            The native authenticated payload, or the first read/render failure.

        """
        result_type = r[m.Cli.AuthenticatedTemplateRender]
        source = u.Infra.codegen_artifact_source(codegen, entry)
        if entry.source_kind == "resource":
            if entry.source_package is None:
                return result_type.fail(
                    f"resource has no explicit package owner: {entry.destination}",
                )
            captured = u.Cli.atomic_read_binary_file_state(source, required=True)
            if captured.failure:
                return result_type.from_failure(captured)
            content = captured.value.content
            if content is None:
                return result_type.fail(
                    f"authenticated resource has no bytes: {source}"
                )
            return result_type.create_from_callable(
                lambda: m.Cli.AuthenticatedTemplateRender(
                    rendered=content.decode(c.DEFAULT_ENCODING),
                    source_states=(captured.value,),
                )
            )
        return u.Cli.template_render_authenticated(source, context)

    @staticmethod
    def _artifact_dependency_plans(
        codegen: m.Infra.CodegenConfigSpec,
        root: Path,
        planned: Sequence[m.Infra.CodegenFilePlan],
    ) -> p.Result[Sequence[m.Infra.CodegenFilePlan]]:
        """Require every selected artifact's outputs in the same plan set.

        Args:
            codegen: The code generation configuration.
            root: The root path for the generated artifacts.
            planned: A sequence of planned file artifacts.

        Returns:
            The planned files, or the first artifact with unplanned dependencies.

        """
        result_type = r[Sequence[m.Infra.CodegenFilePlan]]
        paths = {plan.path for plan in planned}
        for entry in codegen.templates.entries:
            if root / entry.destination not in paths or not entry.requires_artifacts:
                continue
            missing = {
                root / destination
                for destination in u.Cli.dag_closure(
                    codegen.templates.artifact_requirements,
                    frozenset({entry.destination}),
                ).unwrap()
            }.difference(paths)
            if missing:
                return result_type.fail(
                    f"artifact {entry.destination} has unplanned dependencies: "
                    f"{', '.join(str(item) for item in sorted(missing))}",
                )
        return result_type.ok(tuple(planned))

    @staticmethod
    def planned_source_tooling(
        render_inputs: m.Infra.CodegenRenderInputs,
        planned: Sequence[m.Infra.CodegenFilePlan],
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
        # The one runtime-base derivation of generation, over the final sources.
        runtime_bases = u.Infra.runtime_evaluated_base_classes(
            root,
            sources,
            policy.runtime_evaluated_roots,
            source_project=source_project,
        )
        first_party: list[t.JsonValue] = list(
            FlextInfraToolTablesPhase.first_party_namespaces(
                path=root,
                planned_sources=tuple(sources),
                source_project=source_project,
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
        return (
            dependency_services.FlextInfraPyprojectModernizer.tooling_context_from_payload
        )(
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
    ) -> p.Result[tuple[str, ...]]:
        """Read direct references from composed, finalized, or committed metadata.

        Returns:
            The selected metadata's direct-reference names without advancing state.

        """
        if composed is not None:
            document = u.Cli.toml_parse_text(composed)
            if document is None:
                return r[tuple[str, ...]].fail(
                    "planned pyproject is not valid TOML",
                )
            return u.Infra.direct_source_names(document)
        if render_inputs.planned_direct_sources is not None:
            return r[tuple[str, ...]].ok(render_inputs.planned_direct_sources)
        document = u.Cli.toml_read_document(
            render_inputs.target.root / c.PYPROJECT_FILENAME,
        )
        if document.failure:
            return r[tuple[str, ...]].from_failure(document)
        return u.Infra.direct_source_names(document.value)

    @classmethod
    def compose_project_artifact(
        cls,
        repository_root: Path,
        destination: str,
        rendered: str,
        *,
        render_inputs: m.Infra.CodegenRenderInputs | None = None,
    ) -> p.Result[str]:
        """Apply typed project overlays after canonical template rendering.

        Python repairs require the complete planned policy and source context;
        the shared publisher normalizes those bytes, never here.

        Without ``render_inputs`` the committed project catalog overlays the
        render and no pyproject conformance runs.

        Returns:
            The composed artifact text.

        """
        if destination == c.Infra.GITIGNORE:
            overlay = cls._composed_ignore_overlay(
                repository_root,
                rendered,
                render_inputs,
            )
            if overlay.failure:
                return r[str].from_failure(overlay)
            rendered = overlay.value
        composer = {
            c.PYPROJECT_FILENAME: cls._composed_pyproject_overlay,
            c.Infra.MISE_TOML_FILENAME: cls._composed_mise_overlay,
            f"config/{c.Infra.INFRA_CONFIG_FILENAME}": cls._composed_release_overlay,
        }.get(destination)
        if composer is None:
            return r[str].ok(rendered)
        return composer(repository_root, rendered, render_inputs)

    @classmethod
    def _composed_ignore_overlay(
        cls,
        repository_root: Path,
        rendered: str,
        render_inputs: m.Infra.CodegenRenderInputs | None,
    ) -> p.Result[str]:
        """Preserve the live ignore's owned blocks in the render.

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
        suffix = u.Infra.ignore_runtime_suffix(config.Infra.codegen)
        if suffix.failure:
            return r[str].from_failure(suffix)
        return u.Infra.preserve_project_ignore_blocks(
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
    ) -> p.Result[str]:
        """Read the live declaration and preserve its project-owned values.

        Returns:
            The preserved overlay or the original read or composition failure.

        """
        state = u.Cli.atomic_read_binary_file_state(live_path)
        if state.failure:
            return r[str].from_failure(state)
        if state.value.content is None:
            return u.Infra.overlay_preserved(rendered, None)
        return (
            u.Infra
            .recover_live_pyproject_text(
                state.value.content.decode(c.DEFAULT_ENCODING),
            )
            .flat_map(u.Infra.pyproject_regeneration_source)
            .flat_map(lambda live_text: u.Infra.overlay_preserved(rendered, live_text))
        )

    @classmethod
    def _composed_pyproject_overlay(
        cls,
        repository_root: Path,
        rendered: str,
        render_inputs: m.Infra.CodegenRenderInputs | None,
    ) -> p.Result[str]:
        """Overlay, conform, and format the pyproject render.

        Returns:
            The composed pyproject text.

        """
        live_path = repository_root / c.PYPROJECT_FILENAME
        overlaid = cls._live_pyproject_overlay(live_path, rendered)
        if overlaid.failure:
            return overlaid
        composed_rendered = overlaid.value
        if render_inputs is not None:
            conformed = cls.conformed_pyproject_source(
                composed_rendered,
                render_inputs,
            )
            if conformed.failure:
                return conformed
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
            lambda source: (
                f"{c.Infra.BANNER}{cls.rendered_by_stamp()}\n{source.lstrip()}"
            ),
        )

    @classmethod
    def _composed_mise_overlay(
        cls,
        repository_root: Path,
        rendered: str,
        render_inputs: m.Infra.CodegenRenderInputs | None,
    ) -> p.Result[str]:
        """Compose the mise declaration from the resolved artifact catalog.

        Returns:
            The composed mise declaration.

        """
        if render_inputs is None:
            snapshot = u.Infra.snapshot_committed_project_managed_artifacts(
                repository_root,
                read_committed_directory=u.Infra.git_committed_directory_blobs,
            )
            if snapshot.failure:
                return r[str].from_failure(snapshot)
            resolved_artifacts = snapshot.value
        else:
            resolved_artifacts = render_inputs.managed_artifacts
        return (
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

    @classmethod
    def _composed_release_overlay(
        cls,
        repository_root: Path,
        rendered: str,
        _render_inputs: m.Infra.CodegenRenderInputs | None,
    ) -> p.Result[str]:
        """Replace only the declared closure keys, retaining authored YAML.

        Returns:
            The comment-preserving document text.

        """
        current = u.Cli.atomic_read_binary_file_state(
            repository_root / "config" / c.Infra.INFRA_CONFIG_FILENAME,
            required=False,
        )
        if current.failure:
            return r[str].from_failure(current)
        parsed = u.Cli.yaml_roundtrip_load_map_text(
            current.value.content.decode(c.DEFAULT_ENCODING)
            if current.value.content is not None
            else "{}",
        )
        if parsed.failure:
            return r[str].from_failure(parsed)
        declaration = cls._release_declaration(parsed.value)
        if declaration.failure:
            return r[str].from_failure(declaration)
        overlay = u.Cli.yaml_parse(rendered)
        if overlay.failure:
            return r[str].from_failure(overlay)
        u.Cli.yaml_overlay_preserving_order(parsed.value, overlay.value)
        return u.Cli.yaml_roundtrip_dump_text(parsed.value)

    @staticmethod
    def _release_declaration(
        document: Mapping[str, t.Cli.YamlValue],
    ) -> p.Result[Mapping[str, t.Cli.YamlValue]]:
        """Validate only owned namespace shapes without copying authored values.

        Returns:
            The declared release mapping by reference, or its original shape error.

        """
        result_type = r[Mapping[str, t.Cli.YamlValue]]
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
    ) -> p.Result[m.Infra.ReleasePolicySpec]:
        """Select committed closure declarations, never local/private policy.

        Returns:
            The existing typed release policy.

        """
        result_type = r[m.Infra.ReleasePolicySpec]
        owner = u.Infra.git_repository_root(m.Infra.GitRepoRequest(repo_root=root))
        if owner.failure:
            return result_type.from_failure(owner)
        workspace = owner.value.repository_root.resolve()
        if workspace != root.resolve():
            members = u.Infra.git_submodule_declarations(workspace)
            if members.failure:
                return result_type.from_failure(members)
            if not any(
                (workspace / member.path).resolve() == root.resolve()
                for member in members.value
            ):
                return result_type.fail(f"undeclared release policy member: {root}")
        declaration = u.Cli.atomic_read_binary_file_state(
            workspace / "config" / c.Infra.INFRA_CONFIG_FILENAME,
            required=False,
        )
        if declaration.failure:
            return result_type.from_failure(declaration)
        document = u.Cli.yaml_parse(
            declaration.value.content.decode(c.DEFAULT_ENCODING)
            if declaration.value.content is not None
            else "{}",
        )
        return document.flat_map(cls._release_declaration).flat_map(
            lambda section: result_type.create_from_callable(
                lambda: m.Infra.ReleasePolicySpec.model_validate({
                    "build_constraints": config.Infra.release.build_constraints,
                    "maintenance_line": section.get("maintenance_line"),
                    "finalize_maintenance": section.get("finalize_maintenance", False),
                }),
            ),
        )

    def _candidate_manifests(
        self,
        planned: Sequence[m.Infra.CodegenFilePlan],
    ) -> tuple[m.Infra.CodegenFilePlan, ...]:
        """Compose provider and current-phase manifests with original witnesses.

        Returns:
            The deduplicated pyproject manifests in render order.

        """
        return u.Infra.codegen_compose_file_plans(
            tuple(
                plan
                for plan in (*(self.state.provider_plans or ()), *planned)
                if plan.path.name == c.PYPROJECT_FILENAME
            ),
            ordered=True,
        )

    def _rendered_artifact_source(
        self,
        render_inputs: m.Infra.CodegenRenderInputs,
        route: m.Infra.ArtifactRenderRoute,
    ) -> p.Result[m.Cli.AuthenticatedTemplateRender]:
        """Resolve one artifact render route and render its template source.

        ``route.failure_prefix`` carries the only difference between the
        scaffold and existing-repository planners: the stage banner the
        scaffold planner prepends to a render failure.

        Returns:
            The rendered content with its original consumed source observations.

        Raises:
            ValueError: If the catalog entry has no renderable source.

        """
        entry = route.entry
        destination = route.destination
        if entry.source is None:
            msg = f"render entry has no source: {destination}"
            raise ValueError(msg)
        if entry.source_kind == "resource":
            return self._render_artifact_authenticated(
                render_inputs.codegen,
                entry,
                m.Infra.StaticTextRenderSpec(),
            )
        if entry.bootstrap_distribution is not None:
            return self._bootstrap_rendered_source(
                render_inputs,
                entry,
                planned_manifests=route.planned_manifests,
            )
        artifact_context: p.Result[p.Model] = (
            self._release_policy_render_inputs(render_inputs.target.root)
            if destination == f"config/{c.Infra.INFRA_CONFIG_FILENAME}"
            else self._artifact_render_context(
                render_inputs,
                destination=destination,
                project_context=route.project_context,
            )
        )
        if artifact_context.failure:
            return r[m.Cli.AuthenticatedTemplateRender].from_failure(artifact_context)
        rendered = self._render_artifact_authenticated(
            render_inputs.codegen,
            entry,
            artifact_context.value,
        )
        if rendered.failure or rendered.value.rendered.strip():
            return rendered
        source = (
            u.Infra
            .codegen_artifact_source(render_inputs.codegen, entry)
            .expanduser()
            .absolute()
        )
        template = next(
            (state for state in rendered.value.source_states if state.path == source),
            None,
        )
        if template is None or template.content is None:
            return r[m.Cli.AuthenticatedTemplateRender].fail(
                f"rendered template has no original source observation: {source}"
            )
        return self._require_rendered_content(
            rendered.value.rendered,
            template_relpath=entry.source,
            destination=destination,
            failure_prefix=route.failure_prefix,
            template_source=template.content.decode(c.DEFAULT_ENCODING),
        ).map(lambda _content: rendered.value)

    def _bootstrap_rendered_source(
        self,
        render_inputs: m.Infra.CodegenRenderInputs,
        entry: m.Infra.TemplateEntrySpec,
        *,
        planned_manifests: Sequence[m.Infra.CodegenFilePlan],
    ) -> p.Result[m.Cli.AuthenticatedTemplateRender]:
        """Render an executor-bootstrap artifact from its declared closure.

        Returns:
            The rendered content with its original template observations.

        """
        distribution = entry.bootstrap_distribution
        if distribution is None:
            return r[m.Cli.AuthenticatedTemplateRender].fail(
                "bootstrap artifact has no declared executor"
            )
        bootstrap = u.Infra.workspace_bootstrap_requirements(
            render_inputs.target.root,
            render_inputs.workspace,
            distribution,
            planned_manifests=planned_manifests,
        )
        if bootstrap.failure:
            return r[m.Cli.AuthenticatedTemplateRender].from_failure(bootstrap)
        return self._render_artifact_authenticated(
            render_inputs.codegen, entry, bootstrap.value
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
        """Resolve the repository-shaped config specs (ignore/sonar/qlty/envrc).

        Returns:
            The resulting ``p.Result[p.Model] | None`` where None marks a
            destination outside this group.

        """
        target = render_inputs.target
        workspace = render_inputs.workspace
        codegen = render_inputs.codegen
        repository = target.repository
        if destination == c.Infra.GITIGNORE:
            project_patterns: Sequence[str] = (
                render_inputs.managed_artifacts.resolution.artifacts.Gitignore.patterns
            )
            return r[p.Model].ok(
                m.Infra.GitignoreRenderSpec(
                    ignore_sections=u.Infra.ignore_sections(
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
                ),
            )
        if destination == (
            f"{c.Infra.QLTY_CONFIG_DIRNAME}/{c.Infra.QLTY_CONFIG_FILENAME}"
        ):
            return r[p.Model].ok(
                m.Infra.QltyRenderSpec(),
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
            c.Infra.MARKDOWNLINT_IGNORE_FILENAME,
            c.Infra.MARKDOWN_CONFIG_FILENAME,
        }:
            tooling = render_inputs.tooling_runtime
            if tooling is None or tooling.document is None:
                return r[p.Model].fail(
                    "Markdown rendering requires elected tooling inputs"
                )
            markdown = tooling.document.tools.markdown
            spec = m.Infra.MarkdownLintRenderSpec(
                native_config=u.Infra.markdown_native_configuration(
                    markdown, codegen.markdown_exclude_globs
                ),
                exclude=codegen.markdown_exclude_globs,
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
        elif destination == c.Infra.GIT_HOOK_VALIDATOR_RELPATH:
            spec = m.Infra.GitHookRenderSpec(
                preservation_ref_namespaces=(
                    codegen.branch_policy.preservation_ref_namespaces
                ),
            )
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
        superproject = self._ci_superproject(repository_root, branch)
        if superproject is not None and superproject.failure:
            return r[p.Model].from_failure(superproject)
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
                custom_steps=self._custom_ci_steps(
                    repository_root / c.Infra.CUSTOM_CI_STEPS_FILENAME,
                ),
                custom_post_steps=self._custom_ci_steps(
                    repository_root / c.Infra.CUSTOM_CI_POST_STEPS_FILENAME,
                ),
                private_submodules=codegen.ci_private_submodules.get(dist),
                private_dependency_auth=codegen.ci_private_dependency_auth.get(
                    dist,
                ),
                system_packages=tuple(codegen.ci_system_packages.get(dist, ())),
                packages_read=dist in codegen.ci_package_registry_read,
                superproject=None if superproject is None else superproject.value,
            ),
        )

    @staticmethod
    def _ci_superproject(
        repository_root: Path,
        branch: str,
    ) -> p.Result[m.Infra.CiSuperprojectCheckoutSpec] | None:
        """Elect the containing workspace an attached member's CI checks out.

        The native runtime owner decides membership: a repository elected by
        a containing workspace tracks no lock of its own, so its CI installs
        the workspace root lock. The member renders on its workspace's
        integration line, so ``branch`` is the workspace ref as well.

        Returns:
            The checkout contract or the first failure for an attached member;
            ``None`` for a workspace root or standalone repository, which
            elects itself.

        """
        result_type = r[m.Infra.CiSuperprojectCheckoutSpec]
        root = repository_root.resolve()
        runtime = u.Infra.runtime_owner_root(root)
        if runtime.failure:
            return result_type.from_failure(runtime)
        workspace_root = runtime.value.resolve()
        if workspace_root == root:
            return None
        origin = u.Infra.git_remote_url(
            m.Infra.GitRemoteUrlRequest(repo_root=workspace_root),
        )
        if origin.failure:
            return result_type.from_failure(origin)
        return result_type.create_from_callable(
            lambda: m.Infra.CiSuperprojectCheckoutSpec(
                repository=u.Infra.git_remote_identity(origin.value.text),
                ref=branch,
                path=root.relative_to(workspace_root).as_posix(),
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
        scaffold_sources = destination != c.PYPROJECT_FILENAME
        contexts = self._project_contexts
        derived = None if contexts is None else contexts.get(scaffold_sources)
        if derived is not None:
            return r[p.Model].ok(derived)
        context_result = self._project_render_context(
            render_inputs,
            scaffold_sources=scaffold_sources,
        )
        if context_result.failure:
            return r[p.Model].from_failure(context_result)
        if contexts is not None:
            contexts[scaffold_sources] = context_result.value
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
                bootstrap_requirements=Path(
                    codegen.templates.bootstrap_entry.destination
                ),
                bootstrap_report_shell_literal=(
                    u.Infra.bootstrap_operation_report_shell_literal()
                ),
                bootstrap_report_relative_path=(
                    c.Infra.WORKSPACE_BOOTSTRAP_REPORT_RELATIVE_PATH
                ),
                flext_editable_selection_relative_path=(
                    c.Infra.FLEXT_EDITABLE_SELECTION_RELATIVE_PATH
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
    def _custom_ci_steps(source: Path) -> str:
        """Read one project-owned workflow step file, if the project declares it.

        This is the CI counterpart of ``custom.mk``: the generator injects the
        block verbatim and never interprets it, so a project extends its own
        pipeline without the generator learning that project's concerns.

        Returns:
            The resulting ``str``.

        """
        if not source.is_file():
            return ""
        return source.read_text(encoding=c.DEFAULT_ENCODING).rstrip("\n")


__all__: list[str] = ["FlextInfraCodegenConformArtifactRender"]
