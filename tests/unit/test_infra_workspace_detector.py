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
                else (
                    c.Infra.CheckoutKind.INDEPENDENT
                    if role is c.Infra.RepositoryRole.STANDALONE
                    else c.Infra.CheckoutKind.SUBMODULE
                )
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
        payload = spec.model_dump(mode="json", exclude_none=True)
        serialized_content = payload.get("content_only")
        if isinstance(serialized_content, list):
            for content_record in serialized_content:
                if isinstance(content_record, dict):
                    content_record["profile"] = None
        rendered = tm.ok(u.Cli.json_dumps(payload, indent=2))
        manifest = repository_root / "config" / "workspace.yaml"
        manifest.parent.mkdir(parents=True, exist_ok=True)
        tm.ok(u.Cli.atomic_write_text_file(manifest, f"{rendered}\n"))

    @staticmethod
    def _initialize_repository(repository_root: Path) -> None:
        """Create a real main-branch Git repository with one commit."""
        repository_root.mkdir(parents=True)
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

    def test_root_manifest_declares_workspace(self, tmp_path: Path) -> None:
        """Classify a repository with a root manifest as a workspace."""
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
        """Ignore an ancestor .gitmodules file without real Git attachment."""
        project_root = tmp_path / "nested" / "project"
        project_root.mkdir(parents=True)
        (tmp_path / ".gitmodules").write_text("", encoding="utf-8")

        tm.ok(
            FlextInfraWorkspaceDetector().detect(project_root),
            eq=c.Infra.WorkspaceMode.STANDALONE,
        )

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

    def test_conform_profile_is_derived_from_owned_submodules(
        self, tmp_path: Path
    ) -> None:
        """Only config-owned mutable submodules produce a workspace root."""
        root = tmp_path / "root"
        leaf = tmp_path / "leaf"
        root.mkdir()
        leaf.mkdir()
        root_repository = self._repository(
            name="project-root",
            path=".",
            role=c.Infra.RepositoryRole.WORKSPACE_ROOT,
            profile=c.Infra.MakeProfile.WORKSPACE_ROOT,
        )
        managed = self._repository(
            name="project-member",
            path="members/project-member",
            role=c.Infra.RepositoryRole.WORKSPACE_MEMBER,
            profile=c.Infra.MakeProfile.WORKSPACE_MEMBER,
        )
        leaf_repository = self._repository(
            name="project-member",
            path=".",
            role=c.Infra.RepositoryRole.STANDALONE,
            profile=c.Infra.MakeProfile.STANDALONE,
        )
        self._write_manifest(root, root_repository, members=(managed,))
        self._write_manifest(leaf, leaf_repository)

        root_effective = tm.ok(
            FlextInfraWorkspaceDetector.effective_repository(root, root_repository)
        )
        leaf_effective = tm.ok(
            FlextInfraWorkspaceDetector.effective_repository(leaf, leaf_repository)
        )

        tm.that(root_effective.profile, eq=c.Infra.MakeProfile.WORKSPACE_ROOT)
        tm.that(leaf_effective.profile, eq=c.Infra.MakeProfile.STANDALONE)
        tm.that(leaf_effective.role, eq=c.Infra.RepositoryRole.STANDALONE)

    def test_content_only_fork_is_immutable_and_excluded_not_workspace(
        self, tmp_path: Path
    ) -> None:
        """A physical third-party checkout never becomes managed topology."""
        root = self._repository(
            name="consumer",
            path=".",
            role=c.Infra.RepositoryRole.WORKSPACE_ROOT,
            profile=c.Infra.MakeProfile.WORKSPACE_ROOT,
        )
        fork = self._repository(
            name="upstream-fork",
            path="vendor/upstream-fork",
            role=c.Infra.RepositoryRole.WORKSPACE_MEMBER,
            profile=c.Infra.MakeProfile.WORKSPACE_MEMBER,
        ).model_copy(
            update={
                "role": c.Infra.RepositoryRole.CONTENT_ONLY,
                "state": c.Infra.RepositoryState.CONTENT_ONLY,
                "profile": None,
                "codegen": c.Infra.CodegenKind.NONE,
                "package": False,
                "editable": False,
                "read_only": True,
            }
        )
        self._write_manifest(tmp_path, root, content_only=(fork,))

        effective = tm.ok(
            FlextInfraWorkspaceDetector.effective_repository(tmp_path, root)
        )
        excluded = tm.ok(FlextInfraWorkspaceDetector.analysis_exclusion_paths(tmp_path))

        tm.that(effective.profile, eq=c.Infra.MakeProfile.STANDALONE)
        tm.that(excluded, eq=(Path("vendor/upstream-fork"),))

    def test_conform_overlay_is_explicit_legacy_exception(self, tmp_path: Path) -> None:
        """A typed overlay can preserve one legacy topology."""
        declared = self._repository(
            name="legacy",
            path="legacy",
            role=c.Infra.RepositoryRole.WORKSPACE_MEMBER,
            profile=c.Infra.MakeProfile.WORKSPACE_MEMBER,
        )
        overlay = m.Infra.ProjectConformOverlay(
            profile=c.Infra.MakeProfile.WORKSPACE_MEMBER
        )

        effective = tm.ok(
            FlextInfraWorkspaceDetector.effective_repository(
                tmp_path, declared, overlay
            )
        )

        tm.that(effective.profile, eq=c.Infra.MakeProfile.WORKSPACE_MEMBER)

    def test_beads_namespace_defaults_to_project_name_with_legacy_overlay(
        self, tmp_path: Path
    ) -> None:
        """Workspace trackers use project identity unless explicitly overlaid."""
        (tmp_path / ".beads").mkdir()
        (tmp_path / ".gitmodules").write_text("", encoding="utf-8")
        declared = self._repository(
            name="project-root",
            path=".",
            role=c.Infra.RepositoryRole.WORKSPACE_ROOT,
            profile=c.Infra.MakeProfile.WORKSPACE_ROOT,
        )
        member = self._repository(
            name="project-member",
            path="project-member",
            role=c.Infra.RepositoryRole.WORKSPACE_MEMBER,
            profile=c.Infra.MakeProfile.WORKSPACE_MEMBER,
        )
        self._write_manifest(tmp_path, declared, members=(member,))
        tm.ok(
            u.Cli.yaml_dump(
                tmp_path / ".beads" / "config.yaml", {"issue-prefix": "project-root"}
            )
        )
        tm.ok(FlextInfraWorkspaceDetector.validate_beads_namespace(tmp_path, declared))
        tm.ok(
            u.Cli.yaml_dump(
                tmp_path / ".beads" / "config.yaml", {"issue-prefix": "mro"}
            )
        )

        tm.ok(
            FlextInfraWorkspaceDetector.validate_beads_namespace(
                tmp_path, declared, m.Infra.ProjectConformOverlay(beads_namespace="mro")
            )
        )

    def test_declared_real_submodule_is_workspace(self, tmp_path: Path) -> None:
        """Classify a declared and attached Git submodule as a workspace member."""
        member_root = self._attached_member(tmp_path)

        tm.ok(
            FlextInfraWorkspaceDetector().detect(member_root),
            eq=c.Infra.WorkspaceMode.WORKSPACE,
        )

    def test_feature_branch_at_gitlink_is_workspace(self, tmp_path: Path) -> None:
        member_root = self._attached_member(tmp_path)
        tm.ok(
            u.Cli.run_checked(
                ["git", "switch", "-q", "-c", "feature/gitlink-validation"],
                cwd=member_root,
            )
        )

        tm.ok(
            FlextInfraWorkspaceDetector().detect(member_root),
            eq=c.Infra.WorkspaceMode.WORKSPACE,
        )

    def test_detached_head_at_gitlink_is_workspace(self, tmp_path: Path) -> None:
        member_root = self._attached_member(tmp_path)
        tm.ok(
            u.Cli.run_checked(
                ["git", "switch", "-q", "--detach", "HEAD"], cwd=member_root
            )
        )

        tm.ok(
            FlextInfraWorkspaceDetector().detect(member_root),
            eq=c.Infra.WorkspaceMode.WORKSPACE,
        )

    def test_member_head_different_from_gitlink_fails_closed(
        self, tmp_path: Path
    ) -> None:
        member_root = self._attached_member(tmp_path)
        (member_root / "member-change.txt").write_text("changed\n", encoding="utf-8")
        tm.ok(u.Cli.run_checked(["git", "add", "member-change.txt"], cwd=member_root))
        tm.ok(
            u.Cli.run_checked(
                ["git", "commit", "-q", "-m", "Member change"], cwd=member_root
            )
        )

        tm.fail(
            FlextInfraWorkspaceDetector().detect(member_root),
            has="workspace member gitlink mismatch",
        )

    def test_unknown_submodule_path_fails_closed(self, tmp_path: Path) -> None:
        """Reject an attached submodule absent from the parent manifest."""
        member_root = self._attached_member(tmp_path, declare_member=False)

        tm.fail(
            FlextInfraWorkspaceDetector().detect(member_root),
            has="not one active workspace member",
        )

    def test_member_profile_mismatch_fails_closed(self, tmp_path: Path) -> None:
        """Reject a member whose declared profile conflicts with its role."""
        member_root = self._attached_member(
            tmp_path, member_profile=c.Infra.MakeProfile.STANDALONE
        )

        tm.fail(
            FlextInfraWorkspaceDetector().detect(member_root),
            has="role/state/profile/checkout mismatch",
        )

    def test_gitmodule_url_mismatch_fails_closed(self, tmp_path: Path) -> None:
        """Reject a Git submodule whose configured URL differs from the manifest."""
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
        """Reject a Git submodule whose configured branch differs from the manifest."""
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

    def test_malformed_parent_manifest_fails(self, tmp_path: Path) -> None:
        """Reject an attached member when the parent manifest is malformed."""
        member_root = self._attached_member(tmp_path)
        parent_manifest = member_root.parents[1] / "config" / "workspace.yaml"
        parent_manifest.write_text("version: malformed\n", encoding="utf-8")

        tm.fail(FlextInfraWorkspaceDetector().detect(member_root), has="workspace")

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
