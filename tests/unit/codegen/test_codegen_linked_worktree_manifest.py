"""Codegen manifest ownership inside linked worktrees."""

from __future__ import annotations

from pathlib import Path

import pytest
from flext_infra import config
from flext_infra.codegen import FlextInfraCodegenConform
from flext_tests import tm

from tests import c, m, u
from tests.unit.workspace.worktree_fixture import WorktreeFixture


# Conform materializes a full managed tree; the real Git scenarios therefore use
# the config-owned slow budget instead of weakening the global timeout.
@pytest.mark.slow
class TestCodegenLinkedWorktreeManifest:
    """Render into the active lane from its canonical topology owner."""

    def test_standalone_lane_uses_its_principal_manifest(self, tmp_path: Path) -> None:
        """Use principal policy while preserving dirty principal bytes."""
        repository = u.Tests.repository_ref(config.Infra.name).model_copy(
            update={
                "path": Path(),
                "role": c.Infra.RepositoryRole.STANDALONE,
                "checkout": c.Infra.CheckoutKind.INDEPENDENT,
                "editable": False,
            }
        )
        primary = tmp_path / "primary"
        primary_pyproject = WorktreeFixture.write_python_project(
            primary, repository.distribution
        )
        workspace = m.Infra.WorkspaceSpec(
            version=c.Infra.WORKSPACE_MANIFEST_VERSION,
            name=repository.distribution,
            repository=repository,
        )
        tm.ok(
            u.Cli.yaml_dump(
                primary / "config" / "workspace.yaml",
                workspace.model_dump(
                    mode="json",
                    exclude_none=True,
                    exclude={"external_dependency_paths"},
                ),
            )
        )
        u.Tests.initialize_git_repo(primary, repository.url)
        lane = tmp_path / "lane"
        tm.ok(
            u.Infra.git_add_lane_worktree(
                m.Infra.GitWorktreeAddRequest(
                    repo_root=primary,
                    lane=lane,
                    branch="bugfix/lane",
                    base=c.Infra.GIT_HEAD,
                )
            )
        )
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
        tm.that(applied.plan.workspace, eq=workspace)
        tm.that(bool(applied.written_files), eq=True)
        tm.that(
            all(path.is_relative_to(lane) for path in applied.written_files), eq=True
        )
        tm.that((primary / c.Infra.MAKEFILE_FILENAME).exists(), eq=False)
        tm.that(WorktreeFixture.repository_snapshot(primary), eq=primary_snapshot)

    def test_member_lane_uses_superproject_manifest_and_only_writes_lane(
        self, tmp_path: Path
    ) -> None:
        """Run the ALL surface for one member without mutating either dirty owner."""
        (
            superproject,
            primary,
            lane,
            workspace,
            superproject_snapshot,
            primary_snapshot,
        ) = WorktreeFixture.codegen_member_lane(tmp_path)
        applied = tm.ok(
            FlextInfraCodegenConform.execute_request(
                m.Infra.CodegenConformRequest(
                    root=lane,
                    scope=c.Infra.CodegenConformScope.SELF,
                    mode=c.Infra.CodegenConformMode.APPLY,
                )
            )
        )
        makefile = (lane / c.Infra.MAKEFILE_FILENAME).read_text(encoding="utf-8")

        tm.that(makefile, has="MAKE_PROFILE := workspace-member")
        tm.that(applied.plan.workspace.name, eq=workspace.name)
        tm.that(bool(applied.written_files), eq=True)
        tm.that(
            all(path.is_relative_to(lane) for path in applied.written_files), eq=True
        )
        tm.that((primary / c.Infra.MAKEFILE_FILENAME).exists(), eq=False)
        tm.that(WorktreeFixture.repository_snapshot(primary), eq=primary_snapshot)
        tm.that(
            WorktreeFixture.repository_snapshot(superproject), eq=superproject_snapshot
        )

    def test_declared_member_cannot_escape_through_a_linked_path(
        self, tmp_path: Path
    ) -> None:
        """Reject a declared member whose nominal path resolves outside its owner."""
        root = tmp_path / "workspace"
        outside = tmp_path / "outside-member"
        WorktreeFixture.write_python_project(root, config.Infra.name)
        member = u.Tests.repository_ref(
            "flext-cli", role=c.Infra.RepositoryRole.WORKSPACE_MEMBER
        ).model_copy(update={"path": Path("linked-member")})
        WorktreeFixture.write_python_project(outside, member.distribution)
        root_repository = u.Tests.repository_ref(config.Infra.name).model_copy(
            update={
                "path": Path(),
                "role": c.Infra.RepositoryRole.WORKSPACE_ROOT,
                "codegen": c.Infra.CodegenKind.NONE,
            }
        )
        (root / member.path).symlink_to(outside, target_is_directory=True)
        workspace = m.Infra.WorkspaceSpec(
            version=c.Infra.WORKSPACE_MANIFEST_VERSION,
            name=root_repository.distribution,
            repository=root_repository,
            members=(member,),
        )

        result = FlextInfraCodegenConform.execute_request(
            m.Infra.CodegenConformRequest(
                root=root,
                what=c.Infra.CodegenConformSurface.MAKEFILE,
                scope=c.Infra.CodegenConformScope.ALL,
                mode=c.Infra.CodegenConformMode.CHECK,
            ),
            initial_workspace=workspace,
        )

        tm.fail(result, has="declared repository path escapes workspace root")
        tm.that((outside / c.Infra.MAKEFILE_FILENAME).exists(), eq=False)
