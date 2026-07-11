"""Tests for public, manifest-backed workspace mode detection."""

from __future__ import annotations

from pathlib import Path

from flext_tests import tm

from flext_infra.workspace.detector import FlextInfraWorkspaceDetector
from tests import c, m, u


class TestsFlextInfraInfraWorkspaceDetector:
    """Exercise detection through real manifests and Git repositories."""

    # NOTE (multi-agent, mro-wkii.17.10 / agent: implement_topology_detector):
    # scenarios build real Git topology and assert only the detector's public result.

    @staticmethod
    def _repository(
        *,
        name: str,
        path: str,
        role: c.Infra.RepositoryRole,
        profile: c.Infra.MakeProfile,
        url: str | None = None,
        branch: str = "main",
    ) -> m.Infra.RepositoryRef:
        """Build one typed manifest repository contract."""
        return m.Infra.RepositoryRef(
            name=name,
            distribution=name,
            provider="flext",
            url=url or f"https://github.com/flext-sh/{name}.git",
            branch=branch,
            path=path,
            role=role,
            state=c.Infra.RepositoryState.ACTIVE,
            profile=profile,
        )

    @staticmethod
    def _write_manifest(
        repository_root: Path,
        repository: m.Infra.RepositoryRef,
        *,
        members: tuple[m.Infra.RepositoryRef, ...] = (),
    ) -> None:
        """Write one schema-shaped manifest through the public YAML facade."""
        spec = m.Infra.WorkspaceSpec(
            version=1,
            name=repository.name,
            repository=repository,
            members=members,
            content_only=(),
            exclusions=(),
        )
        tm.ok(
            u.Cli.yaml_dump(
                repository_root / "config" / "workspace.yaml",
                spec.model_dump(mode="json", exclude_none=True),
            ),
        )

    @staticmethod
    def _initialize_repository(repository_root: Path) -> None:
        """Create a real main-branch Git repository with one commit."""
        repository_root.mkdir(parents=True)
        tm.ok(
            u.Cli.run_checked(
                ["git", "init", "-q", "-b", "main"],
                cwd=repository_root,
            ),
        )
        tm.ok(
            u.Cli.run_checked(
                ["git", "config", "user.email", "infra@example.com"],
                cwd=repository_root,
            ),
        )
        tm.ok(
            u.Cli.run_checked(
                ["git", "config", "user.name", "Infra Tests"],
                cwd=repository_root,
            ),
        )
        (repository_root / "README.md").write_text(
            "# Repository\n",
            encoding="utf-8",
        )
        tm.ok(u.Cli.run_checked(["git", "add", "README.md"], cwd=repository_root))
        tm.ok(
            u.Cli.run_checked(
                ["git", "commit", "-q", "-m", "Initial commit"],
                cwd=repository_root,
            ),
        )

    @classmethod
    def _attached_member(
        cls,
        tmp_path: Path,
        *,
        declare_member: bool = True,
        member_profile: c.Infra.MakeProfile = c.Infra.MakeProfile.WORKSPACE_MEMBER,
    ) -> Path:
        """Create a real Git superproject and checked-out submodule."""
        workspace_root = tmp_path / "workspace"
        source_root = tmp_path / "member-source"
        cls._initialize_repository(workspace_root)
        cls._initialize_repository(source_root)
        member_path = "members/flext-member"
        tm.ok(
            u.Cli.run_checked(
                [
                    "git",
                    "-c",
                    "protocol.file.allow=always",
                    "submodule",
                    "add",
                    "-q",
                    "-b",
                    "main",
                    str(source_root),
                    member_path,
                ],
                cwd=workspace_root,
            ),
        )
        member_root = workspace_root / member_path
        canonical_url = "https://github.com/flext-sh/flext-member.git"
        section = "submodule.members/flext-member"
        tm.ok(
            u.Cli.run_checked(
                ["git", "remote", "set-url", "origin", canonical_url],
                cwd=member_root,
            ),
        )
        tm.ok(
            u.Cli.run_checked(
                [
                    "git",
                    "config",
                    "--file",
                    ".gitmodules",
                    f"{section}.url",
                    canonical_url,
                ],
                cwd=workspace_root,
            ),
        )
        root_repository = cls._repository(
            name="workspace-root",
            path=".",
            role=c.Infra.RepositoryRole.WORKSPACE_ROOT,
            profile=c.Infra.MakeProfile.WORKSPACE_ROOT,
        )
        declared_repository = cls._repository(
            name="flext-member",
            path=member_path,
            role=c.Infra.RepositoryRole.WORKSPACE_MEMBER,
            profile=member_profile,
            url=canonical_url,
        )
        local_repository = cls._repository(
            name="flext-member",
            path=".",
            role=c.Infra.RepositoryRole.WORKSPACE_MEMBER,
            profile=c.Infra.MakeProfile.WORKSPACE_MEMBER,
            url=canonical_url,
        )
        cls._write_manifest(
            workspace_root,
            root_repository,
            members=(declared_repository,) if declare_member else (),
        )
        cls._write_manifest(member_root, local_repository)
        return member_root

    def test_root_manifest_declares_workspace(self, tmp_path: Path) -> None:
        root_repository = self._repository(
            name="workspace-root",
            path=".",
            role=c.Infra.RepositoryRole.WORKSPACE_ROOT,
            profile=c.Infra.MakeProfile.WORKSPACE_ROOT,
        )
        self._write_manifest(tmp_path, root_repository)

        tm.ok(
            FlextInfraWorkspaceDetector().detect(tmp_path),
            eq=c.Infra.WorkspaceMode.WORKSPACE,
        )

    def test_ancestor_gitmodules_does_not_attach_project(self, tmp_path: Path) -> None:
        project_root = tmp_path / "nested" / "project"
        project_root.mkdir(parents=True)
        (tmp_path / ".gitmodules").write_text("", encoding="utf-8")

        tm.ok(
            FlextInfraWorkspaceDetector().detect(project_root),
            eq=c.Infra.WorkspaceMode.STANDALONE,
        )

    def test_independent_member_clone_is_standalone(self, tmp_path: Path) -> None:
        project_root = tmp_path / "flext-member"
        self._initialize_repository(project_root)
        member_repository = self._repository(
            name="flext-member",
            path=".",
            role=c.Infra.RepositoryRole.WORKSPACE_MEMBER,
            profile=c.Infra.MakeProfile.WORKSPACE_MEMBER,
        )
        self._write_manifest(project_root, member_repository)

        tm.ok(
            FlextInfraWorkspaceDetector().detect(project_root),
            eq=c.Infra.WorkspaceMode.STANDALONE,
        )

    def test_declared_real_submodule_is_workspace(self, tmp_path: Path) -> None:
        member_root = self._attached_member(tmp_path)

        tm.ok(
            FlextInfraWorkspaceDetector().detect(member_root),
            eq=c.Infra.WorkspaceMode.WORKSPACE,
        )

    def test_unknown_submodule_path_fails_closed(self, tmp_path: Path) -> None:
        member_root = self._attached_member(tmp_path, declare_member=False)

        tm.fail(
            FlextInfraWorkspaceDetector().detect(member_root),
            has="not one active workspace member",
        )

    def test_member_profile_mismatch_fails_closed(self, tmp_path: Path) -> None:
        member_root = self._attached_member(
            tmp_path,
            member_profile=c.Infra.MakeProfile.STANDALONE,
        )

        tm.fail(
            FlextInfraWorkspaceDetector().detect(member_root),
            has="role/state/profile mismatch",
        )

    def test_gitmodule_url_mismatch_fails_closed(self, tmp_path: Path) -> None:
        member_root = self._attached_member(tmp_path)
        workspace_root = member_root.parents[1]
        tm.ok(
            u.Cli.run_checked(
                [
                    "git",
                    "config",
                    "--file",
                    ".gitmodules",
                    "submodule.members/flext-member.url",
                    "https://github.com/other-org/flext-member.git",
                ],
                cwd=workspace_root,
            ),
        )

        tm.fail(
            FlextInfraWorkspaceDetector().detect(member_root),
            has="URL mismatch",
        )

    def test_gitmodule_branch_mismatch_fails_closed(self, tmp_path: Path) -> None:
        member_root = self._attached_member(tmp_path)
        workspace_root = member_root.parents[1]
        tm.ok(
            u.Cli.run_checked(
                [
                    "git",
                    "config",
                    "--file",
                    ".gitmodules",
                    "submodule.members/flext-member.branch",
                    "release",
                ],
                cwd=workspace_root,
            ),
        )

        tm.fail(
            FlextInfraWorkspaceDetector().detect(member_root),
            has="branch mismatch",
        )

    def test_malformed_parent_manifest_fails(self, tmp_path: Path) -> None:
        member_root = self._attached_member(tmp_path)
        parent_manifest = member_root.parents[1] / "config" / "workspace.yaml"
        parent_manifest.write_text("version: malformed\n", encoding="utf-8")

        tm.fail(
            FlextInfraWorkspaceDetector().detect(member_root),
            has="workspace",
        )

    def test_malformed_local_manifest_fails(self, tmp_path: Path) -> None:
        manifest = tmp_path / "config" / "workspace.yaml"
        manifest.parent.mkdir()
        manifest.write_text("version: malformed\n", encoding="utf-8")

        tm.fail(
            FlextInfraWorkspaceDetector().detect(tmp_path),
            has="workspace",
        )

    def test_execute_uses_workspace_root(self, tmp_path: Path) -> None:
        tm.ok(
            FlextInfraWorkspaceDetector(workspace_root=tmp_path).execute(),
            eq=c.Infra.WorkspaceMode.STANDALONE,
        )

    def test_invalid_path_returns_failure(self) -> None:
        tm.fail(
            FlextInfraWorkspaceDetector().detect(Path("\0")),
            has="Workspace detection failed",
        )
