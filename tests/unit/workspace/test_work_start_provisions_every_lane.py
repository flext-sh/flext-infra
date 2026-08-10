"""``work start`` provisions the lane it hands back, created or adopted.

Every maintained worktree runs ``make setup``. A start interrupted after
``worktree add`` leaves a registered lane behind, and re-running start adopts it;
adopting used to skip provisioning entirely, so the operator received a lane
carrying whatever half-built environment the interrupted run had left (mro-c6di).
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest
from flext_infra import FlextInfraWorkService, c
from flext_tests import tm
from tests import u

_SETUP_LOG = "setup-runs.log"


def _repository(tmp_path: Path) -> Path:
    """Return a committed repository whose ``setup`` records every invocation."""
    repository = tmp_path / "repository"
    repository.mkdir()
    (repository / "pyproject.toml").write_text(
        '[project]\nname = "fixture"\nversion = "0.1.0"\n'
        'description = "A standard PEP 621 description string"\n',
        encoding="utf-8",
    )
    (repository / "Makefile").write_text(
        ".PHONY: setup\n"
        "setup:\n"
        '\t@test "$(WORKSPACE)" = "$(CURDIR)"\n'
        f'\t@printf "%s\\n" "$(WORKSPACE)" >> "$(CURDIR)/{_SETUP_LOG}"\n',
        encoding="utf-8",
    )
    (repository / ".gitignore").write_text(f"{_SETUP_LOG}\n", encoding="utf-8")
    u.Tests.declare_workspace_ledger(repository, "mro")
    u.Tests.initialize_git_repo(repository)
    return repository


def _install_bd_shim(tmp_path: Path, bead_id: str) -> Path:
    """Install the minimal ``bd`` surface the start saga consumes."""
    store = tmp_path / "beads-store.json"
    store.write_text(
        json.dumps({
            "id": bead_id,
            "status": "open",
            "assignee": None,
            "metadata": {},
            "labels": [],
        }),
        encoding="utf-8",
    )
    shim_dir = tmp_path / "bin"
    shim_dir.mkdir()
    shim = shim_dir / "bd"
    shim.write_text(
        "#!/usr/bin/env python3\n"
        "from __future__ import annotations\n"
        "import json, sys\n"
        f"STORE = {str(store)!r}\n"
        "args = sys.argv[1:]\n"
        "while args:\n"
        "    if args[0] == '-C' and len(args) > 1:\n"
        "        args = args[2:]\n"
        "        continue\n"
        "    if args[0] in {'--json', '--quiet', '-q', '-v', '--verbose'}:\n"
        "        args = args[1:]\n"
        "        continue\n"
        "    break\n"
        "data = json.loads(open(STORE, encoding='utf-8').read())\n"
        "if args[:1] == ['show'] and '--json' in args:\n"
        "    print(json.dumps(data))\n"
        "    raise SystemExit(0)\n"
        "if args[:1] == ['list'] and '--json' in args:\n"
        "    print(json.dumps([data]))\n"
        "    raise SystemExit(0)\n"
        "if args[:1] == ['update']:\n"
        "    i = 1\n"
        "    while i < len(args):\n"
        "        if args[i] == '--set-metadata':\n"
        "            key, value = args[i + 1].split('=', 1)\n"
        "            data.setdefault('metadata', {})[key] = value\n"
        "            i += 2\n"
        "            continue\n"
        "        if args[i] in {'--add-label', '--append-notes'}:\n"
        "            i += 2\n"
        "            continue\n"
        "        i += 1\n"
        "    open(STORE, 'w', encoding='utf-8').write(json.dumps(data))\n"
        "    print('updated')\n"
        "    raise SystemExit(0)\n"
        "raise SystemExit(f'unsupported bd args: {args}')\n",
        encoding="utf-8",
    )
    shim.chmod(0o755)
    return shim_dir


def _start(repository: Path, bead_id: str) -> str:
    """Run one apply-mode start for a fixed kind and slug."""
    return tm.ok(
        FlextInfraWorkService(
            workspace_root=repository,
            operation=c.Infra.WorkOperation.START,
            bead=bead_id,
            kind=c.Infra.WorkKind.FEATURE,
            name="provisioned-lane",
            base="HEAD",
            apply_changes=True,
        ).execute()
    )


def _setup_runs(lane: Path) -> int:
    """Return how many times ``make setup`` ran inside one lane."""
    log = lane / _SETUP_LOG
    if not log.is_file():
        return 0
    return len([line for line in log.read_text(encoding="utf-8").splitlines() if line])


def test_start_provisions_a_new_lane_and_an_adopted_one(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Both the created lane and the re-adopted lane are provisioned."""
    repository = _repository(tmp_path)
    bead_id = "mro-test-start-setup"
    shim_dir = _install_bd_shim(tmp_path, bead_id)
    monkeypatch.setenv("PATH", f"{shim_dir}{os.pathsep}{os.environ.get('PATH', '')}")

    first = _start(repository, bead_id)
    lane = Path(
        next(
            field.removeprefix("receipt.worktree=")
            for field in first.splitlines()
            if field.startswith("receipt.worktree=")
        )
    )
    created_runs = _setup_runs(lane)

    _ = _start(repository, bead_id)

    assert created_runs >= 1, "start left the created lane unprovisioned"
    assert _setup_runs(lane) > created_runs, (
        "start adopted the existing lane without provisioning it"
    )


__all__: tuple[str, ...] = ()
