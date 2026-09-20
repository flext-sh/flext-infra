"""Conformance plan selection and repository topology resolution."""

from __future__ import annotations

import time
from collections.abc import MutableMapping
from pathlib import Path
from typing import TYPE_CHECKING, Literal, override

from flext_core import r

from ... import c, config, m, p, t, u
from ...deps import FlextInfraPyprojectModernizer
from ...services.codegen import FlextInfraCodegen
from ...workspace import FlextInfraWorkspaceDetector
from ...workspace.environment_contracts import FlextInfraWorkspaceEnvironmentContracts
from .file_plans import FlextInfraCodegenConformFilePlans
from .scaffold_plan import FlextInfraCodegenConformScaffoldPlan


class _ConformPlanRoles:
    if TYPE_CHECKING:
        request: m.Infra.CodegenConformRequest | None
        repository_root: Path
        initial_workspace: m.Infra.WorkspaceSpec | None

        def surface_contract(
            self, surface: c.Infra.CodegenConformSurface
        ) -> m.Infra.CodegenConformSurfaceContract: ...
        def retired_projection_plans(
            self, root: Path, profile: c.Infra.MakeProfile
        ) -> p.Result[t.SequenceOf[m.Infra.CodegenFilePlan]]: ...
        def uv_environment_plan(
            self,
            *,
            root: Path,
            repository_root: Path,
            target: m.Infra.RepositoryConformTarget,
            workspace: m.Infra.WorkspaceSpec,
            config: m.Infra.CodegenConfigSpec,
        ) -> m.Infra.UvEnvironmentPlan: ...
        def _scaffold_python_dirs(
            self,
            entries: t.SequenceOf[p.Infra.TemplateEntrySpec],
            profile: c.Infra.MakeProfile,
        ) -> t.StrSequence: ...
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
        ) -> p.Result[m.Infra.ProjectRenderContext]: ...
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
        ) -> p.Result[str]: ...
        def compose_project_artifact(
            self,
            repository_root: Path,
            destination: str,
            rendered: str,
            *,
            managed_artifacts: m.Infra.ProjectManagedArtifactsSnapshot | None = None,
            workspace: m.Infra.WorkspaceSpec | None = None,
            codegen: m.Infra.CodegenConfigSpec | None = None,
            repository: m.Infra.RepositoryRef | None = None,
            target: m.Infra.RepositoryConformTarget | None = None,
        ) -> p.Result[m.Infra.CodegenArtifactComposition]: ...
        def validate_custom_make(
            self, content: str, policy: m.Infra.CustomHandlerPolicy
        ) -> p.Result[bool]: ...
        def _absent_file_plan(
            self, root: Path, path: Path
        ) -> p.Result[m.Infra.CodegenFilePlan]: ...


