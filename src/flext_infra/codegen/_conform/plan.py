"""Conformance plan selection and repository topology resolution."""

from __future__ import annotations

import time
from pathlib import Path
from typing import TYPE_CHECKING, Literal, override

from flext_core import r

from ... import c, config, m, p, t, u
from ...workspace import FlextInfraWorkspaceDetector
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
        @classmethod
        def retired_projection_plans(
            cls, root: Path, profile: c.Infra.MakeProfile
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
        @classmethod
        def compose_project_artifact(
            cls,
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
        @staticmethod
        def validate_custom_make(
            content: str, policy: m.Infra.CustomHandlerPolicy
        ) -> p.Result[bool]: ...
        def _absent_file_plan(
            self, root: Path, path: Path
        ) -> p.Result[m.Infra.CodegenFilePlan]: ...


class FlextInfraCodegenConformPlan(FlextInfraCodegenConformScaffoldPlan):
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
                    # project metadata, including the runtime dependency profile
                    # and the namespace production scope it declares.
                    local_workspace = m.Infra.WorkspaceSpec(
                        name=repository.name,
                        beads=workspace.beads,
                        repository=local_repository,
                        project=declared_member.value.project,
                        namespace_scan_dirs=(declared_member.value.namespace_scan_dirs),
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

    @override
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

    @override
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

    @override
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
