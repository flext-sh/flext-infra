"""Typed Make and project render context projection.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Mapping
from functools import partial
from pathlib import Path

from flext_infra import (
    c,
    check as validation_services,
    config,
    deps as dependency_services,
    m,
    p,
    r,
    t,
    u,
)
from flext_infra._utilities._pyproject.conform import (
    FlextInfraUtilitiesPyprojectConform,
)
from flext_infra.codegen._conform.pyproject_policy import (
    FlextInfraCodegenConformPyprojectPolicy,
)


class FlextInfraCodegenConformContextRender(FlextInfraCodegenConformPyprojectPolicy):
    """Typed Make and project render context projection."""

    @staticmethod
    def resolve_render_inputs(
        *,
        target: m.Infra.RepositoryConformTarget,
        workspace: m.Infra.WorkspaceSpec,
        codegen: m.Infra.CodegenConfigSpec,
        tooling_runtime: m.Infra.ToolingRuntimeContext | None,
        managed_artifacts: m.Infra.ProjectManagedArtifactsSnapshot,
    ) -> m.Infra.CodegenRenderInputs:
        """Resolve every input shared by one repository's renders exactly once.

        The integration branch probes the manifest and, undeclared, the
        published Git line; the project context and every workflow template
        read this one resolution instead of repeating the probe per render.
        An unresolved branch stays absent here: only a render that consumes it
        fails, through ``render_integration_branch``, exactly as before.

        Returns:
            The resulting ``m.Infra.CodegenRenderInputs``.

        """
        branch = FlextInfraCodegenConformContextRender._resolve_integration_branch(
            target=target,
            workspace=workspace,
            codegen=codegen,
        )
        return m.Infra.CodegenRenderInputs(
            target=target,
            workspace=workspace,
            codegen=codegen,
            tooling_runtime=tooling_runtime,
            managed_artifacts=managed_artifacts,
            integration_branch=branch.value if branch.success else None,
        )

    @staticmethod
    def render_integration_branch(
        render_inputs: m.Infra.CodegenRenderInputs,
    ) -> p.Result[str]:
        """Return the plan's integration branch, or the resolver's own failure.

        Returns:
            The plan's integration branch, or the resolver's own failure.

        """
        if render_inputs.integration_branch is not None:
            return r[str].ok(render_inputs.integration_branch)
        return FlextInfraCodegenConformContextRender._resolve_integration_branch(
            target=render_inputs.target,
            workspace=render_inputs.workspace,
            codegen=render_inputs.codegen,
        )

    @staticmethod
    def _resolve_integration_branch(
        *,
        target: m.Infra.RepositoryConformTarget,
        workspace: m.Infra.WorkspaceSpec,
        codegen: m.Infra.CodegenConfigSpec,
    ) -> p.Result[str]:
        """Resolve the repository's integration branch from its declarations.

        The repository's declaration wins; otherwise the published baseline.
        A checkout's HEAD is never consulted (ADR-018 p.10).

        Returns:
            The resulting ``p.Result[str]``.

        """
        return u.Infra.resolve_integration_branch(
            target.root,
            policy_branch=codegen.branch_policy.integration_branch,
            declared=(
                workspace.integration.branch
                if workspace.integration is not None
                else None
            ),
        )

    @classmethod
    def conformed_pyproject_source(
        cls,
        source: str,
        render_inputs: m.Infra.CodegenRenderInputs,
    ) -> p.Result[str]:
        """Conform one pyproject source under the plan's render inputs.

        An attached member renders on its workspace's integration line (a
        governed .gitmodules branch must equal it): the line the render inputs
        resolved once for this plan, never a second probe.

        Returns:
            The conformed pyproject source, or the first resolution failure.

        """
        target, workspace, codegen = (
            render_inputs.target,
            render_inputs.workspace,
            render_inputs.codegen,
        )
        flext_line = u.Infra.flext_integration_line_for_checkout(
            codegen=codegen, repository_root=target.root, workspace=workspace
        )
        if flext_line.failure:
            return r[str].from_failure(flext_line)
        if workspace.integration is None:
            branch = cls.render_integration_branch(render_inputs)
            if branch.failure:
                return r[str].from_failure(branch)
            workspace = workspace.model_copy(
                update={
                    "integration": m.Infra.WorkspaceIntegrationSpec(
                        provider=workspace.repository.provider,
                        branch=branch.value,
                    ),
                },
            )
        toolchain = codegen.toolchain
        return FlextInfraUtilitiesPyprojectConform.pyproject_conform(
            source,
            workspace=workspace,
            required_dev_dependencies=u.Infra.project_development_requirements(
                codegen.scaffold.project,
                distribution=target.repository.distribution,
                kind=target.repository.kind,
            ),
            uv_resolution=m.Infra.UvResolutionSpec(
                link_mode=cls.link_mode(target.repository, toolchain),
                constraint_dependencies=tuple(toolchain.uv_constraint_dependencies),
                override_dependencies=tuple(toolchain.uv_override_dependencies),
                environments=tuple(toolchain.uv_environments),
            ),
            options=u.Infra.PyprojectConformOptions(
                flext_line=flext_line.value,
            ),
        )

    @staticmethod
    def _release_product_verbs(
        repository: m.Infra.RepositoryRef,
    ) -> t.VariadicTuple[m.Infra.MakeVerbSpec]:
        """Derive the opted-in product surface from the native release phases.

        Returns:
            One generated verb per native release phase.

        """
        return (
            tuple(
                m.Infra.MakeVerbSpec(
                    name=f"release-{phase.value}",
                    description=f"Execute the declared release {phase.value} phase.",
                    arguments=(
                        ("PR_TITLE",)
                        if phase is c.Infra.ReleasePhase.PLAN
                        else ("LANE_CHECKPOINT_REF",)
                        if phase is c.Infra.ReleasePhase.VERSION
                        else ("INDEX",)
                        if phase is c.Infra.ReleasePhase.PUBLISH
                        else ()
                    ),
                )
                for phase in c.Infra.ReleasePhase
            )
            if repository.publishes_release
            else ()
        )

    def _elected_extra_verbs(
        self,
        repository: m.Infra.RepositoryRef,
        root: Path,
        codegen: m.Infra.CodegenConfigSpec,
    ) -> t.VariadicTuple[m.Infra.MakeVerbSpec]:
        """Compose authored commands and elected product capabilities once.

        Returns:
            The merged authored, discovered and release verbs.

        """
        release_verbs = self._release_product_verbs(repository)
        return (
            *self._merge_extra_verbs(
                repository.extra_verbs,
                ()
                if repository.script_dispatch is None
                else self._discover_script_verbs(root),
                frozenset(verb.name for verb in (*codegen.make.verbs, *release_verbs)),
            ),
            *release_verbs,
        )

    def make_render_context(
        self,
        render_inputs: m.Infra.CodegenRenderInputs,
    ) -> p.Result[m.Infra.MakeRenderContext]:
        """Build the typed context consumed by the generated Makefile.

        Returns:
            The resulting ``p.Result[m.Infra.MakeRenderContext]``.

        """
        target = render_inputs.target
        workspace = render_inputs.workspace
        codegen = render_inputs.codegen
        repository = target.repository
        repository_root = target.root
        profile = target.make_profile
        tooling_runtime = render_inputs.tooling_runtime
        if tooling_runtime is None:
            return r[m.Infra.MakeRenderContext].fail(
                "Make rendering requires resolved tooling context",
            )
        tooling = tooling_runtime.document
        if tooling is None:
            return r[m.Infra.MakeRenderContext].fail(
                "Make rendering requires the elected tooling document",
            )
        subprojects = (
            tuple(workspace.subprojects)
            if profile is c.Infra.MakeProfile.WORKSPACE
            else ()
        )
        extra_verbs = self._elected_extra_verbs(
            repository,
            repository_root,
            codegen,
        )
        try:
            gates = validation_services.FlextInfraGateRegistry.default()
            delegated_rules = gates.delegated_lint_rules(
                tooling.tools.ruff.lint.rule_owners,
                check_gates=codegen.make.check_gates_default,
                repair_gates=(
                    *codegen.make.check_gates_fixable,
                    *codegen.make.fmt_gates,
                ),
            )
        except ValueError as exc:
            return r[m.Infra.MakeRenderContext].fail(str(exc), exception=exc)
        return r[m.Infra.MakeRenderContext].ok(
            m.Infra.MakeRenderContext(
                pytest=tooling.tools.pytest,
                release_verbs=self._release_product_verbs(repository),
                make=codegen.make,
                mypy_timeout_exit_code=c.Infra.PROCESS_TIMEOUT_EXIT_CODE,
                timeout_command=c.Infra.TIMEOUT_COMMAND,
                timeout_kill_after_seconds=c.Infra.TIMEOUT_KILL_AFTER_SECONDS,
                tooling_runtime=tooling_runtime,
                dist=repository.distribution,
                infra_cli=config.Infra.name,
                examples_module=repository.examples_module,
                python_version=codegen.toolchain.python_version,
                uv_link_mode=self.link_mode(repository, codegen.toolchain),
                ruff_delegated_rules=delegated_rules,
                make_profile=profile,
                workspace_cli_group=c.Infra.CLI_GROUP_WORKSPACE,
                repository_root_rel=self._repository_root_rel(workspace),
                makefile_custom_include=c.Infra.MAKEFILE_CUSTOM_INCLUDE,
                workspace_subprojects=tuple(
                    item.path.as_posix() for item in workspace.subprojects
                ),
                owns_workspace_manifest=(
                    repository_root / "config/workspace.yaml"
                ).is_file(),
                workspace_repositories=subprojects,
                environment_imports=self._declared_environment_imports(
                    target, workspace
                ),
                extra_verbs=extra_verbs,
                script_dispatch=repository.script_dispatch,
            ),
        )

    @staticmethod
    def _project_spec_from_existing(
        repository: m.Infra.RepositoryRef,
        repository_root: Path,
        codegen: m.Infra.CodegenConfigSpec,
    ) -> p.Result[m.Infra.ProjectSpec]:
        """Derive scaffold ProjectSpec from live PEP 621 metadata for existing trees.

        Returns:
            The resulting ``p.Result[m.Infra.ProjectSpec]``.

        """
        metadata = u.Infra.read_project_metadata_result(repository_root)
        if metadata.failure:
            return r[m.Infra.ProjectSpec].from_failure(metadata)
        pep621 = metadata.value.project
        package_name = metadata.value.package_name
        class_stem = metadata.value.class_stem
        alias = u.Infra.package_alias(package_name=package_name)
        identity = u.Infra.project_notice_identity(
            repository_root,
            None,
            codegen.scaffold.project,
        )
        if identity.failure:
            return r[m.Infra.ProjectSpec].from_failure(identity)
        author_name, license_id, year = identity.value
        author_email = pep621.authors[0].email if pep621.authors else None
        if not author_email:
            return r[m.Infra.ProjectSpec].fail(
                f"existing pyproject is missing author email: {repository_root}",
            )
        homepage = pep621.urls.homepage or repository.url.removesuffix(c.GIT_DIR_NAME)
        documentation = pep621.urls.documentation or homepage
        runtime_names = {
            name for item in pep621.dependencies if (name := u.Infra.dep_name(item))
        }
        candidates = tuple(
            base
            for base in codegen.scaffold.project.config_bases
            if base.distribution == repository.distribution
            or base.distribution in runtime_names
        )
        if not candidates:
            return r[m.Infra.ProjectSpec].fail(
                f"declared dependencies expose no config base at {repository_root}",
            )
        return r[m.Infra.ProjectSpec].ok(
            m.Infra.ProjectSpec(
                package_name=package_name,
                class_stem=class_stem,
                namespace=class_stem.removeprefix("Flext") or class_stem,
                constant_name=repository.distribution,
                namespace_attribute=alias,
                alias=alias,
                environment_prefix=f"{package_name.upper()}_",
                description=pep621.description or repository.distribution,
                license=license_id,
                author_name=author_name,
                author_email=author_email,
                upstream=candidates[0].module,
                homepage=homepage,
                documentation=documentation,
                repository_root_rel=".",
                year=year,
                cli_module=(
                    repository_root
                    / c.Infra.DEFAULT_SRC_DIR
                    / package_name
                    / c.Infra.CODEGEN_CLI_MODULE_FILENAME
                ).is_file(),
            ),
        )

    @staticmethod
    def _workspace_version(repository_root: Path) -> p.Result[str]:
        """Read the checkout's version SSOT or the typed initial version.

        The repository's own pyproject.toml is the version SSOT; the release
        protocol is its only writer, so conform reads it and never syncs it.
        A tree that has no pyproject yet is being created: it starts at the
        typed initial version and the protocol owns every change after that.

        Returns:
            The resulting ``p.Result[str]``.

        """
        if (repository_root / c.PYPROJECT_FILENAME).is_file():
            return u.Infra.current_workspace_version(repository_root)
        return r[str].ok(config.Infra.initial_project_version)

    def _resolved_render_project(
        self,
        render_inputs: m.Infra.CodegenRenderInputs,
    ) -> p.Result[m.Infra.ProjectSpec]:
        """Resolve the render project, inheriting workspace namespace scope.

        Existing checkouts declare no scaffold metadata: derive the render
        identity from the live project metadata instead of failing, so
        conforming a governed repository never depends on scaffold-only
        declarations. The manifest-level namespace declaration is the
        repository's production scope for the namespace validator, so a
        checkout that derives its project metadata declares it once at the
        workspace root instead of freezing a full scaffold spec. An explicit
        project-level declaration stays the more specific owner.

        Returns:
            The resulting ``p.Result[m.Infra.ProjectSpec]``.

        """
        target = render_inputs.target
        workspace = render_inputs.workspace
        codegen = render_inputs.codegen
        if workspace.project is not None:
            project = workspace.project
        else:
            derived = self._project_spec_from_existing(
                target.repository,
                target.root,
                codegen,
            )
            if derived.failure:
                return r[m.Infra.ProjectSpec].from_failure(derived)
            project = derived.value
        if workspace.namespace_scan_dirs and not project.namespace_scan_dirs:
            project = project.model_copy(
                update={"namespace_scan_dirs": workspace.namespace_scan_dirs},
            )
        return r[m.Infra.ProjectSpec].ok(project)

    @staticmethod
    def _validated_scaffold_project(
        project: m.Infra.ProjectSpec,
        render_inputs: m.Infra.CodegenRenderInputs,
    ) -> p.Result[m.Infra.ProjectSpec]:
        """Validate the target's own license against supported artifact templates.

        The notice-identity owner applies the one supported-license rule the
        generated notices and artifacts share.

        Returns:
            The original target declaration, with no runtime requirement injection.

        """
        result_type = r[m.Infra.ProjectSpec]
        identity = u.Infra.project_notice_identity(
            render_inputs.target.root,
            project,
            render_inputs.codegen.scaffold.project,
        )
        if identity.failure:
            return result_type.from_failure(identity)
        return result_type.ok(project)

    @classmethod
    def _integration_facts(
        cls,
        render_inputs: m.Infra.CodegenRenderInputs,
    ) -> p.Result[
        t.Triple[
            m.Infra.ProviderIdentitySpec,
            str,
            t.Pair[str, str],
        ]
    ]:
        """Resolve the provider, integration branch, and FLEXT base URL.

        Internal flext-* floors render from the FLEXT line the checkout
        consumes (the infrastructure dependency's own source), never from
        the consumer's organization or branch: a repository in another org
        otherwise renders a mixed family and uv rejects conflicting URLs.

        Returns:
            The resulting ``p.Result[t.Triple[m.Infra.ProviderIdentitySpec,
                str, t.Pair[str, str]]]`` where the pair carries the FLEXT
                base URL and branch.

        """
        result_type = r[t.Triple[m.Infra.ProviderIdentitySpec, str, t.Pair[str, str]]]
        repository_provider = u.Infra.repository_provider(
            render_inputs.target.repository,
        )
        if repository_provider.failure:
            return result_type.from_failure(repository_provider)
        integration_branch = cls.render_integration_branch(render_inputs)
        if integration_branch.failure:
            return result_type.from_failure(integration_branch)
        # Internal flext-* floors render from the FLEXT line the checkout
        # consumes (the infrastructure dependency's own source), never from
        # the consumer's organization or branch: a repository in another org
        # otherwise renders a mixed family and uv rejects conflicting URLs.
        flext_line = u.Infra.flext_integration_line_for_checkout(
            codegen=render_inputs.codegen,
            repository_root=render_inputs.target.root,
            workspace=render_inputs.workspace,
        )
        if flext_line.failure:
            return result_type.from_failure(flext_line)
        flext_git_base_url = flext_line.value.base_url
        if flext_git_base_url is None:
            return result_type.fail(
                "detected FLEXT line carries no provider base URL",
            )
        return result_type.ok((
            repository_provider.value,
            integration_branch.value,
            (flext_git_base_url, flext_line.value.branch),
        ))

    def _development_dependencies(
        self,
        repository_root: Path,
        repository: m.Infra.RepositoryRef,
        codegen: m.Infra.CodegenConfigSpec,
        project: m.Infra.ProjectSpec,
    ) -> p.Result[t.Pair[t.VariadicTuple[t.NonEmptyStr], t.StrSequence]]:
        """Resolve declared and composed development dependencies of one render.

        Args:
            repository_root: Root whose existing pyproject owns declarations.
            repository: Declared immutable repository identity.
            codegen: Codegen contract the repository renders under.
            project: Validated scaffold project of the conform request.

        Returns:
            The declared project dependencies and the validated development
            dependencies, or the first composition or validation failure.

        """
        result_type = r[t.Pair[t.VariadicTuple[t.NonEmptyStr], t.StrSequence]]
        declared = self._declared_dependency_facts(repository_root, project)
        if declared.failure:
            return result_type.from_failure(declared)
        project_dependencies, declared_dev = declared.value
        composed_dev = u.Infra.project_development_requirements(
            codegen.scaffold.project,
            distribution=repository.distribution,
            kind=repository.kind,
            declared=declared_dev,
        )
        development_dependencies = r[
            t.VariadicTuple[t.NonEmptyStr]
        ].create_from_callable(
            partial(t.Infra.NON_EMPTY_STR_SEQ_ADAPTER.validate_python, composed_dev),
        )
        if development_dependencies.failure:
            return result_type.from_failure(development_dependencies)
        return result_type.ok((
            project_dependencies,
            development_dependencies.value,
        ))

    def _project_render_context(
        self,
        render_inputs: m.Infra.CodegenRenderInputs,
        *,
        planned_data_files: t.StrSequence = (),
        scaffold_sources: bool = True,
    ) -> p.Result[m.Infra.ProjectRenderContext]:
        """Build the complete typed context consumed by project templates.

        Returns:
            The resulting ``p.Result[m.Infra.ProjectRenderContext]``.

        """
        target = render_inputs.target
        workspace = render_inputs.workspace
        codegen = render_inputs.codegen
        repository = target.repository
        repository_root = target.root
        project = self._validated_render_project(render_inputs)
        if project.failure:
            return r[m.Infra.ProjectRenderContext].from_failure(project)
        project = project.value
        dependencies = self._development_dependencies(
            repository_root, repository, codegen, project
        )
        if dependencies.failure:
            return r[m.Infra.ProjectRenderContext].from_failure(dependencies)
        project_dependencies, development_dependencies = dependencies.value
        profile = target.make_profile
        tooling_runtime = render_inputs.tooling_runtime
        if tooling_runtime is None or tooling_runtime.document is None:
            return r[m.Infra.ProjectRenderContext].fail(
                "Project rendering requires resolved tooling context"
                if tooling_runtime is None
                else "Project rendering requires the elected tooling document",
            )
        tooling = tooling_runtime.document
        integration = self._integration_facts(render_inputs)
        if integration.failure:
            return r[m.Infra.ProjectRenderContext].from_failure(integration)
        packaged_data_paths = self._resolved_packaged_data(
            repository_root,
            project,
            profile,
            planned_data_files,
        )
        # The repository's own pyproject.toml is the version SSOT; the release
        # protocol is its only writer, so conform reads it and never syncs it.
        # A tree that has no pyproject yet is being created: it starts at the
        # typed initial version and the protocol owns every change after that.
        version = self._workspace_version(repository_root)
        if version.failure:
            return r[m.Infra.ProjectRenderContext].from_failure(version)
        return r[m.Infra.ProjectRenderContext].ok(
            m.Infra.ProjectRenderContext(
                docs_audit=workspace.docs_audit,
                dist=repository.distribution,
                make_profile=profile,
                uv_link_mode=self.link_mode(repository, codegen.toolchain),
                tooling_runtime=tooling_runtime,
                scaffold=codegen.scaffold,
                gitignore_sections=u.Infra.gitignore_sections(
                    codegen,
                    profile=profile,
                    # The declared distribution is the project identity: a
                    # scaffold renders before its pyproject exists, so the
                    # render never reads it back from disk.
                    project_name=repository.distribution,
                    workspace=workspace,
                    project_patterns=(
                        render_inputs.managed_artifacts.resolution.artifacts.Gitignore.patterns
                    ),
                ),
                project_dependencies=project_dependencies,
                development_dependencies=tuple(development_dependencies),
                tooling=tooling,
                environment_path_prepends=(codegen.toolchain.environment_path_prepends),
                beads=workspace.beads,
                ownership_command_prefix=codegen.toolchain.beads.ownership_command_prefix,
                canonical_project_name=target.canonical_project_name,
                const_name=project.constant_name,
                package_name=project.package_name,
                packaged_data_paths=(
                    *packaged_data_paths.files,
                    *packaged_data_paths.directories,
                ),
                project_declaration_resource=(
                    (
                        dependency_services.FlextInfraEnsurePackagingPhase.declaration_resource
                    )(
                        package=repository.package,
                    )
                ),
                packaged_data_excludes=(
                    (
                        dependency_services.FlextInfraEnsurePackagingPhase.resolve_data_excludes
                    )(
                        repository_root,
                        packaged_data_paths,
                        project.packaged_data_excludes,
                    )
                    if profile is not c.Infra.MakeProfile.WORKSPACE
                    else ()
                ),
                namespace_scan_dirs=project.namespace_scan_dirs,
                workspace_integration=workspace.integration,
                # Carry only the validated
                # project declaration; conform owns no inferred Hatch hook.
                hatch_build_hook_path=project.hatch_build_hook_path,
                uv_cache_key_files=(
                    dependency_services.FlextInfraEnsurePackagingPhase.uv_cache_key_files
                )(
                    project.hatch_build_hook_path,
                ),
                class_stem=project.class_stem,
                ns=project.namespace,
                ns_attr=project.namespace_attribute,
                alias=project.alias,
                env_prefix=project.environment_prefix,
                upstream=project.upstream,
                # Scaffolded facades extend the class each upstream letter names
                # in the __all__ that declares it, never the letter itself.
                upstream_facades=(
                    u.Infra.facade_classes(
                        project.upstream,
                        source_root=repository_root,
                    )
                    if scaffold_sources
                    else {}
                ),
                inherited_facets=project.inherited_facets,
                root_packages=project.root_packages,
                repository_namespace_packages=project.repository_namespace_packages,
                root_modules=project.root_modules,
                cli_module=project.cli_module,
                runtime_dependency_overlay=project.runtime_dependency_overlay,
                description=project.description,
                documentation_language=project.documentation_language,
                version=version.value,
                license=project.license,
                python_required_version=codegen.toolchain.python_required_version,
                dependency_cooldown_days=codegen.toolchain.dependency_cooldown_days,
                author_name=project.author_name,
                author_email=project.author_email,
                repository=project.homepage,
                homepage=project.homepage,
                documentation=project.documentation,
                flext_git_base_url=integration.value[2][0],
                flext_git_branch=integration.value[2][1],
                repository_provider=repository.provider,
                repository_git_url=repository.url,
                repository_branch=integration.value[1],
                year=project.year,
            ),
        )

    @staticmethod
    def _declared_dependency_facts(
        repository_root: Path,
        project: m.Infra.ProjectSpec,
    ) -> p.Result[
        t.Pair[t.VariadicTuple[t.NonEmptyStr], t.VariadicTuple[t.NonEmptyStr]]
    ]:
        """Read the declared dependency facts of one render project.

        An existing ``pyproject.toml`` owns the declared runtime dependencies
        and development extras. The repository overlay extends those runtime
        requirements for existing projects as well as new scaffolds.

        Args:
            repository_root: Project root whose pyproject declares the facts.
            project: Resolved render project used before the pyproject exists.

        Returns:
            The non-empty declared dependency names with their declared
            development extras, or the first metadata failure.

        """
        result_type = r[
            t.Pair[t.VariadicTuple[t.NonEmptyStr], t.VariadicTuple[t.NonEmptyStr]]
        ]
        if (repository_root / c.PYPROJECT_FILENAME).is_file():
            metadata = u.Infra.read_project_metadata_result(repository_root)
            if metadata.failure:
                return result_type.from_failure(metadata)
            payload = u.Infra.pyproject_payload(repository_root / c.PYPROJECT_FILENAME)
            groups = u.Cli.toml_mapping_child(payload, c.Infra.DEPENDENCY_GROUPS) or {}
            runtime = r[t.VariadicTuple[t.NonEmptyStr]].create_from_callable(
                partial(
                    t.Infra.NON_EMPTY_STR_SEQ_ADAPTER.validate_python,
                    metadata.value.project.dependencies,
                ),
            )
            if runtime.failure:
                return result_type.from_failure(runtime)
            declared_dev = r[t.VariadicTuple[t.NonEmptyStr]].create_from_callable(
                partial(
                    t.Infra.NON_EMPTY_STR_SEQ_ADAPTER.validate_python,
                    (
                        *t.Infra.STR_SEQ_ADAPTER.validate_python(
                            groups.get(c.Infra.DEV, ()),
                        ),
                        *u.Infra.canonical_dev_dependencies_from_payload(payload),
                    ),
                ),
            )
            if declared_dev.failure:
                return result_type.from_failure(declared_dev)
            return result_type.ok((
                tuple(
                    dict.fromkeys((
                        *runtime.value,
                        *project.runtime_dependency_overlay,
                    ))
                ),
                declared_dev.value,
            ))
        return result_type.ok((project.runtime_dependency_overlay, ()))

    def _validated_render_project(
        self,
        render_inputs: m.Infra.CodegenRenderInputs,
    ) -> p.Result[m.Infra.ProjectSpec]:
        """Resolve and validate the render project of one conform request.

        Args:
            render_inputs: Typed render inputs of the conform request.

        Returns:
            The validated scaffold project, or the first resolution or
            validation failure.

        """
        resolved = self._resolved_render_project(render_inputs)
        if resolved.failure:
            return r[m.Infra.ProjectSpec].from_failure(resolved)
        validated = self._validated_scaffold_project(
            resolved.value,
            render_inputs,
        )
        if validated.failure:
            return r[m.Infra.ProjectSpec].from_failure(validated)
        return r[m.Infra.ProjectSpec].ok(validated.value)

    @staticmethod
    def _resolved_packaged_data(
        repository_root: Path,
        project: m.Infra.ProjectSpec,
        profile: c.Infra.MakeProfile,
        planned_data_files: t.StrSequence,
    ) -> m.Infra.PackagedDataSelection:
        """Resolve the packaged data selection of the target make profile.

        A workspace-profile render owns no packaged data selection: workspace
        aggregation renders no installable project payload of its own.

        Args:
            repository_root: Project root holding the declared data paths.
            project: Resolved render project declaring packaged data.
            profile: Make profile of the conformance target.
            planned_data_files: Planned shared data files of the render.

        Returns:
            The resolved packaged data selection of the render.

        """
        if profile is c.Infra.MakeProfile.WORKSPACE:
            return m.Infra.PackagedDataSelection()
        return dependency_services.FlextInfraEnsurePackagingPhase.resolve_data_paths(
            repository_root,
            project.package_name,
            project.packaged_data_paths,
            planned_data_files,
        )

    @staticmethod
    def _repository_root_rel(workspace: m.Infra.WorkspaceSpec) -> str:
        """Return the environment root owned by the inferred target.

        Returns:
            The environment root owned by the inferred target.

        """
        if workspace.project is not None:
            project_root_rel: str = workspace.project.repository_root_rel
            return project_root_rel
        return "."

    @staticmethod
    def _beads_project_id(repository_root: Path) -> str | None:
        """Return the checkout's own ledger identity, or None if unminted.

        `.beads/identity.toml` is the canonical owner (`[project] id`); the
        generated marker is its projection. An absent file is not a failure —
        it means Beads has not minted an identity for this checkout yet.

        Why the marker read-back: identity.toml is a gitignored per-checkout
        file, so CI clones and fresh runners run unminted while the TRACKED
        marker still carries the ledger identity the repository was cloned
        with. Rendering ``project_id: null`` over it dirties the tree (the
        generated-drift check goes red) and, worse, a pushed rewrite would
        strand every clone's identity — the same class of loss already
        observed in a consumer rig. When identity.toml is absent, read the id
        back from the existing marker so an unminted checkout preserves the
        identity it cloned instead of clobbering it.

        Returns:
            The checkout's own ledger identity, or None if unminted.

        Raises:
            RuntimeError: If failed to read beads identity at.
            ValueError: If beads identity at.

        """
        identity = repository_root / c.Infra.BEADS_DIRNAME / "identity.toml"
        if identity.is_file():
            source = u.Cli.files_read_text(identity)
            if source.failure:
                msg = f"failed to read beads identity at {identity}: {source.error}"
                raise RuntimeError(msg)
            payload = u.Cli.toml_mapping_from_text(source.value)
            if payload is None:
                msg = f"beads identity at {identity} is not valid TOML"
                raise ValueError(msg)
            project = payload.get("project")
            if not isinstance(project, Mapping):
                return None
            value = project.get("id")
            return value.strip() if isinstance(value, str) and value.strip() else None
        marker = repository_root / c.Infra.BEADS_METADATA_RELPATH
        if not marker.is_file():
            return None
        document = u.Cli.json_loads(marker.read_text(encoding="utf-8"))
        if document.failure or not isinstance(document.value, dict):
            return None
        value = document.value.get("project_id")
        return value.strip() if isinstance(value, str) and value.strip() else None


__all__: list[str] = ["FlextInfraCodegenConformContextRender"]
