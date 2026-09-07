"""Repository-local topology contracts."""

from __future__ import annotations

import shutil
from datetime import UTC, datetime
from pathlib import Path

import pytest

from flext_infra import c, m, t
from flext_infra.workspace.detector import FlextInfraWorkspaceDetector
from flext_tests import tm
from tests import u
from tests.unit.workspace import WorktreeFixture


class TestsRepositoryLocalTopology:
    """Prove each repository owns topology through PEP 621 and local Git facts."""

    def test_selected_workspace_manifest_owns_repository_policy(
        self, tmp_path: Path
    ) -> None:
        """Preserve typed local policy after reconciling it with observed Git."""
        root = tmp_path / "manifest-policy"
        name = "fixture-manifest-policy"
        WorktreeFixture.initialize_governed_project(
            root,
            name,
            workspace=name,
            database=name.replace("-", "_"),
            issue_prefix=name,
        )
        exclusion = "fixture-manifest-policy-excluded"
        override = "fixture-manifest-policy-overridden"
        cutoff = datetime.now(UTC).isoformat()
        _ = WorktreeFixture.override_repository_manifest(
            root,
            {
                "kind": c.Infra.ProjectKind.THIRD_PARTY_FORK,
                "uv_link_mode": "clone",
                "dependency_cooldown_exclusions": (exclusion,),
                "dependency_cooldown_overrides": {override: cutoff},
            },
        )

        workspace = tm.ok(FlextInfraWorkspaceDetector.load_workspace_spec(root))

        tm.that(workspace.repository.kind, eq=c.Infra.ProjectKind.THIRD_PARTY_FORK)
        tm.that(workspace.repository.uv_link_mode, eq="clone")
        tm.that(workspace.repository.dependency_cooldown_exclusions, eq=(exclusion,))
        tm.that(
            workspace.repository.dependency_cooldown_overrides, eq={override: cutoff}
        )

    def test_selected_workspace_manifest_rejects_git_contradiction(
        self, tmp_path: Path
    ) -> None:
        """Fail closed when selected declarative identity disagrees with Git."""
        root = tmp_path / "manifest-contradiction"
        name = "fixture-manifest-contradiction"
        WorktreeFixture.initialize_governed_project(
            root,
            name,
            workspace=name,
            database=name.replace("-", "_"),
            issue_prefix=name,
        )
        _ = WorktreeFixture.override_repository_manifest(
            root, {"distribution": "different-distribution"}
        )

        result = FlextInfraWorkspaceDetector.load_workspace_spec(root)

        tm.fail(result, has="workspace manifest contradicts Git")
        tm.that(result.error or "", has="distribution")

    @pytest.mark.parametrize(
        ("overrides", "missing_field", "expected_error"),
        [
            pytest.param({"version": 4}, None, "version", id="unknown-version"),
            pytest.param(
                {"unknown_contract": True}, None, "unknown_contract", id="unknown-field"
            ),
            pytest.param({}, "name", "name", id="missing-name"),
        ],
    )
    def test_selected_workspace_manifest_validates_the_complete_document(
        self,
        tmp_path: Path,
        overrides: dict[str, t.JsonValue],
        missing_field: str | None,
        expected_error: str,
    ) -> None:
        """Reject incompatible or partial manifest envelopes before policy use."""
        root = tmp_path / expected_error
        name = f"fixture-{expected_error}"
        WorktreeFixture.initialize_governed_project(
            root,
            name,
            workspace=name,
            database=name.replace("-", "_"),
            issue_prefix=name,
        )
        observed = tm.ok(FlextInfraWorkspaceDetector.load_workspace_spec(root))
        payload: dict[str, t.JsonValue] = {
            "version": c.Infra.WORKSPACE_MANIFEST_VERSION,
            "name": name,
            "repository": observed.repository.model_dump(mode="json"),
        }
        payload.update(overrides)
        if missing_field is not None:
            del payload[missing_field]
        tm.ok(
            u.Cli.yaml_dump(
                root / "config" / c.Infra.WORKSPACE_MANIFEST_FILENAME, payload
            )
        )

        result = FlextInfraWorkspaceDetector.load_workspace_spec(root)

        tm.fail(result, has="workspace manifest model validation")
        tm.fail(result, has=expected_error)

    def test_loads_typed_beads_identity_from_the_repository_itself(
        self, tmp_path: Path
    ) -> None:
        """Missing or malformed dormant data cannot select an auxiliary capability."""
        root = tmp_path / "project"
        WorktreeFixture.initialize_governed_project(
            root,
            "fixture-project",
            workspace="fixture-workspace",
            database="fixture-database",
            issue_prefix="fixture-prefix",
        )
        dormant_path = root / "config" / "beads.yaml"
        if dormant_content is None:
            dormant_path.unlink()
        else:
            dormant_path.write_text(dormant_content, encoding="utf-8")
        before = dormant_path.read_bytes() if dormant_path.is_file() else None

        workspace = tm.ok(FlextInfraWorkspaceDetector.load_workspace_spec(root))

        tm.that(workspace.name, eq="fixture-project")
        tm.that(workspace.beads, none=True)
        after = dormant_path.read_bytes() if dormant_path.is_file() else None
        tm.that(after, eq=before)

    def test_gitmodules_without_governed_members_remains_standalone(
        self, tmp_path: Path
    ) -> None:
        """Vendored or empty Git topology does not create a FLEXT workspace."""
        root = tmp_path / "workspace"
        WorktreeFixture.initialize_governed_project(
            root,
            "fixture-workspace",
            workspace="fixture-workspace",
            database="fixture-database",
            issue_prefix="fixture-prefix",
        )
        WorktreeFixture.write_gitmodules(root, ())

        mode = tm.ok(FlextInfraWorkspaceDetector().detect(root))
        target = tm.ok(FlextInfraWorkspaceDetector.conform_target(root))

        tm.that(mode, eq=c.Infra.MakeProfile.STANDALONE)
        tm.that(target.make_profile, eq=c.Infra.MakeProfile.STANDALONE)

    def test_parent_gitmodules_never_classifies_or_governs_a_child(
        self, tmp_path: Path
    ) -> None:
        """Ignore every parent input when deriving one child repository."""
        parent = tmp_path / "parent"
        parent.mkdir()
        WorktreeFixture.write_gitmodules(parent, ("child",))
        child = parent / "child"
        WorktreeFixture.initialize_governed_project(
            child,
            "child",
            workspace="child-workspace",
            database="child-database",
            issue_prefix="child-prefix",
        )

        mode = tm.ok(FlextInfraWorkspaceDetector().detect(child))
        workspace = tm.ok(FlextInfraWorkspaceDetector.load_workspace_spec(child))
        resolved = tm.ok(
            u.Infra.git_show_toplevel(m.Infra.GitRepoRequest(repo_root=child))
        ).repository_root

        tm.that(mode, eq=c.Infra.MakeProfile.STANDALONE)
        tm.that(workspace.repository.name, eq="child")
        tm.that(workspace.name, eq="child-workspace")
        tm.that(u.Tests.required_beads(workspace).workspace, eq="child-workspace")
        tm.that(workspace.subprojects, empty=True)
        tm.that(resolved, eq=child.resolve())

    @staticmethod
    def _attached_member(tmp_path: Path) -> Path:
        """Attach a governed member to a parent workspace and return its path."""
        child_source = tmp_path / "child-source"
        WorktreeFixture.initialize_governed_project(
            child_source,
            "fixture-member",
            workspace="member-workspace",
            database="member-database",
            issue_prefix="member-prefix",
            beads_owner=False,
        )
        parent = tmp_path / "parent"
        WorktreeFixture.initialize_governed_project(
            parent,
            "fixture-parent",
            workspace="parent-workspace",
            database="parent-database",
            issue_prefix="parent-prefix",
        )
        member = parent / "apps" / "member"
        shutil.copytree(child_source, member)
        # A composed project follows the workspace ledger through its own
        # declared identity. The ``.beads -> ../.beads`` link that used to
        # carry it is prohibited, and both conform and the detector reject it.
        WorktreeFixture.write_beads_project(
            member,
            workspace="parent-workspace",
            database="parent-database",
            issue_prefix="parent-prefix",
        )
        provider = u.Tests.provider()
        (parent / ".gitmodules").write_text(
            '[submodule "fixture-member"]\n'
            "\tpath = apps/member\n"
            f"\turl = {WorktreeFixture.governed_repository_url('fixture-member')}\n"
            f"\tbranch = {provider.branch}\n",
            encoding="utf-8",
        )
        member_head = tm.ok(
            u.Cli.capture([c.Infra.GIT, "rev-parse", c.Infra.GIT_HEAD], cwd=member)
        )
        tm.ok(u.Cli.run_checked([c.Infra.GIT, "add", ".gitmodules"], cwd=parent))
        tm.ok(
            u.Cli.run_checked(
                [
                    c.Infra.GIT,
                    "update-index",
                    "--add",
                    "--cacheinfo",
                    f"160000,{member_head.strip()},apps/member",
                ],
                cwd=parent,
            )
        )
        tm.ok(
            u.Cli.run_checked(
                [c.Infra.GIT, "commit", "--quiet", "-m", "attach member"], cwd=parent
            )
        )
        return member

    def test_composed_self_load_records_its_workspace_checkout(
        self, tmp_path: Path
    ) -> None:
        """A composed project keeps its own coordinates and the root ledger."""
        member = self._attached_member(tmp_path)

        workspace = tm.ok(FlextInfraWorkspaceDetector.load_workspace_spec(member))

        # Topology is the declared role alone; being checked out inside a
        # workspace right now is the Git fact carried by ``editable``.
        tm.that(workspace.repository.path, eq=Path())
        tm.that(workspace.repository.role, eq=c.Infra.MakeProfile.STANDALONE)
        tm.that(workspace.repository.editable, eq=True)
        tm.that(workspace.beads.workspace, eq="parent-workspace")

    def test_composed_self_load_accepts_a_self_coordinate_manifest(
        self, tmp_path: Path
    ) -> None:
        """One manifest loads standalone and inside a workspace unchanged."""
        member = self._attached_member(tmp_path)
        _ = WorktreeFixture.override_repository_manifest(
            member, {"uv_link_mode": "clone"}
        )

        workspace = tm.ok(FlextInfraWorkspaceDetector.load_workspace_spec(member))

        tm.that(workspace.repository.path, eq=Path())
        tm.that(workspace.repository.role, eq=c.Infra.MakeProfile.STANDALONE)
        tm.that(workspace.repository.uv_link_mode, eq="clone")

    def test_standalone_rejects_a_manifest_that_claims_the_workspace_role(
        self, tmp_path: Path
    ) -> None:
        """A checkout without .gitmodules cannot declare the workspace role."""
        root = tmp_path / "manifest-role-claim"
        name = "fixture-manifest-role-claim"
        WorktreeFixture.initialize_governed_project(
            root,
            name,
            workspace=name,
            database=name.replace("-", "_"),
            issue_prefix=name,
        )
        _ = WorktreeFixture.override_repository_manifest(
            root, {"role": c.Infra.MakeProfile.WORKSPACE}
        )

        result = FlextInfraWorkspaceDetector.load_workspace_spec(root)

        tm.fail(result, has="role 'workspace' contradicts the observed topology")

    def test_workspace_members_inherit_a_single_ledger_identity(
        self, tmp_path: Path
    ) -> None:
        """Reject member-local identities and retain exactly the root ledger."""
        root = tmp_path / "workspace"
        WorktreeFixture.initialize_governed_project(
            root,
            "fixture-workspace",
            workspace="root-workspace",
            database="root-database",
            issue_prefix="root-prefix",
        )
        identities = {
            "fixture-alpha": ("alpha-workspace", "alpha-database", "alpha-prefix"),
            "fixture-beta": ("beta-workspace", "beta-database", "beta-prefix"),
        }
        for project_name, identity in identities.items():
            WorktreeFixture.initialize_governed_project(
                root / project_name,
                project_name,
                workspace=identity[0],
                database=identity[1],
                issue_prefix=identity[2],
                beads_owner=False,
            )
            WorktreeFixture.link_member_beads(
                root / project_name,
                root,
                workspace_name="root-workspace",
                database="root-database",
                issue_prefix="root-prefix",
            )
        WorktreeFixture.write_gitmodules(root, tuple(identities))

        workspace = tm.ok(FlextInfraWorkspaceDetector.load_workspace_spec(root))

        tm.that(
            tuple(project.path.as_posix() for project in workspace.subprojects),
            eq=tuple(identities),
        )
        tm.that(u.Tests.required_beads(workspace).workspace, eq="root-workspace")
        for project_name in identities:
            beads = tm.ok(
                FlextInfraWorkspaceDetector.load_beads_spec(root / project_name)
            )
            tm.that(beads.workspace, eq="root-workspace")
            tm.that(beads.database, eq="root-database")
            tm.that(beads.issue_prefix, eq="root-prefix")
            tm.that((root / project_name / ".beads").is_symlink(), eq=True)

    def test_workspace_excludes_governed_non_python_gitlinks_from_codegen(
        self, tmp_path: Path
    ) -> None:
        """Keep provider-owned services outside Python conformance ownership."""
        root = tmp_path / "workspace"
        WorktreeFixture.initialize_governed_project(
            root,
            "fixture-workspace",
            workspace="root-workspace",
            database="root-database",
            issue_prefix="root-prefix",
        )
        python_project = "fixture-python"
        WorktreeFixture.initialize_governed_project(
            root / python_project,
            python_project,
            workspace="python-workspace",
            database="python-database",
            issue_prefix="python-prefix",
            beads_owner=False,
        )
        WorktreeFixture.link_member_beads(
            root / python_project,
            root,
            workspace_name="root-workspace",
            database="root-database",
            issue_prefix="root-prefix",
        )
        service_project = "fixture-service"
        service_root = root / service_project
        service_root.mkdir()
        (service_root / "go.mod").write_text(
            "module github.com/flext-sh/fixture-service\n", encoding="utf-8"
        )
        u.Tests.initialize_git_repo(
            service_root,
            origin_url=WorktreeFixture.governed_repository_url(service_project),
        )
        WorktreeFixture.write_gitmodules(root, (python_project, service_project))

        workspace = tm.ok(FlextInfraWorkspaceDetector.load_workspace_spec(root))

        tm.that(
            tuple(project.path.as_posix() for project in workspace.subprojects),
            eq=(python_project,),
        )
        tm.that(workspace.external_dependency_paths, eq=(Path(service_project),))
        tm.that(
            FlextInfraWorkspaceDetector.workspace_analysis_exclusion_paths(workspace),
            eq=(Path(service_project),),
        )

    def test_invalid_repository_path_fails_closed(self, tmp_path: Path) -> None:
        """Return a typed failure for a path that is not a repository directory."""
        result = FlextInfraWorkspaceDetector().detect(tmp_path / "absent")

        tm.fail(result, has="not a directory")

    def test_repository_without_origin_fails_closed(self, tmp_path: Path) -> None:
        """Require an explicit origin before classifying provider ownership."""
        root = tmp_path / "without-origin"
        WorktreeFixture.initialize_governed_project(
            root,
            "without-origin",
            workspace="without-origin",
            database="without_origin",
            issue_prefix="without-origin",
        )
        tm.ok(u.Cli.run_checked(["git", "remote", "remove", "origin"], cwd=root))

        result = FlextInfraWorkspaceDetector.load_workspace_spec(root)

        tm.fail(result, has="No item found with id origin")

    def test_pep621_distribution_must_match_git_repository_identity(
        self, tmp_path: Path
    ) -> None:
        """PEP 621 is the owner; Git validates it and never supplies a fallback."""
        root = tmp_path / "identity-conflict"
        WorktreeFixture.initialize_governed_project(
            root,
            "fixture-project",
            workspace="ignored-workspace",
            database="ignored-database",
            issue_prefix="ignored-prefix",
        )
        tm.ok(
            u.Cli.run_checked(
                [
                    "git",
                    "remote",
                    "set-url",
                    "origin",
                    WorktreeFixture.governed_repository_url("different-project"),
                ],
                cwd=root,
            )
        )

        result = FlextInfraWorkspaceDetector.load_workspace_spec(root)

        tm.fail(result, has="repository identity does not match distribution")

    @pytest.mark.parametrize(
        ("missing_key", "expected_error"),
        [
            ("url", "Git submodule URL is missing"),
            ("branch", "Git submodule branch is missing"),
        ],
    )
    def test_gitmodule_requires_complete_contract(
        self, tmp_path: Path, missing_key: str, expected_error: str
    ) -> None:
        """Reject a declared_repository entry without its exact URL or branch."""
        root = tmp_path / missing_key
        WorktreeFixture.initialize_governed_project(
            root,
            "fixture-workspace",
            workspace="fixture-workspace",
            database="fixture_workspace",
            issue_prefix="fixture-workspace",
        )
        provider = u.Tests.provider()
        fields = {
            "url": f"\turl = {provider.base_url}/fixture-child.git\n",
            "branch": f"\tbranch = {provider.branch}\n",
        }
        fields.pop(missing_key)
        (root / c.Infra.GITMODULES).write_text(
            '[submodule "fixture-child"]\n'
            "\tpath = fixture-child\n"
            f"{''.join(fields.values())}",
            encoding="utf-8",
        )

        result = FlextInfraWorkspaceDetector.load_workspace_spec(root)

        tm.fail(result, has=expected_error)

    def test_gitmodule_rejects_duplicate_paths(self, tmp_path: Path) -> None:
        """Reject two declarations that claim the same checkout path."""
        root = tmp_path / "duplicate"
        WorktreeFixture.initialize_governed_project(
            root,
            "fixture-workspace",
            workspace="fixture-workspace",
            database="fixture_workspace",
            issue_prefix="fixture-workspace",
        )
        provider = u.Tests.provider()
        (root / c.Infra.GITMODULES).write_text(
            '[submodule "first"]\n'
            "\tpath = fixture-child\n"
            f"\turl = {provider.base_url}/fixture-child.git\n"
            f"\tbranch = {provider.branch}\n"
            '[submodule "second"]\n'
            "\tpath = fixture-child\n"
            f"\turl = {provider.base_url}/fixture-child.git\n"
            f"\tbranch = {provider.branch}\n",
            encoding="utf-8",
        )

        result = FlextInfraWorkspaceDetector.load_workspace_spec(root)

        tm.fail(result, has="duplicate Git submodule path")

    def test_gitmodule_rejects_malformed_configuration(self, tmp_path: Path) -> None:
        """Reject syntax that cannot define an exact submodule contract."""
        root = tmp_path / "malformed-gitmodules"
        WorktreeFixture.initialize_governed_project(
            root,
            "fixture-workspace",
            workspace="fixture-workspace",
            database="fixture_workspace",
            issue_prefix="fixture-workspace",
        )
        (root / c.Infra.GITMODULES).write_text(
            '[submodule "unterminated"\npath = fixture-child\n', encoding="utf-8"
        )

        result = FlextInfraWorkspaceDetector.load_workspace_spec(root)

        tm.fail(result, has="failed to read Git submodule declarations")

    @pytest.mark.parametrize("declared_path", ["../escape", "/absolute/escape"])
    def test_gitmodule_rejects_escaping_path(
        self, tmp_path: Path, declared_path: str
    ) -> None:
        """Reject relative traversal and absolute checkout destinations."""
        root = tmp_path / "escaping-path"
        WorktreeFixture.initialize_governed_project(
            root,
            "fixture-workspace",
            workspace="fixture-workspace",
            database="fixture_workspace",
            issue_prefix="fixture-workspace",
        )
        provider = u.Tests.provider()
        (root / c.Infra.GITMODULES).write_text(
            '[submodule "fixture-child"]\n'
            f"\tpath = {declared_path}\n"
            f"\turl = {provider.base_url}/fixture-child.git\n"
            f"\tbranch = {provider.branch}\n",
            encoding="utf-8",
        )

        result = FlextInfraWorkspaceDetector.load_workspace_spec(root)

        tm.fail(result, has="invalid Git submodule path")

    def test_gitmodule_rejects_missing_checkout(self, tmp_path: Path) -> None:
        """Reject a governed declaration whose checkout is absent."""
        root = tmp_path / "missing-checkout"
        WorktreeFixture.initialize_governed_project(
            root,
            "fixture-workspace",
            workspace="fixture-workspace",
            database="fixture_workspace",
            issue_prefix="fixture-workspace",
        )
        WorktreeFixture.write_gitmodules(root, ("fixture-child",))

        result = FlextInfraWorkspaceDetector.load_workspace_spec(root)

        tm.fail(result, has="governed subproject checkout is missing")

    def test_uninitialized_gitlink_does_not_borrow_parent_origin(
        self, tmp_path: Path
    ) -> None:
        """Classify an indexed but uninitialized checkout as an external dependency."""
        root = tmp_path / "uninitialized-gitlink"
        WorktreeFixture.initialize_governed_project(
            root,
            "fixture-workspace",
            workspace="fixture-workspace",
            database="fixture_workspace",
            issue_prefix="fixture-workspace",
        )
        child_path = Path("fixture-child")
        WorktreeFixture.write_gitmodules(root, (child_path.as_posix(),))
        recorded = tm.ok(
            u.Cli.capture([c.Infra.GIT, "rev-parse", c.Infra.GIT_HEAD], cwd=root)
        ).strip()
        tm.ok(
            u.Cli.run_checked(
                [
                    c.Infra.GIT,
                    "update-index",
                    "--add",
                    "--cacheinfo",
                    f"160000,{recorded},{child_path.as_posix()}",
                ],
                cwd=root,
            )
        )
        (root / child_path).mkdir()

        workspace = tm.ok(FlextInfraWorkspaceDetector.load_workspace_spec(root))

        tm.that(workspace.subprojects, empty=True)
        tm.that(workspace.external_dependency_paths, eq=(child_path,))

    def test_gitmodule_rejects_provider_branch_divergence(self, tmp_path: Path) -> None:
        """Reject a governed checkout declared on another integration line."""
        root = tmp_path / "branch-divergence"
        WorktreeFixture.initialize_governed_project(
            root,
            "fixture-workspace",
            workspace="fixture-workspace",
            database="fixture_workspace",
            issue_prefix="fixture-workspace",
        )
        WorktreeFixture.write_gitmodules(root, ("fixture-child",))
        gitmodules = root / c.Infra.GITMODULES
        gitmodules.write_text(
            gitmodules.read_text(encoding="utf-8").replace(
                u.Tests.provider().branch, "unexpected-integration"
            ),
            encoding="utf-8",
        )

        result = FlextInfraWorkspaceDetector.load_workspace_spec(root)

        tm.fail(result, has="branch differs from provider policy")

    def test_declared_unmanaged_gitlink_classifies_as_external_dependency(
        self, tmp_path: Path
    ) -> None:
        """Honor the .gitmodules overlay: flext-managed=false is never governed."""
        root = tmp_path / "overlay-external"
        WorktreeFixture.initialize_governed_project(
            root,
            "fixture-workspace",
            workspace="fixture-workspace",
            database="fixture_workspace",
            issue_prefix="fixture-workspace",
        )
        (root / "external-fork").mkdir()
        (root / c.Infra.GITMODULES).write_text(
            '[submodule "external-fork"]\n'
            "\tpath = external-fork\n"
            "\turl = https://github.com/foreign-owner/external-fork.git\n"
            "\tbranch = master\n"
            "\tflext-classification = external-fork\n"
            "\tflext-managed = false\n",
            encoding="utf-8",
        )

        workspace = tm.ok(FlextInfraWorkspaceDetector.load_workspace_spec(root))

        tm.that(workspace.subprojects, empty=True)
        tm.that(workspace.external_dependency_paths, eq=(Path("external-fork"),))

    def test_gitmodule_accepts_the_published_integration_branch(
        self, tmp_path: Path
    ) -> None:
        """Accept a governed checkout declared on the published integration line."""
        root = tmp_path / "integration-line"
        WorktreeFixture.initialize_governed_project(
            root,
            "fixture-workspace",
            workspace="fixture-workspace",
            database="fixture_workspace",
            issue_prefix="fixture-workspace",
        )
        provider = u.Tests.provider()
        baseline = tm.ok(u.Cli.capture([c.Infra.GIT, "rev-parse", "HEAD"], cwd=root))
        tm.ok(
            u.Cli.run_checked(
                [c.Infra.GIT, "update-ref", "refs/remotes/origin/develop", baseline],
                cwd=root,
            )
        )
        tm.ok(
            u.Cli.run_checked(
                [
                    c.Infra.GIT,
                    "update-ref",
                    "-d",
                    f"refs/remotes/origin/{provider.branch}",
                ],
                cwd=root,
            )
        )
        _ = WorktreeFixture.attach_member_child(root)
        (root / c.Infra.GITMODULES).write_text(
            '[submodule "fixture-child"]\n'
            "\tpath = fixture-child\n"
            f"\turl = {WorktreeFixture.governed_repository_url('fixture-child')}\n"
            "\tbranch = develop\n",
            encoding="utf-8",
        )

        workspace = tm.ok(FlextInfraWorkspaceDetector.load_workspace_spec(root))

        tm.that(
            [item.path.as_posix() for item in workspace.subprojects],
            eq=["fixture-child"],
        )

    def test_gitmodule_rejects_origin_url_divergence(self, tmp_path: Path) -> None:
        """Reject a checkout whose origin identity differs from its declaration."""
        root = tmp_path / "url-divergence"
        WorktreeFixture.initialize_governed_project(
            root,
            "fixture-workspace",
            workspace="fixture-workspace",
            database="fixture_workspace",
            issue_prefix="fixture-workspace",
        )
        _ = WorktreeFixture.attach_member_child(root)
        provider = u.Tests.provider()
        (root / c.Infra.GITMODULES).write_text(
            '[submodule "fixture-child"]\n'
            "\tpath = fixture-child\n"
            f"\turl = {provider.base_url}/different-child.git\n"
            f"\tbranch = {provider.branch}\n",
            encoding="utf-8",
        )

        result = FlextInfraWorkspaceDetector.load_workspace_spec(root)

        tm.fail(result, has="subproject origin differs from its .gitmodules URL")

    def test_gitmodule_rejects_unknown_provider_without_raw_url(
        self, tmp_path: Path
    ) -> None:
        """Reject unknown declared_repository ownership before inspecting its checkout."""
        root = tmp_path / "unknown-provider"
        WorktreeFixture.initialize_governed_project(
            root,
            "fixture-workspace",
            workspace="fixture-workspace",
            database="fixture_workspace",
            issue_prefix="fixture-workspace",
        )
        raw_host_marker = "private-submodule-host"
        (root / c.Infra.GITMODULES).write_text(
            '[submodule "fixture-child"]\n'
            "\tpath = fixture-child\n"
            f"\turl = git@{raw_host_marker}:unknown-owner/fixture-child.git\n"
            f"\tbranch = {u.Tests.provider().branch}\n",
            encoding="utf-8",
        )

        result = FlextInfraWorkspaceDetector.load_workspace_spec(root)

        tm.fail(result, has="repository owner must resolve exactly once")
        tm.that(result.error or "", lacks=raw_host_marker)

    def test_governed_remote_identity_normalizes_the_git_suffix(self) -> None:
        """Accept equivalent provider URLs with or without the clone suffix."""
        provider = u.Tests.provider()
        repository = u.Tests.repository_ref("fixture-project").model_copy(
            update={
                "url": u.Tests.repository_ref("fixture-project").url.removesuffix(
                    ".git"
                )
            }
        )

        tm.that(
            FlextInfraWorkspaceDetector.repository_is_governed(repository, provider),
            eq=True,
        )
