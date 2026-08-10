"""Reusable real-Git and executable CLI boundaries for public work scenarios."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Self

import pytest
from flext_infra import c, m, u
from flext_tests import tm
from tests import u as test_u


@dataclass(frozen=True, slots=True)
class PullRequestCreateReceipt:
    argv: tuple[str, ...]

    @property
    def base(self) -> str:
        return self.argv[self.argv.index("--base") + 1]

    @property
    def head(self) -> str:
        return self.argv[self.argv.index("--head") + 1]


@dataclass(frozen=True, slots=True)
class WorkPublicServiceFixture:
    root: Path
    repository: Path
    origin: Path
    store: Path
    pr_receipt: Path

    @classmethod
    def create(cls, root: Path, monkeypatch: pytest.MonkeyPatch) -> Self:
        repository = root / "repository"
        repository.mkdir()
        (repository / "README.md").write_text("fixture\n", encoding="utf-8")
        (repository / "pyproject.toml").write_text(
            '[project]\nname = "fixture"\nversion = "0.1.0"\n'
            'description = "A standard PEP 621 description string"\n',
            encoding="utf-8",
        )
        (repository / "Makefile").write_text(
            '.PHONY: setup\nsetup:\n\t@test "$(WORKSPACE)" = "$(CURDIR)"\n',
            encoding="utf-8",
        )
        repository_ref = test_u.Tests.repository_ref("fixture").model_copy(
            update={"path": Path(), "package": False, "editable": False}
        )
        tm.ok(
            u.Cli.yaml_dump(
                repository / "config" / "workspace.yaml",
                m.Infra.WorkspaceSpec(
                    version=c.Infra.WORKSPACE_MANIFEST_VERSION,
                    name=repository_ref.distribution,
                    repository=repository_ref,
                    ledger_id="mro",
                ).model_dump(mode="json", exclude_none=True),
            )
        )
        test_u.Tests.initialize_git_repo(repository)
        origin = root / "origin.git"
        tm.ok(
            test_u.Cli.run_checked(
                [c.Infra.GIT, "init", "--bare", str(origin)], cwd=root
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
        store = root / "beads-store.json"
        store.write_text("{}", encoding="utf-8")
        pr_receipt = root / "gh-pr-create.json"
        shim_dir = root / "bin"
        shim_dir.mkdir()
        cls._write_bd(shim_dir / "bd", store)
        cls._write_gh(shim_dir / "gh", pr_receipt)
        monkeypatch.setenv(
            "PATH", f"{shim_dir}{os.pathsep}{os.environ.get('PATH', '')}"
        )
        return cls(root, repository, origin, store, pr_receipt)

    def add_issue(
        self, bead_id: str, *, issue_type: str, parent: str | None = None
    ) -> None:
        records = json.loads(self.store.read_text(encoding="utf-8"))
        records[bead_id] = {
            "id": bead_id,
            "status": "open",
            "issue_type": issue_type,
            "parent": parent,
            "assignee": None,
            "metadata": {},
            "labels": [],
        }
        self.store.write_text(json.dumps(records), encoding="utf-8")

    def issue(self, bead_id: str) -> m.Infra.BeadIssue:
        return tm.ok(u.Infra.beads_show(bead_id, root=self.repository))

    def pr_create_receipt(self) -> PullRequestCreateReceipt:
        argv = json.loads(self.pr_receipt.read_text(encoding="utf-8"))
        return PullRequestCreateReceipt(tuple(argv))

    @staticmethod
    def _write_bd(path: Path, store: Path) -> None:
        path.write_text(
            "#!/usr/bin/env python3\nimport json, sys\n"
            f"STORE = {str(store)!r}\nargs = sys.argv[1:]\n"
            "while args and args[0] in {'-C', '--json', '--quiet', '-q'}:\n"
            "    args = args[2:] if args[0] == '-C' else args[1:]\n"
            "data = json.loads(open(STORE, encoding='utf-8').read())\n"
            "bead = args[1] if len(args) > 1 else ''\n"
            "if args[:1] == ['show'] and '--json' in args:\n"
            "    print(json.dumps(data[bead])); raise SystemExit(0)\n"
            "if args[:1] == ['list'] and '--json' in args:\n"
            "    print(json.dumps(list(data.values()))); raise SystemExit(0)\n"
            "if args[:1] == ['update']:\n"
            "    issue = data[bead]; i = 2\n"
            "    while i < len(args):\n"
            "        if args[i] == '--set-metadata':\n"
            "            key, value = args[i + 1].split('=', 1); issue['metadata'][key] = value; i += 2\n"
            "        elif args[i] == '--add-label':\n"
            "            issue['labels'].append(args[i + 1]); i += 2\n"
            "        elif args[i] == '--append-notes': i += 2\n"
            "        elif args[i] == '--claim': issue['assignee'] = 'worker'; i += 1\n"
            "        else: i += 1\n"
            "    open(STORE, 'w', encoding='utf-8').write(json.dumps(data)); print('updated'); raise SystemExit(0)\n"
            "raise SystemExit(f'unsupported bd args: {args}')\n",
            encoding="utf-8",
        )
        path.chmod(0o755)

    @staticmethod
    def _write_gh(path: Path, receipt: Path) -> None:
        path.write_text(
            "#!/usr/bin/env python3\nimport json, sys\nargs = sys.argv[1:]\n"
            f"RECEIPT = {str(receipt)!r}\n"
            "if args[:2] == ['pr', 'create']:\n"
            "    open(RECEIPT, 'w', encoding='utf-8').write(json.dumps(args)); print('https://example.test/pr/41'); raise SystemExit(0)\n"
            "if args[:2] == ['pr', 'list']:\n"
            "    exists = __import__('pathlib').Path(RECEIPT).exists()\n"
            "    rows = ('https://example.test/pr/41' if exists else '') if '--jq' in args else ('[{\"number\": \"41\", \"url\": \"https://example.test/pr/41\"}]' if exists else '[]')\n"
            "    print(rows); raise SystemExit(0)\n"
            "raise SystemExit(f'unsupported gh args: {args}')\n",
            encoding="utf-8",
        )
        path.chmod(0o755)


__all__: tuple[str, ...] = ("PullRequestCreateReceipt", "WorkPublicServiceFixture")
