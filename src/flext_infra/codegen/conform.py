"""Unified, fail-closed conformance for new and existing repositories.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import TYPE_CHECKING, Annotated, override

from flext_core import r
from flext_infra.base import s
from flext_infra.constants import c
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

    @classmethod
    def execute_request(
        cls,
        request: m.Infra.CodegenConformRequest,
    ) -> p.Result[m.Infra.CodegenResult]:
        """Execute one already validated public CLI request."""
        service = cls(workspace_root=request.root, request=request)
        return service.execute()

    @override
    def execute(self) -> p.Result[m.Infra.CodegenResult]:
        """Run check or apply and require a verified fixed point."""
        request = self.request or m.Infra.CodegenConformRequest(
            root=self.workspace_root,
        )
        planned = self.plan(request)
        if planned.failure:
            return r[m.Infra.CodegenResult].fail(
                planned.error or "codegen conform planning failed",
            )
        plan = planned.value
        blocked = tuple(file for file in plan.files if file.blocked)
        if blocked:
            details = "; ".join(
                f"{file.path}: {file.reason or 'managed WIP'}" for file in blocked
            )
            return r[m.Infra.CodegenResult].fail(
                f"codegen conform blocked before writes: {details}",
            )
        changed = tuple(file for file in plan.files if file.changed)
        mode = c.Infra.CodegenConformMode(request.mode)
        if mode is c.Infra.CodegenConformMode.CHECK:
            if changed:
                paths = ", ".join(str(file.path) for file in changed)
                return r[m.Infra.CodegenResult].fail(
                    f"codegen drift detected: {paths}",
                )
            return r[m.Infra.CodegenResult].ok(
                m.Infra.CodegenResult(plan=plan),
            )
        written: list[Path] = []
        for file in changed:
            result = u.Cli.atomic_write_text_file(file.path, file.rendered)
            if result.failure:
                return r[m.Infra.CodegenResult].fail(
                    result.error or f"atomic write failed: {file.path}",
                )
            written.append(file.path)
        verified = self.plan(request)
        if verified.failure:
            return r[m.Infra.CodegenResult].fail(
                verified.error or "post-apply conform verification failed",
            )
        verified_plan = verified.value
        residual = tuple(file for file in verified_plan.files if file.changed)
        if residual:
            paths = ", ".join(str(file.path) for file in residual)
            return r[m.Infra.CodegenResult].fail(
                f"codegen apply did not reach a fixed point: {paths}",
            )
        return r[m.Infra.CodegenResult].ok(
            m.Infra.CodegenResult(
                plan=verified_plan,
                written_files=tuple(written),
            ),
        )

    def plan(
        self,
        request: m.Infra.CodegenConformRequest,
    ) -> p.Result[m.Infra.CodegenPlan]:
        """Build and validate the complete selection without writing."""
        config_result = self.load_config()
        if config_result.failure:
            return r[m.Infra.CodegenPlan].fail(
                config_result.error or "codegen configuration load failed",
            )
        config = config_result.value
        workspace_result = FlextInfraWorkspaceDetector.load_workspace_spec(
            request.root,
        )
        if workspace_result.failure:
            return r[m.Infra.CodegenPlan].fail(
                workspace_result.error or "workspace manifest load failed",
            )
        workspace = workspace_result.value
        catalog_result = self._validate_workspace_catalog(config, workspace)
        if catalog_result.failure:
            return r[m.Infra.CodegenPlan].fail(
                catalog_result.error or "workspace catalog validation failed",
            )
        selected_result = self._select_repositories(request, workspace)
        if selected_result.failure:
            return r[m.Infra.CodegenPlan].fail(
                selected_result.error or "repository selection failed",
            )
        selected = selected_result.value
        files: list[m.Infra.CodegenFilePlan] = []
        environments: list[m.Infra.UvEnvironmentPlan] = []
        for repository in selected:
            root = self._repository_root(request.root, workspace, repository)
            if not root.is_dir():
                return r[m.Infra.CodegenPlan].fail(
                    f"declared repository checkout is missing: {root}",
                )
            repository_workspace = workspace
            if repository.name != workspace.repository.name:
                member_manifest = FlextInfraWorkspaceDetector.load_workspace_spec(root)
                if member_manifest.failure:
                    return r[m.Infra.CodegenPlan].fail(
                        member_manifest.error
                        or f"member workspace manifest load failed: {root}",
                    )
                repository_workspace = member_manifest.value
                if repository_workspace.repository.model_dump(
                    mode="json"
                ) != repository.model_dump(mode="json"):
                    return r[m.Infra.CodegenPlan].fail(
                        f"member manifest differs from root topology: {repository.name}",
                    )
            repository_plan = self._plan_repository(
                root=root,
                repository=repository,
                workspace=repository_workspace,
                config=config,
            )
            if repository_plan.failure:
                return r[m.Infra.CodegenPlan].fail(
                    repository_plan.error or f"repository planning failed: {root}",
                )
            files.extend(repository_plan.value)
            environments.append(
                self._uv_environment_plan(
                    root=root,
                    workspace_root=request.root,
                    repository=repository,
                    workspace=workspace,
                    config=config,
                ),
            )
        return r[m.Infra.CodegenPlan].ok(
            m.Infra.CodegenPlan(
                request=request,
                repositories=selected,
                workspace=workspace,
                make_spec=config.make,
                uv_environments=tuple(environments),
                files=tuple(files),
            ),
        )

    @staticmethod
    def _package_root() -> Path:
        """Return the installed flext-infra package root."""
        return Path(__file__).resolve().parent.parent

    @classmethod
    def load_config(cls) -> p.Result[m.Infra.CodegenConfigSpec]:
        """Load schema-validated codegen data and prove its model roundtrip."""
        package_root = cls._package_root()
        source = package_root / "config" / c.Infra.CODEGEN_CONFIG_FILENAME
        schema = package_root / "schemas" / c.Infra.CODEGEN_SCHEMA_FILENAME
        loaded = u.Cli.config_load(source, schema_path=schema)
        if loaded.failure:
            return r[m.Infra.CodegenConfigSpec].fail(
                loaded.error or f"invalid codegen configuration: {source}",
            )
        try:
            parsed = m.Infra.CodegenConfigSpec.model_validate(loaded.value.data)
            roundtrip = m.Infra.CodegenConfigSpec.model_validate(
                parsed.model_dump(mode="python"),
            )
        except c.ValidationError as exc:
            return r[m.Infra.CodegenConfigSpec].fail_op(
                "codegen configuration model validation",
                exc,
            )
        return r[m.Infra.CodegenConfigSpec].ok(roundtrip)

    @staticmethod
    def _validate_workspace_catalog(
        config: m.Infra.CodegenConfigSpec,
        workspace: m.Infra.WorkspaceSpec,
    ) -> p.Result[bool]:
        """Require declared fleet members to match their global Git contracts."""
        local_refs = (workspace.repository, *workspace.members, *workspace.content_only)
        for local in local_refs:
            known = next(
                (item for item in config.repositories if item.name == local.name),
                None,
            )
            if known is None:
                if local is workspace.repository and not workspace.members:
                    continue
                return r[bool].fail(
                    f"repository is not classified in codegen catalog: {local.name}",
                )
            local_payload = local.model_dump(mode="json")
            known_payload = known.model_dump(mode="json")
            if local_payload != known_payload:
                return r[bool].fail(
                    f"workspace repository differs from catalog: {local.name}",
                )
        return r[bool].ok(True)

    @staticmethod
    def _select_repositories(
        request: m.Infra.CodegenConformRequest,
        workspace: m.Infra.WorkspaceSpec,
    ) -> p.Result[tuple[m.Infra.RepositoryRef, ...]]:
        """Resolve self/members/all from the local manifest only."""
        scope = c.Infra.CodegenConformScope(request.scope)
        if scope is c.Infra.CodegenConformScope.SELF:
            return r[tuple[m.Infra.RepositoryRef, ...]].ok((workspace.repository,))
        if scope is c.Infra.CodegenConformScope.MEMBERS:
            if not workspace.members:
                return r[tuple[m.Infra.RepositoryRef, ...]].fail(
                    "members scope requires a workspace-root manifest",
                )
            return r[tuple[m.Infra.RepositoryRef, ...]].ok(tuple(workspace.members))
        return r[tuple[m.Infra.RepositoryRef, ...]].ok(
            (workspace.repository, *workspace.members),
        )

    @staticmethod
    def _repository_root(
        root: Path,
        workspace: m.Infra.WorkspaceSpec,
        repository: m.Infra.RepositoryRef,
    ) -> Path:
        """Resolve one selected checkout without sibling discovery."""
        if repository.name == workspace.repository.name:
            return root
        return (root / repository.path).resolve()

    def _plan_repository(
        self,
        *,
        root: Path,
        repository: m.Infra.RepositoryRef,
        workspace: m.Infra.WorkspaceSpec,
        config: m.Infra.CodegenConfigSpec,
    ) -> p.Result[t.SequenceOf[m.Infra.CodegenFilePlan]]:
        """Render every codegen-owned output and validate custom/lock owners."""
        if repository.profile is None:
            return r[t.SequenceOf[m.Infra.CodegenFilePlan]].fail(
                f"active repository has no Make profile: {repository.name}",
            )
        profile = c.Infra.MakeProfile(repository.profile)
        context = self._render_context(repository, workspace)
        planned: list[m.Infra.CodegenFilePlan] = []
        templates_root = self._package_root() / "templates" / config.templates.root
        generated_destinations = frozenset({
            ".gitmodules",
            ".mise.toml",
            ".python-version",
            "Makefile",
        })
        for entry in config.templates.entries:
            if entry.delegate != "render" or profile not in entry.profiles:
                continue
            if entry.destination not in generated_destinations:
                continue
            rendered = u.Cli.template_render(
                templates_root / entry.source,
                context,
            )
            if rendered.failure:
                return r[t.SequenceOf[m.Infra.CodegenFilePlan]].fail(
                    rendered.error or f"template render failed: {entry.source}",
                )
            file_plan = self._file_plan(root, entry.destination, rendered.value)
            if file_plan.failure:
                return r[t.SequenceOf[m.Infra.CodegenFilePlan]].fail(
                    file_plan.error
                    or f"managed file planning failed: {entry.destination}",
                )
            planned.append(file_plan.value)
        pyproject = root / c.Infra.PYPROJECT_FILENAME
        if not pyproject.is_file():
            return r[t.SequenceOf[m.Infra.CodegenFilePlan]].fail(
                f"pyproject.toml must exist before conform: {pyproject}",
            )
        pyproject_read = u.Cli.files_read_text(pyproject)
        if pyproject_read.failure:
            return r[t.SequenceOf[m.Infra.CodegenFilePlan]].fail(
                pyproject_read.error or f"pyproject read failed: {pyproject}",
            )
        pyproject_result = u.Infra.pyproject_conform(
            pyproject_read.value,
            repositories=config.repositories,
            workspace=workspace,
            toolchain=config.toolchain,
        )
        if pyproject_result.failure:
            return r[t.SequenceOf[m.Infra.CodegenFilePlan]].fail(
                pyproject_result.error or f"pyproject conform failed: {pyproject}",
            )
        pyproject_plan = self._file_plan(
            root,
            c.Infra.PYPROJECT_FILENAME,
            pyproject_result.value,
        )
        if pyproject_plan.failure:
            return r[t.SequenceOf[m.Infra.CodegenFilePlan]].fail(
                pyproject_plan.error or f"pyproject planning failed: {pyproject}",
            )
        planned.append(pyproject_plan.value)
        custom_result = self._plan_custom(root, config)
        if custom_result.failure:
            return r[t.SequenceOf[m.Infra.CodegenFilePlan]].fail(
                custom_result.error or f"custom Make validation failed: {root}",
            )
        planned.append(custom_result.value)
        return r[t.SequenceOf[m.Infra.CodegenFilePlan]].ok(tuple(planned))

    @staticmethod
    def _render_context(
        repository: m.Infra.RepositoryRef,
        workspace: m.Infra.WorkspaceSpec,
    ) -> t.JsonMapping:
        """Dump typed repository records at the template boundary."""
        profile = c.Infra.MakeProfile(repository.profile)
        member_paths = [item.path.as_posix() for item in workspace.members]
        member_records = [item.model_dump(mode="json") for item in workspace.members]
        root_rel = "."
        if profile is c.Infra.MakeProfile.WORKSPACE_MEMBER:
            depth = max(1, len(repository.path.parts))
            root_rel = "/".join(".." for _ in range(depth))
        return t.Cli.JSON_MAPPING_ADAPTER.validate_python({
            "dist": repository.distribution,
            "make_profile": profile.value,
            "workspace_root_rel": root_rel,
            "workspace_members": member_paths,
            "workspace_repositories": member_records,
        })

    def _plan_custom(
        self,
        root: Path,
        config: m.Infra.CodegenConfigSpec,
    ) -> p.Result[m.Infra.CodegenFilePlan]:
        """Create a missing custom file or validate existing private handlers."""
        path = root / config.make.custom_handler_policy.filename
        if path.is_file():
            read = u.Cli.files_read_text(path)
            if read.failure:
                return r[m.Infra.CodegenFilePlan].fail(
                    read.error or f"custom Make read failed: {path}",
                )
            validation = self._validate_custom_make(
                read.value,
                config.make.custom_handler_policy,
            )
            if validation.failure:
                return r[m.Infra.CodegenFilePlan].fail(
                    validation.error or f"invalid custom Make handlers: {path}",
                )
            digest = u.Cli.sha256_content(read.value)
            return r[m.Infra.CodegenFilePlan].ok(
                m.Infra.CodegenFilePlan(
                    path=path,
                    rendered=read.value,
                    expected_sha256=digest,
                    current_sha256=digest,
                    changed=False,
                ),
            )
        template = (
            self._package_root() / "templates" / "project" / "base" / "custom.mk.j2"
        )
        rendered = u.Cli.template_render(template, {"dist": root.name})
        if rendered.failure:
            return r[m.Infra.CodegenFilePlan].fail(
                rendered.error or "custom.mk template render failed",
            )
        return self._file_plan(root, path.name, rendered.value)

    @staticmethod
    def _validate_custom_make(
        content: str,
        policy: m.Infra.CustomHandlerPolicy,
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
                f"custom.mk line {line_number} is not a private custom handler",
            )
        return r[bool].ok(True)

    def _file_plan(
        self,
        root: Path,
        relative_path: str,
        rendered: str,
    ) -> p.Result[m.Infra.CodegenFilePlan]:
        """Compare one expected output and block only changed dirty content."""
        path = root / relative_path
        current = ""
        if path.is_file():
            read = u.Cli.files_read_text(path)
            if read.failure:
                return r[m.Infra.CodegenFilePlan].fail(
                    read.error or f"managed file read failed: {path}",
                )
            current = read.value
        expected_sha = u.Cli.sha256_content(rendered)
        current_sha = u.Cli.sha256_content(current) if path.is_file() else ""
        changed = current != rendered
        dirty = changed and self._managed_path_is_dirty(root, path)
        return r[m.Infra.CodegenFilePlan].ok(
            m.Infra.CodegenFilePlan(
                path=path,
                rendered=rendered,
                expected_sha256=expected_sha,
                current_sha256=current_sha,
                changed=changed,
                blocked=dirty,
                reason="uncommitted WIP in managed file" if dirty else "",
            ),
        )

    @staticmethod
    def _managed_path_is_dirty(root: Path, path: Path) -> bool:
        """Return true only for file-scoped tracked or untracked Git WIP."""
        repo_check = u.Cli.run_raw(
            [c.Infra.GIT, "rev-parse", "--is-inside-work-tree"],
            cwd=root,
        )
        if repo_check.failure or repo_check.value.exit_code != 0:
            return False
        try:
            relative = path.relative_to(root).as_posix()
        except ValueError:
            return True
        status = u.Cli.run_raw(
            [c.Infra.GIT, "status", "--porcelain", "--", relative],
            cwd=root,
        )
        return (
            status.success
            and status.value.exit_code == 0
            and bool(status.value.stdout.strip())
        )

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
        runtime_root = (
            workspace_root
            if profile
            in {
                c.Infra.MakeProfile.WORKSPACE_ROOT,
                c.Infra.MakeProfile.WORKSPACE_MEMBER,
            }
            and bool(workspace.members)
            else root
        )
        groups: tuple[str, ...] = ("dev", "codegen")
        editable_paths: tuple[Path, ...] = ()
        if profile is c.Infra.MakeProfile.WORKSPACE_ROOT:
            groups = (*groups, "workspace")
            editable_paths = (
                workspace_root,
                *(workspace_root / item.path for item in workspace.members),
            )
        return m.Infra.UvEnvironmentPlan(
            project_root=root,
            runtime_root=runtime_root,
            lock_path=root / c.Infra.UV_LOCK_FILENAME,
            python_version=config.toolchain.python_version,
            uv_version=config.toolchain.uv_version,
            groups=groups,
            editable_paths=editable_paths,
        )


__all__: list[str] = ["FlextInfraCodegenConform"]
