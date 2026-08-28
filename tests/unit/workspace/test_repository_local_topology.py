"""Repository-local topology and Beads identity contracts."""

from __future__ import annotations

from pathlib import Path

import pytest
from flext_infra import c, config, m, t
from flext_infra.workspace.detector import FlextInfraWorkspaceDetector
from flext_tests import tm

from tests import u
from tests.unit.workspace.worktree_fixture import WorktreeFixture


class TestsRepositoryLocalTopology:
    """Prove each repository owns its topology and typed Beads identity."""

    def test_loads_typed_beads_identity_from_the_repository_itself(
        self, tmp_path: Path
    ) -> None:
        """Parse all four required fields once into the public typed model."""
        root = tmp_path / "project"
        WorktreeFixture.initialize_governed_project(
            root,
            "fixture-project",
            workspace="fixture-workspace",
            database="fixture-database",
            issue_prefix="fixture-prefix",
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

    @pytest.mark.parametrize(
        "remote",
        [
            "https://github.com/flext-sh/fixture-project.git",
            "git@github.com:flext-sh/fixture-project.git",
            "git@private-github-alias:flext-sh/fixture-project.git",
        ],
    )
    def test_provider_resolution_reuses_semantic_git_identity(
        self, remote: str
    ) -> None:
        """Resolve HTTPS, SSH, and SSH aliases through one owner identity."""
        provider = u.Tests.provider()

        resolved = tm.ok(
            u.Infra.remote_provider(remote, config.Infra.codegen.providers)
        )

        tm.that(resolved, eq=provider)

    def test_provider_resolution_rejects_unknown_owner_without_raw_url(self) -> None:
        """Fail unknown ownership without leaking the original remote string."""
        raw_host_marker = "private-host-marker"
        result = u.Infra.remote_provider(
            f"git@{raw_host_marker}:unknown-owner/fixture-project.git",
            config.Infra.codegen.providers,
        )

        tm.fail(result, has="repository owner must resolve exactly once")
        tm.that(result.error or "", lacks=raw_host_marker)

    def test_provider_resolution_rejects_duplicate_owners(self) -> None:
        """Fail when two configured providers claim the same organization."""
        provider = u.Tests.provider()
        duplicate = provider.model_copy(update={"name": "duplicate-provider"})

        result = u.Infra.remote_provider(
            "git@github-alias:flext-sh/fixture-project.git", (provider, duplicate)
        )

        tm.fail(result, has="repository owner must resolve exactly once")
