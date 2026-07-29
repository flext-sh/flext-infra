"""Tests for public, manifest-backed workspace mode detection."""

from __future__ import annotations

from pathlib import Path

from flext_infra import config
from flext_infra.workspace.detector import FlextInfraWorkspaceDetector
from flext_tests import tm
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
            path=Path(path),
            role=role,
            state=c.Infra.RepositoryState.ACTIVE,
            profile=profile,
            checkout=(
                c.Infra.CheckoutKind.ROOT
                if role is c.Infra.RepositoryRole.WORKSPACE_ROOT
                else c.Infra.CheckoutKind.SUBMODULE
            ),
            codegen=c.Infra.CodegenKind.CONFORM,
            package=role is not c.Infra.RepositoryRole.WORKSPACE_ROOT,
            editable=role is c.Infra.RepositoryRole.WORKSPACE_MEMBER,
            read_only=False,
        )

    @staticmethod
    def _write_manifest(
        repository_root: Path,
        repository: m.Infra.RepositoryRef,
        *,
        members: tuple[m.Infra.RepositoryRef, ...] = (),
        content_only: tuple[m.Infra.RepositoryRef, ...] = (),
    ) -> None:
        """Write one schema-shaped manifest through the public YAML facade."""
        spec = m.Infra.WorkspaceSpec(
            version=c.Infra.WORKSPACE_MANIFEST_VERSION,
            name=repository.name,
            repository=repository,
            members=members,
            content_only=content_only,
            exclusions=(),
        )
        tm.ok(
            u.Cli.yaml_dump(
                repository_root / "config" / "workspace.yaml",
                spec.model_dump(mode="json", exclude_none=True),
            )
        )

    @staticmethod
    def _initialize_repository(repository_root: Path) -> None:
        """Create a real main-branch Git repository with one commit."""
        repository_root.mkdir(parents=True, exist_ok=True)
        tm.ok(
            u.Cli.run_checked(["git", "init", "-q", "-b", "main"], cwd=repository_root)
        )
        tm.ok(
            u.Cli.run_checked(
                ["git", "config", "user.email", "infra@example.com"],
                cwd=repository_root,
            )
        )
        tm.ok(
            u.Cli.run_checked(
                ["git", "config", "user.name", "Infra Tests"], cwd=repository_root
            )
        )
        (repository_root / "README.md").write_text("# Repository\n", encoding="utf-8")
        tm.ok(u.Cli.run_checked(["git", "add", "README.md"], cwd=repository_root))
        tm.ok(
            u.Cli.run_checked(
                ["git", "commit", "-q", "-m", "Initial commit"], cwd=repository_root
            )
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
            )
        )
        member_root = workspace_root / member_path
        canonical_url = "https://github.com/flext-sh/flext-member.git"
        section = "submodule.members/flext-member"
        tm.ok(
            u.Cli.run_checked(
                ["git", "remote", "set-url", "origin", canonical_url], cwd=member_root
            )
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
            )
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

    @classmethod
    def _external_repository(cls, path: str) -> m.Infra.RepositoryRef:
        """Build one typed, read-only content checkout contract."""
        return cls._repository(
            name=Path(path).name,
            path=path,
            role=c.Infra.RepositoryRole.CONTENT_ONLY,
            profile=c.Infra.MakeProfile.WORKSPACE_MEMBER,
        ).model_copy(
            update={
                "state": c.Infra.RepositoryState.CONTENT_ONLY,
                "codegen": c.Infra.CodegenKind.NONE,
                "package": False,
                "editable": False,
                "read_only": True,
            }
        )

    def test_root_manifest_without_gitlinks_is_standalone(self, tmp_path: Path) -> None:
        """Treat the manifest as metadata, never as runtime topology evidence."""
        root_repository = self._repository(
            name="workspace-root",
            path=".",
            role=c.Infra.RepositoryRole.WORKSPACE_ROOT,
            profile=c.Infra.MakeProfile.WORKSPACE_ROOT,
        )
        self._write_manifest(tmp_path, root_repository)

        tm.ok(
            FlextInfraWorkspaceDetector().detect(tmp_path),
            eq=c.Infra.WorkspaceMode.STANDALONE,
        )

    def test_ancestor_gitmodules_does_not_attach_project(self, tmp_path: Path) -> None:
        """Ignore an ancestor .gitmodules file without real Git attachment."""
        project_root = tmp_path / "nested" / "project"
        project_root.mkdir(parents=True)
        (tmp_path / ".gitmodules").write_text("", encoding="utf-8")

        tm.ok(
            FlextInfraWorkspaceDetector().detect(project_root),
            eq=c.Infra.WorkspaceMode.STANDALONE,
        )

    def test_empty_local_gitmodules_without_gitlinks_is_standalone(
        self, tmp_path: Path
    ) -> None:
        self._initialize_repository(tmp_path)
        (tmp_path / c.Infra.GITMODULES).write_text("", encoding="utf-8")

        topology = tm.ok(FlextInfraWorkspaceDetector.inspect(tmp_path))
        tm.that(topology.mode, eq=c.Infra.WorkspaceMode.STANDALONE)
        tm.that(topology.managed_gitlinks, eq=())
        tm.that(topology.external_gitlinks, eq=())

    def test_content_only_gitlinks_do_not_create_a_workspace(
        self, tmp_path: Path
    ) -> None:
        member_root = self._attached_member(tmp_path)
        workspace_root = member_root.parents[1]
        root_repository = self._repository(
            name="workspace-root",
            path=".",
            role=c.Infra.RepositoryRole.WORKSPACE_ROOT,
            profile=c.Infra.MakeProfile.WORKSPACE_ROOT,
        )
        external = self._external_repository("members/flext-member")
        self._write_manifest(
            workspace_root, root_repository, content_only=(external,)
        )

        topology = tm.ok(FlextInfraWorkspaceDetector.inspect(workspace_root))

        tm.that(topology.mode, eq=c.Infra.WorkspaceMode.STANDALONE)
        tm.that(topology.managed_gitlinks, eq=())
        tm.that(topology.external_gitlinks, eq=("members/flext-member",))

    def test_mixed_gitlinks_classify_ownership_without_external_fanout(
        self, tmp_path: Path
    ) -> None:
        member_root = self._attached_member(tmp_path)
        workspace_root = member_root.parents[1]
        external_source = tmp_path / "external-source"
        self._initialize_repository(external_source)
        external_path = "vendor/external-content"
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
                    str(external_source),
                    external_path,
                ],
                cwd=workspace_root,
            )
        )
        root_repository = self._repository(
            name="workspace-root",
            path=".",
            role=c.Infra.RepositoryRole.WORKSPACE_ROOT,
            profile=c.Infra.MakeProfile.WORKSPACE_ROOT,
        )
        managed = self._repository(
            name="flext-member",
            path="members/flext-member",
            role=c.Infra.RepositoryRole.WORKSPACE_MEMBER,
            profile=c.Infra.MakeProfile.WORKSPACE_MEMBER,
        )
        external = self._external_repository(external_path)
        self._write_manifest(
            workspace_root,
            root_repository,
            members=(managed,),
            content_only=(external,),
        )

        topology = tm.ok(FlextInfraWorkspaceDetector.inspect(workspace_root))

        tm.that(topology.mode, eq=c.Infra.WorkspaceMode.WORKSPACE)
        tm.that(topology.managed_gitlinks, eq=("members/flext-member",))
        tm.that(topology.external_gitlinks, eq=(external_path,))

    def test_independent_member_clone_is_standalone(self, tmp_path: Path) -> None:
        """Classify an independently cloned member as standalone."""
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

    def test_repository_with_indexed_submodule_is_workspace(
        self, tmp_path: Path
    ) -> None:
        """Classify the gitlink owner, not its attached member, as workspace."""
        member_root = self._attached_member(tmp_path)
        workspace_root = member_root.parents[1]

        tm.ok(
            FlextInfraWorkspaceDetector().detect(workspace_root),
            eq=c.Infra.WorkspaceMode.WORKSPACE,
        )
        tm.ok(
            FlextInfraWorkspaceDetector().detect(member_root),
            eq=c.Infra.WorkspaceMode.STANDALONE,
        )

    def test_attached_member_feature_branch_is_standalone(
        self, tmp_path: Path
    ) -> None:
        member_root = self._attached_member(tmp_path)
        tm.ok(
            u.Cli.run_checked(
                ["git", "switch", "-q", "-c", "feature/gitlink-validation"],
                cwd=member_root,
            )
        )

        tm.ok(
            FlextInfraWorkspaceDetector().detect(member_root),
            eq=c.Infra.WorkspaceMode.STANDALONE,
        )

    def test_attached_member_detached_head_is_standalone(
        self, tmp_path: Path
    ) -> None:
        member_root = self._attached_member(tmp_path)
        tm.ok(
            u.Cli.run_checked(
                ["git", "switch", "-q", "--detach", "HEAD"], cwd=member_root
            )
        )

        tm.ok(
            FlextInfraWorkspaceDetector().detect(member_root),
            eq=c.Infra.WorkspaceMode.STANDALONE,
        )

    def test_workspace_mode_depends_on_index_not_member_head(
        self, tmp_path: Path
    ) -> None:
        member_root = self._attached_member(tmp_path)
        workspace_root = member_root.parents[1]
        (member_root / "member-change.txt").write_text("changed\n", encoding="utf-8")
        tm.ok(u.Cli.run_checked(["git", "add", "member-change.txt"], cwd=member_root))
        tm.ok(
            u.Cli.run_checked(
                ["git", "commit", "-q", "-m", "Member change"], cwd=member_root
            )
        )

        tm.ok(
            FlextInfraWorkspaceDetector().detect(workspace_root),
            eq=c.Infra.WorkspaceMode.WORKSPACE,
        )

    def test_uninitialized_indexed_submodule_keeps_workspace_profile(
        self, tmp_path: Path
    ) -> None:
        """Use the committed gitlink even when its working tree is not initialized."""
        member_root = self._attached_member(tmp_path)
        workspace_root = member_root.parents[1]
        tm.ok(
            u.Cli.run_checked(
                ["git", "submodule", "deinit", "-q", "-f", "--all"],
                cwd=workspace_root,
            )
        )

        tm.ok(
            FlextInfraWorkspaceDetector().detect(workspace_root),
            eq=c.Infra.WorkspaceMode.WORKSPACE,
        )

    def test_current_repository_resolution_never_crosses_gitlink(
        self, tmp_path: Path
    ) -> None:
        member_root = self._attached_member(tmp_path)

        tm.that(
            tm.ok(
                FlextInfraWorkspaceDetector.resolve_repository_root(member_root)
            ),
            eq=member_root.resolve(),
        )

    def test_inspection_derives_attached_standalone_without_beads(
        self, tmp_path: Path
    ) -> None:
        member_root = self._attached_member(tmp_path)
        declared = self._repository(
            name="flext-member",
            path="members/flext-member",
            role=c.Infra.RepositoryRole.WORKSPACE_MEMBER,
            profile=c.Infra.MakeProfile.WORKSPACE_MEMBER,
        )

        topology = tm.ok(FlextInfraWorkspaceDetector.inspect(member_root, declared))
        effective = topology.repository
        tm.that(effective is not None, eq=True)
        assert effective is not None
        tm.that(effective.path, eq=declared.path)
        tm.that(effective.role, eq=c.Infra.RepositoryRole.STANDALONE)
        tm.that(effective.profile, eq=c.Infra.MakeProfile.STANDALONE)
        tm.that(effective.checkout, eq=c.Infra.CheckoutKind.SUBMODULE)
        tm.that(topology.attached, eq=True)
        tm.that(topology.beads_enabled, eq=False)

    def test_attached_member_rejects_beads_overlay(self, tmp_path: Path) -> None:
        member_root = self._attached_member(tmp_path)
        declared = self._repository(
            name="flext-member",
            path="members/flext-member",
            role=c.Infra.RepositoryRole.WORKSPACE_MEMBER,
            profile=c.Infra.MakeProfile.WORKSPACE_MEMBER,
        )
        overlay = m.Infra.RepositoryRef.model_validate({
            **declared.model_dump(),
            "beads": True,
        })

        tm.fail(
            FlextInfraWorkspaceDetector.inspect(member_root, overlay),
            has="forbidden for an attached Git submodule",
        )

    def test_gitmodules_without_indexed_gitlink_fails_closed(
        self, tmp_path: Path
    ) -> None:
        member_root = self._attached_member(tmp_path)
        workspace_root = member_root.parents[1]
        tm.ok(
            u.Cli.run_checked(
                ["git", "add", c.Infra.GITMODULES], cwd=workspace_root
            )
        )
        tm.ok(
            u.Cli.run_checked(
                ["git", "rm", "--cached", "-q", "-f", "members/flext-member"],
                cwd=workspace_root,
            )
        )

        tm.fail(
            FlextInfraWorkspaceDetector().detect(workspace_root),
            has="declared Git submodules and indexed gitlinks differ",
        )

    def test_parent_manifest_does_not_control_member_runtime_profile(
        self, tmp_path: Path
    ) -> None:
        member_root = self._attached_member(tmp_path)
        parent_manifest = member_root.parents[1] / "config" / "workspace.yaml"
        parent_manifest.write_text("version: malformed\n", encoding="utf-8")

        tm.fail(FlextInfraWorkspaceDetector().detect(member_root), has="workspace")

    def test_unknown_submodule_path_fails_closed(self, tmp_path: Path) -> None:
        member_root = self._attached_member(tmp_path, declare_member=False)

        tm.fail(
            FlextInfraWorkspaceDetector().detect(member_root),
            has="not one active workspace member",
        )

    def test_member_profile_mismatch_fails_closed(self, tmp_path: Path) -> None:
        member_root = self._attached_member(
            tmp_path, member_profile=c.Infra.MakeProfile.STANDALONE
        )

        tm.fail(
            FlextInfraWorkspaceDetector().detect(member_root),
            has="role/state/profile/checkout mismatch",
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
            )
        )

        tm.fail(FlextInfraWorkspaceDetector().detect(member_root), has="URL mismatch")

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
            )
        )

        tm.fail(
            FlextInfraWorkspaceDetector().detect(member_root), has="branch mismatch"
        )

    def test_member_head_mismatch_fails_closed(self, tmp_path: Path) -> None:
        member_root = self._attached_member(tmp_path)
        (member_root / "change.txt").write_text("changed\n", encoding="utf-8")
        tm.ok(u.Cli.run_checked(["git", "add", "change.txt"], cwd=member_root))
        tm.ok(
            u.Cli.run_checked(
                ["git", "commit", "-q", "-m", "change"], cwd=member_root
            )
        )

        tm.fail(
            FlextInfraWorkspaceDetector().detect(member_root),
            has="workspace member gitlink mismatch",
        )

    def test_malformed_local_manifest_fails(self, tmp_path: Path) -> None:
        """Reject a malformed repository-local manifest."""
        manifest = tmp_path / "config" / "workspace.yaml"
        manifest.parent.mkdir()
        manifest.write_text("version: malformed\n", encoding="utf-8")

        tm.fail(FlextInfraWorkspaceDetector().detect(tmp_path), has="workspace")

    def test_execute_uses_workspace_root(self, tmp_path: Path) -> None:
        """Execute detection against the detector's configured workspace root."""
        tm.ok(
            FlextInfraWorkspaceDetector(workspace_root=tmp_path).execute(),
            eq=c.Infra.WorkspaceMode.STANDALONE,
        )

    def test_invalid_path_returns_failure(self) -> None:
        """Return a typed failure for an invalid filesystem path."""
        tm.fail(
            FlextInfraWorkspaceDetector().detect(Path("\0")),
            has="Workspace detection failed",
        )

    def test_manifestless_repo_derives_spec_from_catalog(self, tmp_path: Path) -> None:
        """Derive a generic minimal spec from the catalog when no manifest exists."""
        # mro-4gbp: the engine catalog declares only repositories it owns, so the
        # fixture is derived from whatever this engine publishes - never a
        # hardcoded name and never a downstream consumer.
        declared = config.Infra.codegen.repositories[0]
        (tmp_path / "pyproject.toml").write_text(
            f'[project]\nname = "{declared.name}"\nversion = "0.0.0"\n',
            encoding="utf-8",
        )
        spec = tm.ok(FlextInfraWorkspaceDetector.load_workspace_spec(tmp_path))
        tm.that(spec.name, eq=declared.name)
        tm.that(spec.repository.role, eq=declared.role)
        tm.that(spec.version, eq=c.Infra.WORKSPACE_MANIFEST_VERSION)

    def test_manifestless_repo_absent_from_catalog_fails_closed(
        self, tmp_path: Path
    ) -> None:
        """Fail closed for a manifest-less project absent from the catalog."""
        (tmp_path / "pyproject.toml").write_text(
            '[project]\nname = "not-a-declared-flext-project"\nversion = "0.0.0"\n',
            encoding="utf-8",
        )
        tm.fail(
            FlextInfraWorkspaceDetector.load_workspace_spec(tmp_path),
            has="absent from the codegen catalog",
        )

    def test_manifested_repo_absent_from_catalog_loads_spec(
        self, tmp_path: Path
    ) -> None:
        """Load a valid manifest even when the project is absent from the catalog."""
        repository = self._repository(
            name="consumer-project",
            path=".",
            role=c.Infra.RepositoryRole.WORKSPACE_ROOT,
            profile=c.Infra.MakeProfile.WORKSPACE_ROOT,
        )
        self._write_manifest(tmp_path, repository)

        spec = tm.ok(FlextInfraWorkspaceDetector.load_workspace_spec(tmp_path))
        tm.that(spec.name, eq="consumer-project")
        tm.that(spec.repository.name, eq="consumer-project")
