"""Real Git + shim bd behavior for make work saga."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import TYPE_CHECKING

import flext_infra
import pytest
from flext_infra import FlextInfraWorkService, c, u
from flext_tests import tm
from tests import u as test_u

if TYPE_CHECKING:
    from pathlib import Path as PathType


class TestsFlextInfraWorkService:
    """Public work saga owns bead/branch/worktree registration."""

    @staticmethod
    def _repository(tmp_path: PathType) -> PathType:
        repository = tmp_path / "repository"
        repository.mkdir()
        (repository / "README.md").write_text("fixture\n", encoding="utf-8")
        (repository / "pyproject.toml").write_text(
            '[project]\nname = "fixture"\nversion = "0.1.0"\n'
            'description = "A standard PEP 621 description string"\n',
            encoding="utf-8",
        )
        (repository / "Makefile").write_text(
            ".PHONY: setup\n"
            "setup:\n"
            '\t@test "$(WORKSPACE)" = "$(CURDIR)"\n'
            '\t@grep -q "^\\[project\\]" "$(WORKSPACE)/pyproject.toml"\n'
            '\t@printf "setting up %s\\n" "$(WORKSPACE)"\n',
            encoding="utf-8",
        )
        beads = repository / ".beads"
        beads.mkdir()
        (beads / "config.yaml").write_text('issue-prefix: "mro"\n', encoding="utf-8")
        test_u.Tests.initialize_git_repo(repository)
        return repository

    @staticmethod
    def _install_bd_shim(tmp_path: PathType, bead_id: str) -> PathType:
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
            "if args[:1] == ['update']:\n"
            "    i = 1\n"
            "    while i < len(args):\n"
            "        if args[i] == '--set-metadata':\n"
            "            key, value = args[i + 1].split('=', 1)\n"
            "            data.setdefault('metadata', {})[key] = value\n"
            "            i += 2\n"
            "            continue\n"
            "        if args[i] == '--add-label':\n"
            "            labels = data.setdefault('labels', [])\n"
            "            if args[i + 1] not in labels:\n"
            "                labels.append(args[i + 1])\n"
            "            i += 2\n"
            "            continue\n"
            "        if args[i] == '--append-notes':\n"
            "            notes = data.setdefault('notes', [])\n"
            "            notes.append(args[i + 1])\n"
            "            i += 2\n"
            "            continue\n"
            "        if args[i] == '--claim':\n"
            "            data['assignee'] = 'worker'\n"
            "            i += 1\n"
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

    @staticmethod
    def _install_gh_shim(tmp_path: PathType) -> PathType:
        shim_dir = tmp_path / "bin"
        shim_dir.mkdir(exist_ok=True)
        shim = shim_dir / "gh"
        shim.write_text(
            "#!/usr/bin/env python3\n"
            "from __future__ import annotations\n"
            "import json, sys\n"
            "args = sys.argv[1:]\n"
            "if args[:2] == ['pr', 'list']:\n"
            "    print('[]')\n"
            "    raise SystemExit(0)\n"
            "if args[:2] == ['pr', 'create']:\n"
            "    print('https://example.test/pr/1')\n"
            "    raise SystemExit(0)\n"
            "if args[:2] == ['pr', 'view']:\n"
            "    print(json.dumps({'state': 'MERGED', 'mergedAt': '2026-08-03T00:00:00Z', 'headRefName': ''}))\n"
            "    raise SystemExit(0)\n"
            "raise SystemExit(f'unsupported gh args: {args}')\n",
            encoding="utf-8",
        )
        shim.chmod(0o755)
        return shim_dir

    def test_start_registers_lane_and_status_reports_metadata(
        self, tmp_path: PathType, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        repository = self._repository(tmp_path)
        bead_id = "mro-test-work"
        shim_dir = self._install_bd_shim(tmp_path, bead_id)
        monkeypatch.setenv(
            "PATH", f"{shim_dir}{os.pathsep}{os.environ.get('PATH', '')}"
        )
        started = tm.ok(
            FlextInfraWorkService(
                workspace_root=repository,
                operation=c.Infra.WorkOperation.START,
                bead=bead_id,
                kind=c.Infra.WorkKind.FEATURE,
                name="example-lane",
                base="HEAD",
                apply_changes=True,
            ).execute()
        )
        tm.that(started, has="BRANCH=feature/example-lane")
        tm.that(started, has="WORKTREE=")
        status = tm.ok(
            FlextInfraWorkService(
                workspace_root=repository,
                operation=c.Infra.WorkOperation.STATUS,
                bead=bead_id,
                apply_changes=False,
            ).execute()
        )
        tm.that(status, has="metadata.branch: feature/example-lane")
        tm.that(status, has="metadata.worktree:")

    def test_finish_refuses_primary_checkout(
        self, tmp_path: PathType, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        repository = self._repository(tmp_path)
        bead_id = "mro-test-primary"
        shim_dir = self._install_bd_shim(tmp_path, bead_id)
        monkeypatch.setenv(
            "PATH", f"{shim_dir}{os.pathsep}{os.environ.get('PATH', '')}"
        )
        store = tmp_path / "beads-store.json"
        payload = json.loads(store.read_text(encoding="utf-8"))
        payload["metadata"] = {
            "branch": "feature/primary-abuse",
            "worktree": str(repository),
            "integration_base": "HEAD",
            "head_oid": tm.ok(
                test_u.Infra.git_capture(repository, ("rev-parse", "HEAD"))
            ),
        }
        store.write_text(json.dumps(payload), encoding="utf-8")
        result = FlextInfraWorkService(
            workspace_root=repository,
            operation=c.Infra.WorkOperation.FINISH,
            bead=bead_id,
            apply_changes=True,
        ).execute()
        tm.fail(result, has="refuses the primary worktree")

    def test_start_requires_bead(self, tmp_path: PathType) -> None:
        repository = self._repository(tmp_path)
        result = FlextInfraWorkService(
            workspace_root=repository,
            operation=c.Infra.WorkOperation.START,
            kind=c.Infra.WorkKind.FEATURE,
            name="no-bead",
            base="HEAD",
            apply_changes=True,
        ).execute()
        tm.fail(result, has="requires --bead")

    def test_beads_resolve_prefers_parent_workspace_config(
        self, tmp_path: PathType
    ) -> None:
        workspace = tmp_path / "workspace"
        member = workspace / "member"
        member.mkdir(parents=True)
        (workspace / ".beads").mkdir()
        (workspace / ".beads" / "config.yaml").write_text(
            'issue-prefix: "mro"\n', encoding="utf-8"
        )
        test_u.Tests.initialize_git_repo(member)
        resolved = tm.ok(u.Infra.beads_resolve_root(member))
        assert str(resolved) == str(workspace.resolve())
        resolved_workspace = tm.ok(u.Infra.beads_resolve_root(workspace))
        assert str(resolved_workspace) == str(workspace.resolve())

    def test_finish_removes_lane_and_updates_metadata(
        self, tmp_path: PathType, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        repository = self._repository(tmp_path)
        bead_id = "mro-test-finish"
        shim_dir = self._install_bd_shim(tmp_path, bead_id)
        self._install_gh_shim(tmp_path)
        monkeypatch.setenv(
            "PATH", f"{shim_dir}{os.pathsep}{os.environ.get('PATH', '')}"
        )
        started = tm.ok(
            FlextInfraWorkService(
                workspace_root=repository,
                operation=c.Infra.WorkOperation.START,
                bead=bead_id,
                kind=c.Infra.WorkKind.BUGFIX,
                name="finish-lane",
                base="HEAD",
                apply_changes=True,
            ).execute()
        )
        tm.that(started, has="BRANCH=bugfix/finish-lane")
        store = json.loads((tmp_path / "beads-store.json").read_text(encoding="utf-8"))
        lane = store["metadata"]["worktree"]
        head = store["metadata"]["head_oid"]
        store["metadata"]["pr_number"] = "1"
        (tmp_path / "beads-store.json").write_text(json.dumps(store), encoding="utf-8")
        finished = tm.ok(
            FlextInfraWorkService(
                workspace_root=repository,
                operation=c.Infra.WorkOperation.FINISH,
                bead=bead_id,
                apply_changes=True,
            ).execute()
        )
        tm.that(finished, has="FINISHED BRANCH=bugfix/finish-lane")
        assert not Path(lane).exists()
        updated = json.loads(
            (tmp_path / "beads-store.json").read_text(encoding="utf-8")
        )
        assert updated["metadata"]["worktree"] == "removed"
        assert updated["metadata"]["head_oid"] == head

    def test_finish_cas_mismatch_fails(
        self, tmp_path: PathType, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        repository = self._repository(tmp_path)
        bead_id = "mro-test-cas"
        shim_dir = self._install_bd_shim(tmp_path, bead_id)
        self._install_gh_shim(tmp_path)
        monkeypatch.setenv(
            "PATH", f"{shim_dir}{os.pathsep}{os.environ.get('PATH', '')}"
        )
        tm.ok(
            FlextInfraWorkService(
                workspace_root=repository,
                operation=c.Infra.WorkOperation.START,
                bead=bead_id,
                kind=c.Infra.WorkKind.FEATURE,
                name="cas-lane",
                base="HEAD",
                apply_changes=True,
            ).execute()
        )
        store = json.loads((tmp_path / "beads-store.json").read_text(encoding="utf-8"))
        store["metadata"]["head_oid"] = "0" * 40
        store["metadata"]["pr_number"] = "1"
        (tmp_path / "beads-store.json").write_text(json.dumps(store), encoding="utf-8")
        result = FlextInfraWorkService(
            workspace_root=repository,
            operation=c.Infra.WorkOperation.FINISH,
            bead=bead_id,
            apply_changes=True,
        ).execute()
        tm.fail(result, has="CAS failed")

    def test_land_refuses_permanent_branch(
        self, tmp_path: PathType, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        repository = self._repository(tmp_path)
        bead_id = "mro-test-land-perm"
        shim_dir = self._install_bd_shim(tmp_path, bead_id)
        monkeypatch.setenv(
            "PATH", f"{shim_dir}{os.pathsep}{os.environ.get('PATH', '')}"
        )
        store = tmp_path / "beads-store.json"
        payload = json.loads(store.read_text(encoding="utf-8"))
        payload["metadata"] = {
            "branch": "main",
            "worktree": str(tmp_path / "fake-lane"),
            "integration_base": "HEAD",
            "head_oid": "a" * 40,
        }
        store.write_text(json.dumps(payload), encoding="utf-8")
        result = FlextInfraWorkService(
            workspace_root=repository,
            operation=c.Infra.WorkOperation.LAND,
            bead=bead_id,
            apply_changes=True,
        ).execute()
        tm.fail(result, has="permanent branch")

    def test_land_requires_head_oid(
        self, tmp_path: PathType, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        repository = self._repository(tmp_path)
        bead_id = "mro-test-land-oid"
        shim_dir = self._install_bd_shim(tmp_path, bead_id)
        monkeypatch.setenv(
            "PATH", f"{shim_dir}{os.pathsep}{os.environ.get('PATH', '')}"
        )
        tm.ok(
            FlextInfraWorkService(
                workspace_root=repository,
                operation=c.Infra.WorkOperation.START,
                bead=bead_id,
                kind=c.Infra.WorkKind.FEATURE,
                name="land-oid",
                base="HEAD",
                apply_changes=True,
            ).execute()
        )
        store = json.loads((tmp_path / "beads-store.json").read_text(encoding="utf-8"))
        store["metadata"]["head_oid"] = ""
        (tmp_path / "beads-store.json").write_text(json.dumps(store), encoding="utf-8")
        result = FlextInfraWorkService(
            workspace_root=repository,
            operation=c.Infra.WorkOperation.LAND,
            bead=bead_id,
            apply_changes=True,
        ).execute()
        tm.fail(result, has="missing metadata.head_oid")

    def test_land_refuses_metadata_worktree_mismatch(
        self, tmp_path: PathType, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        repository = self._repository(tmp_path)
        bead_id = "mro-test-land-bind"
        shim_dir = self._install_bd_shim(tmp_path, bead_id)
        monkeypatch.setenv(
            "PATH", f"{shim_dir}{os.pathsep}{os.environ.get('PATH', '')}"
        )
        tm.ok(
            FlextInfraWorkService(
                workspace_root=repository,
                operation=c.Infra.WorkOperation.START,
                bead=bead_id,
                kind=c.Infra.WorkKind.FEATURE,
                name="land-bind",
                base="HEAD",
                apply_changes=True,
            ).execute()
        )
        poison = tmp_path / "poison-tree"
        poison.mkdir()
        (poison / "README.md").write_text("poison\n", encoding="utf-8")
        test_u.Tests.initialize_git_repo(poison)
        store = json.loads((tmp_path / "beads-store.json").read_text(encoding="utf-8"))
        store["metadata"]["worktree"] = str(poison)
        (tmp_path / "beads-store.json").write_text(json.dumps(store), encoding="utf-8")
        result = FlextInfraWorkService(
            workspace_root=repository,
            operation=c.Infra.WorkOperation.LAND,
            bead=bead_id,
            apply_changes=True,
        ).execute()
        tm.fail(result, has="does not match registered lane")

    def test_finish_requires_head_oid(
        self, tmp_path: PathType, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        repository = self._repository(tmp_path)
        bead_id = "mro-test-finish-oid"
        shim_dir = self._install_bd_shim(tmp_path, bead_id)
        self._install_gh_shim(tmp_path)
        monkeypatch.setenv(
            "PATH", f"{shim_dir}{os.pathsep}{os.environ.get('PATH', '')}"
        )
        tm.ok(
            FlextInfraWorkService(
                workspace_root=repository,
                operation=c.Infra.WorkOperation.START,
                bead=bead_id,
                kind=c.Infra.WorkKind.BUGFIX,
                name="finish-oid",
                base="HEAD",
                apply_changes=True,
            ).execute()
        )
        store = json.loads((tmp_path / "beads-store.json").read_text(encoding="utf-8"))
        store["metadata"]["head_oid"] = ""
        store["metadata"]["pr_number"] = "1"
        (tmp_path / "beads-store.json").write_text(json.dumps(store), encoding="utf-8")
        result = FlextInfraWorkService(
            workspace_root=repository,
            operation=c.Infra.WorkOperation.FINISH,
            bead=bead_id,
            apply_changes=True,
        ).execute()
        tm.fail(result, has="missing metadata.head_oid")

    def test_finish_refuses_permanent_branch_via_config_integration(
        self, tmp_path: PathType, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        repository = self._repository(tmp_path)
        config = repository / "config"
        config.mkdir()
        (config / "workspace.yaml").write_text(
            "integration:\n  branch: 0.12.0-dev\n", encoding="utf-8"
        )
        bead_id = "mro-test-finish-perm"
        shim_dir = self._install_bd_shim(tmp_path, bead_id)
        monkeypatch.setenv(
            "PATH", f"{shim_dir}{os.pathsep}{os.environ.get('PATH', '')}"
        )
        store = tmp_path / "beads-store.json"
        payload = json.loads(store.read_text(encoding="utf-8"))
        payload["metadata"] = {
            "branch": "0.12.0-dev",
            "worktree": str(tmp_path / "fake-lane"),
            "integration_base": "",
            "head_oid": "a" * 40,
        }
        store.write_text(json.dumps(payload), encoding="utf-8")
        result = FlextInfraWorkService(
            workspace_root=repository,
            operation=c.Infra.WorkOperation.FINISH,
            bead=bead_id,
            apply_changes=True,
        ).execute()
        tm.fail(result, has="permanent branch")

    def test_finish_refuses_already_removed(
        self, tmp_path: PathType, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        repository = self._repository(tmp_path)
        bead_id = "mro-test-finish-removed"
        shim_dir = self._install_bd_shim(tmp_path, bead_id)
        monkeypatch.setenv(
            "PATH", f"{shim_dir}{os.pathsep}{os.environ.get('PATH', '')}"
        )
        store = tmp_path / "beads-store.json"
        payload = json.loads(store.read_text(encoding="utf-8"))
        payload["metadata"] = {
            "branch": "bugfix/gone",
            "worktree": "removed",
            "integration_base": "HEAD",
            "head_oid": "a" * 40,
        }
        store.write_text(json.dumps(payload), encoding="utf-8")
        result = FlextInfraWorkService(
            workspace_root=repository,
            operation=c.Infra.WorkOperation.FINISH,
            bead=bead_id,
            apply_changes=True,
        ).execute()
        tm.fail(result, has="already removed")

    def test_status_reports_after_start(
        self, tmp_path: PathType, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        repository = self._repository(tmp_path)
        bead_id = "mro-test-status-detail"
        shim_dir = self._install_bd_shim(tmp_path, bead_id)
        monkeypatch.setenv(
            "PATH", f"{shim_dir}{os.pathsep}{os.environ.get('PATH', '')}"
        )
        tm.ok(
            FlextInfraWorkService(
                workspace_root=repository,
                operation=c.Infra.WorkOperation.START,
                bead=bead_id,
                kind=c.Infra.WorkKind.FEATURE,
                name="status-detail",
                base="HEAD",
                apply_changes=True,
            ).execute()
        )
        status = tm.ok(
            FlextInfraWorkService(
                workspace_root=repository,
                operation=c.Infra.WorkOperation.STATUS,
                bead=bead_id,
                apply_changes=False,
            ).execute()
        )
        tm.that(status, has="branch: feature/status-detail")
        tm.that(status, has="primary_checkout:")

    def test_finish_refuses_metadata_worktree_mismatch(
        self, tmp_path: PathType, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        repository = self._repository(tmp_path)
        bead_id = "mro-test-finish-bind"
        shim_dir = self._install_bd_shim(tmp_path, bead_id)
        self._install_gh_shim(tmp_path)
        monkeypatch.setenv(
            "PATH", f"{shim_dir}{os.pathsep}{os.environ.get('PATH', '')}"
        )
        tm.ok(
            FlextInfraWorkService(
                workspace_root=repository,
                operation=c.Infra.WorkOperation.START,
                bead=bead_id,
                kind=c.Infra.WorkKind.BUGFIX,
                name="finish-bind",
                base="HEAD",
                apply_changes=True,
            ).execute()
        )
        poison = tmp_path / "poison-finish"
        poison.mkdir()
        (poison / "README.md").write_text("poison\n", encoding="utf-8")
        test_u.Tests.initialize_git_repo(poison)
        store = json.loads((tmp_path / "beads-store.json").read_text(encoding="utf-8"))
        store["metadata"]["worktree"] = str(poison)
        store["metadata"]["pr_number"] = "1"
        (tmp_path / "beads-store.json").write_text(json.dumps(store), encoding="utf-8")
        result = FlextInfraWorkService(
            workspace_root=repository,
            operation=c.Infra.WorkOperation.FINISH,
            bead=bead_id,
            apply_changes=True,
        ).execute()
        tm.fail(result, has="does not match registered lane")

    def test_start_rejects_invalid_slug(
        self, tmp_path: PathType, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        repository = self._repository(tmp_path)
        bead_id = "mro-test-bad-slug"
        shim_dir = self._install_bd_shim(tmp_path, bead_id)
        monkeypatch.setenv(
            "PATH", f"{shim_dir}{os.pathsep}{os.environ.get('PATH', '')}"
        )
        result = FlextInfraWorkService(
            workspace_root=repository,
            operation=c.Infra.WorkOperation.START,
            bead=bead_id,
            kind=c.Infra.WorkKind.FEATURE,
            name="Not_Kebab",
            base="HEAD",
            apply_changes=True,
        ).execute()
        tm.fail(result, has="kebab-case required")

    def test_start_rejects_forbidden_slug(
        self, tmp_path: PathType, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        repository = self._repository(tmp_path)
        bead_id = "mro-test-forbidden-slug"
        shim_dir = self._install_bd_shim(tmp_path, bead_id)
        monkeypatch.setenv(
            "PATH", f"{shim_dir}{os.pathsep}{os.environ.get('PATH', '')}"
        )
        result = FlextInfraWorkService(
            workspace_root=repository,
            operation=c.Infra.WorkOperation.START,
            bead=bead_id,
            kind=c.Infra.WorkKind.FEATURE,
            name="temp",
            base="HEAD",
            apply_changes=True,
        ).execute()
        tm.fail(result, has="forbidden work slug")

    def test_start_requires_apply(self, tmp_path: PathType) -> None:
        repository = self._repository(tmp_path)
        result = FlextInfraWorkService(
            workspace_root=repository,
            operation=c.Infra.WorkOperation.START,
            bead="mro-test-start-apply",
            kind=c.Infra.WorkKind.FEATURE,
            name="needs-apply",
            base="HEAD",
            apply_changes=False,
        ).execute()
        tm.fail(result, has="requires --apply")

    def test_land_requires_apply(
        self, tmp_path: PathType, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        repository = self._repository(tmp_path)
        bead_id = "mro-test-land-apply"
        shim_dir = self._install_bd_shim(tmp_path, bead_id)
        monkeypatch.setenv(
            "PATH", f"{shim_dir}{os.pathsep}{os.environ.get('PATH', '')}"
        )
        result = FlextInfraWorkService(
            workspace_root=repository,
            operation=c.Infra.WorkOperation.LAND,
            bead=bead_id,
            apply_changes=False,
        ).execute()
        tm.fail(result, has="requires --apply")

    def test_land_cas_mismatch_fails(
        self, tmp_path: PathType, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        repository = self._repository(tmp_path)
        bead_id = "mro-test-land-cas"
        shim_dir = self._install_bd_shim(tmp_path, bead_id)
        self._install_gh_shim(tmp_path)
        monkeypatch.setenv(
            "PATH", f"{shim_dir}{os.pathsep}{os.environ.get('PATH', '')}"
        )
        tm.ok(
            FlextInfraWorkService(
                workspace_root=repository,
                operation=c.Infra.WorkOperation.START,
                bead=bead_id,
                kind=c.Infra.WorkKind.FEATURE,
                name="land-cas",
                base="HEAD",
                apply_changes=True,
            ).execute()
        )
        store = json.loads((tmp_path / "beads-store.json").read_text(encoding="utf-8"))
        store["metadata"]["head_oid"] = "0" * 40
        (tmp_path / "beads-store.json").write_text(json.dumps(store), encoding="utf-8")
        result = FlextInfraWorkService(
            workspace_root=repository,
            operation=c.Infra.WorkOperation.LAND,
            bead=bead_id,
            apply_changes=True,
        ).execute()
        tm.fail(result, has="CAS failed")

    def test_land_refuses_dirty_lane(
        self, tmp_path: PathType, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        repository = self._repository(tmp_path)
        bead_id = "mro-test-land-dirty"
        shim_dir = self._install_bd_shim(tmp_path, bead_id)
        self._install_gh_shim(tmp_path)
        monkeypatch.setenv(
            "PATH", f"{shim_dir}{os.pathsep}{os.environ.get('PATH', '')}"
        )
        tm.ok(
            FlextInfraWorkService(
                workspace_root=repository,
                operation=c.Infra.WorkOperation.START,
                bead=bead_id,
                kind=c.Infra.WorkKind.BUGFIX,
                name="land-dirty",
                base="HEAD",
                apply_changes=True,
            ).execute()
        )
        store = json.loads((tmp_path / "beads-store.json").read_text(encoding="utf-8"))
        lane = Path(store["metadata"]["worktree"])
        (lane / "dirty.txt").write_text("dirty\n", encoding="utf-8")
        result = FlextInfraWorkService(
            workspace_root=repository,
            operation=c.Infra.WorkOperation.LAND,
            bead=bead_id,
            apply_changes=True,
        ).execute()
        tm.fail(result, has="clean lane worktree")

    def test_makefile_j2_exposes_work_builtins_on_workspace(self) -> None:
        template = (
            Path(flext_infra.__file__).resolve().parent
            / "templates"
            / "project"
            / "base"
            / "Makefile.j2"
        ).read_text(encoding="utf-8")
        tm.that(template, has="override WORKSPACE := $(PROJECT_ROOT)/$(PROJECT)")
        tm.that(template, has="_builtin_work_status:")
        tm.that(template, has="_builtin_work_start:")
        tm.that(template, has="_builtin_work_land:")
        tm.that(template, has="_builtin_work_finish:")
        tm.that(
            template,
            has='workspace work --workspace "$(WORKSPACE)" --operation status',
        )
        tm.that(
            template,
            has='workspace work --workspace "$(WORKSPACE)" --operation land',
        )

    def test_finish_refuses_missing_lane(
        self, tmp_path: PathType, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        repository = self._repository(tmp_path)
        bead_id = "mro-test-finish-missing"
        shim_dir = self._install_bd_shim(tmp_path, bead_id)
        self._install_gh_shim(tmp_path)
        monkeypatch.setenv(
            "PATH", f"{shim_dir}{os.pathsep}{os.environ.get('PATH', '')}"
        )
        tm.ok(
            FlextInfraWorkService(
                workspace_root=repository,
                operation=c.Infra.WorkOperation.START,
                bead=bead_id,
                kind=c.Infra.WorkKind.BUGFIX,
                name="finish-missing",
                base="HEAD",
                apply_changes=True,
            ).execute()
        )
        store = json.loads((tmp_path / "beads-store.json").read_text(encoding="utf-8"))
        lane = Path(store["metadata"]["worktree"])
        store["metadata"]["pr_number"] = "1"
        (tmp_path / "beads-store.json").write_text(json.dumps(store), encoding="utf-8")
        for child in sorted(lane.rglob("*"), reverse=True):
            if child.is_file() or child.is_symlink():
                child.unlink()
            elif child.is_dir():
                child.rmdir()
        lane.rmdir()
        result = FlextInfraWorkService(
            workspace_root=repository,
            operation=c.Infra.WorkOperation.FINISH,
            bead=bead_id,
            apply_changes=True,
        ).execute()
        tm.fail(result, has="lane worktree missing")
        updated = json.loads(
            (tmp_path / "beads-store.json").read_text(encoding="utf-8")
        )
        assert updated["metadata"]["worktree"] != "removed"

    def test_finish_fails_when_pr_list_errors(
        self, tmp_path: PathType, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        repository = self._repository(tmp_path)
        bead_id = "mro-test-finish-gh-fail"
        shim_dir = self._install_bd_shim(tmp_path, bead_id)
        monkeypatch.setenv(
            "PATH", f"{shim_dir}{os.pathsep}{os.environ.get('PATH', '')}"
        )
        tm.ok(
            FlextInfraWorkService(
                workspace_root=repository,
                operation=c.Infra.WorkOperation.START,
                bead=bead_id,
                kind=c.Infra.WorkKind.FEATURE,
                name="finish-gh-fail",
                base="HEAD",
                apply_changes=True,
            ).execute()
        )
        gh = shim_dir / "gh"
        gh.write_text(
            "#!/usr/bin/env python3" + chr(10)
            + "import sys" + chr(10)
            + "raise SystemExit('gh unavailable')" + chr(10),
            encoding="utf-8",
        )
        gh.chmod(0o755)
        result = FlextInfraWorkService(
            workspace_root=repository,
            operation=c.Infra.WorkOperation.FINISH,
            bead=bead_id,
            apply_changes=True,
        ).execute()
        tm.fail(result, has="gh unavailable")

    def test_finish_refuses_pr_head_mismatch(
        self, tmp_path: PathType, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        repository = self._repository(tmp_path)
        bead_id = "mro-test-finish-pr-head"
        shim_dir = self._install_bd_shim(tmp_path, bead_id)
        monkeypatch.setenv(
            "PATH", f"{shim_dir}{os.pathsep}{os.environ.get('PATH', '')}"
        )
        tm.ok(
            FlextInfraWorkService(
                workspace_root=repository,
                operation=c.Infra.WorkOperation.START,
                bead=bead_id,
                kind=c.Infra.WorkKind.BUGFIX,
                name="finish-pr-head",
                base="HEAD",
                apply_changes=True,
            ).execute()
        )
        store = json.loads((tmp_path / "beads-store.json").read_text(encoding="utf-8"))
        store["metadata"]["pr_number"] = "9"
        (tmp_path / "beads-store.json").write_text(json.dumps(store), encoding="utf-8")
        gh = shim_dir / "gh"
        gh.write_text(
            "#!/usr/bin/env python3" + chr(10)
            + "import json, sys" + chr(10)
            + "print(json.dumps({'state': 'MERGED', 'mergedAt': '2026-08-03T00:00:00Z', 'headRefName': 'feature/other'}))" + chr(10),
            encoding="utf-8",
        )
        gh.chmod(0o755)
        result = FlextInfraWorkService(
            workspace_root=repository,
            operation=c.Infra.WorkOperation.FINISH,
            bead=bead_id,
            apply_changes=True,
        ).execute()
        tm.fail(result, has="does not match lane branch")

    def test_land_refuses_integration_base_drift(
        self, tmp_path: PathType, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        repository = self._repository(tmp_path)
        config = repository / "config"
        config.mkdir()
        (config / "workspace.yaml").write_text(
            "integration:" + chr(10) + "  branch: 0.12.0-dev" + chr(10),
            encoding="utf-8",
        )
        bead_id = "mro-test-land-base-drift"
        shim_dir = self._install_bd_shim(tmp_path, bead_id)
        self._install_gh_shim(tmp_path)
        monkeypatch.setenv(
            "PATH", f"{shim_dir}{os.pathsep}{os.environ.get('PATH', '')}"
        )
        tm.ok(
            FlextInfraWorkService(
                workspace_root=repository,
                operation=c.Infra.WorkOperation.START,
                bead=bead_id,
                kind=c.Infra.WorkKind.FEATURE,
                name="land-base-drift",
                base="HEAD",
                apply_changes=True,
            ).execute()
        )
        store = json.loads((tmp_path / "beads-store.json").read_text(encoding="utf-8"))
        store["metadata"]["integration_base"] = "attacker-base"
        (tmp_path / "beads-store.json").write_text(json.dumps(store), encoding="utf-8")
        result = FlextInfraWorkService(
            workspace_root=repository,
            operation=c.Infra.WorkOperation.LAND,
            bead=bead_id,
            apply_changes=True,
        ).execute()
        tm.fail(result, has="integration_base drift")
