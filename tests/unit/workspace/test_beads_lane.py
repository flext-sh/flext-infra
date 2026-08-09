"""Verify Beads ledger ownership for workspace members."""

from __future__ import annotations

from pathlib import Path

from flext_infra import c, u
from flext_tests import tm
from tests import u as test_u


def _repository(root: Path) -> Path:
    root.mkdir()
    (root / "README.md").write_text("fixture\n", encoding="utf-8")
    beads = root / ".beads"
    beads.mkdir()
    (beads / "config.yaml").write_text('issue-prefix: "mro"\n', encoding="utf-8")
    test_u.Tests.initialize_git_repo(root)
    return root


def test_submodule_routes_to_governing_workspace_ledger(tmp_path: Path) -> None:
    workspace = _repository(tmp_path / "workspace")
    member_source = _repository(tmp_path / "member-source")
    tm.ok(
        test_u.Cli.run_checked(
            [
                c.Infra.GIT,
                "-c",
                "protocol.file.allow=always",
                "submodule",
                "add",
                str(member_source),
                "member",
            ],
            cwd=workspace,
        )
    )
    member = workspace / "member"

    resolved = tm.ok(u.Infra.beads_resolve_root(member))

    assert resolved == workspace.resolve()
