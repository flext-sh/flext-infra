"""Real Git + shim bd behavior for make work saga."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import TYPE_CHECKING

import flext_infra
import pytest
from flext_infra import FlextInfraWorkService, FlextInfraWorktreeService, c, m, u
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
        # Why: lanes nest inside the workspace, so the lane container must be
        # ignored or every parent lane would report itself dirty.
        (repository / ".gitignore").write_text(
            f"{c.Infra.WORKTREES_DIRNAME}/\n", encoding="utf-8"
        )
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
    def _epic_of(bead_id: str) -> tuple[str, str, str, str]:
        """Return the parent epic id, slug, lane directory, and branch."""
        epic_id = f"{bead_id}-epic"
        slug = "parent-epic"
        lane_dir = f"{epic_id}-{slug}"
        return epic_id, slug, lane_dir, f"epic/{lane_dir}"

    @classmethod
    def _provision_parent_epic(cls, repository: PathType, bead_id: str) -> PathType:
        """Register the parent epic lane every bead lane must nest under."""
        _, _, lane_dir, branch = cls._epic_of(bead_id)
        lane = repository / c.Infra.WORKTREES_DIRNAME / lane_dir
        tm.ok(
            test_u.Cli.run_checked(
                [c.Infra.GIT, "worktree", "add", "-b", branch, str(lane), "HEAD"],
                cwd=repository,
            )
        )
        return lane

    @classmethod
    def _install_bd_shim(
        cls, tmp_path: PathType, bead_id: str, *, update_fails: bool = False
    ) -> PathType:
        """Install a `bd` surface holding one bead and its parent epic lane."""
        repository = tmp_path / "repository"
        epic_id, epic_slug, _, _ = cls._epic_of(bead_id)
        epic_lane = cls._provision_parent_epic(repository, bead_id)
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
                            "slug": epic_slug,
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
            f"    if {update_fails!r} and args[1] == store['child']:\n"
            "        raise SystemExit('bd update refused')\n"
            "    i = 2\n"
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
            "    open(STORE, 'w', encoding='utf-8').write(json.dumps(store))\n"
            "    print('updated')\n"
            "    raise SystemExit(0)\n"
            "raise SystemExit(f'unsupported bd args: {args}')\n",
            encoding="utf-8",
        )
        shim.chmod(0o755)
        return shim_dir

    @staticmethod
    def _install_gh_shim(
        tmp_path: PathType,
        *,
        pr_list: str = "[]",
        pr_view: str = (
            '{"state": "MERGED", "mergedAt": "2026-08-03T00:00:00Z", "headRefName": ""}'
        ),
    ) -> PathType:
        shim_dir = tmp_path / "bin"
        shim_dir.mkdir(exist_ok=True)
        shim = shim_dir / "gh"
        shim.write_text(
            "#!/usr/bin/env python3\n"
            "from __future__ import annotations\n"
            "import sys\n"
            f"PR_LIST = {pr_list!r}\n"
            f"PR_VIEW = {pr_view!r}\n"
            "args = sys.argv[1:]\n"
            "if args[:2] == ['pr', 'list']:\n"
            "    print(PR_LIST)\n"
            "    raise SystemExit(0)\n"
            "if args[:2] == ['pr', 'create']:\n"
            "    print('https://example.test/pr/1')\n"
            "    raise SystemExit(0)\n"
            "if args[:2] == ['pr', 'view']:\n"
            "    print(PR_VIEW)\n"
            "    raise SystemExit(0)\n"
            "raise SystemExit(f'unsupported gh args: {args}')\n",
            encoding="utf-8",
        )
        shim.chmod(0o755)
        return shim_dir

    @staticmethod
    def _attach_bare_origin(tmp_path: PathType, repository: PathType) -> PathType:
        """Replace the self-referencing fixture remote with a pushable origin."""
        origin = tmp_path / "origin.git"
        tm.ok(
            test_u.Cli.run_checked(
                [c.Infra.GIT, "init", "--bare", str(origin)], cwd=tmp_path
            )
        )
        tm.ok(
            test_u.Cli.run_checked(
                [c.Infra.GIT, "remote", "set-url", "origin", str(origin)],
                cwd=repository,
            )
        )
        tm.ok(
            test_u.Cli.run_checked(
                [c.Infra.GIT, "push", "origin", "main"], cwd=repository
            )
        )
        return origin

    @staticmethod
    def _store(tmp_path: PathType) -> dict[str, object]:
        """Return the whole bd shim store."""
        payload: dict[str, object] = json.loads(
            (tmp_path / "beads-store.json").read_text(encoding="utf-8")
        )
        return payload

    @classmethod
    def _write_store(cls, tmp_path: PathType, store: dict[str, object]) -> None:
        """Persist a mutated bd shim store."""
        (tmp_path / "beads-store.json").write_text(json.dumps(store), encoding="utf-8")

    @staticmethod
    def _mapping(value: object, what: str) -> dict[str, object]:
        """Narrow one decoded JSON value to the mapping it must be."""
        if not isinstance(value, dict):
            message = f"bd shim store has no {what} mapping"
            raise TypeError(message)
        return {str(key): item for key, item in value.items()}

    @classmethod
    def _bead(cls, tmp_path: PathType) -> dict[str, object]:
        """Return the bead record under test."""
        store = cls._store(tmp_path)
        beads = cls._mapping(store["beads"], "bead")
        return cls._mapping(beads[str(store["child"])], "bead record")

    @classmethod
    def _metadata(cls, tmp_path: PathType) -> dict[str, str]:
        """Return the lane metadata the bd shim persisted for the bead."""
        metadata = cls._mapping(cls._bead(tmp_path)["metadata"], "lane metadata")
        return {key: str(value) for key, value in metadata.items()}

    @classmethod
    def _root_entry(cls, tmp_path: PathType) -> m.Infra.WorkLaneEntry:
        """Return the workspace-root entry of the persisted lane matrix."""
        matrix = m.Infra.WorkLaneMatrix.model_validate_json(
            cls._metadata(tmp_path)[c.Infra.WORK_BEADS_MATRIX_KEY]
        )
        return next(entry for entry in matrix.entries if entry.project == ".")

    @classmethod
    def _set_root_entry(cls, tmp_path: PathType, **updates: str) -> None:
        """Rewrite the workspace-root matrix entry the bd shim persisted."""
        metadata = cls._metadata(tmp_path)
        matrix = m.Infra.WorkLaneMatrix.model_validate_json(
            metadata[c.Infra.WORK_BEADS_MATRIX_KEY]
        )
        entries = tuple(
            entry.model_copy(update=updates) if entry.project == "." else entry
            for entry in matrix.entries
        )
        store = cls._store(tmp_path)
        beads = cls._mapping(store["beads"], "bead")
        record = cls._mapping(beads[str(store["child"])], "bead record")
        # Why: _mapping rebuilds the outer mapping but keeps the very same nested
        # objects, so writing through this metadata reaches the persisted store.
        record_metadata = cls._mapping(record["metadata"], "lane metadata")
        record_metadata[c.Infra.WORK_BEADS_MATRIX_KEY] = m.Infra.WorkLaneMatrix(
            entries=entries
        ).model_dump_json()
        record["metadata"] = record_metadata
        beads[str(store["child"])] = record
        store["beads"] = beads
        cls._write_store(tmp_path, store)

    @staticmethod
    def _branch(bead_id: str, kind: c.Infra.WorkKind, slug: str) -> str:
        """Return the canonical Bead-derived lane branch."""
        return f"{kind.value}/{bead_id}-{slug}"

    @staticmethod
    def _commit_in(lane: PathType, message: str) -> None:
        tm.ok(
            test_u.Cli.run_checked(
                [c.Infra.GIT, "commit", "--allow-empty", "-m", message], cwd=lane
            )
        )

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
        branch = self._branch(bead_id, c.Infra.WorkKind.FEATURE, "example-lane")
        _, _, epic_dir, epic_branch = self._epic_of(bead_id)
        tm.that(started, has=f"BRANCH={branch}")
        tm.that(
            started,
            has=(
                f"WORKTREE={repository}/{c.Infra.WORKTREES_DIRNAME}/{epic_dir}"
                f"/{c.Infra.WORKTREES_DIRNAME}/{bead_id}-example-lane"
            ),
        )
        tm.that(started, has=f"BASE={epic_branch}")
        matrix = m.Infra.WorkLaneMatrix.model_validate_json(
            self._metadata(tmp_path)[c.Infra.WORK_BEADS_MATRIX_KEY]
        )
        assert matrix.entries[0].model_dump().keys() == {
            "project",
            "branch",
            "head_oid",
            "pr_number",
            "pr_url",
            "state",
        }
        status = tm.ok(
            FlextInfraWorkService(
                workspace_root=repository,
                operation=c.Infra.WorkOperation.STATUS,
                bead=bead_id,
                apply_changes=False,
            ).execute()
        )
        tm.that(status, has=f"metadata.branch: {branch}")
        tm.that(status, has="metadata.worktree:")
        tm.that(status, has=f"lane_parent_branch: {epic_branch}")
        tm.that(status, has=f"lane_base: {epic_branch}")

    def test_finish_refuses_primary_checkout(
        self, tmp_path: PathType, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        repository = self._repository(tmp_path)
        bead_id = "mro-test-primary"
        shim_dir = self._install_bd_shim(tmp_path, bead_id)
        monkeypatch.setenv(
            "PATH", f"{shim_dir}{os.pathsep}{os.environ.get('PATH', '')}"
        )
        store = self._store(tmp_path)
        store["beads"][bead_id]["metadata"] = {  # type: ignore[index]
            "kind": c.Infra.WorkKind.FEATURE.value,
            "slug": "primary-abuse",
            "worktree": str(repository),
            "integration_base": "HEAD",
        }
        self._write_store(tmp_path, store)
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

    def test_beads_resolve_refuses_a_member_tracker(self, tmp_path: PathType) -> None:
        """A member `.beads/` is never adopted: the workspace root owns it."""
        member_source = tmp_path / "member-source"
        member_source.mkdir()
        (member_source / "README.md").write_text("member\n", encoding="utf-8")
        (member_source / ".beads").mkdir()
        (member_source / ".beads" / "config.yaml").write_text(
            'issue-prefix: "flext-infra"\n', encoding="utf-8"
        )
        test_u.Tests.initialize_git_repo(member_source)
        workspace = self._repository(tmp_path)
        (workspace / ".beads").mkdir(exist_ok=True)
        (workspace / ".beads" / "config.yaml").write_text(
            'issue-prefix: "mro"\n', encoding="utf-8"
        )
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

        resolved = tm.ok(u.Infra.beads_resolve_root(workspace / "member"))

        assert str(resolved) == str(workspace.resolve())

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
        branch = self._branch(bead_id, c.Infra.WorkKind.BUGFIX, "finish-lane")
        tm.that(started, has=f"BRANCH={branch}")
        lane = self._metadata(tmp_path)["worktree"]
        head = self._root_entry(tmp_path).head_oid
        self._set_root_entry(tmp_path, pr_number="1")
        finished = tm.ok(
            FlextInfraWorkService(
                workspace_root=repository,
                operation=c.Infra.WorkOperation.FINISH,
                bead=bead_id,
                apply_changes=True,
            ).execute()
        )
        tm.that(finished, has=f"FINISHED BRANCH={branch}")
        assert not Path(lane).exists()
        assert self._metadata(tmp_path)["worktree"] == "removed"
        assert self._root_entry(tmp_path).head_oid == head

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
        self._set_root_entry(tmp_path, head_oid="0" * 40, pr_number="1")
        result = FlextInfraWorkService(
            workspace_root=repository,
            operation=c.Infra.WorkOperation.FINISH,
            bead=bead_id,
            apply_changes=True,
        ).execute()
        tm.fail(result, has="CAS failed")

    def test_land_refuses_a_branch_that_is_not_bead_derived(
        self, tmp_path: PathType, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A poisoned metadata branch (even `main`) never reaches Git."""
        repository = self._repository(tmp_path)
        bead_id = "mro-test-land-perm"
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
                name="land-perm",
                base="HEAD",
                apply_changes=True,
            ).execute()
        )
        self._set_root_entry(tmp_path, branch="main")
        result = FlextInfraWorkService(
            workspace_root=repository,
            operation=c.Infra.WorkOperation.LAND,
            bead=bead_id,
            apply_changes=True,
        ).execute()
        tm.fail(result, has="does not match the derived lane branch")

    def test_land_requires_a_valid_matrix_head(
        self, tmp_path: PathType, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """An empty CAS head is refused by the serialized matrix contract."""
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
        metadata = self._metadata(tmp_path)
        store = self._store(tmp_path)
        store["beads"][bead_id]["metadata"][c.Infra.WORK_BEADS_MATRIX_KEY] = (  # type: ignore[index]
            metadata[c.Infra.WORK_BEADS_MATRIX_KEY].replace(
                self._root_entry(tmp_path).head_oid, ""
            )
        )
        self._write_store(tmp_path, store)
        result = FlextInfraWorkService(
            workspace_root=repository,
            operation=c.Infra.WorkOperation.LAND,
            bead=bead_id,
            apply_changes=True,
        ).execute()
        tm.fail(result, has="invalid serialized workspace lane matrix")

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
        store = self._store(tmp_path)
        store["beads"][bead_id]["metadata"]["worktree"] = str(poison)  # type: ignore[index]
        self._write_store(tmp_path, store)
        result = FlextInfraWorkService(
            workspace_root=repository,
            operation=c.Infra.WorkOperation.LAND,
            bead=bead_id,
            apply_changes=True,
        ).execute()
        tm.fail(result, has="is not the derived lane path")

    def test_finish_refuses_a_branch_that_is_not_bead_derived(
        self, tmp_path: PathType, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A poisoned integration-shaped branch never reaches teardown."""
        repository = self._repository(tmp_path)
        config = repository / "config"
        config.mkdir()
        (config / "workspace.yaml").write_text(
            "integration:\n  branch: 0.12.0-dev\n", encoding="utf-8"
        )
        bead_id = "mro-test-finish-perm"
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
                name="finish-perm",
                base="HEAD",
                apply_changes=True,
            ).execute()
        )
        self._set_root_entry(tmp_path, branch="0.12.0-dev")
        result = FlextInfraWorkService(
            workspace_root=repository,
            operation=c.Infra.WorkOperation.FINISH,
            bead=bead_id,
            apply_changes=True,
        ).execute()
        tm.fail(result, has="does not match the derived lane branch")

    def test_finish_refuses_already_removed(
        self, tmp_path: PathType, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        repository = self._repository(tmp_path)
        bead_id = "mro-test-finish-removed"
        shim_dir = self._install_bd_shim(tmp_path, bead_id)
        monkeypatch.setenv(
            "PATH", f"{shim_dir}{os.pathsep}{os.environ.get('PATH', '')}"
        )
        store = self._store(tmp_path)
        store["beads"][bead_id]["metadata"] = {  # type: ignore[index]
            "kind": c.Infra.WorkKind.BUGFIX.value,
            "slug": "gone",
            "worktree": "removed",
            "integration_base": "HEAD",
        }
        self._write_store(tmp_path, store)
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
        tm.that(
            status,
            has=f"branch: {self._branch(bead_id, c.Infra.WorkKind.FEATURE, 'status-detail')}",
        )
        tm.that(status, has="lane_kind: feature")
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
        self._set_root_entry(tmp_path, pr_number="1")
        store = self._store(tmp_path)
        store["beads"][bead_id]["metadata"]["worktree"] = str(poison)  # type: ignore[index]
        self._write_store(tmp_path, store)
        result = FlextInfraWorkService(
            workspace_root=repository,
            operation=c.Infra.WorkOperation.FINISH,
            bead=bead_id,
            apply_changes=True,
        ).execute()
        tm.fail(result, has="is not the derived lane path")

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
        self._set_root_entry(tmp_path, head_oid="0" * 40)
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
        lane = Path(self._metadata(tmp_path)["worktree"])
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
        tm.that(template, has="ifneq ($(filter work,$(MAKECMDGOALS)),work)")
        tm.that(template, has="_builtin_work_status:")
        tm.that(template, has="_builtin_work_start:")
        tm.that(template, has="_builtin_work_land:")
        tm.that(template, has="_builtin_work_finish:")
        tm.that(
            template, has='workspace work --workspace "$(WORKSPACE)" --operation status'
        )
        tm.that(
            template, has='workspace work --workspace "$(WORKSPACE)" --operation land'
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
        lane = Path(self._metadata(tmp_path)["worktree"])
        self._set_root_entry(tmp_path, pr_number="1")
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
        tm.fail(result, has="matrix project checkout is missing")
        assert self._metadata(tmp_path)["worktree"] != "removed"

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
            "#!/usr/bin/env python3"
            + chr(10)
            + "import sys"
            + chr(10)
            + "raise SystemExit('gh unavailable')"
            + chr(10),
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
        self._set_root_entry(tmp_path, pr_number="9")
        gh = shim_dir / "gh"
        gh.write_text(
            "#!/usr/bin/env python3"
            + chr(10)
            + "import json, sys"
            + chr(10)
            + "print(json.dumps({'state': 'MERGED', 'mergedAt': '2026-08-03T00:00:00Z', 'headRefName': 'feature/other'}))"
            + chr(10),
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
        store = self._store(tmp_path)
        store["beads"][bead_id]["metadata"]["integration_base"] = "attacker-base"  # type: ignore[index]
        self._write_store(tmp_path, store)
        result = FlextInfraWorkService(
            workspace_root=repository,
            operation=c.Infra.WorkOperation.LAND,
            bead=bead_id,
            apply_changes=True,
        ).execute()
        tm.fail(result, has="integration_base drift")

    def test_start_idempotent_same_lane_refreshes_head(
        self, tmp_path: PathType, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Re-running start on a bound bead refreshes CAS instead of failing."""
        repository = self._repository(tmp_path)
        bead_id = "mro-test-start-idempotent"
        shim_dir = self._install_bd_shim(tmp_path, bead_id)
        monkeypatch.setenv(
            "PATH", f"{shim_dir}{os.pathsep}{os.environ.get('PATH', '')}"
        )
        first = tm.ok(
            FlextInfraWorkService(
                workspace_root=repository,
                operation=c.Infra.WorkOperation.START,
                bead=bead_id,
                kind=c.Infra.WorkKind.FEATURE,
                name="idempotent-lane",
                base="HEAD",
                apply_changes=True,
            ).execute()
        )
        tm.that(first, has="receipt.operation=start")
        lane = Path(self._metadata(tmp_path)["worktree"])
        stale_head = self._root_entry(tmp_path).head_oid
        self._commit_in(lane, "lane work")
        second = tm.ok(
            FlextInfraWorkService(
                workspace_root=repository,
                operation=c.Infra.WorkOperation.START,
                bead=bead_id,
                kind=c.Infra.WorkKind.FEATURE,
                name="idempotent-lane",
                base="HEAD",
                apply_changes=True,
            ).execute()
        )
        refreshed = self._root_entry(tmp_path)
        assert self._metadata(tmp_path)["worktree"] == str(lane)
        assert refreshed.head_oid != stale_head
        tm.that(second, has=f"receipt.head_oid={refreshed.head_oid}")
        tm.that(second, has=f"receipt.worktree={lane}")
        assert lane.is_dir()

    def test_start_recovers_existing_lane_without_metadata(
        self, tmp_path: PathType, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A lane registered by an interrupted start is adopted, not rejected."""
        repository = self._repository(tmp_path)
        bead_id = "mro-test-start-recover"
        shim_dir = self._install_bd_shim(tmp_path, bead_id)
        monkeypatch.setenv(
            "PATH", f"{shim_dir}{os.pathsep}{os.environ.get('PATH', '')}"
        )
        _, _, epic_dir, _ = self._epic_of(bead_id)
        branch = self._branch(bead_id, c.Infra.WorkKind.FEATURE, "recover-lane")
        orphan = tm.ok(
            FlextInfraWorktreeService(
                workspace_root=repository,
                operation=c.Infra.WorktreeOperation.ADD,
                branch=branch,
                base="HEAD",
                lane_dir=f"{bead_id}-recover-lane",
                parent_lane=repository / c.Infra.WORKTREES_DIRNAME / epic_dir,
                apply_changes=True,
            ).execute()
        )
        assert self._metadata(tmp_path) == {}
        parent_lane = repository / c.Infra.WORKTREES_DIRNAME / epic_dir
        (parent_lane / "parent-wip.txt").write_text(
            "later parent WIP\n", encoding="utf-8"
        )
        started = tm.ok(
            FlextInfraWorkService(
                workspace_root=repository,
                operation=c.Infra.WorkOperation.START,
                bead=bead_id,
                kind=c.Infra.WorkKind.FEATURE,
                name="recover-lane",
                base="HEAD",
                apply_changes=True,
            ).execute()
        )
        tm.that(started, has=f"receipt.worktree={orphan}")
        tm.that(started, has=f"receipt.branch={branch}")
        assert self._metadata(tmp_path)["worktree"] == orphan

    def test_start_rolls_back_lane_when_beads_update_fails(
        self, tmp_path: PathType, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A lane the saga cannot register on its bead must not survive."""
        repository = self._repository(tmp_path)
        bead_id = "mro-test-start-rollback"
        shim_dir = self._install_bd_shim(tmp_path, bead_id, update_fails=True)
        monkeypatch.setenv(
            "PATH", f"{shim_dir}{os.pathsep}{os.environ.get('PATH', '')}"
        )
        result = FlextInfraWorkService(
            workspace_root=repository,
            operation=c.Infra.WorkOperation.START,
            bead=bead_id,
            kind=c.Infra.WorkKind.FEATURE,
            name="rollback-lane",
            base="HEAD",
            apply_changes=True,
        ).execute()
        tm.fail(result, has="bd update refused")
        tm.fail(result, has="rolled back")
        _, _, epic_dir, _ = self._epic_of(bead_id)
        orphaned = FlextInfraWorktreeService.registered_lane(
            repository,
            self._branch(bead_id, c.Infra.WorkKind.FEATURE, "rollback-lane"),
            repository
            / c.Infra.WORKTREES_DIRNAME
            / epic_dir
            / c.Infra.WORKTREES_DIRNAME
            / f"{bead_id}-rollback-lane",
        )
        tm.fail(orphaned, has="is not registered")

    def test_land_happy_path_push_and_pr_updates_metadata(
        self, tmp_path: PathType, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Land pushes the lane, records the PR, and emits a land receipt."""
        repository = self._repository(tmp_path)
        self._attach_bare_origin(tmp_path, repository)
        bead_id = "mro-test-land-happy"
        shim_dir = self._install_bd_shim(tmp_path, bead_id)
        self._install_gh_shim(
            tmp_path, pr_list='[{"number": "7", "url": "https://example.test/pr/7"}]'
        )
        monkeypatch.setenv(
            "PATH", f"{shim_dir}{os.pathsep}{os.environ.get('PATH', '')}"
        )
        tm.ok(
            FlextInfraWorkService(
                workspace_root=repository,
                operation=c.Infra.WorkOperation.START,
                bead=bead_id,
                kind=c.Infra.WorkKind.FEATURE,
                name="land-happy",
                base="HEAD",
                apply_changes=True,
            ).execute()
        )
        landed = tm.ok(
            FlextInfraWorkService(
                workspace_root=repository,
                operation=c.Infra.WorkOperation.LAND,
                bead=bead_id,
                apply_changes=True,
            ).execute()
        )
        root_entry = self._root_entry(tmp_path)
        _, _, _, epic_branch = self._epic_of(bead_id)
        branch = self._branch(bead_id, c.Infra.WorkKind.FEATURE, "land-happy")
        tm.that(landed, has="receipt.operation=land")
        tm.that(landed, has="receipt.pr=7")
        tm.that(landed, has=f"receipt.base={epic_branch}")
        tm.that(landed, has=f"receipt.head_oid={root_entry.head_oid}")
        assert root_entry.pr_number == "7"
        assert root_entry.pr_url == "https://example.test/pr/7"
        pushed = tm.ok(
            test_u.Infra.git_rev_parse(
                m.Infra.GitCommitishRequest(
                    repo_root=repository, commitish=f"refs/remotes/origin/{branch}"
                )
            )
        ).oid
        assert pushed == root_entry.head_oid

    def test_land_allows_ancestor_cas(
        self, tmp_path: PathType, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Lane commits made after start are a fast-forward, not a CAS conflict."""
        repository = self._repository(tmp_path)
        self._attach_bare_origin(tmp_path, repository)
        bead_id = "mro-test-land-ancestor"
        shim_dir = self._install_bd_shim(tmp_path, bead_id)
        self._install_gh_shim(
            tmp_path, pr_list='[{"number": "3", "url": "https://example.test/pr/3"}]'
        )
        monkeypatch.setenv(
            "PATH", f"{shim_dir}{os.pathsep}{os.environ.get('PATH', '')}"
        )
        tm.ok(
            FlextInfraWorkService(
                workspace_root=repository,
                operation=c.Infra.WorkOperation.START,
                bead=bead_id,
                kind=c.Infra.WorkKind.FEATURE,
                name="land-ancestor",
                base="HEAD",
                apply_changes=True,
            ).execute()
        )
        recorded = self._root_entry(tmp_path).head_oid
        lane = Path(self._metadata(tmp_path)["worktree"])
        self._commit_in(lane, "lane advance")
        landed = tm.ok(
            FlextInfraWorkService(
                workspace_root=repository,
                operation=c.Infra.WorkOperation.LAND,
                bead=bead_id,
                apply_changes=True,
            ).execute()
        )
        advanced = self._root_entry(tmp_path).head_oid
        assert advanced != recorded
        tm.that(landed, has=f"receipt.head_oid={advanced}")

    def test_land_push_rejection_reports_shas(
        self, tmp_path: PathType, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A rejected push names both SHAs so the operator can judge divergence."""
        repository = self._repository(tmp_path)
        self._attach_bare_origin(tmp_path, repository)
        bead_id = "mro-test-land-reject"
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
                name="land-reject",
                base="HEAD",
                apply_changes=True,
            ).execute()
        )
        lane = Path(self._metadata(tmp_path)["worktree"])
        self._commit_in(repository, "remote advance")
        remote_oid = tm.ok(
            test_u.Infra.git_repository_head(
                m.Infra.GitRepoRequest(repo_root=repository)
            )
        ).oid
        tm.ok(
            test_u.Cli.run_checked(
                [
                    c.Infra.GIT,
                    "push",
                    "origin",
                    "HEAD:refs/heads/"
                    + self._branch(bead_id, c.Infra.WorkKind.FEATURE, "land-reject"),
                ],
                cwd=repository,
            )
        )
        tm.ok(test_u.Cli.run_checked([c.Infra.GIT, "fetch", "origin"], cwd=lane))
        self._commit_in(lane, "lane diverge")
        local_oid = tm.ok(
            test_u.Infra.git_repository_head(m.Infra.GitRepoRequest(repo_root=lane))
        ).oid
        result = FlextInfraWorkService(
            workspace_root=repository,
            operation=c.Infra.WorkOperation.LAND,
            bead=bead_id,
            apply_changes=True,
        ).execute()
        tm.fail(result, has=f"local={local_oid.strip()}")
        tm.fail(result, has=f"remote={remote_oid.strip()}")

    def test_finish_refuses_open_pr_state(
        self, tmp_path: PathType, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """An open PR still owns the lane, so finish must refuse to retire it."""
        repository = self._repository(tmp_path)
        bead_id = "mro-test-finish-open"
        shim_dir = self._install_bd_shim(tmp_path, bead_id)
        self._install_gh_shim(
            tmp_path, pr_view='{"state": "OPEN", "mergedAt": null, "headRefName": ""}'
        )
        monkeypatch.setenv(
            "PATH", f"{shim_dir}{os.pathsep}{os.environ.get('PATH', '')}"
        )
        tm.ok(
            FlextInfraWorkService(
                workspace_root=repository,
                operation=c.Infra.WorkOperation.START,
                bead=bead_id,
                kind=c.Infra.WorkKind.BUGFIX,
                name="finish-open",
                base="HEAD",
                apply_changes=True,
            ).execute()
        )
        self._set_root_entry(tmp_path, pr_number="5")
        result = FlextInfraWorkService(
            workspace_root=repository,
            operation=c.Infra.WorkOperation.FINISH,
            bead=bead_id,
            apply_changes=True,
        ).execute()
        tm.fail(result, has="requires merged PR #5; state=OPEN")

    def test_finish_refuses_closed_unmerged_pr(
        self, tmp_path: PathType, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A closed-without-merge PR abandoned the work; the lane stays."""
        repository = self._repository(tmp_path)
        bead_id = "mro-test-finish-closed"
        shim_dir = self._install_bd_shim(tmp_path, bead_id)
        self._install_gh_shim(
            tmp_path, pr_view='{"state": "CLOSED", "mergedAt": null, "headRefName": ""}'
        )
        monkeypatch.setenv(
            "PATH", f"{shim_dir}{os.pathsep}{os.environ.get('PATH', '')}"
        )
        tm.ok(
            FlextInfraWorkService(
                workspace_root=repository,
                operation=c.Infra.WorkOperation.START,
                bead=bead_id,
                kind=c.Infra.WorkKind.BUGFIX,
                name="finish-closed",
                base="HEAD",
                apply_changes=True,
            ).execute()
        )
        self._set_root_entry(tmp_path, pr_number="6")
        result = FlextInfraWorkService(
            workspace_root=repository,
            operation=c.Infra.WorkOperation.FINISH,
            bead=bead_id,
            apply_changes=True,
        ).execute()
        tm.fail(result, has="requires merged PR #6; state=CLOSED")
        assert self._metadata(tmp_path)["worktree"] != "removed"

    def test_finish_refuses_open_pr_without_pr_number(
        self, tmp_path: PathType, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Without a recorded PR the branch query is the only merge evidence."""
        repository = self._repository(tmp_path)
        bead_id = "mro-test-finish-open-query"
        shim_dir = self._install_bd_shim(tmp_path, bead_id)
        self._install_gh_shim(tmp_path, pr_list='[{"number": "8"}]')
        monkeypatch.setenv(
            "PATH", f"{shim_dir}{os.pathsep}{os.environ.get('PATH', '')}"
        )
        tm.ok(
            FlextInfraWorkService(
                workspace_root=repository,
                operation=c.Infra.WorkOperation.START,
                bead=bead_id,
                kind=c.Infra.WorkKind.BUGFIX,
                name="finish-open-query",
                base="HEAD",
                apply_changes=True,
            ).execute()
        )
        result = FlextInfraWorkService(
            workspace_root=repository,
            operation=c.Infra.WorkOperation.FINISH,
            bead=bead_id,
            apply_changes=True,
        ).execute()
        tm.fail(
            result,
            has=(
                "refuses open PR on "
                + self._branch(bead_id, c.Infra.WorkKind.BUGFIX, "finish-open-query")
            ),
        )

    def test_start_status_land_finish_idempotent_status_twice(
        self, tmp_path: PathType, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """The full lane lifecycle runs once, and status never mutates it."""
        repository = self._repository(tmp_path)
        self._attach_bare_origin(tmp_path, repository)
        bead_id = "mro-test-lifecycle"
        shim_dir = self._install_bd_shim(tmp_path, bead_id)
        self._install_gh_shim(
            tmp_path, pr_list='[{"number": "9", "url": "https://example.test/pr/9"}]'
        )
        monkeypatch.setenv(
            "PATH", f"{shim_dir}{os.pathsep}{os.environ.get('PATH', '')}"
        )
        started = tm.ok(
            FlextInfraWorkService(
                workspace_root=repository,
                operation=c.Infra.WorkOperation.START,
                bead=bead_id,
                kind=c.Infra.WorkKind.FEATURE,
                name="lifecycle-lane",
                base="HEAD",
                apply_changes=True,
            ).execute()
        )
        tm.that(started, has="receipt.operation=start")
        status_service = FlextInfraWorkService(
            workspace_root=repository,
            operation=c.Infra.WorkOperation.STATUS,
            bead=bead_id,
            apply_changes=False,
        )
        first_status = tm.ok(status_service.execute())
        second_status = tm.ok(status_service.execute())
        assert first_status == second_status
        landed = tm.ok(
            FlextInfraWorkService(
                workspace_root=repository,
                operation=c.Infra.WorkOperation.LAND,
                bead=bead_id,
                apply_changes=True,
            ).execute()
        )
        tm.that(landed, has="receipt.operation=land")
        finished = tm.ok(
            FlextInfraWorkService(
                workspace_root=repository,
                operation=c.Infra.WorkOperation.FINISH,
                bead=bead_id,
                apply_changes=True,
            ).execute()
        )
        tm.that(finished, has="receipt.operation=finish")
        tm.that(finished, has="receipt.pr=9")
        tm.that(
            finished,
            has=(
                "receipt.branch="
                + self._branch(bead_id, c.Infra.WorkKind.FEATURE, "lifecycle-lane")
            ),
        )
        assert self._metadata(tmp_path)["worktree"] == "removed"

    def test_start_refuses_a_bead_without_a_parent_epic(
        self, tmp_path: PathType, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A bead lane has no place to live without its epic lane."""
        repository = self._repository(tmp_path)
        bead_id = "mro-test-orphan"
        shim_dir = self._install_bd_shim(tmp_path, bead_id)
        monkeypatch.setenv(
            "PATH", f"{shim_dir}{os.pathsep}{os.environ.get('PATH', '')}"
        )
        store = self._store(tmp_path)
        del store["beads"][bead_id]["parent"]  # type: ignore[index]
        self._write_store(tmp_path, store)

        result = FlextInfraWorkService(
            workspace_root=repository,
            operation=c.Infra.WorkOperation.START,
            bead=bead_id,
            kind=c.Infra.WorkKind.FEATURE,
            name="orphan-lane",
            base="HEAD",
            apply_changes=True,
        ).execute()

        tm.fail(result, has="has no tracker parent")

    def test_start_refuses_a_parent_epic_without_a_lane(
        self, tmp_path: PathType, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """An epic that never started a lane cannot own child lanes."""
        repository = self._repository(tmp_path)
        bead_id = "mro-test-unstarted-parent"
        shim_dir = self._install_bd_shim(tmp_path, bead_id)
        monkeypatch.setenv(
            "PATH", f"{shim_dir}{os.pathsep}{os.environ.get('PATH', '')}"
        )
        epic_id, _, _, _ = self._epic_of(bead_id)
        store = self._store(tmp_path)
        store["beads"][epic_id]["metadata"] = {}  # type: ignore[index]
        self._write_store(tmp_path, store)

        result = FlextInfraWorkService(
            workspace_root=repository,
            operation=c.Infra.WorkOperation.START,
            bead=bead_id,
            kind=c.Infra.WorkKind.FEATURE,
            name="unstarted-parent",
            base="HEAD",
            apply_changes=True,
        ).execute()

        tm.fail(result, has="has no lane metadata (kind/slug)")

    def test_start_refuses_a_parent_epic_outside_its_canonical_path(
        self, tmp_path: PathType, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A parent epic registered anywhere else is refused, never adopted."""
        repository = self._repository(tmp_path)
        bead_id = "mro-test-rogue-parent"
        shim_dir = self._install_bd_shim(tmp_path, bead_id)
        monkeypatch.setenv(
            "PATH", f"{shim_dir}{os.pathsep}{os.environ.get('PATH', '')}"
        )
        _, _, epic_dir, epic_branch = self._epic_of(bead_id)
        canonical = repository / c.Infra.WORKTREES_DIRNAME / epic_dir
        tm.ok(
            test_u.Cli.run_checked(
                [
                    c.Infra.GIT,
                    "worktree",
                    "move",
                    str(canonical),
                    str(tmp_path / "away"),
                ],
                cwd=repository,
            )
        )

        result = FlextInfraWorkService(
            workspace_root=repository,
            operation=c.Infra.WorkOperation.START,
            bead=bead_id,
            kind=c.Infra.WorkKind.FEATURE,
            name="rogue-parent",
            base="HEAD",
            apply_changes=True,
        ).execute()

        tm.fail(result, has="registered outside its canonical lane")
        tm.fail(result, has=epic_branch)

    def test_start_refuses_a_dirty_parent_epic_lane(
        self, tmp_path: PathType, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A child lane is carved out of its parent checkout, so it must be clean."""
        repository = self._repository(tmp_path)
        bead_id = "mro-test-dirty-parent"
        shim_dir = self._install_bd_shim(tmp_path, bead_id)
        monkeypatch.setenv(
            "PATH", f"{shim_dir}{os.pathsep}{os.environ.get('PATH', '')}"
        )
        _, _, epic_dir, _ = self._epic_of(bead_id)
        epic_lane = repository / c.Infra.WORKTREES_DIRNAME / epic_dir
        (epic_lane / "README.md").write_text("parent WIP\n", encoding="utf-8")

        result = FlextInfraWorkService(
            workspace_root=repository,
            operation=c.Infra.WorkOperation.START,
            bead=bead_id,
            kind=c.Infra.WorkKind.FEATURE,
            name="dirty-parent",
            base="HEAD",
            apply_changes=True,
        ).execute()

        tm.fail(result, has="is dirty at")
        tm.fail(result, has=str(epic_lane))

    def test_finish_refuses_a_lane_that_owns_child_lanes(
        self, tmp_path: PathType, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Removing a parent lane would delete its children's checkouts."""
        repository = self._repository(tmp_path)
        bead_id = "mro-test-parent-finish"
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
                name="parent-finish",
                base="HEAD",
                apply_changes=True,
            ).execute()
        )
        lane = Path(self._metadata(tmp_path)["worktree"])
        child = tm.ok(
            FlextInfraWorktreeService(
                workspace_root=repository,
                operation=c.Infra.WorktreeOperation.ADD,
                branch="feature/mro-test-parent-finish.1-child",
                base="HEAD",
                lane_dir="mro-test-parent-finish.1-child",
                parent_lane=lane,
                apply_changes=True,
            ).execute()
        )
        self._set_root_entry(tmp_path, pr_number="1")

        result = FlextInfraWorkService(
            workspace_root=repository,
            operation=c.Infra.WorkOperation.FINISH,
            bead=bead_id,
            apply_changes=True,
        ).execute()

        tm.fail(result, has="it still owns child lanes")
        tm.fail(result, has=child)
        assert lane.is_dir()

    def test_makefile_j2_help_scopes_apply_to_mutating_work_selectors(self) -> None:
        """Help must not demand APPLY=Y for the read-only default selector."""
        template = (
            Path(flext_infra.__file__).resolve().parent
            / "templates"
            / "project"
            / "base"
            / "Makefile.j2"
        ).read_text(encoding="utf-8")
        tm.that(
            template,
            has="{{ verb.default_what }} is read-only; other WHATs require APPLY=Y",
        )
