"""Public CLI behavior for CSV-driven symbol renames."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from flext_tests import tm

from flext_infra import c, main as infra_main

if TYPE_CHECKING:
    from pathlib import Path


def _rename_fixture(tmp_path: Path) -> tuple[Path, Path, Path]:
    root = tmp_path / "workspace"
    root.mkdir()
    source_path = root / "sample.py"
    source_path.write_text(
        "from __future__ import annotations\n\nold_name = 1\n", encoding="utf-8"
    )
    csv_path = tmp_path / "renames.csv"
    csv_path.write_text("old,new\nold_name,new_name\n", encoding="utf-8")
    return root, source_path, csv_path


class TestsFlextInfraApplyRenamesCli:
    @staticmethod
    def _run_inner(*args: str) -> int:
        return infra_main(["refactor", "apply-renames", *args])

    def test_default_mode_reports_pending_rename_without_mutation(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        root, source_path, csv_path = _rename_fixture(tmp_path)
        original = source_path.read_text(encoding="utf-8")
        monkeypatch.setenv(c.Infra.WORKTREE_TRANSACTION_ENV, "1")

        result = self._run_inner("--csv", str(csv_path), "--roots", str(root))

        tm.that(result, ne=0)
        tm.that(source_path.read_text(encoding="utf-8"), eq=original)

    def test_apply_mode_rewrites_source(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        root, source_path, csv_path = _rename_fixture(tmp_path)
        monkeypatch.setenv(c.Infra.WORKTREE_TRANSACTION_ENV, "1")

        result = self._run_inner(
            "--csv", str(csv_path), "--roots", str(root), "--apply"
        )

        tm.that(result, eq=0)
        source = source_path.read_text(encoding="utf-8")
        tm.that(source, has="new_name = 1")
        tm.that(source, lacks="old_name")

    def test_apply_route_uses_worktree_transaction(self) -> None:
        tm.that(
            "refactor:apply-renames" in c.Infra.WORKTREE_TRANSACTION_APPLY_ROUTES,
            eq=True,
        )
