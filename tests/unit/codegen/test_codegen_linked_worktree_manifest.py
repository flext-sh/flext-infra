"""Repository-local topology ownership inside linked worktrees."""

from __future__ import annotations

from pathlib import Path

import pytest
from flext_infra import c, m
from flext_infra.codegen import FlextInfraCodegenConform
from flext_infra.workspace.detector import FlextInfraWorkspaceDetector
from flext_tests import tm

from tests import u
from tests.unit.workspace.worktree_fixture import WorktreeFixture


# Conform materializes a full managed tree; the real Git scenarios therefore use
# the config-owned slow budget instead of weakening the global timeout.
@pytest.mark.slow
class TestCodegenLinkedWorktreeTopology:
    """Keep topology inputs and writes owned by the repository being conformed."""

    def test_linked_lane_reads_its_local_beads_identity_and_only_writes_lane(
        self, tmp_path: Path
    ) -> None:
        """Use dirty lane-local policy without reading or mutating the primary."""
        primary = tmp_path / "primary"
        primary_pyproject = WorktreeFixture.initialize_governed_project(
            primary,
            "fixture-project",
            workspace="primary-workspace",
            database="primary-database",
            issue_prefix="primary-prefix",
        )
        lane = tmp_path / "lane"
        tm.ok(
            u.Infra.git_add_lane_worktree(
                m.Infra.GitWorktreeAddRequest(
                    repo_root=primary,
                    lane=lane,
                    branch="bugfix/lane-local-topology",
                    base=c.Infra.GIT_HEAD,
                )
            )
        )
        lane_beads = WorktreeFixture.write_beads_project(
            lane,
            workspace="lane-workspace",
            database="lane-database",
            issue_prefix="lane-prefix",
        )
        lane_beads_bytes = lane_beads.read_bytes()
        primary_pyproject.write_text(
            f"{primary_pyproject.read_text(encoding='utf-8')}# human WIP\n",
            encoding="utf-8",
        )
        primary_snapshot = WorktreeFixture.repository_snapshot(primary)

        applied = tm.ok(
            FlextInfraCodegenConform.execute_request(
                m.Infra.CodegenConformRequest(
                    root=lane,
                    what=c.Infra.CodegenConformSurface.MAKEFILE,
                    scope=c.Infra.CodegenConformScope.SELF,
                    mode=c.Infra.CodegenConformMode.APPLY,
                )
            )
        )

        makefile = (lane / c.Infra.MAKEFILE_FILENAME).read_text(encoding="utf-8")
        tm.that(makefile, has="MAKE_PROFILE := standalone")
        tm.that(applied.plan.workspace.beads.workspace, eq="lane-workspace")
        tm.that(applied.plan.workspace.beads.database, eq="lane-database")
        tm.that(applied.plan.workspace.beads.issue_prefix, eq="lane-prefix")
        tm.that(bool(applied.written_files), eq=True)
        tm.that(
            all(path.is_relative_to(lane) for path in applied.written_files), eq=True
        )
        tm.that(
            tm.ok(FlextInfraWorkspaceDetector.resolve_workspace_root(lane)),
            eq=lane.resolve(),
        )
        tm.that(lane_beads.read_bytes(), eq=lane_beads_bytes)
        tm.that((primary / c.Infra.MAKEFILE_FILENAME).exists(), eq=False)
        tm.that(WorktreeFixture.repository_snapshot(primary), eq=primary_snapshot)

    @pytest.mark.parametrize(
        ("beads_content", "expected_error"),
        [
            pytest.param(None, "missing", id="missing"),
            pytest.param("version: [\nworkspace: invalid\n", "Beads", id="malformed"),
        ],
    )
    def test_invalid_local_beads_identity_fails_before_any_write(
        self, tmp_path: Path, beads_content: str | None, expected_error: str
    ) -> None:
        """Fail planning atomically when the required local input is invalid."""
        root = tmp_path / "project"
        WorktreeFixture.initialize_governed_project(
            root,
            "fixture-project",
            workspace="fixture-workspace",
            database="fixture-database",
            issue_prefix="fixture-prefix",
        )
        beads_path = root / "config" / "beads.yaml"
        if beads_content is None:
            beads_path.unlink()
        else:
            beads_path.write_text(beads_content, encoding="utf-8")
        before = WorktreeFixture.repository_snapshot(root)

        result = FlextInfraCodegenConform.execute_request(
            m.Infra.CodegenConformRequest(
                root=root,
                scope=c.Infra.CodegenConformScope.SELF,
                mode=c.Infra.CodegenConformMode.APPLY,
            )
        )

        tm.fail(result, has=expected_error)
        tm.that(WorktreeFixture.repository_snapshot(root), eq=before)

    def test_subproject_identities_and_topology_inputs_are_never_rewritten(
        self, tmp_path: Path
    ) -> None:
        """Conform distinct subprojects without copying identity from the root."""
        root = tmp_path / "workspace"
        WorktreeFixture.initialize_governed_project(
            root,
            "fixture-workspace",
            workspace="root-workspace",
            database="root-database",
            issue_prefix="root-prefix",
        )
        project_names = ("fixture-alpha", "fixture-beta")
        expected_identities = {
            "fixture-alpha": ("alpha-workspace", "alpha-database", "alpha-prefix"),
            "fixture-beta": ("beta-workspace", "beta-database", "beta-prefix"),
        }
        for project_name, identity in expected_identities.items():
            WorktreeFixture.initialize_governed_project(
                root / project_name,
                project_name,
                workspace=identity[0],
                database=identity[1],
                issue_prefix=identity[2],
            )
        gitmodules = WorktreeFixture.write_gitmodules(root, project_names)
        u.Tests.git_bootstrap(root, ("add", c.Infra.GITMODULES, *project_names))
        u.Tests.git_bootstrap(
            root, ("commit", "-m", "fixture: declare independent subprojects")
        )
        protected_bytes = {
            gitmodules: gitmodules.read_bytes(),
            **{
                root / project_name / "config" / "beads.yaml": (
                    root / project_name / "config" / "beads.yaml"
                ).read_bytes()
                for project_name in project_names
            },
        }

        workspace = tm.ok(FlextInfraWorkspaceDetector.load_workspace_spec(root))
        tm.that(
            tuple(project.path.as_posix() for project in workspace.subprojects),
            eq=project_names,
        )
        for project_name, identity in expected_identities.items():
            beads = tm.ok(
                FlextInfraWorkspaceDetector.load_beads_spec(root / project_name)
            )
            tm.that((beads.workspace, beads.database, beads.issue_prefix), eq=identity)

        applied = tm.ok(
            FlextInfraCodegenConform.execute_request(
                m.Infra.CodegenConformRequest(
                    root=root,
                    scope=c.Infra.CodegenConformScope.SUBPROJECTS,
                    mode=c.Infra.CodegenConformMode.APPLY,
                )
            )
        )

        tm.that(bool(applied.written_files), eq=True)
        for path, content in protected_bytes.items():
            tm.that(path.read_bytes(), eq=content)
        tm.that(
            tuple(
                path
                for path in applied.written_files
                if path == gitmodules or path.name == "beads.yaml"
            ),
            empty=True,
        )

    def test_declared_subproject_cannot_escape_through_a_linked_path(
        self, tmp_path: Path
    ) -> None:
        """Reject a declared subproject whose path resolves outside its owner."""
        root = tmp_path / "workspace"
        outside = tmp_path / "outside-project"
        WorktreeFixture.initialize_governed_project(
            root,
            "fixture-workspace",
            workspace="root-workspace",
            database="root-database",
            issue_prefix="root-prefix",
        )
        WorktreeFixture.initialize_governed_project(
            outside,
            "linked-project",
            workspace="outside-workspace",
            database="outside-database",
            issue_prefix="outside-prefix",
        )
        (root / "linked-project").symlink_to(outside, target_is_directory=True)
        WorktreeFixture.write_gitmodules(root, ("linked-project",))
        outside_snapshot = WorktreeFixture.repository_snapshot(outside)

        result = FlextInfraCodegenConform.execute_request(
            m.Infra.CodegenConformRequest(
                root=root,
                what=c.Infra.CodegenConformSurface.MAKEFILE,
                scope=c.Infra.CodegenConformScope.SUBPROJECTS,
                mode=c.Infra.CodegenConformMode.CHECK,
            )
        )

        tm.fail(result, has="escapes workspace root")
        tm.that(WorktreeFixture.repository_snapshot(outside), eq=outside_snapshot)
