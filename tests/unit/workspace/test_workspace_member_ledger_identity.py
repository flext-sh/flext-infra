"""Workspace members must resolve one ledger without owning a second identity."""

from __future__ import annotations

import shutil
from pathlib import Path

from flext_infra.workspace import FlextInfraWorkspaceDetector
from flext_tests import tm
from tests import u
from tests.unit.workspace.worktree_fixture import WorktreeFixture


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
    (parent / ".gitmodules").write_text(
        '[submodule "fixture-member"]\n'
        "\tpath = apps/member\n"
        f"\turl = {WorktreeFixture.governed_repository_url('fixture-member')}\n"
        f"\tbranch = {provider.branch}\n",
        encoding="utf-8",
    )
    member_head = tm.ok(u.Cli.capture(["git", "rev-parse", "HEAD"], cwd=member))
    tm.ok(u.Cli.run_checked(["git", "add", ".gitmodules"], cwd=parent))
    tm.ok(
        u.Cli.run_checked(
            [
                "git",
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
            ["git", "commit", "--quiet", "-m", "attach member"], cwd=parent
        )
    )
    return member, parent


def test_submodule_self_load_accepts_an_independent_ledger(tmp_path: Path) -> None:
    """A member owning a real ledger directory keeps its own identity."""
    member, _ = _attach_member_to_workspace(tmp_path)
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

    tm.that(workspace.beads.workspace, eq="member-workspace")
    tm.that(workspace.beads.database, eq="member-database")


def test_submodule_self_load_accepts_config_only_ledger(tmp_path: Path) -> None:
    """A member's config remains sufficient when it owns no ledger directory."""
    member, _ = _attach_member_to_workspace(tmp_path)
    (member / ".beads").unlink()
    WorktreeFixture.write_beads_project(
        member,
        workspace="member-workspace",
        database="member-database",
        issue_prefix="member-prefix",
    )

    workspace = tm.ok(FlextInfraWorkspaceDetector.load_workspace_spec(member))

    tm.that(workspace.beads.workspace, eq="member-workspace")


def test_submodule_self_load_rejects_a_divergent_linked_identity(
    tmp_path: Path,
) -> None:
    """A linked member cannot self-authorize a second ledger."""
    member, _ = _attach_member_to_workspace(tmp_path)
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
