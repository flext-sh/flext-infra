"""The Beads adapter is the sole untrusted JSON parsing boundary."""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest
from flext_infra import c, config, m, u
from flext_tests import tm
from tests import u as test_u


def _repository(tmp_path: Path) -> Path:
    repository = tmp_path / "repository"
    repository.mkdir()
    test_u.Tests.declare_workspace_ledger(repository, "mro")
    test_u.Tests.initialize_git_repo(repository)
    return repository


def _integration_branch(repository: Path) -> str:
    manifest = u.Cli.yaml_load_mapping(repository / "config" / "workspace.yaml")
    workspace = m.Infra.WorkspaceSpec.model_validate(manifest)
    provider = next(
        item
        for item in config.Infra.codegen.providers
        if item.name == workspace.repository.provider
    )
    return u.Infra.resolve_integration_branch(workspace, provider)


def _install_bd(tmp_path: Path, payload: str) -> Path:
    shim_dir = tmp_path / "bin"
    shim_dir.mkdir()
    shim = shim_dir / "bd"
    shim.write_text(
        "#!/usr/bin/env python3\n"
        "from __future__ import annotations\n"
        "import sys\n"
        f"PAYLOAD = {payload!r}\n"
        "args = sys.argv[1:]\n"
        "if 'show' in args or 'list' in args:\n"
        "    print(PAYLOAD)\n"
        "    raise SystemExit(0)\n"
        "raise SystemExit('unsupported')\n",
        encoding="utf-8",
    )
    shim.chmod(0o755)
    return shim_dir


def test_beads_show_rejects_malformed_payload(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repository = _repository(tmp_path)
    shim_dir = _install_bd(
        tmp_path, '[{"id": "mro-test", "metadata": {"provisioning": "ready"}}]'
    )
    monkeypatch.setenv("PATH", f"{shim_dir}{os.pathsep}{os.environ.get('PATH', '')}")

    result = u.Infra.beads_show("mro-test", root=repository)

    tm.fail(result, has="validation")


def test_beads_list_returns_only_typed_reservations(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repository = _repository(tmp_path)
    integration_branch = _integration_branch(repository)
    records = [
        {
            "id": "mro-ready",
            "status": "open",
            "issue_type": "feature",
            "parent": None,
            "metadata": {
                "branch": "feature/ready-lane",
                "namespace": "feature",
                "worktree": "ready-lane",
                "kind": "feature",
                "slug": "ready-lane",
                "integration_base": integration_branch,
                "role": "plain",
                "provisioning": "ready",
                "head_oid": "abc",
            },
        },
        {
            "id": "mro-pending",
            "status": "open",
            "issue_type": "feature",
            "parent": None,
            "metadata": {
                "branch": "feature/pending-lane",
                "namespace": "feature",
                "worktree": "pending-lane",
                "kind": "feature",
                "slug": "pending-lane",
                "integration_base": integration_branch,
                "role": "plain",
                "provisioning": "pending",
                "matrix": {
                    "entries": [
                        {
                            "project": ".",
                            "branch": "feature/pending-lane",
                            "head_oid": "def",
                            "state": "started",
                        }
                    ]
                },
            },
        },
    ]
    shim_dir = _install_bd(tmp_path, json.dumps(records))
    monkeypatch.setenv("PATH", f"{shim_dir}{os.pathsep}{os.environ.get('PATH', '')}")

    reservations = tm.ok(u.Infra.beads_list_reservations(root=repository))

    assert len(reservations) == 2
    ready_metadata = reservations[0].metadata
    assert isinstance(ready_metadata, m.Infra.ReadyLaneMetadata)
    assert ready_metadata.matrix is None
    assert reservations[1].metadata is not None
    assert (
        reservations[1].metadata.provisioning == c.Infra.WorkProvisioningState.PENDING
    )


def test_legacy_ready_without_matrix_fails_closed_when_start_requests_adoption(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repository = _repository(tmp_path)
    integration_branch = _integration_branch(repository)
    bead_id = "mro-test"
    record = {
        "id": bead_id,
        "status": "open",
        "issue_type": "epic",
        "metadata": {
            "worktree": "typed-lane",
            "kind": "epic",
            "slug": "typed-lane",
            "integration_base": integration_branch,
        },
    }
    shim_dir = _install_bd(tmp_path, json.dumps([record]))
    monkeypatch.setenv("PATH", f"{shim_dir}{os.pathsep}{os.environ.get('PATH', '')}")

    tm.fail(
        u.Infra.beads_show(bead_id, root=repository, adopt_legacy_ready=True),
        has="matrix",
    )


@pytest.mark.parametrize("decoded", [False, True])
def test_start_adopts_live_legacy_epic_matrix_payload(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, *, decoded: bool
) -> None:
    repository = _repository(tmp_path)
    integration_branch = _integration_branch(repository)
    epic_bead_id = "mro-fixture-epic"
    entries = [
        {
            "project": "." if index == 0 else f"flext-member-{index}",
            "branch": "epic/tracker-governance",
            "head_oid": f"{index + 1:040x}",
            "pr_number": "",
            "pr_url": "",
            "state": "started",
        }
        for index in range(32)
    ]
    matrix = {"entries": entries}
    record = {
        "id": epic_bead_id,
        "status": "in_progress",
        "issue_type": "epic",
        "metadata": {
            "integration_base": integration_branch,
            "kind": "epic",
            "matrix": matrix if decoded else json.dumps(matrix),
            "slug": "tracker-governance",
            "worktree": str(repository),
        },
    }
    shim_dir = _install_bd(tmp_path, json.dumps([record]))
    monkeypatch.setenv("PATH", f"{shim_dir}{os.pathsep}{os.environ.get('PATH', '')}")

    adopted = tm.ok(
        u.Infra.beads_show(epic_bead_id, root=repository, adopt_legacy_ready=True)
    )

    assert isinstance(adopted.metadata, m.Infra.ReadyLaneMetadata)
    assert adopted.metadata.matrix is not None
    assert adopted.metadata.branch == "epic/tracker-governance"
    assert adopted.metadata.namespace == c.Infra.WorkBranchNamespace.EPIC
    assert adopted.metadata.kind is None
    assert len(adopted.metadata.matrix.entries) == 32
    assert adopted.metadata.matrix.entries == tuple(
        m.Infra.WorkLaneEntry.model_validate(entry) for entry in entries
    )


def test_start_ignores_unrelated_metadata_that_only_contains_matrix(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repository = _repository(tmp_path)
    record = {
        "id": "mro-test",
        "status": "open",
        "issue_type": "feature",
        "metadata": {
            "matrix": {
                "entries": [
                    {
                        "project": ".",
                        "branch": "feature/unrelated",
                        "head_oid": "abc",
                        "state": "started",
                    }
                ]
            }
        },
    }
    shim_dir = _install_bd(tmp_path, json.dumps([record]))
    monkeypatch.setenv("PATH", f"{shim_dir}{os.pathsep}{os.environ.get('PATH', '')}")

    issue = tm.ok(
        u.Infra.beads_show("mro-test", root=repository, adopt_legacy_ready=True)
    )

    assert issue.metadata is None


__all__: tuple[str, ...] = ()
"""The Beads adapter is the sole untrusted JSON parsing boundary."""