class FlextInfraCodegenConformPlan(
    _ConformPlanRoles, FlextInfraCodegenConformScaffoldPlan
):
    """Conformance planning across scaffold and existing repositories."""

    def plan(
        self: p.Infra.CodegenConform, request: m.Infra.CodegenConformRequest
    ) -> p.Result[m.Infra.CodegenPlan]:
        """Build and validate the complete selection without writing."""
        config_spec = config.Infra.codegen
        root = request.root.expanduser().resolve()
        repository_root = root
        workspace = self.initial_workspace
        if workspace is None:
            workspace_result = FlextInfraWorkspaceDetector.load_workspace_spec(
                repository_root
            )
            if workspace_result.failure:
                return r[m.Infra.CodegenPlan].from_failure(workspace_result)
            workspace = workspace_result.value
        current_repository = workspace.repository
        if self.initial_workspace is None:
            current_target_result = FlextInfraWorkspaceDetector.conform_target(
                root, workspace
            )
            if current_target_result.failure:
                return r[m.Infra.CodegenPlan].from_failure(current_target_result)
            current_target = current_target_result.value
            current_repository = current_target.repository
        else:
            current_target = m.Infra.RepositoryConformTarget(
                repository=current_repository,
                root=root,
                make_profile=current_repository.role,
                beads=workspace.beads,
                project=workspace.project,
                canonical_project_name=current_repository.distribution,
                ci_enabled=True,
                gascity_enabled=workspace.gascity_enabled,
                external_dependency_paths=workspace.external_dependency_paths,
            )
        selected_result = self._select_repositories(
            request, workspace, current_repository
        )
        if selected_result.failure:
            return r[m.Infra.CodegenPlan].from_failure(selected_result)
        selected = selected_result.value
        contract = self.surface_contract(c.Infra.CodegenConformSurface(request.what))
        files: list[m.Infra.CodegenFilePlan] = []
        environments: list[m.Infra.UvEnvironmentPlan] = []
        total_repositories = len(selected)
        u.Cli.info(f"stage=plan repositories={total_repositories}")
        for repository_index, repository in enumerate(selected, start=1):
            repository_started = time.monotonic()
            u.Cli.progress(
                repository_index, total_repositories, repository.name, "conform"
            )
            u.Cli.info(
                f"  stage=topology repository={repository.name} "
                f"role={repository.role.value} kind={repository.kind.value}"
            )
            if repository.kind is not c.Infra.ProjectKind.INTERNAL_FLEXT:
                u.Cli.info(
                    f"  stage=skip repository={repository.name} "
                    f"kind={repository.kind.value} is not rewritten by generation"
                )
                continue
            is_current_repository = repository.name == current_target.repository.name
            if is_current_repository:
                repository_root = current_target.root
                if repository_root != root:
                    return r[m.Infra.CodegenPlan].fail(
                        "current conformance target differs from the requested root: "
                        f"{repository_root} != {root}"
                    )
            else:
                # The governing root is the requested checkout, never the
                # previous iteration's member: resolving the second declared
                # repository against the first produced <root>/alpha/beta.
                repository_root_result = self._repository_root(
                    root, workspace, repository
                )
                if repository_root_result.failure:
                    return r[m.Infra.CodegenPlan].from_failure(repository_root_result)
                repository_root = repository_root_result.value
            if repository_root.exists() and not repository_root.is_dir():
                return r[m.Infra.CodegenPlan].fail(
                    f"declared repository path is not a directory: {repository_root}"
                )
            if not repository_root.is_dir() and self.initial_workspace is None:
                return r[m.Infra.CodegenPlan].fail(
                    f"declared repository checkout is missing: {repository_root}"
                )
            if is_current_repository:
                target = current_target
                local_workspace = workspace
            else:
                if repository.path != Path():
                    declared_member = FlextInfraWorkspaceDetector.load_workspace_spec(
                        repository_root
                    )
                    if declared_member.failure:
                        return r[m.Infra.CodegenPlan].from_failure(declared_member)
                    local_repository = repository.model_copy(update={"path": Path()})
                    # The parent owns topology and selection; the member owns its
                    # project metadata, including the runtime dependency profile.
                    local_workspace = m.Infra.WorkspaceSpec(
                        name=repository.name,
                        beads=workspace.beads,
                        repository=local_repository,
                        project=declared_member.value.project,
                    )
                else:
                    local_workspace_result = (
                        FlextInfraWorkspaceDetector.load_workspace_spec(repository_root)
                    )
                    if local_workspace_result.failure:
                        return r[m.Infra.CodegenPlan].from_failure(
                            local_workspace_result
                        )
                    local_workspace = local_workspace_result.value
                target_result = FlextInfraWorkspaceDetector.conform_target(
                    repository_root, local_workspace
                )
                if target_result.failure:
                    return r[m.Infra.CodegenPlan].from_failure(target_result)
                target = target_result.value
                if repository.path != Path():
                    target = target.model_copy(update={"repository": repository})
            if (
                self.initial_workspace is not None
                and repository.name == workspace.repository.name
            ):
                repository_plan = self._plan_scaffold_repository(
                    root=repository_root,
                    repository=target.repository,
                    target=target,
                    workspace=local_workspace,
                    codegen=config_spec,
                    contract=contract,
                )
            else:
                repository_plan = self._plan_existing_repository(
                    root=repository_root,
                    repository_root=repository_root,
                    repository=target.repository,
                    target=target,
                    workspace=local_workspace,
                    codegen=config_spec,
                    contract=contract,
                )
            if repository_plan.failure:
                return r[m.Infra.CodegenPlan].from_failure(repository_plan)
            governed = self._complete_governed_plans(
                repository_root,
                repository_plan.value,
                config_spec,
                contract,
                profile=target.make_profile,
            )
            if governed.failure:
                return r[m.Infra.CodegenPlan].from_failure(governed)
            files.extend(governed.value)
            if contract.complete_governed:
                retired = self.retired_projection_plans(
                    repository_root, target.make_profile
                )
                if retired.failure:
                    return r[m.Infra.CodegenPlan].from_failure(retired)
                governed_paths = {item.path for item in governed.value}
                files.extend(
                    item for item in retired.value if item.path not in governed_paths
                )
            environments.append(
                self.uv_environment_plan(
                    root=repository_root,
                    target=target,
                    workspace=local_workspace,
                    config=config_spec,
                )
            )
            u.Cli.status(
                "conform",
                repository.name,
                result=True,
                elapsed=time.monotonic() - repository_started,
            )
        return r[m.Infra.CodegenPlan].ok(
            m.Infra.CodegenPlan(
                request=request,
                repositories=selected,
                workspace=workspace,
                make_spec=config_spec.make,
                uv_environments=tuple(environments),
                files=tuple(files),
            )
        )

    def _plan_scaffold_repository(
        self,
        *,
        root: Path,
        repository: m.Infra.RepositoryRef,
        target: m.Infra.RepositoryConformTarget,
        workspace: m.Infra.WorkspaceSpec,
        codegen: m.Infra.CodegenConfigSpec,
        contract: m.Infra.CodegenConformSurfaceContract,
    ) -> p.Result[t.SequenceOf[m.Infra.CodegenFilePlan]]:
        """Render the complete scaffold for ``codegen new`` only."""
        project = workspace.project
        if project is None:
            return r[t.SequenceOf[m.Infra.CodegenFilePlan]].fail(
                f"scaffold workspace has no project metadata: {workspace.name}"
            )
        profile = target.make_profile
        pyproject = root / c.Infra.PYPROJECT_FILENAME
        managed_artifacts = u.Infra.empty_snapshot()
        # New and existing repositories share the exact same
        # root-scoped modernizer pipeline, so first generation is a fixed point.
        # A declared subproject consumes the workspace root
        # tooling profile even before the atomic scaffold creates files on disk.
        tooling_root = target.root
        modernizer = FlextInfraPyprojectModernizer(
            repository_root=tooling_root,
            skip_check=True,
            managed_artifacts=managed_artifacts.resolution,
        )
        analysis_exclusions = tuple(
            path.as_posix()
            for path in (
                *target.external_dependency_paths,
                *workspace.external_dependency_paths,
            )
        )
        declared_python_dirs = self._scaffold_python_dirs(
            codegen.templates.entries, profile
        )
        # Why (flext-6itas.4): a scaffold's declared roots are the complete
        # future topology only for a subproject/standalone target; a workspace
        # root aggregates subproject trees it has not declared here.
        declared_python_dirs_are_complete = profile is not c.Infra.MakeProfile.WORKSPACE
        tooling_result = modernizer.resolve_tooling_context(
            project_name=repository.distribution,
            package_name=project.package_name,
            path=pyproject,
            root_modules=project.root_modules,
            root_packages=project.root_packages,
            declared_python_dirs=declared_python_dirs,
            declared_python_dirs_are_complete=declared_python_dirs_are_complete,
            analysis_exclusions=analysis_exclusions,
        )
        if tooling_result.failure:
            return r[t.SequenceOf[m.Infra.CodegenFilePlan]].from_failure(tooling_result)
        context_result = self._project_render_context(
            repository,
            target,
            workspace,
            codegen,
            tooling_runtime=tooling_result.value,
            repository_root=pyproject.parent,
            managed_artifacts=managed_artifacts.resolution,
            use_committed_artifacts=False,
        )
        if context_result.failure:
            return r[t.SequenceOf[m.Infra.CodegenFilePlan]].from_failure(context_result)
        context = context_result.value
        planned: list[m.Infra.CodegenFilePlan] = []
        templates_root = u.Infra.codegen_templates_root(codegen)
        seen_destinations: set[str] = set()
        # One selection and one formatted path govern validation and planning.
        scaffold_entries = tuple(
            (
                entry,
                entry.destination.format(
                    package_name=context.package_name, ns=context.ns
                ),
            )
            for entry in codegen.templates.entries
            if profile in entry.profiles
            and (not entry.requires_release_protocol or repository.publishes_release)
            and (
                contract.destinations is None
                or entry.destination in contract.destinations
            )
        )
        for entry, destination in scaffold_entries:
            source = (templates_root / entry.source).resolve()
            if not source.is_relative_to(templates_root) or not source.is_file():
                return r[t.SequenceOf[m.Infra.CodegenFilePlan]].fail(
                    f"template source is missing or escapes its root: {entry.source}"
                )
            relative = Path(destination)
            if relative.is_absolute() or ".." in relative.parts:
                return r[t.SequenceOf[m.Infra.CodegenFilePlan]].fail(
                    f"template destination escapes repository root: {destination}"
                )
            if destination in seen_destinations:
                return r[t.SequenceOf[m.Infra.CodegenFilePlan]].fail(
                    f"duplicate template destination: {destination}"
                )
            seen_destinations.add(destination)
            path = root / relative
            if path.exists() and not path.is_file():
                return r[t.SequenceOf[m.Infra.CodegenFilePlan]].fail(
                    f"template destination is not a regular file: {path}"
                )
            for parent in path.parents:
                if parent == root:
                    break
                if parent.exists() and not parent.is_dir():
                    return r[t.SequenceOf[m.Infra.CodegenFilePlan]].fail(
                        f"template destination parent is not a directory: {parent}"
                    )
        for entry, destination in scaffold_entries:
            if entry.delegate != "render":
                continue
            if destination == c.Infra.PYPROJECT_FILENAME and not contract.pyproject:
                continue
            if not contract.delegates and destination != c.Infra.PYPROJECT_FILENAME:
                continue
            # Why (flext-l2296 → superseded): same rationale as the managed
            # path above — the generated .envrc Gas City activation reads this
            # marker fail-loudly at direnv load, so a fresh scaffold must seed
            # it (mintable project_id=None) instead of skipping the plan.
            rendered = self._rendered_artifact_source(
                templates_root=templates_root,
                template_relpath=entry.source,
                failure_prefix=f"stage=templates repository={repository.name} ",
                dist=context.dist,
                repository=repository,
                repository_root=root,
                target=target,
                workspace=workspace,
                codegen=codegen,
                destination=destination,
                tooling_runtime=tooling_result.value,
                project_context=context,
                managed_artifacts=managed_artifacts.resolution,
            )
            if rendered.failure:
                return r[t.SequenceOf[m.Infra.CodegenFilePlan]].from_failure(rendered)
            rendered_content = self.compose_project_artifact(
                root,
                destination,
                rendered.value,
                managed_artifacts=managed_artifacts,
                workspace=workspace,
                codegen=codegen,
                repository=repository,
                target=target,
            )
            if rendered_content.failure:
                return r[t.SequenceOf[m.Infra.CodegenFilePlan]].from_failure(
                    rendered_content
                )
            file_plan = FlextInfraCodegenConformFilePlans.file_plan(
                root,
                destination,
                rendered_content.value.rendered,
                source_states=rendered_content.value.source_states,
            )
            if file_plan.failure:
                return r[t.SequenceOf[m.Infra.CodegenFilePlan]].from_failure(file_plan)
            planned.append(file_plan.value)
        return r[t.SequenceOf[m.Infra.CodegenFilePlan]].ok(tuple(planned))

    def _plan_existing_repository(
        self,
        *,
        root: Path,
        repository_root: Path,
        repository: m.Infra.RepositoryRef,
        target: m.Infra.RepositoryConformTarget,
        workspace: m.Infra.WorkspaceSpec,
        codegen: m.Infra.CodegenConfigSpec,
        contract: m.Infra.CodegenConformSurfaceContract,
    ) -> p.Result[t.SequenceOf[m.Infra.CodegenFilePlan]]:
        """Conform every declared managed surface in an existing repository."""
        stage_started = time.monotonic()
        u.Cli.info(f"  stage=pyproject repository={repository.name}")
        pyproject = root / c.Infra.PYPROJECT_FILENAME
        if not pyproject.is_file():
            return r[t.SequenceOf[m.Infra.CodegenFilePlan]].fail(
                f"existing repository has no pyproject.toml: {root}; "
                "scaffold templates are available only through codegen new"
            )
        metadata = u.Infra.read_project_metadata_result(root)
        if metadata.failure:
            return r[t.SequenceOf[m.Infra.CodegenFilePlan]].from_failure(metadata)
        dist = metadata.value.project.name
        if dist != repository.distribution:
            return r[t.SequenceOf[m.Infra.CodegenFilePlan]].fail(
                "PEP 621 project name does not match catalog distribution: "
                f"{dist} != {repository.distribution}"
            )
        managed_artifacts = u.Infra.snapshot_committed_project_managed_artifacts(root)
        if managed_artifacts.failure:
            return r[t.SequenceOf[m.Infra.CodegenFilePlan]].from_failure(
                managed_artifacts
            )
        u.Cli.info(
            f"  stage=managed-artifacts repository={repository.name} "
            f"elapsed={time.monotonic() - stage_started:.2f}s"
        )
        stage_started = time.monotonic()
        modernizer = FlextInfraPyprojectModernizer(
            repository_root=repository_root,
            skip_check=True,
            managed_artifacts=managed_artifacts.value.resolution,
        )
        tooling_context = modernizer.resolve_tooling_context(
            project_name=repository.distribution,
            package_name=metadata.value.package_name,
            path=pyproject,
            root_modules=(
                target.project.root_modules if target.project is not None else ()
            ),
            root_packages=(
                target.project.root_packages if target.project is not None else ()
            ),
            declared_python_dirs=self._scaffold_python_dirs(
                codegen.templates.entries, target.make_profile
            ),
            analysis_exclusions=tuple(
                path.as_posix() for path in target.external_dependency_paths
            ),
        )
        if tooling_context.failure:
            return r[t.SequenceOf[m.Infra.CodegenFilePlan]].from_failure(
                tooling_context
            )
        u.Cli.info(
            f"  stage=tooling-context repository={repository.name} "
            f"elapsed={time.monotonic() - stage_started:.2f}s"
        )
        managed_result = self._plan_existing_templates(
            root=root,
            repository=repository,
            target=target,
            workspace=workspace,
            codegen=codegen,
            tooling_runtime=tooling_context.value,
            contract=contract,
            managed_artifacts=managed_artifacts.value,
        )
        if managed_result.failure:
            return r[t.SequenceOf[m.Infra.CodegenFilePlan]].from_failure(managed_result)
        planned = list(managed_result.value)
        if contract.custom:
            custom_result = self._plan_existing_custom(
                root, codegen, profile=target.make_profile.value
            )
            if custom_result.failure:
                return r[t.SequenceOf[m.Infra.CodegenFilePlan]].from_failure(
                    custom_result
                )
            planned.extend(custom_result.value)
        return r[t.SequenceOf[m.Infra.CodegenFilePlan]].ok(tuple(planned))

    def _plan_existing_templates(
        self,
        *,
        root: Path,
        repository: m.Infra.RepositoryRef,
        target: m.Infra.RepositoryConformTarget,
        workspace: m.Infra.WorkspaceSpec,
        codegen: m.Infra.CodegenConfigSpec,
        tooling_runtime: m.Infra.ToolingRuntimeContext,
        contract: m.Infra.CodegenConformSurfaceContract,
        managed_artifacts: m.Infra.ProjectManagedArtifactsSnapshot,
    ) -> p.Result[t.SequenceOf[m.Infra.CodegenFilePlan]]:
        """Render configured overwrite-owned templates for an existing tree."""
        u.Cli.info(f"  stage=templates repository={repository.name}")
        profile = target.make_profile
        templates_root = u.Infra.codegen_templates_root(codegen)
        planned: list[m.Infra.CodegenFilePlan] = []
        for managed in codegen.managed_files:
            if not target.ci_enabled and managed.path.parts[:2] == (
                ".github",
                "workflows",
            ):
                continue
            if (
                contract.destinations is not None
                and managed.path.as_posix() not in contract.destinations
            ):
                continue
            pyproject_skipped = managed.path == Path(c.Infra.PYPROJECT_FILENAME) and (
                not contract.pyproject
                or (
                    workspace.project is None
                    and profile is c.Infra.MakeProfile.WORKSPACE
                )
            )
            if managed.path == Path(c.Infra.CUSTOM_MAKE_FILENAME) or pyproject_skipped:
                continue
            entries = tuple(
                entry
                for entry in codegen.templates.entries
                if entry.destination == managed.path.as_posix()
                and entry.delegate == "render"
            )
            if not entries:
                continue
            if len(entries) != 1:
                return r[t.SequenceOf[m.Infra.CodegenFilePlan]].fail(
                    f"managed file requires exactly one render template: {managed.path}"
                )
            entry = entries[0]
            relative = Path(entry.destination)
            if relative.is_absolute() or ".." in relative.parts:
                return r[t.SequenceOf[m.Infra.CodegenFilePlan]].fail(
                    f"managed destination escapes repository root: {entry.destination}"
                )
            path = (root / relative).resolve()
            # Why (flext-l2296): the ledger metadata is minted by Beads at
            # first use, so a fresh clone legitimately lacks it. Planning an
            # absent runtime artifact made the gen check gate fail on every
            # clean checkout. When the file exists, the identity-preserving
            # refresh below still applies.
            if (
                entry.destination == c.Infra.BEADS_METADATA_RELPATH
                and not path.is_file()
            ):
                continue
            try:
                path.relative_to(root.resolve())
            except ValueError:
                return r[t.SequenceOf[m.Infra.CodegenFilePlan]].fail(
                    f"managed destination escapes repository root: {entry.destination}"
                )
            if profile not in entry.profiles or (
                entry.requires_release_protocol and not target.publishes_release
            ):
                # Profile- and capability-excluded workflows must not keep firing.
                # Conform, rather than a user, retires the generated orphan.
                if (
                    managed.path.parts[:2] == (".github", "workflows")
                    and path.is_file()
                ):
                    # Keep the typed read result distinct from its string payload.
                    orphan_read = u.Cli.files_read_text(path)
                    if orphan_read.failure:
                        return r[t.SequenceOf[m.Infra.CodegenFilePlan]].from_failure(
                            orphan_read
                        )
                    absent_plan = self._absent_file_plan(root, path)
                    if absent_plan.failure:
                        return r[t.SequenceOf[m.Infra.CodegenFilePlan]].from_failure(
                            absent_plan
                        )
                    planned.append(
                        absent_plan.value.model_copy(
                            update={"owner": managed.owner, "policy": managed.policy}
                        )
                    )
                continue
            rendered = self._rendered_artifact_source(
                templates_root=templates_root,
                template_relpath=entry.source,
                failure_prefix="",
                dist=repository.distribution,
                repository=repository,
                repository_root=root,
                target=target,
                workspace=workspace,
                codegen=codegen,
                destination=entry.destination,
                tooling_runtime=tooling_runtime,
                project_context=None,
                managed_artifacts=managed_artifacts.resolution,
            )
            if rendered.failure:
                return r[t.SequenceOf[m.Infra.CodegenFilePlan]].from_failure(rendered)
            rendered_content = rendered.value
            composed = self.compose_project_artifact(
                root,
                entry.destination,
                rendered_content,
                managed_artifacts=managed_artifacts,
                workspace=workspace,
                codegen=codegen,
                repository=repository,
                target=target,
            )
            if composed.failure:
                return r[t.SequenceOf[m.Infra.CodegenFilePlan]].from_failure(composed)
            rendered_content = composed.value.rendered
            conflict_marker = u.Infra.first_merge_conflict_marker(rendered_content)
            if conflict_marker is not None:
                return r[t.SequenceOf[m.Infra.CodegenFilePlan]].fail(
                    "rendered template contains a merge conflict marker: "
                    f"source={entry.source}; target={path}; root={root}; "
                    f"marker={conflict_marker}"
                )
            file_plan = FlextInfraCodegenConformFilePlans.file_plan(
                root,
                entry.destination,
                rendered_content,
                mode=managed.mode,
                source_states=composed.value.source_states,
            )
            if file_plan.failure:
                return r[t.SequenceOf[m.Infra.CodegenFilePlan]].from_failure(file_plan)
            planned.append(file_plan.value)
        return r[t.SequenceOf[m.Infra.CodegenFilePlan]].ok(tuple(planned))

    def _plan_existing_custom(
        self,
        root: Path,
        config: m.Infra.CodegenConfigSpec,
        *,
        profile: str | None = None,
    ) -> p.Result[t.SequenceOf[m.Infra.CodegenFilePlan]]:
        """Validate the handwritten Make surface against its profile contract."""
        policy = config.make.custom_handler_policies.get(
            profile or "", config.make.custom_handler_policy
        )
        path = root / policy.filename
        if path.exists() and not path.is_file():
            return r[t.SequenceOf[m.Infra.CodegenFilePlan]].fail(
                f"custom Make destination is not a regular file: {path}"
            )
        plans: list[m.Infra.CodegenFilePlan] = []
        if path.is_file():
            read = u.Cli.files_read_text(path)
            if read.failure:
                return r[t.SequenceOf[m.Infra.CodegenFilePlan]].from_failure(read)
            validation = self.validate_custom_make(read.value, policy)
            if validation.failure:
                return r[t.SequenceOf[m.Infra.CodegenFilePlan]].from_failure(validation)
            planned = FlextInfraCodegenConformFilePlans.file_plan(
                root, policy.filename, read.value
            )
            if planned.failure:
                return r[t.SequenceOf[m.Infra.CodegenFilePlan]].from_failure(planned)
            plans.append(planned.value)
        layout = u.Infra.layout(root)
        if layout is not None and layout.class_stem:
            families: tuple[Literal["u", "p"], ...] = ("u", "p")
            for family in families:
                rendered = u.Infra.render_utility_facade(
                    layout.package_dir, family=family
                )
                if rendered is None:
                    continue
                relative = (
                    layout.package_dir
                    / (c.Infra.FAMILY_PUBLIC_MODULES[family] + c.Infra.EXT_PYTHON)
                ).relative_to(root)
                utility_plan = FlextInfraCodegenConformFilePlans.file_plan(
                    root, relative.as_posix(), rendered
                )
                if utility_plan.failure:
                    return r[t.SequenceOf[m.Infra.CodegenFilePlan]].from_failure(
                        utility_plan
                    )
                plans.append(utility_plan.value)
        return r[t.SequenceOf[m.Infra.CodegenFilePlan]].ok(tuple(plans))

    @staticmethod
    def _complete_governed_plans(
        root: Path,
        planned: t.SequenceOf[m.Infra.CodegenFilePlan],
        codegen: m.Infra.CodegenConfigSpec,
        contract: m.Infra.CodegenConformSurfaceContract,
        *,
        profile: c.Infra.MakeProfile,
    ) -> p.Result[t.SequenceOf[m.Infra.CodegenFilePlan]]:
        """Attach ownership metadata and represent every governed root artifact.

        Only the ``ALL`` surface completes the full governed set; the
        pyproject-scoped surfaces (``DEPENDENCIES``/``PYPROJECT``) keep the plan
        restricted to what their own planners already produced.
        """
        governed_by_path = {item.path: item for item in codegen.managed_files}
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
                }
            )
            if relative in represented_indexes:
                completed[represented_indexes[relative]] = governed_file
            else:
                represented_indexes[relative] = len(completed)
                completed.append(governed_file)
        if not contract.complete_governed:
            return r[t.SequenceOf[m.Infra.CodegenFilePlan]].ok(tuple(completed))
        for relative, governed in governed_by_path.items():
            if relative in represented:
                continue
            path = root / relative
            if path.exists() and not path.is_file():
                return r[t.SequenceOf[m.Infra.CodegenFilePlan]].fail(
                    f"governed artifact is not a regular file: {path}"
                )
            entry_profiles = tuple(
                entry.profiles
                for entry in codegen.templates.entries
                if entry.destination == relative.as_posix()
            )
            if entry_profiles:
                allowed = {item for profiles in entry_profiles for item in profiles}
                if profile not in allowed:
                    continue
            if not path.exists():
                continue
            current = ""
            if path.is_file():
                read = u.Cli.files_read_text(path)
                if read.failure:
                    return r[t.SequenceOf[m.Infra.CodegenFilePlan]].from_failure(read)
                current = read.value
            if (
                governed.policy == "merge"
                and governed.owner == c.Infra.CODEGEN_OWNER_VSCODE
            ):
                # Owner-merge dispatch: owners with a canonical document merge
                # (vscode settings today) produce their rendered content here.
                merged = FlextInfraCodegen.render_vscode_settings(root)
                if merged.failure:
                    return r[t.SequenceOf[m.Infra.CodegenFilePlan]].from_failure(merged)
                if merged.value != current:
                    merged_plan = FlextInfraCodegenConformFilePlans.file_plan(
                        root, relative.as_posix(), merged.value, mode=governed.mode
                    )
                    if merged_plan.failure:
                        return r[t.SequenceOf[m.Infra.CodegenFilePlan]].from_failure(
                            merged_plan
                        )
                    completed.append(
                        merged_plan.value.model_copy(
                            update={"owner": governed.owner, "policy": governed.policy}
                        )
                    )
                    continue
            if (
                governed.policy == "merge"
                and relative.as_posix() == c.Infra.ENVRC_LOCAL_RELPATH
            ):
                # Local overrides never carry generated content: the merge
                # strips stale generated sections and deletes the file when
                # nothing custom remains, so `.envrc` stays the single
                # beads activation owner.
                normalized = (
                    FlextInfraWorkspaceEnvironmentContracts.envrc_local_normalized(
                        current
                    )
                )
                if normalized == current:
                    current_plan = FlextInfraCodegenConformFilePlans.file_plan(
                        root, relative.as_posix(), current, mode=governed.mode
                    )
                    if current_plan.failure:
                        return r[t.SequenceOf[m.Infra.CodegenFilePlan]].from_failure(
                            current_plan
                        )
                    completed.append(
                        current_plan.value.model_copy(
                            update={"owner": governed.owner, "policy": governed.policy}
                        )
                    )
                    continue
                if not normalized:
                    before = u.Cli.atomic_read_binary_file_state(path, required=False)
                    if before.failure:
                        return r[t.SequenceOf[m.Infra.CodegenFilePlan]].from_failure(
                            before
                        )
                    completed.append(
                        m.Infra.CodegenFilePlan(
                            project=root,
                            path=path,
                            before=before.value,
                            desired_content=None,
                            desired_mode=None,
                            owner=governed.owner,
                            policy=governed.policy,
                        )
                    )
                    continue
                merged_plan = FlextInfraCodegenConformFilePlans.file_plan(
                    root, relative.as_posix(), normalized, mode=governed.mode
                )
                if merged_plan.failure:
                    return r[t.SequenceOf[m.Infra.CodegenFilePlan]].from_failure(
                        merged_plan
                    )
                completed.append(
                    merged_plan.value.model_copy(
                        update={"owner": governed.owner, "policy": governed.policy}
                    )
                )
                continue
            current_plan = FlextInfraCodegenConformFilePlans.file_plan(
                root, relative.as_posix(), current, mode=governed.mode
            )
            if current_plan.failure:
                return r[t.SequenceOf[m.Infra.CodegenFilePlan]].from_failure(
                    current_plan
                )
            completed.append(
                current_plan.value.model_copy(
                    update={"owner": governed.owner, "policy": governed.policy}
                )
            )
        return r[t.SequenceOf[m.Infra.CodegenFilePlan]].ok(tuple(completed))

    @staticmethod
    @staticmethod
    def _select_repositories(
        request: m.Infra.CodegenConformRequest,
        workspace: m.Infra.WorkspaceSpec,
        current_repository: m.Infra.RepositoryRef,
    ) -> p.Result[t.VariadicTuple[m.Infra.RepositoryRef]]:
        """Resolve self/subprojects/all from the local read-only topology."""
        scope = c.Infra.CodegenConformScope(request.scope)
        if scope is c.Infra.CodegenConformScope.SELF:
            selected = (current_repository,)
        elif scope is c.Infra.CodegenConformScope.DECLARED:
            if not workspace.subprojects:
                return r[t.VariadicTuple[m.Infra.RepositoryRef]].fail(
                    "subprojects scope requires local .gitmodules entries"
                )
            selected = tuple(workspace.subprojects)
        else:
            selected = (workspace.repository, *workspace.subprojects)
        mutable = tuple(
            repository
            for repository in selected
            if repository.codegen is not c.Infra.CodegenKind.NONE
            and not repository.read_only
        )
        if not mutable:
            return r[t.VariadicTuple[m.Infra.RepositoryRef]].fail(
                "selected repositories do not permit code generation"
            )
        return r[t.VariadicTuple[m.Infra.RepositoryRef]].ok(mutable)

    @staticmethod
    def _repository_root(
        root: Path, workspace: p.Infra.WorkspaceSpec, repository: p.Infra.RepositoryRef
    ) -> p.Result[Path]:
        """Resolve one declared checkout without escaping its workspace owner."""
        if repository.name == workspace.repository.name:
            return r[Path].ok(root)
        resolved_root = root.resolve()
        resolved: Path = (resolved_root / repository.path).resolve()
        if not resolved.is_relative_to(resolved_root):
            return r[Path].fail(
                "declared repository path escapes workspace root: "
                f"{repository.path.as_posix()}"
            )
        return r[Path].ok(resolved)

    @staticmethod
    def _repository_root_rel(workspace: m.Infra.WorkspaceSpec) -> str:
        """Return the environment root owned by the inferred target."""
        if workspace.project is not None:
            project_root_rel: str = workspace.project.repository_root_rel
            return project_root_rel
        return "."

    @staticmethod
    @override
    def _repository_provider(
        repository: m.Infra.RepositoryRef,
    ) -> p.Result[m.Infra.ProviderIdentitySpec]:
        """Resolve one repository to its self-declared provider identity."""
        return u.Infra.repository_provider(repository)
