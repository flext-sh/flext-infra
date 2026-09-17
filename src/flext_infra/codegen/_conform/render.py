"""Artifact composition and render context projection."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path

from ... import c, config, m, p, r, t, u
from ...deps import FlextInfraEnsureRuffConfigPhase
from .bootstrap import FlextInfraCodegenConformBootstrap
from .misc import FlextInfraCodegenConformMisc


class FlextInfraCodegenConformRender:
    """Artifact composition and render context projection."""

    @staticmethod
    def compose_project_artifact(
        repository_root: Path,
        destination: str,
        rendered: str,
        *,
        managed_artifacts: m.Infra.ProjectManagedArtifactsSnapshot | None = None,
        workspace: m.Infra.WorkspaceSpec | None = None,
        codegen: m.Infra.CodegenConfigSpec | None = None,
        repository: m.Infra.RepositoryRef | None = None,
        target: m.Infra.RepositoryConformTarget | None = None,
    ) -> p.Result[m.Infra.CodegenArtifactComposition]:
        """Apply typed project overlays after canonical template rendering."""
        if destination == c.Infra.PYPROJECT_FILENAME:
            live_path = repository_root / c.Infra.PYPROJECT_FILENAME
            live: str | None = None
            if live_path.is_file():
                # Overlay reads the live text (managed merge conflicts
                # resolved) and never writes it.
                recovered_live = u.Infra.live_pyproject_text(live_path)
                if recovered_live.failure:
                    return r[m.Infra.CodegenArtifactComposition].from_failure(
                        recovered_live
                    )
                live = recovered_live.value
            overlaid = u.Infra.overlay_preserved(rendered, live)
            if overlaid.failure:
                return r[m.Infra.CodegenArtifactComposition].from_failure(overlaid)
            rendered = overlaid.value
            if workspace is not None and codegen is not None and repository is not None:
                profile = (
                    target.make_profile
                    if target is not None
                    else c.Infra.MakeProfile.STANDALONE
                )
                excludes = (
                    FlextInfraCodegenConformMisc.routed_uv_exclude_dependencies(
                        repository=repository, target=target, codegen=codegen
                    )
                    if target is not None
                    else ()
                )
                conformed = FlextInfraCodegenConformMisc.conformed_pyproject_source(
                    rendered,
                    repository=repository,
                    workspace=workspace,
                    codegen=codegen,
                    workspace_mode=profile,
                    uv_exclude_dependencies=excludes,
                )
                if conformed.failure:
                    return r[m.Infra.CodegenArtifactComposition].from_failure(conformed)
                rendered = conformed.value
            formatted = u.Infra.format_toml_source(
                rendered,
                path=live_path,
                toolchain_root=repository_root,
                taplo_version=config.Infra.codegen.toolchain.taplo_version,
            )
            rendered = formatted.value if formatted.success else rendered
        if destination != c.Infra.MISE_TOML_FILENAME:
            return r[m.Infra.CodegenArtifactComposition].ok(
                m.Infra.CodegenArtifactComposition(rendered=rendered)
            )
        resolved_artifacts = managed_artifacts
        if resolved_artifacts is None:
            snapshot = u.Infra.snapshot_committed_project_managed_artifacts(
                repository_root
            )
            if snapshot.failure:
                return r[m.Infra.CodegenArtifactComposition].from_failure(snapshot)
            resolved_artifacts = snapshot.value
        composed = (
            u.Infra.compose_mise_toml_from_snapshot(
                resolved_artifacts.sources, rendered
            )
            if resolved_artifacts.sources
            else u.Infra.compose_mise_toml_from_resolution(
                resolved_artifacts.resolution, rendered
            )
        )
        if composed.failure:
            return r[m.Infra.CodegenArtifactComposition].from_failure(composed)
        config_sources = u.Infra.snapshot_config_sources(repository_root)
        if config_sources.failure:
            return r[m.Infra.CodegenArtifactComposition].from_failure(config_sources)
        return r[m.Infra.CodegenArtifactComposition].ok(
            m.Infra.CodegenArtifactComposition(
                rendered=composed.value, source_states=config_sources.value
            )
        )

    def _rendered_artifact_source(
        self,
        *,
        templates_root: Path,
        template_relpath: Path,
        failure_prefix: str,
        dist: str,
        repository: m.Infra.RepositoryRef,
        repository_root: Path,
        target: m.Infra.RepositoryConformTarget,
        workspace: m.Infra.WorkspaceSpec,
        codegen: m.Infra.CodegenConfigSpec,
        destination: str,
        tooling_runtime: m.Infra.ToolingRuntimeContext,
        project_context: m.Infra.ProjectRenderContext | None,
        managed_artifacts: m.Infra.ProjectManagedArtifactsResolution | None = None,
    ) -> p.Result[str]:
        """Resolve one artifact render context and render its template source.

        ``failure_prefix`` carries the only difference between the scaffold and
        existing-repository planners: the stage banner the scaffold planner
        prepends to a render failure.
        """
        artifact_context = self._artifact_render_context(
            dist=dist,
            repository=repository,
            repository_root=repository_root,
            target=target,
            workspace=workspace,
            codegen=codegen,
            destination=destination,
            tooling_runtime=tooling_runtime,
            project_context=project_context,
            managed_artifacts=managed_artifacts,
        )
        if artifact_context.failure:
            return r[str].from_failure(artifact_context)
        rendered = u.Cli.template_render(
            templates_root / template_relpath, artifact_context.value
        )
        if rendered.failure:
            return r[str].fail(
                f"{failure_prefix}"
                f"template={template_relpath}: "
                f"{rendered.error or 'template render failed'}"
            )
        return rendered

    def _artifact_render_context(
        self,
        *,
        dist: str,
        repository: m.Infra.RepositoryRef,
        repository_root: Path,
        target: m.Infra.RepositoryConformTarget,
        workspace: m.Infra.WorkspaceSpec,
        codegen: m.Infra.CodegenConfigSpec,
        destination: str,
        tooling_runtime: m.Infra.ToolingRuntimeContext,
        project_context: m.Infra.ProjectRenderContext | None,
        managed_artifacts: m.Infra.ProjectManagedArtifactsResolution | None = None,
    ) -> p.Result[p.Model]:
        """Resolve one governed artifact to its canonical typed render input."""
        if destination == c.Infra.GITIGNORE:
            project_patterns: t.StrSequence = (
                managed_artifacts.artifacts.Gitignore.patterns
                if managed_artifacts is not None
                else ()
            )
            return r[p.Model].ok(
                m.Infra.GitignoreRenderSpec(
                    gitignore_sections=self._gitignore_sections(
                        codegen,
                        profile=target.make_profile,
                        project_name=repository_root.name,
                        workspace=workspace,
                        project_patterns=project_patterns,
                    )
                )
            )
        if destination == ".pre-commit-config.yaml":
            return r[p.Model].ok(
                m.Infra.MakeWorkflowRenderSpec(dist=dist, make=codegen.make)
            )
        if destination in {
            ".markdownlint.json",
            ".markdownlintignore",
            ".qlty/qlty.toml",
        }:
            return r[p.Model].ok(
                m.Infra.MarkdownLintRenderSpec(tooling=config.Infra.tooling)
            )
        if destination == ".envrc":
            # Conform targets always own a governed Beads identity, so the
            # rendered tier is binary here: city server wiring when the
            # repository declares city participation, the repository-local
            # bd base otherwise.
            return r[p.Model].ok(
                m.Infra.EnvrcRenderSpec(
                    state_directory_name=codegen.toolchain.state_directory_name,
                    scratch_namespace=codegen.toolchain.scratch_namespace,
                    scratch_home_relative=(codegen.toolchain.scratch_home_relative),
                    pycache_namespace=codegen.toolchain.pycache_namespace,
                    environment_path_prepends=(
                        codegen.toolchain.environment_path_prepends
                    ),
                    mise_bootstrap=(self._mise_bootstrap_environment()),
                    gascity=(
                        m.Infra.BeadsWorkspaceEnvironmentSpec()
                        if target.gascity_enabled
                        else m.Infra.BeadsWorkspaceEnvironmentSpec(backend="local")
                    ),
                )
            )
        if destination in {".mise.toml", ".python-version"}:
            # Computed toolchain fields are projections, not inputs: filter the
            # dump to the render spec's declared fields before construction.
            toolchain_data = {
                field_name: value
                for field_name, value in codegen.toolchain.model_dump().items()
                if field_name in m.Infra.MiseTomlRenderSpec.model_fields
            }
            toolchain_data["gascity_enabled"] = target.gascity_enabled
            return r[p.Model].ok(m.Infra.MiseTomlRenderSpec(**toolchain_data))

        if destination == c.Infra.BEADS_CONFIG_RELPATH:
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
                        dict.fromkeys((*project_types, *required_types))
                    ),
                    dolt_mode=beads.dolt_mode,
                    export_auto=beads.export_auto,
                    backup_enabled=beads.backup_enabled,
                    dolt_disable_event_flush=beads.dolt_disable_event_flush,
                )
            )
        if destination == c.Infra.BEADS_METADATA_RELPATH:
            # Why: this marker is regenerated on every `make gen`, but the
            # ledger identity inside it is owned by the checkout, not by the
            # fleet SSOT. Rendering without it stripped the key, and Beads then
            # minted a NEW identity on next access — rig gmn lost
            # 2b1a0582-… that way (commit 3e7ba1e). Read it back so a
            # regeneration is identity-preserving.
            return r[p.Model].ok(
                m.Infra.BeadsMetadataRenderSpec(
                    database=target.beads.database,
                    dolt_mode=codegen.toolchain.beads.dolt_mode,
                    project_id=self._beads_project_id(repository_root),
                )
            )
        if destination.startswith(".github/"):
            provider = self._repository_provider(repository, codegen)
            if provider.failure:
                return r[p.Model].from_failure(provider)
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
            branch = u.Infra.resolve_integration_branch(workspace, provider.value)
            return r[p.Model].ok(
                m.Infra.GithubWorkflowRenderSpec(
                    dist=dist,
                    make_profile=target.make_profile,
                    gascity_enabled=target.gascity_enabled,
                    repository_branch=branch,
                    ci_trigger_branches=tuple(
                        dict.fromkeys((
                            *codegen.branch_policy.ci_trigger_branches,
                            branch,
                        ))
                    ),
                    python_version=codegen.toolchain.python_version,
                    state_directory_name=codegen.toolchain.state_directory_name,
                    github_actions=codegen.github_actions,
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
                    checkout_submodules=codegen.checkout_submodules_overrides.get(
                        dist, codegen.checkout_submodules
                    ),
                    custom_steps=self._custom_ci_steps(repository_root),
                    private_submodules=codegen.ci_private_submodules.get(dist),
                    private_dependency_auth=codegen.ci_private_dependency_auth.get(
                        dist
                    ),
                    system_packages=tuple(codegen.ci_system_packages.get(dist, ())),
                )
            )
        destination_path = Path(destination)
        if (
            destination_path.parent.as_posix() == "tests/fixtures/ci/docker"
            and destination_path.suffix == ".Dockerfile"
        ):
            return r[p.Model].ok(
                m.Infra.DistroDockerRenderSpec(
                    package_name=dist.replace("-", "_"),
                    python_version=codegen.toolchain.python_version,
                    make=codegen.make,
                    mise_bootstrap=self._mise_bootstrap_environment(),
                )
            )
        if destination == c.Infra.RELEASE_GITLEAKS_CONFIG_PATH:
            # Why (flext-to3n7): the release build phase snapshots the gitleaks
            # policy from the repository; it is fleet policy owned by
            # config/infra.yaml, never scaffold-only project metadata.
            return r[p.Model].ok(
                m.Infra.ReleasePolicySpec(
                    build_constraints=config.Infra.release.build_constraints
                )
            )
        if destination == c.Infra.MAKEFILE_FILENAME:
            profile = target.make_profile
            subprojects = (
                tuple(workspace.subprojects)
                if profile is c.Infra.MakeProfile.WORKSPACE
                else ()
            )
            gitlinks = self._managed_gitlinks(workspace, codegen)
            if gitlinks.failure:
                return r[p.Model].from_failure(gitlinks)
            return r[p.Model].ok(
                m.Infra.MakefileRenderSpec(
                    pytest=config.Infra.tooling.tools.pytest,
                    mise_bootstrap=self._mise_bootstrap_environment(),
                    dist=dist,
                    state_directory_name=codegen.toolchain.state_directory_name,
                    scratch_namespace=codegen.toolchain.scratch_namespace,
                    scratch_home_relative=codegen.toolchain.scratch_home_relative,
                    infra_cli=config.Infra.name,
                    make_profile=profile,
                    makefile_custom_include=c.Infra.MAKEFILE_CUSTOM_INCLUDE,
                    repository_root_rel=self._repository_root_rel(workspace),
                    workspace_subprojects=tuple(
                        item.path.as_posix() for item in workspace.subprojects
                    ),
                    workspace_repositories=subprojects,
                    workspace_gitlinks=gitlinks.value,
                    uv_link_mode=FlextInfraCodegenConformBootstrap.link_mode(
                        repository, codegen.toolchain
                    ),
                    uv_version=codegen.toolchain.uv_version,
                    make=codegen.make,
                    extra_verbs=(
                        self._merge_extra_verbs(
                            repository.extra_verbs,
                            (
                                ()
                                if repository.script_dispatch is None
                                else self._discover_script_verbs(repository_root)
                            ),
                            frozenset(verb.name for verb in codegen.make.verbs),
                        )
                    ),
                    script_dispatch=repository.script_dispatch,
                    workspace_cli_group=c.Infra.CLI_GROUP_WORKSPACE,
                    mypy_memory_limit_mb=c.Infra.MYPY_MEMORY_LIMIT_MB_DEFAULT,
                    mypy_timeout_seconds=c.Infra.MYPY_TIMEOUT_SECONDS_DEFAULT,
                    mypy_timeout_exit_code=c.Infra.PROCESS_TIMEOUT_EXIT_CODE,
                    mypy_signal_exit_offset=c.Infra.PROCESS_SIGNAL_EXIT_OFFSET,
                    prlimit_command=c.Infra.PRLIMIT_COMMAND,
                    prlimit_address_space_option=(c.Infra.PRLIMIT_ADDRESS_SPACE_OPTION),
                    timeout_command=c.Infra.TIMEOUT_COMMAND,
                    timeout_kill_after_seconds=c.Infra.TIMEOUT_KILL_AFTER_SECONDS,
                    pytest_process_timeout_seconds=(
                        config.Infra.tooling.tools.pytest.process_timeout_seconds
                    ),
                )
            )
        if destination == c.Infra.CUSTOM_MAKE_FILENAME:
            # Existing repositories project custom routes from the same typed
            # Make contract as Makefile; they do not require scaffold-only
            # project metadata.
            make_context = self.make_render_context(
                repository,
                target,
                workspace,
                codegen,
                tooling_runtime=tooling_runtime,
                repository_root=repository_root,
            )
            if make_context.failure:
                return r[p.Model].from_failure(make_context)
            return r[p.Model].ok(make_context.value)
        if destination in {
            c.Infra.MARKDOWNLINT_CONFIG_FILENAME,
            c.Infra.MARKDOWNLINT_IGNORE_FILENAME,
        }:
            return r[p.Model].ok(
                m.Infra.ToolingRenderSpec(tooling=config.Infra.tooling)
            )
        if project_context is not None:
            return r[p.Model].ok(project_context)
        context_result = self._project_render_context(
            repository,
            target,
            workspace,
            codegen,
            tooling_runtime=tooling_runtime,
            repository_root=repository_root,
            managed_artifacts=managed_artifacts,
            use_committed_artifacts=project_context is None,
        )
        if context_result.failure:
            return r[p.Model].from_failure(context_result)
        return r[p.Model].ok(context_result.value)

    def make_render_context(
        self,
        repository: m.Infra.RepositoryRef,
        target: m.Infra.RepositoryConformTarget,
        workspace: m.Infra.WorkspaceSpec,
        codegen: m.Infra.CodegenConfigSpec,
        *,
        tooling_runtime: m.Infra.ToolingRuntimeContext,
        repository_root: Path,
    ) -> p.Result[m.Infra.MakeRenderContext]:
        """Build the typed context consumed by the generated Makefile."""
        profile = target.make_profile
        subprojects = (
            tuple(workspace.subprojects)
            if profile is c.Infra.MakeProfile.WORKSPACE
            else ()
        )
        gitlinks = self._managed_gitlinks(workspace, codegen)
        if gitlinks.failure:
            return r[m.Infra.MakeRenderContext].from_failure(gitlinks)
        extra_verbs = self._merge_extra_verbs(
            repository.extra_verbs,
            (
                ()
                if repository.script_dispatch is None
                else self._discover_script_verbs(repository_root)
            ),
            frozenset(verb.name for verb in codegen.make.verbs),
        )
        return r[m.Infra.MakeRenderContext].ok(
            m.Infra.MakeRenderContext(
                pytest=config.Infra.tooling.tools.pytest,
                mise_bootstrap=(self._mise_bootstrap_environment()),
                make=codegen.make,
                mypy_memory_limit_mb=c.Infra.MYPY_MEMORY_LIMIT_MB_DEFAULT,
                mypy_timeout_seconds=c.Infra.MYPY_TIMEOUT_SECONDS_DEFAULT,
                mypy_timeout_exit_code=c.Infra.PROCESS_TIMEOUT_EXIT_CODE,
                mypy_signal_exit_offset=c.Infra.PROCESS_SIGNAL_EXIT_OFFSET,
                prlimit_command=c.Infra.PRLIMIT_COMMAND,
                prlimit_address_space_option=c.Infra.PRLIMIT_ADDRESS_SPACE_OPTION,
                timeout_command=c.Infra.TIMEOUT_COMMAND,
                timeout_kill_after_seconds=c.Infra.TIMEOUT_KILL_AFTER_SECONDS,
                tooling_runtime=tooling_runtime,
                dist=repository.distribution,
                infra_cli=config.Infra.name,
                python_version=codegen.toolchain.python_version,
                uv_link_mode=FlextInfraCodegenConformBootstrap.link_mode(
                    repository, codegen.toolchain
                ),
                # ProjectRenderContext replaces this with the composed map.
                # Pass the neutral value explicitly so Pydantic never deep-copies
                # the MappingProxyType model default while building the base.
                ruff_per_file_ignores={},
                make_profile=profile,
                workspace_cli_group=c.Infra.CLI_GROUP_WORKSPACE,
                repository_root_rel=self._repository_root_rel(workspace),
                makefile_custom_include=c.Infra.MAKEFILE_CUSTOM_INCLUDE,
                workspace_subprojects=tuple(
                    item.path.as_posix() for item in workspace.subprojects
                ),
                workspace_repositories=subprojects,
                workspace_gitlinks=gitlinks.value,
                extra_verbs=extra_verbs,
                script_dispatch=repository.script_dispatch,
            )
        )

    @staticmethod
    def _project_spec_from_existing(
        repository: m.Infra.RepositoryRef,
        repository_root: Path,
        codegen: m.Infra.CodegenConfigSpec,
    ) -> p.Result[m.Infra.ProjectSpec]:
        """Derive scaffold ProjectSpec from live PEP 621 metadata for existing trees."""
        metadata = u.Infra.read_project_metadata_result(repository_root)
        if metadata.failure:
            return r[m.Infra.ProjectSpec].from_failure(metadata)
        pep621 = metadata.value.project
        package_name = metadata.value.package_name
        class_stem = metadata.value.class_stem
        alias = u.Infra.package_alias(package_name=package_name)
        namespace = class_stem.removeprefix("Flext") or class_stem
        author = pep621.authors[0] if pep621.authors else None
        author_name = author.name if author is not None and author.name else ""
        author_email = author.email if author is not None and author.email else ""
        if not author_name or not author_email:
            return r[m.Infra.ProjectSpec].fail(
                f"existing pyproject is missing author name/email: {repository_root}"
            )
        homepage = pep621.urls.homepage or repository.url.removesuffix(".git")
        documentation = pep621.urls.documentation or homepage
        runtime_names = {
            name for item in pep621.dependencies if (name := u.Infra.dep_name(item))
        }
        profiles = codegen.scaffold.project.dependency_profiles
        # The root of the dependency tree declares no upstream distribution:
        # a distribution that IS a profile's upstream owns that profile.
        own_profile = next(
            (
                item
                for item in profiles
                if item.project is None
                and item.upstream.replace("_", "-") == repository.distribution
            ),
            None,
        )
        candidates = (
            (own_profile,)
            if own_profile is not None
            else tuple(
                item
                for item in profiles
                if item.project is None
                and item.upstream.replace("_", "-") in runtime_names
            )
        )
        # A profile whose upstream is itself a runtime dependency of another
        # candidate is implied by it; the declared upstream is the most
        # specific candidate, never the first catalog row that happens to match.
        runtime_of = {
            item.upstream: {
                name
                for dependency in item.runtime
                if (name := u.Infra.dep_name(dependency))
            }
            for item in candidates
        }
        direct = tuple(
            item
            for item in candidates
            if not any(
                item.upstream.replace("_", "-") in runtime_of[other.upstream]
                for other in candidates
                if other is not item
            )
        )
        if len(direct) != 1:
            return r[m.Infra.ProjectSpec].fail(
                "scaffold.project.dependency_profiles.upstream must match live "
                f"dependencies exactly once at {repository_root}: "
                f"{tuple(item.upstream for item in direct)}"
            )
        upstream = direct[0].upstream
        licenses = codegen.scaffold.project.supported_licenses
        return r[m.Infra.ProjectSpec].ok(
            m.Infra.ProjectSpec(
                package_name=package_name,
                class_stem=class_stem,
                namespace=namespace,
                constant_name=repository.distribution,
                namespace_attribute=alias,
                alias=alias,
                environment_prefix=f"{package_name.upper()}_",
                description=pep621.description or repository.distribution,
                license=licenses[0],
                author_name=author_name,
                author_email=author_email,
                upstream=upstream,
                homepage=homepage,
                documentation=documentation,
                repository_root_rel=".",
                year=codegen.scaffold.project.copyright_year,
            )
        )

    def _project_render_context(
        self,
        repository: m.Infra.RepositoryRef,
        target: m.Infra.RepositoryConformTarget,
        workspace: m.Infra.WorkspaceSpec,
        codegen: m.Infra.CodegenConfigSpec,
        *,
        tooling_runtime: m.Infra.ToolingRuntimeContext,
        repository_root: Path,
        managed_artifacts: m.Infra.ProjectManagedArtifactsResolution | None = None,
        use_committed_artifacts: bool = True,
    ) -> p.Result[m.Infra.ProjectRenderContext]:
        """Build the complete typed context consumed by project templates."""
        if workspace.project is None:
            # Existing checkouts declare no scaffold metadata: derive the render
            # identity from the live project metadata instead of failing, so
            # conforming a governed repository never depends on scaffold-only
            # declarations.
            derived = self._project_spec_from_existing(
                repository, repository_root, codegen
            )
            if derived.failure:
                return r[m.Infra.ProjectRenderContext].from_failure(derived)
            project = derived.value
        else:
            project = workspace.project
        dependency_profile = next(
            (
                item
                for item in codegen.scaffold.project.dependency_profiles
                if item.project is None and item.upstream == project.upstream
            ),
            None,
        )
        if dependency_profile is None:
            return r[m.Infra.ProjectRenderContext].fail(
                f"unsupported scaffold upstream: {project.upstream}"
            )
        additions = tuple(
            item
            for item in codegen.scaffold.project.dependency_profiles
            if item.project == repository.distribution
        )
        if additions:
            dependency_profile = m.Infra.ScaffoldDependencyProfileSpec.model_validate({
                **dependency_profile.model_dump(),
                "runtime": tuple(
                    dict.fromkeys((
                        *dependency_profile.runtime,
                        *(
                            requirement
                            for item in additions
                            for requirement in item.runtime
                        ),
                    ))
                ),
                "codegen": tuple(
                    dict.fromkeys((
                        *dependency_profile.codegen,
                        *(
                            requirement
                            for item in additions
                            for requirement in item.codegen
                        ),
                    ))
                ),
            })
        if project.license not in codegen.scaffold.project.supported_licenses:
            supported = ", ".join(codegen.scaffold.project.supported_licenses)
            return r[m.Infra.ProjectRenderContext].fail(
                f"unsupported scaffold license: {project.license}; "
                f"supported licenses: {supported}"
            )
        profile = target.make_profile
        make_context = self.make_render_context(
            repository,
            target,
            workspace,
            codegen,
            tooling_runtime=tooling_runtime,
            repository_root=repository_root,
        )
        if make_context.failure:
            return r[m.Infra.ProjectRenderContext].from_failure(make_context)
        repository_provider = self._repository_provider(repository, codegen)
        if repository_provider.failure:
            return r[m.Infra.ProjectRenderContext].from_failure(repository_provider)
        flext_provider = repository_provider.value
        packaged_data_dirs = (
            tuple(
                data_dir
                for data_dir in config.Infra.tooling.tools.hatch.packaged_data_dirs
                if any(
                    profile in entry.profiles
                    and Path(entry.destination).parts
                    and Path(entry.destination).parts[0] == data_dir
                    for entry in codegen.templates.entries
                )
            )
            if profile is not c.Infra.MakeProfile.WORKSPACE
            else ()
        )
        catalog_artifacts = managed_artifacts
        if use_committed_artifacts:
            committed = u.Infra.load_committed_project_managed_artifacts(
                repository_root
            )
            if committed.failure:
                return r[m.Infra.ProjectRenderContext].from_failure(committed)
            catalog_artifacts = committed.value
        project_patterns: t.StrSequence = (
            catalog_artifacts.artifacts.Gitignore.patterns
            if catalog_artifacts is not None
            else ()
        )
        # The repository's own pyproject.toml is the version SSOT; the release
        # protocol is its only writer, so conform reads it and never syncs it.
        # A tree that has no pyproject yet is being created: it starts at the
        # typed initial version and the protocol owns every change after that.
        version_result = (
            u.Infra.current_workspace_version(repository_root)
            if (repository_root / c.Infra.PYPROJECT_FILENAME).is_file()
            else r[str].ok(config.Infra.initial_project_version)
        )
        if version_result.failure:
            return r[m.Infra.ProjectRenderContext].from_failure(version_result)
        return r[m.Infra.ProjectRenderContext].ok(
            m.Infra.ProjectRenderContext(
                **make_context.value.model_dump(
                    by_alias=True,
                    exclude={"mise_bootstrap", "ruff_per_file_ignores"},
                    exclude_computed_fields=True,
                ),
                mise_bootstrap=self._mise_bootstrap_environment(),
                scaffold=codegen.scaffold,
                gitignore_sections=self._gitignore_sections(
                    codegen,
                    profile=profile,
                    project_name=repository_root.name,
                    workspace=workspace,
                    project_patterns=project_patterns,
                ),
                dependency_profile=dependency_profile,
                tooling=config.Infra.tooling,
                # Why: the fleet policy alone is not the effective Ruff contract.
                # A repository may carry an operator-authorized exemption in its
                # committed ``config/*.yaml`` ManagedArtifacts catalog, and
                # ensure_ruff composes the two when it edits a pyproject in
                # place. The template rendered only the fleet map, so a full
                # render silently dropped the local overlay -- flext-infra's
                # own _rope exemption disappeared on every conform and returned
                # 12 SLF001 findings the operator had already ruled on. Compose
                # from the commit catalog so both paths produce the same
                # effective map and concurrent worktree WIP cannot change a
                # projection.
                ruff_per_file_ignores=(
                    FlextInfraEnsureRuffConfigPhase.compose_per_file_ignores(
                        repository_root, managed_artifacts=catalog_artifacts
                    )
                ),
                environment_path_prepends=(codegen.toolchain.environment_path_prepends),
                beads_tool_selector=codegen.toolchain.beads.selector,
                beads_tool_version=codegen.toolchain.beads.version,
                # prerelease is load-bearing: every fork release of bd carries a
                # suffixed tag (-fdN) and mise refuses to resolve one unless
                # told the release is a prerelease. Omitting it silently pinned
                # every rig to upstream, which lacks the bd list cycle guard.
                beads_tool_prerelease=codegen.toolchain.beads.prerelease,
                beads=workspace.beads,
                canonical_project_name=target.canonical_project_name,
                const_name=project.constant_name,
                package_name=project.package_name,
                packaged_data_dirs=packaged_data_dirs,
                namespace_scan_dirs=project.namespace_scan_dirs,
                class_stem=project.class_stem,
                ns=project.namespace,
                ns_attr=project.namespace_attribute,
                alias=project.alias,
                env_prefix=project.environment_prefix,
                upstream=project.upstream,
                inherited_facets=project.inherited_facets,
                root_packages=project.root_packages,
                root_modules=project.root_modules,
                runtime_dependency_overlay=project.runtime_dependency_overlay,
                description=project.description,
                version=version_result.value,
                license=project.license,
                python_required_version=codegen.toolchain.python_required_version,
                kubectl_version=codegen.toolchain.kubectl_version,
                helm_version=codegen.toolchain.helm_version,
                kind_version=codegen.toolchain.kind_version,
                direnv_version=codegen.toolchain.direnv_version,
                uv_version=codegen.toolchain.uv_version,
                qlty_version=codegen.toolchain.qlty_version,
                node_version=codegen.toolchain.node_version,
                jscpd_version=codegen.toolchain.jscpd_version,
                waza_version=codegen.toolchain.waza_version,
                taplo_version=codegen.toolchain.taplo_version,
                ast_grep_version=codegen.toolchain.ast_grep_version,
                gitleaks_version=codegen.toolchain.gitleaks_version,
                scc_version=codegen.toolchain.scc_version,
                kubeconform_version=codegen.toolchain.kubeconform_version,
                go_version=codegen.toolchain.go_version,
                author_name=project.author_name,
                author_email=project.author_email,
                repository=project.homepage,
                homepage=project.homepage,
                documentation=project.documentation,
                flext_git_base_url=flext_provider.base_url,
                flext_git_branch=flext_provider.branch,
                repository_provider=repository.provider,
                repository_git_url=repository.url,
                repository_branch=u.Infra.resolve_integration_branch(
                    workspace, repository_provider.value
                ),
                year=project.year,
            )
        )

    @classmethod
    def _managed_gitlinks(
        cls, workspace: m.Infra.WorkspaceSpec, codegen: m.Infra.CodegenConfigSpec
    ) -> p.Result[t.VariadicTuple[m.Infra.ManagedGitlinkSpec]]:
        """Resolve provider baselines only for mutable governed subprojects."""
        resolved: list[m.Infra.ManagedGitlinkSpec] = []
        for repository in workspace.subprojects:
            provider = cls._repository_provider(repository, codegen)
            if provider.failure:
                return r[tuple[m.Infra.ManagedGitlinkSpec, ...]].from_failure(provider)
            resolved.append(
                m.Infra.ManagedGitlinkSpec(
                    repository=repository,
                    branch=u.Infra.resolve_integration_branch(
                        workspace, provider.value
                    ),
                )
            )
        return r[tuple[m.Infra.ManagedGitlinkSpec, ...]].ok(tuple(resolved))

    @staticmethod
    def _beads_project_id(repository_root: Path) -> str | None:
        """Return the checkout's own ledger identity, or None if unminted.

        `.beads/identity.toml` is the canonical owner (`[project] id`); the
        generated marker is its projection. An absent file is not a failure —
        it means Beads has not minted an identity for this checkout yet.
        """
        identity = repository_root / ".beads" / "identity.toml"
        if not identity.is_file():
            return None
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

    @staticmethod
    def _custom_ci_steps(repository_root: Path) -> str:
        """Read the project-owned workflow steps, if the project declares any.

        This is the CI counterpart of ``custom.mk``: the generator injects the
        block verbatim and never interprets it, so a project extends its own
        pipeline without the generator learning that project's concerns.
        """
        source: Path = repository_root / c.Infra.CUSTOM_CI_STEPS_FILENAME
        if not source.is_file():
            return ""
        return source.read_text(encoding=c.DEFAULT_ENCODING).rstrip("\n")
