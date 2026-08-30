"""Repository-local topology and Beads identity contracts."""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest
from flext_infra import c, m, t
from flext_infra.workspace.detector import FlextInfraWorkspaceDetector
from flext_tests import tm

from tests import u
from tests.unit.workspace.worktree_fixture import WorktreeFixture


class TestsRepositoryLocalTopology:
    """Prove each repository owns its topology and typed Beads identity."""

    def test_loads_typed_beads_identity_from_the_repository_itself(
        self, tmp_path: Path
    ) -> None:
        """Parse required identity and project extensions into one typed model."""
        root = tmp_path / "project"
        WorktreeFixture.initialize_governed_project(
            root,
            "fixture-project",
            workspace="fixture-workspace",
            database="fixture-database",
            issue_prefix="fixture-prefix",
            custom_issue_types=("incident",),
        )

        beads = tm.ok(FlextInfraWorkspaceDetector.load_beads_spec(root))
        workspace = tm.ok(FlextInfraWorkspaceDetector.load_workspace_spec(root))

        tm.that(type(beads), eq=m.Infra.BeadsProjectSpec)
        tm.that(
            beads.model_dump(mode="json"),
            eq={
                "version": 1,
                "workspace": "fixture-workspace",
                "database": "fixture-database",
                "issue_prefix": "fixture-prefix",
                "custom_issue_types": ["incident"],
            },
        )
        tm.that(workspace.beads, eq=beads)

    @pytest.mark.parametrize(
        "missing_field", ["version", "workspace", "database", "issue_prefix"]
    )
    def test_beads_identity_requires_every_declared_field(
        self, tmp_path: Path, missing_field: str
    ) -> None:
        """Reject partial identity instead of inferring a value elsewhere."""
        root = tmp_path / missing_field
        WorktreeFixture.initialize_governed_project(
            root,
            f"fixture-{missing_field}",
            workspace="fixture-workspace",
            database="fixture-database",
            issue_prefix="fixture-prefix",
        )
        payload: dict[str, t.JsonValue] = {
            "version": 1,
            "workspace": "fixture-workspace",
            "database": "fixture-database",
            "issue_prefix": "fixture-prefix",
        }
        del payload[missing_field]
        tm.ok(u.Cli.yaml_dump(root / "config" / "beads.yaml", payload))

        result = FlextInfraWorkspaceDetector.load_beads_spec(root)

        tm.fail(result, has=missing_field)

    @pytest.mark.parametrize(
        ("field", "invalid_value"),
        [
            pytest.param("version", 2, id="unknown-version"),
            pytest.param("workspace", "", id="empty-workspace"),
            pytest.param("database", ["not", "a", "scalar"], id="database-list"),
            pytest.param("issue_prefix", None, id="null-prefix"),
            pytest.param(
                "custom_issue_types",
                ["incident", "incident"],
                id="duplicate-custom-type",
            ),
        ],
    )
    def test_beads_identity_rejects_malformed_values(
        self, tmp_path: Path, field: str, invalid_value: t.JsonValue
    ) -> None:
        """Fail closed on values outside the typed local contract."""
        root = tmp_path / field
        WorktreeFixture.initialize_governed_project(
            root,
            f"fixture-{field}",
            workspace="fixture-workspace",
            database="fixture-database",
            issue_prefix="fixture-prefix",
        )
        payload: dict[str, t.JsonValue] = {
            "version": 1,
            "workspace": "fixture-workspace",
            "database": "fixture-database",
            "issue_prefix": "fixture-prefix",
            "custom_issue_types": [],
        }
        payload[field] = invalid_value
        tm.ok(u.Cli.yaml_dump(root / "config" / "beads.yaml", payload))

        result = FlextInfraWorkspaceDetector.load_beads_spec(root)

        tm.fail(result, has=field)

    def test_only_own_gitmodules_classifies_a_repository_as_workspace(
        self, tmp_path: Path
    ) -> None:
        """Classify from the repository's own live Git declaration."""
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

        tm.that(mode, eq=c.Infra.WorkspaceMode.WORKSPACE)
        tm.that(target.make_profile, eq=c.Infra.MakeProfile.WORKSPACE)

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
        resolved = tm.ok(FlextInfraWorkspaceDetector.resolve_workspace_root(child))

        tm.that(mode, eq=c.Infra.WorkspaceMode.STANDALONE)
        tm.that(workspace.repository.name, eq="child")
        tm.that(workspace.name, eq="child-workspace")
        tm.that(workspace.beads.workspace, eq="child-workspace")
        tm.that(workspace.subprojects, empty=True)
        tm.that(resolved, eq=child.resolve())

    def test_conform_target_follows_the_published_integration_branch(
        self, tmp_path: Path
    ) -> None:
        """Derive the target baseline from live Git, not the provider default."""
        root = tmp_path / "published-integration"
        WorktreeFixture.initialize_governed_project(
            root,
            "fixture-workspace",
            workspace="fixture-workspace",
            database="fixture-database",
            issue_prefix="fixture-prefix",
        )
        provider = u.Tests.provider()
        baseline = tm.ok(u.Cli.capture([c.Infra.GIT, "rev-parse", "HEAD"], cwd=root))
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
        tm.ok(
            u.Cli.run_checked(
                [c.Infra.GIT, "update-ref", "refs/remotes/origin/dev", baseline],
                cwd=root,
            )
        )

        target = tm.ok(FlextInfraWorkspaceDetector.conform_target(root))

        tm.that(target.baseline_branch, eq="dev")

    def test_submodule_self_load_preserves_its_checkout_relationship(
        self, tmp_path: Path
    ) -> None:
        """A child owns its identity without erasing the physical gitlink fact."""
        child_source = tmp_path / "child-source"
        WorktreeFixture.initialize_governed_project(
            child_source,
            "fixture-member",
            workspace="member-workspace",
            database="member-database",
            issue_prefix="member-prefix",
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
        provider = u.Tests.provider()
        (parent / ".gitmodules").write_text(
            "[submodule 'fixture-member']\n"
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

        workspace = tm.ok(FlextInfraWorkspaceDetector.load_workspace_spec(member))

        tm.that(workspace.repository.path, eq=Path())
        tm.that(workspace.repository.checkout, eq=c.Infra.CheckoutKind.SUBMODULE)

    def test_workspace_preserves_distinct_subproject_identities(
        self, tmp_path: Path
    ) -> None:
        """Accept local child identities without copying the root identity."""
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
            )
        WorktreeFixture.write_gitmodules(root, tuple(identities))

        workspace = tm.ok(FlextInfraWorkspaceDetector.load_workspace_spec(root))

        tm.that(
            tuple(project.path.as_posix() for project in workspace.subprojects),
            eq=tuple(identities),
        )
        tm.that(workspace.beads.workspace, eq="root-workspace")
        for project_name, identity in identities.items():
            beads = tm.ok(
                FlextInfraWorkspaceDetector.load_beads_spec(root / project_name)
            )
            tm.that((beads.workspace, beads.database, beads.issue_prefix), eq=identity)

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
        """Reject a subproject entry without its exact URL or branch."""
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
        child = root / "fixture-child"
        WorktreeFixture.initialize_governed_project(
            child,
            "fixture-child",
            workspace="fixture-child",
            database="fixture_child",
            issue_prefix="fixture-child",
        )
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
        child = root / "fixture-child"
        WorktreeFixture.initialize_governed_project(
            child,
            "fixture-child",
            workspace="fixture-child",
            database="fixture_child",
            issue_prefix="fixture-child",
        )
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
        """Reject unknown subproject ownership before inspecting its checkout."""
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
