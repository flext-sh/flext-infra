"""Strict manifest-backed workspace mode detection.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, override

from flext_core import r
from flext_infra import c, config, m, u
from flext_infra.base import s
from flext_infra.workspace._detector_topology import (
    FlextInfraWorkspaceTopologyMixin,
)

if TYPE_CHECKING:
    from flext_infra import p


class FlextInfraWorkspaceDetector(
    FlextInfraWorkspaceTopologyMixin, s[c.Infra.WorkspaceMode]
):
    """Classify only declared roots and real, declared Git submodules."""

    @classmethod
    def _unattached_member(
        cls,
        repository_root: Path,
        declared_paths: frozenset[Path],
        providers: dict[str, m.Infra.ProviderSpec],
        member: m.Infra.RepositoryRef,
    ) -> p.Result[tuple[Path, ...]]:
        """Validate one mutable member of an unattached repository root."""
        if member.read_only:
            return r[tuple[Path, ...]].ok(())
        provider = providers.get(member.provider)
        if provider is None or not cls._repository_is_governed(member, provider):
            return r[tuple[Path, ...]].fail(
                "mutable workspace member is not first-party governed: "
                f"{member.name}"
            )
        if member.path not in declared_paths:
            return r[tuple[Path, ...]].fail(
                "governed workspace member is absent from .gitmodules: "
                f"{member.path.as_posix()}"
            )
        return cls._gitmodule_contract(
            repository_root, member.path.as_posix()
        ).flat_map(
            lambda contract: (
                r[tuple[Path, ...]].ok((member.path,))
                if contract == (member.url, member.branch)
                else r[tuple[Path, ...]].fail(
                    f"governed workspace member contract differs: {member.name}"
                )
            )
        )

    @classmethod
    def _unattached_workspace_mode(
        cls,
        repository_root: Path,
        declared_paths: frozenset[Path],
        workspace: m.Infra.WorkspaceSpec,
    ) -> p.Result[c.Infra.WorkspaceMode]:
        """Classify an unattached root from all governed manifest members."""
        providers = {item.name: item for item in config.Infra.codegen.providers}
        return r.traverse(
            workspace.members,
            lambda member: cls._unattached_member(
                repository_root, declared_paths, providers, member
            ),
        ).map(
            lambda governed: (
                c.Infra.WorkspaceMode.WORKSPACE
                if any(paths for paths in governed)
                else c.Infra.WorkspaceMode.STANDALONE
            )
        )

    @classmethod
    def _unattached_mode(
        cls,
        repository_root: Path,
        workspace_specs: tuple[m.Infra.WorkspaceSpec, ...],
    ) -> p.Result[c.Infra.WorkspaceMode]:
        """Classify a repository with no physical Git superproject."""
        attached_marker = cls._declares_attached_standalone(repository_root)
        if attached_marker.failure:
            return r[c.Infra.WorkspaceMode].fail(
                attached_marker.error or "unable to read workspace attachment marker"
            )
        if attached_marker.value:
            return r[c.Infra.WorkspaceMode].ok(c.Infra.WorkspaceMode.WORKSPACE_MEMBER)
        declared = u.Infra.git_declared_submodule_paths(repository_root)
        if declared.failure:
            return r[c.Infra.WorkspaceMode].fail(
                declared.error or "unable to read Git submodule topology"
            )
        if not declared.value:
            return r[c.Infra.WorkspaceMode].ok(c.Infra.WorkspaceMode.STANDALONE)
        workspace = (
            r[m.Infra.WorkspaceSpec].ok(workspace_specs[0])
            if workspace_specs
            else cls.load_workspace_spec(repository_root)
        )
        return workspace.flat_map(
            lambda workspace: cls._unattached_workspace_mode(
                repository_root, frozenset(declared.value), workspace
            )
        )

    @staticmethod
    def _member_root_and_path(
        project_root: Path, superproject_root: Path
    ) -> p.Result[tuple[Path, str]]:
        """Resolve a physical member checkout and its superproject-relative path."""
        member_root = u.Cli.capture(
            [c.Infra.GIT, "rev-parse", "--show-toplevel"], cwd=project_root
        )
        if member_root.failure:
            return r[tuple[Path, str]].fail(
                member_root.error or "unable to resolve Git repository root"
            )
        resolved_root = Path(member_root.value).resolve()
        try:
            member_path = resolved_root.relative_to(superproject_root).as_posix()
        except ValueError as exc:
            return r[tuple[Path, str]].fail_op("Workspace detection", exc)
        return r[tuple[Path, str]].ok((resolved_root, member_path))

    @staticmethod
    def _select_registered_member(
        parent_spec: m.Infra.WorkspaceSpec, member_path: str
    ) -> p.Result[tuple[m.Infra.RepositoryRef, ...]]:
        """Select zero or one governed member row for a physical gitlink."""
        declared_members = tuple(
            repository
            for repository in parent_spec.members
            if repository.path.as_posix() == member_path
        )
        if not declared_members:
            return r[tuple[m.Infra.RepositoryRef, ...]].ok(())
        if len(declared_members) != 1:
            return r[tuple[m.Infra.RepositoryRef, ...]].fail(
                f"Git submodule path is not one active workspace member: {member_path}"
            )
        return r[tuple[m.Infra.RepositoryRef, ...]].ok(declared_members)

    @classmethod
    def _registered_member(
        cls,
        superproject_root: Path,
        parent_spec: m.Infra.WorkspaceSpec,
        member_path: str,
    ) -> p.Result[tuple[m.Infra.RepositoryRef, ...]]:
        """Validate the parent topology before selecting its member row."""
        declared_paths = u.Infra.git_declared_submodule_paths(superproject_root)
        if declared_paths.failure:
            return r[tuple[m.Infra.RepositoryRef, ...]].fail(
                declared_paths.error or "unable to read Git submodule topology"
            )
        if Path(member_path) not in declared_paths.value:
            return r[tuple[m.Infra.RepositoryRef, ...]].fail(
                f"Git submodule path is not declared: {member_path}"
            )
        parent_contract = cls._validate_local_repository(parent_spec.repository)
        if parent_contract.failure:
            return r[tuple[m.Infra.RepositoryRef, ...]].fail(parent_contract.error)
        if parent_spec.repository.role is not c.Infra.RepositoryRole.WORKSPACE_ROOT:
            return r[tuple[m.Infra.RepositoryRef, ...]].fail(
                "Git superproject manifest role must be workspace-root"
            )
        return cls._select_registered_member(parent_spec, member_path)

    @staticmethod
    def _repository_contract_matches(
        local: m.Infra.RepositoryRef, declared: m.Infra.RepositoryRef
    ) -> bool:
        """Compare the immutable member fields shared by parent and local specs."""
        return all(
            (
                local.name == declared.name,
                local.distribution == declared.distribution,
                local.provider == declared.provider,
                local.branch == declared.branch,
                local.url == declared.url,
                local.role is declared.role,
                local.state is declared.state,
                local.checkout is declared.checkout,
                local.codegen is declared.codegen,
                local.package == declared.package,
                local.editable == declared.editable,
                local.read_only == declared.read_only,
            )
        )

    @classmethod
    def _local_member_contract(
        cls,
        member_root: Path,
        supplied: tuple[m.Infra.WorkspaceSpec, ...],
        declared: m.Infra.RepositoryRef,
        member_path: str,
    ) -> p.Result[bool]:
        """Validate an optional local manifest against its parent-owned row."""
        if supplied:
            return cls._validate_local_member_workspace(
                supplied[0], declared, member_path
            )
        local_manifest = cls._manifest_path(member_root)
        if not local_manifest.is_file():
            return r[bool].ok(True)
        return cls.load_workspace_spec(member_root).flat_map(
            lambda workspace: cls._validate_local_member_workspace(
                workspace, declared, member_path
            )
        )

    @classmethod
    def _validate_local_member_workspace(
        cls,
        workspace: m.Infra.WorkspaceSpec,
        declared: m.Infra.RepositoryRef,
        member_path: str,
    ) -> p.Result[bool]:
        """Compare one concrete local workspace to its parent declaration."""
        if not cls._repository_contract_matches(
            workspace.repository, declared
        ):
            return r[bool].fail(
                f"local and parent workspace member contracts differ: {member_path}"
            )
        return r[bool].ok(True)

    @staticmethod
    def _member_origin(member_root: Path, member_path: str) -> p.Result[str]:
        """Read the required origin of one physical workspace member."""
        origin = u.Cli.capture(
            [c.Infra.GIT, "config", "--get", "remote.origin.url"], cwd=member_root
        )
        if origin.failure or not origin.value:
            return r[str].fail(
                origin.error or f"workspace member origin is missing: {member_path}"
            )
        return r[str].ok(origin.value)

    @staticmethod
    def _member_gitlink_head(
        superproject_root: Path, member_path: str
    ) -> p.Result[str]:
        """Read the indexed commit of one exact Git submodule path."""
        gitlink = u.Cli.capture(
            [c.Infra.GIT, "ls-files", "--stage", "--", member_path],
            cwd=superproject_root,
        )
        if gitlink.failure or not gitlink.value:
            return r[str].fail(
                gitlink.error or f"workspace member gitlink is missing: {member_path}"
            )
        match gitlink.value.split():
            case ["160000", gitlink_head, "0", indexed_path] if (
                indexed_path == member_path
            ):
                return r[str].ok(gitlink_head)
            case _:
                return r[str].fail(
                    f"workspace member gitlink is malformed: {member_path}"
                )

    @staticmethod
    def _member_head(member_root: Path, member_path: str) -> p.Result[str]:
        """Read the checked-out commit of one physical workspace member."""
        member_head = u.Cli.capture(
            [c.Infra.GIT, "rev-parse", "--verify", "HEAD^{commit}"], cwd=member_root
        )
        if member_head.failure or not member_head.value:
            return r[str].fail(
                member_head.error or f"workspace member HEAD is missing: {member_path}"
            )
        return r[str].ok(member_head.value)

    @staticmethod
    def _validate_gitmodule_values(
        contract: tuple[str, str],
        origin: str,
        declared: m.Infra.RepositoryRef,
        member_path: str,
    ) -> p.Result[bool]:
        """Match member URL, provider, and branch to its parent declaration."""
        gitmodule_url, gitmodule_branch = contract
        if gitmodule_url != declared.url or origin != declared.url:
            return r[bool].fail(f"workspace member URL mismatch: {member_path}")
        provider_exists = any(
            provider.name == declared.provider
            for provider in config.Infra.codegen.providers
        )
        if not provider_exists:
            return r[bool].fail(
                f"workspace member provider is unknown: {declared.provider}"
            )
        if gitmodule_branch != declared.branch:
            return r[bool].fail(f"workspace member branch mismatch: {member_path}")
        return r[bool].ok(True)

    @classmethod
    def _validated_gitmodule_identity(
        cls,
        superproject_root: Path,
        member_root: Path,
        member_path: str,
        declared: m.Infra.RepositoryRef,
    ) -> p.Result[bool]:
        """Validate the member's declared and checked-out remote identity."""
        return cls._gitmodule_contract(superproject_root, member_path).flat_map(
            lambda contract: cls._member_origin(member_root, member_path).flat_map(
                lambda origin: cls._validate_gitmodule_values(
                    contract, origin, declared, member_path
                )
            )
        )

    @classmethod
    def _validated_commit_identity(
        cls, superproject_root: Path, member_root: Path, member_path: str
    ) -> p.Result[bool]:
        """Require the checked-out member commit to equal its indexed gitlink."""
        return cls._member_gitlink_head(superproject_root, member_path).flat_map(
            lambda gitlink_head: cls._member_head(member_root, member_path).flat_map(
                lambda member_head: (
                    r[bool].ok(True)
                    if member_head == gitlink_head
                    else r[bool].fail(
                        "workspace member gitlink mismatch: "
                        f"{member_path} expected {gitlink_head} got {member_head}"
                    )
                )
            )
        )

    @classmethod
    def _validate_member_git_contract(
        cls,
        superproject_root: Path,
        member_root: Path,
        member_path: str,
        declared: m.Infra.RepositoryRef,
    ) -> p.Result[bool]:
        """Validate remote and commit identity through the one Git contract."""
        return cls._validated_gitmodule_identity(
            superproject_root, member_root, member_path, declared
        ).flat_map(
            lambda _: cls._validated_commit_identity(
                superproject_root, member_root, member_path
            )
        )

    @classmethod
    def _registered_member_mode(
        cls,
        member_root: Path,
        superproject_root: Path,
        declared_members: tuple[m.Infra.RepositoryRef, ...],
        local_workspaces: tuple[m.Infra.WorkspaceSpec, ...],
    ) -> p.Result[c.Infra.WorkspaceMode]:
        """Validate a governed member or retain an undeclared gitlink as standalone."""
        if not declared_members:
            return r[c.Infra.WorkspaceMode].ok(c.Infra.WorkspaceMode.STANDALONE)
        declared = declared_members[0]
        member_path = declared.path.as_posix()
        return cls._local_member_contract(
            member_root, local_workspaces, declared, member_path
        ).flat_map(
            lambda _: cls._validate_member_git_contract(
                superproject_root, member_root, member_path, declared
            )
        ).map(lambda _: c.Infra.WorkspaceMode.WORKSPACE_MEMBER)

    @classmethod
    def validate_registered_member(
        cls,
        project_root: Path,
        superproject_root: Path,
        parent_spec: m.Infra.WorkspaceSpec,
        local_workspaces: tuple[m.Infra.WorkspaceSpec, ...] = (),
    ) -> p.Result[c.Infra.WorkspaceMode]:
        """Validate one physical Gitlink against its typed workspace contract."""
        return cls._member_root_and_path(project_root, superproject_root).flat_map(
            lambda identity: cls._registered_member(
                superproject_root, parent_spec, identity[1]
            ).flat_map(
                lambda declared_members: cls._registered_member_mode(
                    identity[0],
                    superproject_root,
                    declared_members,
                    local_workspaces,
                )
            )
        )

    @classmethod
    def _detect_attached(
        cls,
        project_root: Path,
        superproject_root: Path,
        workspace_specs: tuple[m.Infra.WorkspaceSpec, ...],
    ) -> p.Result[c.Infra.WorkspaceMode]:
        """Load the parent SSOT and validate one real attached member."""
        parent_manifest = cls._manifest_path(superproject_root)
        if not parent_manifest.is_file():
            return r[c.Infra.WorkspaceMode].ok(c.Infra.WorkspaceMode.STANDALONE)
        parent = cls.load_workspace_spec(superproject_root)
        if parent.failure:
            return r[c.Infra.WorkspaceMode].fail(parent.error)
        return cls.validate_registered_member(
            project_root, superproject_root, parent.value, workspace_specs
        )

    @staticmethod
    def _resolved_project_root(project_root: Path) -> p.Result[Path]:
        """Resolve and validate the requested project directory."""
        try:
            resolved_root = project_root.resolve()
        except c.EXC_OS_RUNTIME_TYPE as exc:
            return r[Path].fail_op("Workspace detection", exc)
        if not resolved_root.is_dir():
            return r[Path].fail(f"project root is not a directory: {resolved_root}")
        return r[Path].ok(resolved_root)

    @classmethod
    def _local_workspace(
        cls, project_root: Path
    ) -> p.Result[tuple[m.Infra.WorkspaceSpec, ...]]:
        """Load and validate the optional repository-local workspace manifest."""
        if not cls._manifest_path(project_root).is_file():
            return r[tuple[m.Infra.WorkspaceSpec, ...]].ok(())
        return cls.load_workspace_spec(project_root).flat_map(
            lambda workspace: cls._validate_local_repository(
                workspace.repository
            ).map(lambda _: (workspace,))
        )

    @classmethod
    def _outside_git_mode(
        cls,
        project_root: Path,
        workspace_specs: tuple[m.Infra.WorkspaceSpec, ...],
        git_probe: p.Cli.CommandOutput,
    ) -> p.Result[c.Infra.WorkspaceMode]:
        """Classify a path rejected by Git's work-tree probe."""
        if (project_root / c.Infra.GIT_DIR).exists():
            return r[c.Infra.WorkspaceMode].fail(
                git_probe.stderr.strip() or "invalid Git repository metadata"
            )
        return cls._unattached_mode(project_root, workspace_specs)

    @classmethod
    def _inside_git_mode(
        cls,
        project_root: Path,
        workspace_specs: tuple[m.Infra.WorkspaceSpec, ...],
    ) -> p.Result[c.Infra.WorkspaceMode]:
        """Classify a valid Git work tree from its physical superproject."""
        superproject = u.Cli.capture(
            [c.Infra.GIT, "rev-parse", "--show-superproject-working-tree"],
            cwd=project_root,
        )
        if superproject.failure:
            return r[c.Infra.WorkspaceMode].fail(
                superproject.error or "unable to resolve Git superproject"
            )
        if not superproject.value:
            return cls._unattached_mode(project_root, workspace_specs)
        return cls._detect_attached(
            project_root, Path(superproject.value).resolve(), workspace_specs
        )

    @classmethod
    def _probe_workspace_mode(
        cls,
        project_root: Path,
        workspace_specs: tuple[m.Infra.WorkspaceSpec, ...],
    ) -> p.Result[c.Infra.WorkspaceMode]:
        """Classify one project after Git accepts or rejects its work tree."""
        git_probe = u.Cli.run_raw(
            [c.Infra.GIT, "rev-parse", "--is-inside-work-tree"], cwd=project_root
        )
        if git_probe.failure:
            return r[c.Infra.WorkspaceMode].fail(
                git_probe.error or "unable to execute Git workspace probe"
            )
        if git_probe.value.exit_code != 0:
            return cls._outside_git_mode(
                project_root, workspace_specs, git_probe.value
            )
        return cls._inside_git_mode(project_root, workspace_specs)

    def detect(self, project_root: Path) -> p.Result[c.Infra.WorkspaceMode]:
        """Detect workspace mode from typed manifests and real Git metadata."""
        return self._resolved_project_root(project_root).flat_map(
            lambda resolved_root: self._local_workspace(resolved_root).flat_map(
                lambda workspace: self._probe_workspace_mode(
                    resolved_root, workspace
                )
            )
        )

    @override
    def execute(self) -> p.Result[c.Infra.WorkspaceMode]:
        """Execute the workspace detection flow."""
        return self.detect(self.workspace_root)


__all__: list[str] = ["FlextInfraWorkspaceDetector"]
