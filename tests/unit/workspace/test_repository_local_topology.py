"""Repository-local topology and Beads identity contracts."""

from __future__ import annotations

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
