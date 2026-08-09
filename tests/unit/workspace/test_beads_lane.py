"""Verify Beads ledger ownership for workspace members."""

from __future__ import annotations

from pathlib import Path

from flext_infra import c, m, u
from flext_tests import tm
from tests import u as test_u


def _repository(root: Path, *, ledger_id: str) -> Path:
    root.mkdir()
    (root / "README.md").write_text("fixture\n", encoding="utf-8")
    repository = test_u.Tests.repository_ref(root.name).model_copy(
        update={"path": Path(), "package": False, "editable": False}
    )
    workspace = m.Infra.WorkspaceSpec(
        version=c.Infra.WORKSPACE_MANIFEST_VERSION,
        name=repository.distribution,
        repository=repository,
        ledger_id=ledger_id,
    )
    tm.ok(
        u.Cli.yaml_dump(
            root / "config" / "workspace.yaml",
            workspace.model_dump(mode="json", exclude_none=True),
        )
    )
    test_u.Tests.initialize_git_repo(root)
    return root


def test_submodule_routes_to_governing_workspace_ledger(tmp_path: Path) -> None:
    workspace = _repository(tmp_path / "workspace", ledger_id="workspace-ledger")
    member_source = _repository(tmp_path / "member-source", ledger_id="member-ledger")
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
    member_beads = member / ".beads"
    member_beads.mkdir()
    declaration = m.Infra.BeadsTrackerDeclaration(issue_prefix="member-local")
    (member_beads / "config.yaml").write_text(
        f'issue-prefix: "{declaration.issue_prefix}"\n', encoding="utf-8"
    )

    resolved = tm.ok(u.Infra.beads_resolve_root(member))

    assert resolved == workspace.resolve()
