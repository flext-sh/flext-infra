"""Unified, fail-closed conformance for new and existing repositories.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import TYPE_CHECKING, Annotated, override

from flext_core import r
from flext_infra import config
from flext_infra.base import s
from flext_infra.constants import c
from flext_infra.deps.modernizer import FlextInfraPyprojectModernizer
from flext_infra.models import m
from flext_infra.typings import t
from flext_infra.utilities import u
from flext_infra.workspace.detector import FlextInfraWorkspaceDetector

if TYPE_CHECKING:
    from flext_infra.protocols import p


class FlextInfraCodegenConform(s[m.Infra.CodegenResult]):
    """Plan every selected output, then atomically write only a clean plan."""

    # NOTE (multi-agent, mro-wkii.17 / agent: codex): this is the only
    # orchestrator for Make/toolchain/source conformance. Rendering stays in
    # flext-cli; Git-source TOML policy and attached detection are composed from
    # their separately owned u.Infra/workspace services.
    request: Annotated[
        m.Infra.CodegenConformRequest | None,
        m.Field(default=None, exclude=True, description="Validated conform request"),
    ] = None
    initial_workspace: Annotated[
        m.Infra.WorkspaceSpec | None,
        m.Field(
            default=None,
            exclude=True,
            description="Validated initial manifest included in the atomic plan",
        ),
    ] = None

    @classmethod
    def execute_request(
        cls,
        request: m.Infra.CodegenConformRequest,
        initial_workspace: m.Infra.WorkspaceSpec | None = None,
    ) -> p.Result[m.Infra.CodegenResult]:
        """Execute one already validated public CLI request."""
        service = cls(
            workspace_root=request.root.expanduser().resolve(),
            request=request,
            initial_workspace=initial_workspace,
        )
        return service.execute()

    @override
    def execute(self) -> p.Result[m.Infra.CodegenResult]:
        """Run check or apply and require a verified fixed point."""
        request = self.request or m.Infra.CodegenConformRequest(
            root=self.workspace_root
        )
        planned = self.plan(request)
        if planned.failure:
            return r[m.Infra.CodegenResult].fail(
                planned.error or "codegen conform planning failed"
            )
        plan = planned.value
        blocked = tuple(file for file in plan.files if file.blocked)
        if blocked:
            details = "; ".join(
                f"{file.path}: {file.reason or 'managed WIP'}" for file in blocked
            )
            return r[m.Infra.CodegenResult].fail(
                f"codegen conform blocked before writes: {details}"
            )
        changed = tuple(file for file in plan.files if file.changed)
        mode = c.Infra.CodegenConformMode(request.mode)
        if mode is c.Infra.CodegenConformMode.CHECK:
            if changed:
                paths = ", ".join(str(file.path) for file in changed)
                return r[m.Infra.CodegenResult].fail(f"codegen drift detected: {paths}")
            return r[m.Infra.CodegenResult].ok(m.Infra.CodegenResult(plan=plan))
        written: list[Path] = []
        for file in changed:
            result = self._apply_file_plan(file)
            if result.failure:
                return r[m.Infra.CodegenResult].fail(
                    result.error or f"atomic codegen operation failed: {file.path}"
                )
            written.append(file.path)
        verified = self.plan(request)
        if verified.failure:
            return r[m.Infra.CodegenResult].fail(
                verified.error or "post-apply conform verification failed"
            )
        verified_plan = verified.value
        residual = tuple(file for file in verified_plan.files if file.changed)
        if residual:
            paths = ", ".join(str(file.path) for file in residual)
            return r[m.Infra.CodegenResult].fail(
                f"codegen apply did not reach a fixed point: {paths}"
            )
        return r[m.Infra.CodegenResult].ok(
            m.Infra.CodegenResult(plan=verified_plan, written_files=tuple(written))
        )

    def plan(
        self, request: m.Infra.CodegenConformRequest
    ) -> p.Result[m.Infra.CodegenPlan]:
        """Build and validate the complete selection without writing."""
        config_spec = config.Infra.codegen
        root = request.root.expanduser().resolve()
        workspace_root = root
        workspace = self.initial_workspace
        if workspace is None:
            workspace_root_result = FlextInfraWorkspaceDetector.resolve_workspace_root(
                root
            )
            if workspace_root_result.failure:
                return r[m.Infra.CodegenPlan].fail(
                    workspace_root_result.error or "workspace root resolution failed"
                )
            workspace_root = workspace_root_result.value
            workspace_result = FlextInfraWorkspaceDetector.load_workspace_spec(
                workspace_root
            )
            if workspace_result.failure:
                return r[m.Infra.CodegenPlan].fail(
                    workspace_result.error or "workspace manifest load failed"
                )
            workspace = workspace_result.value
        catalog_result = self._validate_workspace_catalog(config_spec, workspace)
        if catalog_result.failure:
            return r[m.Infra.CodegenPlan].fail(
                catalog_result.error or "workspace catalog validation failed"
            )
        current_repository = workspace.repository
        if root != workspace_root:
            try:
                current_path = root.relative_to(workspace_root).as_posix()
            except ValueError as exc:
                return r[m.Infra.CodegenPlan].fail_op(
                    "repository workspace resolution", exc
                )
            current_matches = tuple(
                repository
                for repository in workspace.members
                if repository.path.as_posix() == current_path
            )
            if len(current_matches) != 1:
                return r[m.Infra.CodegenPlan].fail(
                    f"repository is not one declared workspace member: {current_path}"
                )
            current_repository = current_matches[0]
        selected_result = self._select_repositories(
            request, workspace, current_repository
        )
        if selected_result.failure:
            return r[m.Infra.CodegenPlan].fail(
                selected_result.error or "repository selection failed"
            )
        selected = selected_result.value
        files: list[m.Infra.CodegenFilePlan] = []
        environments: list[m.Infra.UvEnvironmentPlan] = []
        for repository in selected:
            repository_root = self._repository_root(
                workspace_root, workspace, repository
            )
            if repository_root.exists() and not repository_root.is_dir():
                return r[m.Infra.CodegenPlan].fail(
                    f"declared repository path is not a directory: {repository_root}"
                )
            if not repository_root.is_dir() and self.initial_workspace is None:
                return r[m.Infra.CodegenPlan].fail(
                    f"declared repository checkout is missing: {repository_root}"
                )
            # mro-wkii.17.26 (codex): parent topology and selected repository
            # jointly own attached-member conformance; no local manifest is needed.
            # mro-j47u (codex): existing repositories cannot reach the scaffold
            # catalog. Project creation is the only template-rendering lifecycle.
            if (
                self.initial_workspace is not None
                and repository.name == workspace.repository.name
            ):
                repository_plan = self._plan_scaffold_repository(
                    root=repository_root,
                    repository=repository,
                    workspace=workspace,
                    codegen=config_spec,
                )
            else:
                repository_plan = self._plan_existing_repository(
                    root=repository_root,
                    repository=repository,
                    workspace_root=workspace_root,
                    repository=repository,
                    workspace=workspace,
                    codegen=config_spec,
                )
            if repository_plan.failure:
                return r[m.Infra.CodegenPlan].fail(
                    repository_plan.error
                    or f"repository planning failed: {repository_root}"
                )
            files.extend(repository_plan.value)
            environments.append(
                self._uv_environment_plan(
                    root=repository_root,
                    workspace_root=workspace_root,
                    repository=repository,
                    workspace=workspace,
                    config=config_spec,
                )
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

    @staticmethod
    def _package_root() -> Path:
        """Return the installed flext-infra package root."""
        return Path(__file__).resolve().parent.parent

    @staticmethod
    def _validate_workspace_catalog(
        config: m.Infra.CodegenConfigSpec, workspace: m.Infra.WorkspaceSpec
    ) -> p.Result[bool]:
        """Require declared fleet members to match their global Git contracts."""
        local_refs = (workspace.repository, *workspace.members, *workspace.content_only)
        for local in local_refs:
            known = next(
                (item for item in config.repositories if item.name == local.name), None
            )
            if known is None:
                if local is workspace.repository and not workspace.members:
                    continue
                return r[bool].fail(
                    f"repository is not classified in codegen catalog: {local.name}"
                )
            local_payload = local.model_dump(mode="json")
            known_payload = known.model_dump(mode="json")
            if local_payload != known_payload:
                return r[bool].fail(
                    f"workspace repository differs from catalog: {local.name}"
                )
        return r[bool].ok(True)

    @staticmethod
    def _select_repositories(
        request: m.Infra.CodegenConformRequest,
        workspace: m.Infra.WorkspaceSpec,
        current_repository: m.Infra.RepositoryRef,
    ) -> p.Result[tuple[m.Infra.RepositoryRef, ...]]:
        """Resolve self/members/all from the governing topology manifest."""
        scope = c.Infra.CodegenConformScope(request.scope)
        if scope is c.Infra.CodegenConformScope.SELF:
            return r[tuple[m.Infra.RepositoryRef, ...]].ok((current_repository,))
        if scope is c.Infra.CodegenConformScope.MEMBERS:
            if not workspace.members:
                return r[tuple[m.Infra.RepositoryRef, ...]].fail(
                    "members scope requires a workspace-root manifest"
                )
            return r[tuple[m.Infra.RepositoryRef, ...]].ok(tuple(workspace.members))
        return r[tuple[m.Infra.RepositoryRef, ...]].ok((
            workspace.repository,
            *workspace.members,
        ))

    @staticmethod
    def _repository_root(
        root: Path, workspace: p.Infra.WorkspaceSpec, repository: p.Infra.RepositoryRef
    ) -> Path:
        """Resolve one selected checkout without sibling discovery."""
        if repository.name == workspace.repository.name:
            return root
        return (root / repository.path).resolve()

    def _plan_scaffold_repository(
        self,
        *,
        root: Path,
        repository: m.Infra.RepositoryRef,
        workspace: m.Infra.WorkspaceSpec,
        codegen: m.Infra.CodegenConfigSpec,
    ) -> p.Result[t.SequenceOf[m.Infra.CodegenFilePlan]]:
        """Render the complete scaffold for ``codegen new`` only."""
        if repository.profile is None:
            return r[t.SequenceOf[m.Infra.CodegenFilePlan]].fail(
                f"active repository has no Make profile: {repository.name}"
            )
        project = workspace.project
        if project is None:
            return r[t.SequenceOf[m.Infra.CodegenFilePlan]].fail(
                f"scaffold workspace has no project metadata: {workspace.name}"
            )
        profile = c.Infra.MakeProfile(repository.profile)
        pyproject = root / c.Infra.PYPROJECT_FILENAME
        # mro-j47u (codex): new and existing repositories share the exact same
        # root-scoped modernizer pipeline, so first generation is a fixed point.
        # NOTE(mro-p68a.5, agent codex): a declared member consumes its parent
        # tooling profile even before the atomic scaffold creates files on disk.
        tooling_root = (
            root.parent if profile is c.Infra.MakeProfile.WORKSPACE_MEMBER else root
        )
        modernizer = FlextInfraPyprojectModernizer(
            workspace_root=tooling_root, skip_check=True
        )
        tooling_result = modernizer.resolve_tooling_context(
            project_name=repository.distribution,
            package_name=project.package_name,
            path=pyproject,
            declared_python_dirs=(
                config.Infra.tooling.tools.pyright.path_rules.source_dir,
            ),
        )
        if tooling_result.failure:
            return r[t.SequenceOf[m.Infra.CodegenFilePlan]].fail(
                tooling_result.error or f"tooling render failed: {pyproject}"
            )
        context_result = self._render_context(
            repository, workspace, codegen, tooling_runtime=tooling_result.value
        )
        if context_result.failure:
            return r[t.SequenceOf[m.Infra.CodegenFilePlan]].fail(
                context_result.error or "project render context is invalid"
            )
        context = context_result.value
        planned: list[m.Infra.CodegenFilePlan] = []
        templates_root = (
            u.Infra.resource_root("templates") / codegen.templates.root
        ).resolve()
        seen_destinations: set[str] = set()
        for entry in codegen.templates.entries:
            if profile not in entry.profiles:
                continue
            source = (templates_root / entry.source).resolve()
            if not source.is_relative_to(templates_root) or not source.is_file():
                return r[t.SequenceOf[m.Infra.CodegenFilePlan]].fail(
                    f"template source is missing or escapes its root: {entry.source}"
                )
            destination = entry.destination.format(
                package_name=context.package_name, ns=context.ns
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
        for entry in codegen.templates.entries:
            if profile not in entry.profiles:
                continue
            # mro-i6nq.10: One formatted path governs validation and planning.
            destination = entry.destination.format(
                package_name=context.package_name, ns=context.ns
            )
            if entry.delegate == "manifest":
                # NOTE (multi-agent, mro-wkii.17 / agent: uv_overlay_owner):
                # template rendering retains the canonical context instance.
                rendered_manifest = u.Cli.template_render(
                    templates_root / entry.source, context
                )
                if rendered_manifest.failure:
                    return r[t.SequenceOf[m.Infra.CodegenFilePlan]].fail(
                        rendered_manifest.error
                        or f"manifest render failed: {entry.source}"
                    )
                manifest_validation = self._validate_initial_manifest(
                    rendered_manifest.value, workspace
                )
                if manifest_validation.failure:
                    return r[t.SequenceOf[m.Infra.CodegenFilePlan]].fail(
                        manifest_validation.error
                        or "initial workspace manifest validation failed"
                    )
                manifest_plan = self._file_plan(
                    root, destination, rendered_manifest.value, block_existing=True
                )
                if manifest_plan.failure:
                    return r[t.SequenceOf[m.Infra.CodegenFilePlan]].fail(
                        manifest_plan.error or "workspace manifest planning failed"
                    )
                planned.append(manifest_plan.value)
                continue
            if entry.delegate != "render":
                continue
            if destination == c.Infra.PYPROJECT_FILENAME:
                continue
            rendered = u.Cli.template_render(templates_root / entry.source, context)
            if rendered.failure:
                return r[t.SequenceOf[m.Infra.CodegenFilePlan]].fail(
                    rendered.error or f"template render failed: {entry.source}"
                )
            file_plan = self._file_plan(
                root, destination, rendered.value, block_existing=True
            )
            if file_plan.failure:
                return r[t.SequenceOf[m.Infra.CodegenFilePlan]].fail(
                    file_plan.error
                    or f"managed file planning failed: {entry.destination}"
                )
            planned.append(file_plan.value)
        pyproject_entry = next(
            (
                item
                for item in codegen.templates.entries
                if item.destination == c.Infra.PYPROJECT_FILENAME
                and profile in item.profiles
                and item.delegate == "render"
            ),
            None,
        )
        if pyproject_entry is None:
            return r[t.SequenceOf[m.Infra.CodegenFilePlan]].fail(
                "pyproject template is missing from codegen configuration"
            )
        pyproject_render = u.Cli.template_render(
            templates_root / pyproject_entry.source, context
        )
        if pyproject_render.failure:
            return r[t.SequenceOf[m.Infra.CodegenFilePlan]].fail(
                pyproject_render.error or "pyproject template render failed"
            )
        initial_tooling = modernizer.conform_source(
            pyproject_render.value,
            path=pyproject,
            declared_python_dirs=(
                config.Infra.tooling.tools.pyright.path_rules.source_dir,
            ),
        )
        if initial_tooling.failure:
            return r[t.SequenceOf[m.Infra.CodegenFilePlan]].fail(
                initial_tooling.error or f"initial tooling conform failed: {pyproject}"
            )
        prepared_result = u.Infra.pyproject_conform(
            initial_tooling.value,
            repositories=codegen.repositories,
            workspace=workspace,
            toolchain=codegen.toolchain,
        )
        if prepared_result.failure:
            return r[t.SequenceOf[m.Infra.CodegenFilePlan]].fail(
                prepared_result.error or f"pyproject prepare failed: {pyproject}"
            )
        final_tooling = modernizer.conform_source(
            prepared_result.value,
            path=pyproject,
            declared_python_dirs=(
                config.Infra.tooling.tools.pyright.path_rules.source_dir,
            ),
        )
        if final_tooling.failure:
            return r[t.SequenceOf[m.Infra.CodegenFilePlan]].fail(
                final_tooling.error or f"final tooling conform failed: {pyproject}"
            )
        pyproject_result = u.Infra.pyproject_conform(
            final_tooling.value,
            repositories=codegen.repositories,
            workspace=workspace,
            toolchain=codegen.toolchain,
            build=codegen.scaffold.build,
            resources=(*codegen.scaffold.resources, *context.project_resources),
            project_root=root,
            package_name=context.package_name,
            allow_missing_required=True,
        )
        if pyproject_result.failure:
            return r[t.SequenceOf[m.Infra.CodegenFilePlan]].fail(
                pyproject_result.error or f"pyproject conform failed: {pyproject}"
            )
        pyproject_plan = self._file_plan(
            root,
            c.Infra.PYPROJECT_FILENAME,
            pyproject_result.value,
            block_existing=True,
        )
        if pyproject_plan.failure:
            return r[t.SequenceOf[m.Infra.CodegenFilePlan]].fail(
                pyproject_plan.error or f"pyproject planning failed: {pyproject}"
            )
        planned.append(pyproject_plan.value)
        return r[t.SequenceOf[m.Infra.CodegenFilePlan]].ok(tuple(planned))

    def _plan_existing_repository(
        self,
        *,
        root: Path,
        repository: m.Infra.RepositoryRef,
        workspace_root: Path,
        repository: m.Infra.RepositoryRef,
        workspace: m.Infra.WorkspaceSpec,
        codegen: m.Infra.CodegenConfigSpec,
    ) -> p.Result[t.SequenceOf[m.Infra.CodegenFilePlan]]:
        """Conform every declared managed surface in an existing repository."""
        pyproject = root / c.Infra.PYPROJECT_FILENAME
        if not pyproject.is_file():
            return r[t.SequenceOf[m.Infra.CodegenFilePlan]].fail(
                f"existing repository has no pyproject.toml: {root}; "
                "scaffold templates are available only through codegen new"
            )
        pyproject_read = u.Cli.files_read_text(pyproject)
        if pyproject_read.failure:
            return r[t.SequenceOf[m.Infra.CodegenFilePlan]].fail(
                pyproject_read.error or f"pyproject read failed: {pyproject}"
            )
        package_name = repository.distribution.replace("-", "_")
        project_resources = (
            workspace.project.resources
            if workspace.project is not None
            and repository.name == workspace.repository.name
            else ()
        )
        resources = (*config.scaffold.resources, *project_resources)
        prepared_result = u.Infra.pyproject_conform(
            pyproject_read.value,
            repositories=codegen.repositories,
            workspace=workspace,
            toolchain=config.toolchain,
            build=config.scaffold.build,
            resources=resources,
            project_root=root,
            package_name=package_name,
        )
        if prepared_result.failure:
            return r[t.SequenceOf[m.Infra.CodegenFilePlan]].fail(
                prepared_result.error or f"pyproject preparation failed: {pyproject}"
            )
        modernizer = FlextInfraPyprojectModernizer(
            workspace_root=workspace_root, skip_check=True
        )
        tooling_context = modernizer.resolve_tooling_context(
            project_name=repository.distribution,
            package_name=u.Infra.project_package_name(root),
            path=pyproject,
            declared_python_dirs=(
                config.Infra.tooling.tools.pyright.path_rules.source_dir,
            ),
        )
        if tooling_context.failure:
            return r[t.SequenceOf[m.Infra.CodegenFilePlan]].fail(
                tooling_context.error or f"tooling render failed: {pyproject}"
            )
        # NOTE (multi-agent, mro-45r9): dependency-derived tooling consumes the
        # canonical groups first; the final pass restores the Git-source contract.
        tooling_result = modernizer.conform_source(
            prepared_result.value, path=pyproject
        )
        if tooling_result.failure:
            return r[t.SequenceOf[m.Infra.CodegenFilePlan]].fail(
                tooling_result.error or f"tooling conform failed: {pyproject}"
            )
        resource_plans = self._resource_move_plans(
            root, package_name=package_name, resources=resources
        )
        if resource_plans.failure:
            return r[t.SequenceOf[m.Infra.CodegenFilePlan]].fail(
                resource_plans.error or f"resource layout planning failed: {root}"
            )
        pyproject_result = u.Infra.pyproject_conform(
            tooling_result.value,
            repositories=codegen.repositories,
            workspace=workspace,
            toolchain=config.toolchain,
            build=config.scaffold.build,
            resources=resources,
            project_root=root,
            package_name=package_name,
        )
        if pyproject_result.failure:
            return r[t.SequenceOf[m.Infra.CodegenFilePlan]].fail(
                pyproject_result.error or f"pyproject conform failed: {pyproject}"
            )
        pyproject_plan = self._file_plan(
            root, c.Infra.PYPROJECT_FILENAME, pyproject_result.value
        )
        if pyproject_plan.failure:
            return r[t.SequenceOf[m.Infra.CodegenFilePlan]].fail(
                pyproject_plan.error or f"pyproject planning failed: {pyproject}"
            )
        planned = [*resource_plans.value, pyproject_plan.value]
        custom_result = self._plan_existing_custom(root, config)
        if custom_result.failure:
            return r[t.SequenceOf[m.Infra.CodegenFilePlan]].fail(
                custom_result.error or f"custom Make validation failed: {root}"
            )
        planned.extend(custom_result.value)
        return r[t.SequenceOf[m.Infra.CodegenFilePlan]].ok(tuple(planned))

    def _plan_existing_templates(
        self,
        *,
        root: Path,
        repository: m.Infra.RepositoryRef,
        workspace: m.Infra.WorkspaceSpec,
        codegen: m.Infra.CodegenConfigSpec,
        tooling_runtime: m.Infra.ToolingRuntimeContext,
    ) -> p.Result[t.SequenceOf[m.Infra.CodegenFilePlan]]:
        """Render configured overwrite-owned templates for an existing tree."""
        if repository.profile is None:
            return r[t.SequenceOf[m.Infra.CodegenFilePlan]].fail(
                f"active repository has no Make profile: {repository.name}"
            )
        profile = c.Infra.MakeProfile(repository.profile)
        context_result = self._render_context(
            repository, workspace, codegen, tooling_runtime=tooling_runtime
        )
        if context_result.failure:
            return r[t.SequenceOf[m.Infra.CodegenFilePlan]].fail(
                context_result.error or "project render context is invalid"
            )
        templates_root = (
            self._package_root() / "templates" / codegen.templates.root
        ).resolve()
        planned: list[m.Infra.CodegenFilePlan] = []
        for managed in codegen.managed_files:
            if not managed.overwrite or managed.path == Path(
                c.Infra.PYPROJECT_FILENAME
            ):
                continue
            entries = tuple(
                entry
                for entry in codegen.templates.entries
                if entry.destination == managed.path.as_posix()
                and entry.delegate == "render"
            )
            if len(entries) != 1:
                return r[t.SequenceOf[m.Infra.CodegenFilePlan]].fail(
                    f"managed file requires exactly one render template: {managed.path}"
                )
            entry = entries[0]
            if profile not in entry.profiles:
                continue
            rendered = u.Cli.template_render(
                templates_root / entry.source, context_result.value
            )
            if rendered.failure:
                return r[t.SequenceOf[m.Infra.CodegenFilePlan]].fail(
                    rendered.error or f"template render failed: {entry.source}"
                )
            file_plan = self._file_plan(root, entry.destination, rendered.value)
            if file_plan.failure:
                return r[t.SequenceOf[m.Infra.CodegenFilePlan]].fail(
                    file_plan.error
                    or f"managed file planning failed: {entry.destination}"
                )
            planned.append(file_plan.value)
        return r[t.SequenceOf[m.Infra.CodegenFilePlan]].ok(tuple(planned))

    @staticmethod
    def _render_context(
        repository: m.Infra.RepositoryRef,
        workspace: m.Infra.WorkspaceSpec,
        codegen: m.Infra.CodegenConfigSpec,
        *,
        tooling_runtime: m.Infra.ToolingRuntimeContext,
    ) -> p.Result[m.Infra.ProjectRenderContext]:
        """Build the complete typed template context from manifest data."""
        project = workspace.project
        if project is None:
            return r[m.Infra.ProjectRenderContext].fail(
                f"workspace manifest has no project metadata: {workspace.name}"
            )
        profile = c.Infra.MakeProfile(repository.profile)
        provider = next(
            (item for item in codegen.providers if item.name == repository.provider),
            None,
        )
        if provider is None:
            return r[m.Infra.ProjectRenderContext].fail(
                f"repository provider is not configured: {repository.provider}"
            )
        dependency_profile = next(
            (
                item
                for item in codegen.scaffold.project.dependency_profiles
                if item.upstream == project.upstream
            ),
            None,
        )
        if dependency_profile is None:
            return r[m.Infra.ProjectRenderContext].fail(
                f"unsupported scaffold upstream: {project.upstream}"
            )
        if project.license not in codegen.scaffold.project.supported_licenses:
            supported = ", ".join(codegen.scaffold.project.supported_licenses)
            return r[m.Infra.ProjectRenderContext].fail(
                f"unsupported scaffold license: {project.license}; "
                f"supported licenses: {supported}"
            )
        members = (
            tuple(workspace.members)
            if profile is c.Infra.MakeProfile.WORKSPACE_ROOT
            else ()
        )
        workspace_root_rel = (
            Path(*(".." for _ in repository.path.parts)).as_posix()
            if profile is c.Infra.MakeProfile.WORKSPACE_MEMBER and repository.path.parts
            else project.workspace_root_rel
        )
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
            if profile is not c.Infra.MakeProfile.WORKSPACE_ROOT
            else ()
        )
        return r[m.Infra.ProjectRenderContext].ok(
            m.Infra.ProjectRenderContext(
                scaffold=codegen.scaffold,
                dependency_profile=dependency_profile,
                make=codegen.make,
                tooling=config.Infra.tooling,
                tooling_runtime=tooling_runtime,
                dist=repository.distribution,
                const_name=project.constant_name,
                package_name=project.package_name,
                packaged_data_dirs=packaged_data_dirs,
                class_stem=project.class_stem,
                ns=project.namespace,
                ns_attr=project.namespace_attribute,
                alias=project.alias,
                env_prefix=project.environment_prefix,
                upstream=project.upstream,
                description=project.description,
                version=project.version,
                license=project.license,
                python_version=codegen.toolchain.python_minor_version,
                python_toolchain_version=codegen.toolchain.python_version,
                python_required_version=codegen.toolchain.python_required_version,
                uv_version=codegen.toolchain.uv_version,
                uv_required_version=codegen.toolchain.uv_required_version,
                uv_link_mode=codegen.toolchain.uv_link_mode,
                author_name=project.author_name,
                author_email=project.author_email,
                repository=project.homepage,
                homepage=project.homepage,
                documentation=project.documentation,
                flext_git_base_url=provider.base_url,
                flext_git_branch=provider.branch,
                make_profile=profile,
                workspace_root_rel=workspace_root_rel,
                repository_provider=repository.provider,
                repository_git_url=repository.url,
                repository_branch=repository.branch,
                year=project.year,
                project_resources=project.resources,
                workspace_members=tuple(
                    item.path.as_posix() for item in workspace.members
                ),
                workspace_repositories=members,
                workspace_content_only=tuple(workspace.content_only),
                workspace_exclusions=tuple(workspace.exclusions),
            )
        )

    @classmethod
    def _validate_initial_manifest(
        cls, rendered: str, expected: m.Infra.WorkspaceSpec
    ) -> p.Result[bool]:
        """Validate rendered manifest syntax, schema, model, and exact payload."""
        parsed = u.Cli.yaml_parse(rendered)
        if parsed.failure:
            return r[bool].fail(parsed.error or "workspace manifest YAML is invalid")
        schema = u.Infra.resource_root("schemas") / c.Infra.WORKSPACE_SCHEMA_FILENAME
        schema_result = u.Cli.schema_validate(parsed.value, schema)
        if schema_result.failure:
            return r[bool].fail(
                schema_result.error or "workspace manifest schema is invalid"
            )
        try:
            validated = m.Infra.WorkspaceSpec.model_validate(parsed.value)
        except c.ValidationError as exc:
            return r[bool].fail_op("workspace manifest model validation", exc)
        if validated != expected:
            return r[bool].fail("rendered workspace manifest differs from input model")
        return r[bool].ok(True)

    def _plan_existing_custom(
        self, root: Path, config: m.Infra.CodegenConfigSpec
    ) -> p.Result[t.SequenceOf[m.Infra.CodegenFilePlan]]:
        """Validate an existing custom Make surface without creating one."""
        path = root / config.make.custom_handler_policy.filename
        if path.exists() and not path.is_file():
            return r[t.SequenceOf[m.Infra.CodegenFilePlan]].fail(
                f"custom Make destination is not a regular file: {path}"
            )
        if not path.is_file():
            return r[t.SequenceOf[m.Infra.CodegenFilePlan]].ok(())
        read = u.Cli.files_read_text(path)
        if read.failure:
            return r[t.SequenceOf[m.Infra.CodegenFilePlan]].fail(
                read.error or f"custom Make read failed: {path}"
            )
        validation = self._validate_custom_make(
            read.value, config.make.custom_handler_policy
        )
        if validation.failure:
            return r[t.SequenceOf[m.Infra.CodegenFilePlan]].fail(
                validation.error or f"invalid custom Make handlers: {path}"
            )
        digest = u.Cli.sha256_content(read.value)
        return r[t.SequenceOf[m.Infra.CodegenFilePlan]].ok((
            m.Infra.CodegenFilePlan(
                path=path,
                rendered=read.value,
                expected_sha256=digest,
                current_sha256=digest,
                changed=False,
            ),
        ))

    @staticmethod
    def _validate_custom_make(
        content: str, policy: m.Infra.CustomHandlerPolicy
    ) -> p.Result[bool]:
        """Reject public targets, aliases, includes, and toolchain declarations."""
        target_re = re.compile(policy.target_pattern)
        for line_number, raw_line in enumerate(content.splitlines(), start=1):
            if not raw_line or raw_line.lstrip().startswith("#"):
                continue
            if raw_line[0].isspace():
                continue
            if raw_line.startswith(".PHONY:"):
                names = raw_line.partition(":")[2].split()
                if names and all(target_re.fullmatch(name) for name in names):
                    continue
            target = raw_line.partition(":")[0].strip() if ":" in raw_line else ""
            if target and target_re.fullmatch(target):
                continue
            return r[bool].fail(
                f"custom.mk line {line_number} is not a private custom handler"
            )
        return r[bool].ok(True)

    def _file_plan(
        self,
        root: Path,
        relative_path: str,
        rendered: str,
        *,
        block_existing: bool = False,
    ) -> p.Result[m.Infra.CodegenFilePlan]:
        """Compare one expected output and block only changed dirty content."""
        path = root / relative_path
        if path.exists() and not path.is_file():
            return r[m.Infra.CodegenFilePlan].fail(
                f"managed destination is not a regular file: {path}"
            )
        current = ""
        if path.is_file():
            read = u.Cli.files_read_text(path)
            if read.failure:
                return r[m.Infra.CodegenFilePlan].fail(
                    read.error or f"managed file read failed: {path}"
                )
            current = read.value
        expected_sha = u.Cli.sha256_content(rendered)
        current_sha = u.Cli.sha256_content(current) if path.is_file() else ""
        changed = current != rendered
        existing_conflict = changed and path.is_file() and block_existing
        dirty = existing_conflict
        if changed and path.is_file() and not existing_conflict:
            wip = self._managed_path_wip(root, path)
            if wip.failure:
                return r[m.Infra.CodegenFilePlan].fail(
                    wip.error or f"managed Git status failed: {path}"
                )
            dirty = wip.value
        return r[m.Infra.CodegenFilePlan].ok(
            m.Infra.CodegenFilePlan(
                path=path,
                rendered=rendered,
                expected_sha256=expected_sha,
                current_sha256=current_sha,
                changed=changed,
                blocked=dirty,
                reason=(
                    "existing content conflicts with initial generation"
                    if existing_conflict
                    else "uncommitted WIP in managed file"
                    if dirty
                    else ""
                ),
            )
        )

    @staticmethod
    def _resource_move_plans(
        root: Path, *, package_name: str, resources: t.SequenceOf[m.Infra.ResourceSpec]
    ) -> p.Result[tuple[m.Infra.CodegenFilePlan, ...]]:
        """Plan namespace-to-root resource cutovers from actual directory presence."""
        package_root = root / "src" / package_name
        plans: list[m.Infra.CodegenFilePlan] = []
        for resource in resources:
            target = root / resource.source
            source = package_root / resource.source
            if target.exists() and not target.is_dir():
                return r[tuple[m.Infra.CodegenFilePlan, ...]].fail(
                    f"resource root is not a directory: {target}"
                )
            if source.exists() and not source.is_dir():
                return r[tuple[m.Infra.CodegenFilePlan, ...]].fail(
                    f"package resource is not a directory: {source}"
                )
            if target.is_dir() and source.is_dir():
                return r[tuple[m.Infra.CodegenFilePlan, ...]].fail(
                    f"resource collision requires one canonical owner: {target} and {source}"
                )
            if source.is_dir():
                plans.append(
                    m.Infra.CodegenFilePlan(
                        path=target,
                        operation="move",
                        source_path=source,
                        expected_sha256=u.Cli.sha256_content(
                            f"{source.as_posix()}->{target.as_posix()}"
                        ),
                        changed=True,
                    )
                )
                continue
            if resource.required and not target.is_dir():
                return r[tuple[m.Infra.CodegenFilePlan, ...]].fail(
                    f"required resource directory is missing: {target}"
                )
        return r[tuple[m.Infra.CodegenFilePlan, ...]].ok(tuple(plans))

    @staticmethod
    def _apply_file_plan(file: m.Infra.CodegenFilePlan) -> p.Result[bool]:
        """Apply one prevalidated write or directory move without replacement."""
        if file.operation == "write":
            return u.Cli.atomic_write_text_file(file.path, file.rendered)
        source = file.source_path
        if source is None or not source.is_dir():
            return r[bool].fail(f"planned move source is unavailable: {source}")
        if file.path.exists():
            return r[bool].fail(f"planned move destination already exists: {file.path}")
        try:
            _ = source.rename(file.path)
        except OSError as exc:
            return r[bool].fail_op(f"move {source} to {file.path}", exc)
        return r[bool].ok(True)

    @staticmethod
    def _managed_path_wip(root: Path, path: Path) -> p.Result[bool]:
        """Return file-scoped Git WIP and fail when status cannot be proven."""
        repo_check = u.Cli.run_raw(
            [c.Infra.GIT, "rev-parse", "--is-inside-work-tree"], cwd=root
        )
        if (
            repo_check.failure
            or repo_check.value.exit_code != 0
            or repo_check.value.stdout.strip() != "true"
        ):
            return r[bool].fail(f"cannot verify managed Git state: {root}")
        try:
            relative = path.relative_to(root).as_posix()
        except ValueError:
            return r[bool].fail(f"managed path escapes repository root: {path}")
        status = u.Cli.run_raw(
            [c.Infra.GIT, "status", "--porcelain", "--", relative], cwd=root
        )
        if status.failure or status.value.exit_code != 0:
            return r[bool].fail(f"cannot inspect managed Git path: {path}")
        return r[bool].ok(bool(status.value.stdout.strip()))

    @staticmethod
    def _uv_environment_plan(
        *,
        root: Path,
        workspace_root: Path,
        repository: m.Infra.RepositoryRef,
        workspace: m.Infra.WorkspaceSpec,
        config: m.Infra.CodegenConfigSpec,
    ) -> m.Infra.UvEnvironmentPlan:
        """Describe the exact setup overlay without executing uv."""
        profile = c.Infra.MakeProfile(repository.profile)
        attached_member = profile is c.Infra.MakeProfile.WORKSPACE_MEMBER and bool(
            workspace.members
        )
        workspace_environment = (
            profile is c.Infra.MakeProfile.WORKSPACE_ROOT or attached_member
        )
        environment_root = workspace_root if workspace_environment else root
        groups: tuple[str, ...] = ("dev", "codegen")
        editable_repositories: tuple[m.Infra.RepositoryRef, ...] = ()
        if workspace_environment:
            groups = (*groups, "workspace")
            editable_repositories = (workspace.repository, *workspace.members)
        return m.Infra.UvEnvironmentPlan(
            project_root=root,
            environment_root=environment_root,
            lock_path=environment_root / c.Infra.UV_LOCK_FILENAME,
            python_version=config.toolchain.python_version,
            uv_version=config.toolchain.uv_version,
            groups=groups,
            editable_repositories=editable_repositories,
        )


__all__: list[str] = ["FlextInfraCodegenConform"]
