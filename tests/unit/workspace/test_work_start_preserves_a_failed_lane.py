"""A lane whose provisioning fails survives so the next start resumes it.

Provisioning is the slowest and most fragile part of ``work start``: it clones
every governed submodule and builds the environment. Destroying the checkout on
failure threw away minutes of work and forced a manual re-clone, and the operator
hit exactly that twice — a stale submodule checkout failed ``make setup`` and the
lane vanished with it.

Failure must therefore be RESUMABLE: keep the lane and its branch exactly as they
are, report the real cause, and let the same command continue from the existing
checkout once the cause is resolved.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest
from flext_core import p as core_p
from flext_infra import FlextInfraWorkService, c
from flext_tests import tm
from tests import u

_SETUP_MARKER = "setup-attempted"


def _repository(tmp_path: Path, *, setup_exit: int) -> Path:
    """Return a committed repository whose ``setup`` exits with ``setup_exit``."""
    repository = tmp_path / "repository"
    repository.mkdir()
    (repository / "pyproject.toml").write_text(
        '[project]\nname = "fixture"\nversion = "0.1.0"\n'
        'description = "A standard PEP 621 description string"\n',
        encoding="utf-8",
    )
    # The marker proves provisioning really ran inside the lane before failing,
    # so a surviving lane cannot be confused with one that was never created.
    (repository / "Makefile").write_text(
        ".PHONY: setup\n"
        "setup:\n"
        f'\t@printf "%s\\n" "$(CURDIR)" >> "$(CURDIR)/{_SETUP_MARKER}"\n'
        f"\t@exit {setup_exit}\n",
        encoding="utf-8",
    )
    (repository / ".gitignore").write_text(
        f"{_SETUP_MARKER}\n{c.Infra.WORKTREES_DIRNAME}/\n", encoding="utf-8"
    )
    beads = repository / ".beads"
    beads.mkdir()
    (beads / "config.yaml").write_text('issue-prefix: "mro"\n', encoding="utf-8")
    u.Tests.initialize_git_repo(repository)
    return repository


def _epic_lane(repository: Path, bead_id: str) -> Path:
    """Return the canonical parent epic lane of one bead."""
    return repository / c.Infra.WORKTREES_DIRNAME / f"{bead_id}-epic-parent-epic"


def _install_bd_shim(tmp_path: Path, bead_id: str) -> Path:
    """Install the ``bd`` surface plus the parent epic lane start requires."""
    repository = tmp_path / "repository"
    epic_id = f"{bead_id}-epic"
    epic_lane = _epic_lane(repository, bead_id)
    tm.ok(
        u.Cli.run_checked(
            [
                c.Infra.GIT,
                "worktree",
                "add",
                "-b",
                f"epic/{epic_id}-parent-epic",
                str(epic_lane),
                "HEAD",
            ],
            cwd=repository,
        )
    )
    store = tmp_path / "beads-store.json"
    store.write_text(
        json.dumps({
            "child": bead_id,
            "beads": {
                epic_id: {
                    "id": epic_id,
                    "status": "open",
                    "assignee": None,
                    "metadata": {
                        "kind": c.Infra.WorkKind.EPIC.value,
                        "slug": "parent-epic",
                        "worktree": str(epic_lane),
                    },
                    "labels": [],
                },
                bead_id: {
                    "id": bead_id,
                    "status": "open",
                    "assignee": None,
                    "parent": epic_id,
                    "metadata": {},
                    "labels": [],
                },
            },
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
        "store = json.loads(open(STORE, encoding='utf-8').read())\n"
        "beads = store['beads']\n"
        "if len(args) < 2 or args[1] not in beads:\n"
        "    raise SystemExit(f'unknown bead: {args}')\n"
        "data = beads[args[1]]\n"
        "if args[:1] == ['show'] and '--json' in args:\n"
        "    print(json.dumps(data))\n"
        "    raise SystemExit(0)\n"
        "if args[:1] == ['update']:\n"
        "    i = 2\n"
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
        "    open(STORE, 'w', encoding='utf-8').write(json.dumps(store))\n"
        "    print('updated')\n"
        "    raise SystemExit(0)\n"
        "raise SystemExit(f'unsupported bd args: {args}')\n",
        encoding="utf-8",
    )
    shim.chmod(0o755)
    return shim_dir


def _start(repository: Path, bead_id: str) -> core_p.Result[str]:
    """Run one apply-mode start for a fixed kind and slug."""
    return FlextInfraWorkService(
        workspace_root=repository,
        operation=c.Infra.WorkOperation.START,
        bead=bead_id,
        kind=c.Infra.WorkKind.FEATURE,
        name="resumable-lane",
        base="HEAD",
        apply_changes=True,
    ).execute()


def _lane_paths(repository: Path, bead_id: str) -> list[Path]:
    """Return every registered lane below the bead's parent epic lane."""
    listed = tm.ok(
        u.Cli.capture(["git", "worktree", "list", "--porcelain"], cwd=repository)
    )
    container = _epic_lane(repository, bead_id) / c.Infra.WORKTREES_DIRNAME
    return [
        registered
        for line in listed.splitlines()
        if line.startswith("worktree ")
        for registered in (Path(line.removeprefix("worktree ").strip()),)
        if registered.is_relative_to(container)
    ]


class TestsWorkStartPreservesAFailedLane:
    """Provisioning failure keeps the lane so the next start resumes it."""

    def test_failed_provisioning_preserves_the_lane_and_reports_the_cause(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """The lane survives, and the error names it as resumable."""
        repository = _repository(tmp_path, setup_exit=1)
        bead_id = "mro-test-start-resumable"
        shim_dir = _install_bd_shim(tmp_path, bead_id)
        monkeypatch.setenv(
            "PATH", f"{shim_dir}{os.pathsep}{os.environ.get('PATH', '')}"
        )

        outcome = _start(repository, bead_id)

        tm.that(outcome.failure, eq=True)
        lanes = _lane_paths(repository, bead_id)
        tm.that(len(lanes), eq=1, msg="provisioning failure destroyed the lane")
        tm.that(lanes[0].is_dir(), eq=True)
        tm.that((lanes[0] / _SETUP_MARKER).is_file(), eq=True)
        tm.that(outcome.error or "", has="preserved")


__all__: tuple[str, ...] = ()
