"""Strict manifest-backed workspace mode detection.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, override

from flext_core import r
from flext_infra.base import s
from flext_infra.constants import c
from flext_infra.models import m
from flext_infra.typings import t
from flext_infra.utilities import u

if TYPE_CHECKING:
    from flext_infra.protocols import p


class FlextInfraWorkspaceDetector(s[c.Infra.WorkspaceMode]):
    """Classify only declared roots and real, declared Git submodules."""

    # NOTE (multi-agent, mro-wkii.17.10 / agent: implement_topology_detector):
    # workspace membership is proven from the manifest SSOT plus Git's own
    # superproject metadata; ancestor and sibling discovery is intentionally absent.

    @staticmethod
    def _manifest_path(repository_root: Path) -> Path:
        """Return the repository-local topology manifest path."""
        return repository_root / c.CONFIG_DIR_NAME / c.Infra.WORKSPACE_MANIFEST_FILENAME

    @staticmethod
    def _schema_path() -> Path:
        """Return the packaged schema consumed by the public config facade."""
        return (
            Path(__file__).resolve().parents[1]
            / c.CONFIG_SCHEMAS_DIR_NAME
            / c.Infra.WORKSPACE_SCHEMA_FILENAME
        )

    @classmethod
    def load_workspace_spec(
        cls,
        repository_root: Path,
    ) -> p.Result[m.Infra.WorkspaceSpec]:
        """Load the canonical repository-local workspace manifest."""
        manifest_path = cls._manifest_path(repository_root)
        loaded = u.Cli.config_load(
            manifest_path,
            schema_path=cls._schema_path(),
            expand_env=False,
        )
        if loaded.failure:
            return r[m.Infra.WorkspaceSpec].fail(
                loaded.error or f"invalid workspace manifest: {manifest_path}",
            )
        try:
            # mro-i6nq.10: Validate the pure config model at its loading boundary.
            validated = m.Infra.WorkspaceSpec.model_validate(loaded.value.data)
        except c.ValidationError as exc:
            return r[m.Infra.WorkspaceSpec].fail_op(
                f"workspace manifest model validation ({manifest_path})",
                exc,
            )
        return r[m.Infra.WorkspaceSpec].ok(validated)

    @staticmethod
    def _validate_local_repository(
        repository: m.Infra.RepositoryRef,
    ) -> p.Result[bool]:
        """Validate the role/profile invariants for a local manifest owner."""
        if repository.path.as_posix() != ".":
            return r[bool].fail("local repository manifest path must be '.'")
        if repository.state != c.Infra.RepositoryState.ACTIVE:
            return r[bool].fail("local repository must have active state")
        expected_profile = {
            c.Infra.RepositoryRole.WORKSPACE_ROOT: c.Infra.MakeProfile.WORKSPACE_ROOT,
            c.Infra.RepositoryRole.WORKSPACE_MEMBER: (
                c.Infra.MakeProfile.WORKSPACE_MEMBER
            ),
            c.Infra.RepositoryRole.STANDALONE: c.Infra.MakeProfile.STANDALONE,
        }.get(repository.role)
        if expected_profile is None:
            return r[bool].fail(
                f"unsupported local repository role: {repository.role.value}",
            )
        if repository.profile != expected_profile:
            return r[bool].fail(
                "local repository role/profile mismatch: "
                f"{repository.role.value}/{repository.profile}",
            )
        return r[bool].ok(True)

    @staticmethod
    def _unattached_mode(
        workspace_spec: m.Infra.WorkspaceSpec | None,
    ) -> c.Infra.WorkspaceMode:
        """Classify a repository that Git proves has no superproject."""
        if (
            workspace_spec is not None
            and workspace_spec.repository.role == c.Infra.RepositoryRole.WORKSPACE_ROOT
        ):
            return c.Infra.WorkspaceMode.WORKSPACE
        return c.Infra.WorkspaceMode.STANDALONE

    @staticmethod
    def _gitmodule_contract(
        superproject_root: Path,
        member_path: str,
    ) -> p.Result[t.StrPair]:
        """Read the exact URL and branch for one declared Git submodule path."""
        gitmodules_path = superproject_root / c.Infra.GITMODULES
        if not gitmodules_path.is_file():
            return r[t.StrPair].fail(
                f"Git superproject has no {c.Infra.GITMODULES}: {superproject_root}",
            )
        entries = u.Cli.capture(
            [
                c.Infra.GIT,
                "config",
                "--file",
                c.Infra.GITMODULES,
                "--get-regexp",
                r"^submodule\..*\.path$",
            ],
            cwd=superproject_root,
        )
        if entries.failure:
            return r[t.StrPair].fail(
                entries.error or "unable to read Git submodule paths",
            )
        matching_keys: t.MutableSequenceOf[str] = []
        for line in entries.value.splitlines():
            if not line.strip():
                continue
            match line.split(maxsplit=1):
                case [key, path] if path == member_path:
                    matching_keys.append(key)
                case [_, _]:
                    continue
                case _:
                    return r[t.StrPair].fail("malformed Git submodule path entry")
        if len(matching_keys) != 1:
            return r[t.StrPair].fail(
                f"Git submodule path must be declared exactly once: {member_path}",
            )
        section = matching_keys[0].removesuffix(".path")
        url = u.Cli.capture(
            [
                c.Infra.GIT,
                "config",
                "--file",
                c.Infra.GITMODULES,
                "--get",
                f"{section}.url",
            ],
            cwd=superproject_root,
        )
        if url.failure or not url.value:
            return r[t.StrPair].fail(
                url.error or f"Git submodule URL is missing: {member_path}",
            )
        branch = u.Cli.capture(
            [
                c.Infra.GIT,
                "config",
                "--file",
                c.Infra.GITMODULES,
                "--get",
                f"{section}.branch",
            ],
            cwd=superproject_root,
        )
        if branch.failure or not branch.value:
            return r[t.StrPair].fail(
                branch.error or f"Git submodule branch is missing: {member_path}",
            )
        return r[t.StrPair].ok((url.value, branch.value))

    @classmethod
    def _detect_attached(
        cls,
        project_root: Path,
        superproject_root: Path,
        workspace_spec: m.Infra.WorkspaceSpec | None,
    ) -> p.Result[c.Infra.WorkspaceMode]:
        """Validate a real submodule against the parent and local manifests."""
        member_root_result = u.Cli.capture(
            [c.Infra.GIT, "rev-parse", "--show-toplevel"],
            cwd=project_root,
        )
        if member_root_result.failure:
            return r[c.Infra.WorkspaceMode].fail(
                member_root_result.error or "unable to resolve Git repository root",
            )
        member_root = Path(member_root_result.value).resolve()
        try:
            member_path = member_root.relative_to(superproject_root).as_posix()
        except ValueError as exc:
            return r[c.Infra.WorkspaceMode].fail_op("Workspace detection", exc)

        parent_manifest = cls._manifest_path(superproject_root)
        if not parent_manifest.is_file():
            return r[c.Infra.WorkspaceMode].fail(
                f"Git superproject has no workspace manifest: {parent_manifest}",
            )
        parent_result = cls.load_workspace_spec(superproject_root)
        if parent_result.failure:
            return r[c.Infra.WorkspaceMode].fail(parent_result.error)
        parent_spec = parent_result.value
        parent_contract = cls._validate_local_repository(parent_spec.repository)
        if parent_contract.failure:
            return r[c.Infra.WorkspaceMode].fail(parent_contract.error)
        if parent_spec.repository.role != c.Infra.RepositoryRole.WORKSPACE_ROOT:
            return r[c.Infra.WorkspaceMode].fail(
                "Git superproject manifest role must be workspace-root",
            )

        declared_members = tuple(
            repository
            for repository in parent_spec.members
            if repository.path.as_posix() == member_path
        )
        if len(declared_members) != 1:
            return r[c.Infra.WorkspaceMode].fail(
                f"Git submodule path is not one active workspace member: {member_path}",
            )
        declared = declared_members[0]
        if (
            declared.state != c.Infra.RepositoryState.ACTIVE
            or declared.role != c.Infra.RepositoryRole.WORKSPACE_MEMBER
            or declared.profile != c.Infra.MakeProfile.WORKSPACE_MEMBER
        ):
            return r[c.Infra.WorkspaceMode].fail(
                f"workspace member role/state/profile mismatch: {member_path}",
            )

        local_spec = workspace_spec
        local_manifest = cls._manifest_path(member_root)
        if local_spec is None and local_manifest.is_file():
            local_result = cls.load_workspace_spec(member_root)
            if local_result.failure:
                return r[c.Infra.WorkspaceMode].fail(local_result.error)
            local_spec = local_result.value
        if local_spec is not None:
            local_repository = local_spec.repository
            comparable_local = (
                local_repository.name,
                local_repository.distribution,
                local_repository.provider,
                local_repository.url,
                local_repository.branch,
                local_repository.role,
                local_repository.state,
                local_repository.profile,
            )
            comparable_declared = (
                declared.name,
                declared.distribution,
                declared.provider,
                declared.url,
                declared.branch,
                declared.role,
                declared.state,
                declared.profile,
            )
            if comparable_local != comparable_declared:
                return r[c.Infra.WorkspaceMode].fail(
                    f"local and parent workspace member contracts differ: {member_path}",
                )

        gitmodule_result = cls._gitmodule_contract(superproject_root, member_path)
        if gitmodule_result.failure:
            return r[c.Infra.WorkspaceMode].fail(gitmodule_result.error)
        gitmodule_url, gitmodule_branch = gitmodule_result.value
        origin = u.Cli.capture(
            [c.Infra.GIT, "config", "--get", "remote.origin.url"],
            cwd=member_root,
        )
        if origin.failure or not origin.value:
            return r[c.Infra.WorkspaceMode].fail(
                origin.error or f"workspace member origin is missing: {member_path}",
            )
        branch = u.Cli.capture(
            [c.Infra.GIT, "branch", "--show-current"],
            cwd=member_root,
        )
        if branch.failure or not branch.value:
            return r[c.Infra.WorkspaceMode].fail(
                branch.error or f"workspace member branch is missing: {member_path}",
            )
        if gitmodule_url != declared.url or origin.value != declared.url:
            return r[c.Infra.WorkspaceMode].fail(
                f"workspace member URL mismatch: {member_path}",
            )
        if gitmodule_branch != declared.branch or branch.value != declared.branch:
            return r[c.Infra.WorkspaceMode].fail(
                f"workspace member branch mismatch: {member_path}",
            )
        return r[c.Infra.WorkspaceMode].ok(c.Infra.WorkspaceMode.WORKSPACE)

    def detect(self, project_root: Path) -> p.Result[c.Infra.WorkspaceMode]:
        """Detect workspace mode from typed manifests and real Git metadata."""
        try:
            resolved_project_root = project_root.resolve()
        except c.EXC_OS_RUNTIME_TYPE as exc:
            return r[c.Infra.WorkspaceMode].fail_op("Workspace detection", exc)
        if not resolved_project_root.is_dir():
            return r[c.Infra.WorkspaceMode].fail(
                f"project root is not a directory: {resolved_project_root}",
            )

        workspace_spec: m.Infra.WorkspaceSpec | None = None
        local_manifest = self._manifest_path(resolved_project_root)
        if local_manifest.is_file():
            local_result = self.load_workspace_spec(resolved_project_root)
            if local_result.failure:
                return r[c.Infra.WorkspaceMode].fail(local_result.error)
            # mro-i6nq.10: Unwrap only after the fail-closed result branch.
            local_spec = local_result.unwrap()
            local_contract = self._validate_local_repository(
                local_spec.repository,
            )
            if local_contract.failure:
                return r[c.Infra.WorkspaceMode].fail(local_contract.error)
            workspace_spec = local_spec

        git_probe = u.Cli.run_raw(
            [c.Infra.GIT, "rev-parse", "--is-inside-work-tree"],
            cwd=resolved_project_root,
        )
        if git_probe.failure:
            return r[c.Infra.WorkspaceMode].fail(
                git_probe.error or "unable to execute Git workspace probe",
            )
        if git_probe.value.exit_code != 0:
            if (resolved_project_root / c.Infra.GIT_DIR).exists():
                return r[c.Infra.WorkspaceMode].fail(
                    git_probe.value.stderr.strip() or "invalid Git repository metadata",
                )
            return r[c.Infra.WorkspaceMode].ok(
                self._unattached_mode(workspace_spec),
            )

        superproject_result = u.Cli.capture(
            [c.Infra.GIT, "rev-parse", "--show-superproject-working-tree"],
            cwd=resolved_project_root,
        )
        if superproject_result.failure:
            return r[c.Infra.WorkspaceMode].fail(
                superproject_result.error or "unable to resolve Git superproject",
            )
        if not superproject_result.value:
            return r[c.Infra.WorkspaceMode].ok(
                self._unattached_mode(workspace_spec),
            )
        return self._detect_attached(
            resolved_project_root,
            Path(superproject_result.value).resolve(),
            workspace_spec,
        )

    @override
    def execute(self) -> p.Result[c.Infra.WorkspaceMode]:
        """Execute the workspace detection flow."""
        return self.detect(self.workspace_root)


__all__: list[str] = ["FlextInfraWorkspaceDetector"]
