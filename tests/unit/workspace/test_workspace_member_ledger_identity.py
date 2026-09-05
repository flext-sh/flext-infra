"""Workspace members must resolve one ledger without owning a second identity."""

from __future__ import annotations

import shutil
from pathlib import Path

from flext_infra import c
from flext_infra.workspace import FlextInfraWorkspaceDetector
from flext_tests import tm
from tests import u
from tests.unit.workspace.worktree_fixture import WorktreeFixture


class TestsWorkspaceMemberLedgerIdentity:
    """Prove parent and member identities remain in their own coordinates."""

    @staticmethod
    def _attach_member_to_workspace(tmp_path: Path) -> tuple[Path, Path]:
        """Create one governed, committed workspace/member checkout pair."""
        child_source = tmp_path / "child-source"
        WorktreeFixture.initialize_governed_project(
            child_source,
            "fixture-member",
            workspace="member-workspace",
            database="member-database",
            issue_prefix="member-prefix",
            beads_owner=False,
        )
        parent = tmp_path / "workspace"
        WorktreeFixture.initialize_governed_project(
            parent,
            "fixture-workspace",
            workspace="root-workspace",
            database="root-database",
            issue_prefix="root-prefix",
        )
        member = parent / "apps" / "member"
        shutil.copytree(child_source, member)
        WorktreeFixture.link_member_beads(
            member,
            parent,
            workspace_name="root-workspace",
            database="root-database",
            issue_prefix="root-prefix",
        )
        provider = u.Tests.provider()
        (parent / c.Infra.GITMODULES).write_text(
            '[submodule "fixture-member"]\n'
            "\tpath = apps/member\n"
            f"\turl = {WorktreeFixture.governed_repository_url('fixture-member')}\n"
            f"\tbranch = {provider.branch}\n",
            encoding="utf-8",
        )
        member_head = tm.ok(
            u.Cli.capture([c.Infra.GIT, "rev-parse", "HEAD"], cwd=member)
        )
        tm.ok(u.Cli.run_checked([c.Infra.GIT, "add", c.Infra.GITMODULES], cwd=parent))
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
        return member, parent

    def test_parent_does_not_load_member_local_manifest(self, tmp_path: Path) -> None:
        """A parent observes member paths without parsing the member-local manifest."""
        member, parent = self._attach_member_to_workspace(tmp_path)
        member_manifest = member / "config/workspace.yaml"
        member_manifest.parent.mkdir(parents=True, exist_ok=True)
        member_manifest.write_text(
            "version: parent-must-not-parse-member-manifest\n", encoding="utf-8"
        )

        workspace = tm.ok(FlextInfraWorkspaceDetector.load_workspace_spec(parent))

        tm.that(
            tuple(item.path for item in workspace.declared_repositories),
            has=Path("apps/member"),
        )

    def test_submodule_self_load_accepts_an_independent_ledger(
        self, tmp_path: Path
    ) -> None:
        """A member owning a real ledger directory keeps its own identity."""
        member, _ = self._attach_member_to_workspace(tmp_path)
        member_beads = member / ".beads"
        member_beads.unlink()
        member_beads.mkdir()
        WorktreeFixture.write_beads_project(
            member,
            workspace="member-workspace",
            database="member-database",
            issue_prefix="member-prefix",
        )

        workspace = tm.ok(FlextInfraWorkspaceDetector.load_workspace_spec(member))

        tm.that(u.Tests.required_beads(workspace).workspace, eq="member-workspace")
        tm.that(u.Tests.required_beads(workspace).database, eq="member-database")

    def test_submodule_self_load_accepts_config_only_ledger(
        self, tmp_path: Path
    ) -> None:
        """A member's config remains sufficient when it owns no ledger directory."""
        member, _ = self._attach_member_to_workspace(tmp_path)
        (member / ".beads").unlink()
        WorktreeFixture.write_beads_project(
            member,
            workspace="member-workspace",
            database="member-database",
            issue_prefix="member-prefix",
        )

        workspace = tm.ok(FlextInfraWorkspaceDetector.load_workspace_spec(member))

        tm.that(u.Tests.required_beads(workspace).workspace, eq="member-workspace")

    def test_submodule_self_load_rejects_a_divergent_linked_identity(
        self, tmp_path: Path
    ) -> None:
        """A linked member cannot self-authorize a second ledger."""
        member, _ = self._attach_member_to_workspace(tmp_path)
        WorktreeFixture.write_beads_project(
            member,
            workspace="rogue-workspace",
            database="rogue-database",
            issue_prefix="rogue-prefix",
        )

        workspace = FlextInfraWorkspaceDetector.load_workspace_spec(member)

        tm.that(workspace.failure, eq=True)
        tm.that(str(workspace.error), has="member Beads routing identity differs")
        tm.that(str(workspace.error), has="rogue-workspace")


__all__: tuple[str, ...] = ()
