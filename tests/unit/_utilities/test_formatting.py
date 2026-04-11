from __future__ import annotations

from pathlib import Path

from tests import c, u


class TestsFlextInfraUtilitiesFormattingRunRuffFix:
    def test_run_ruff_fix_runs_check_and_format(self, tmp_path: Path) -> None:
        target = tmp_path / "sample.py"
        target.write_text("x=1\n", encoding="utf-8")

        u.Infra.run_ruff_fix(target)

        assert target.read_text(encoding="utf-8") == "x = 1\n"

    def test_run_ruff_fix_handles_init_file_quietly(self, tmp_path: Path) -> None:
        target = tmp_path / c.Infra.Files.INIT_PY
        target.write_text("x=1\n", encoding="utf-8")

        u.Infra.run_ruff_fix(target, include_format=False, quiet=True)

        assert target.read_text(encoding="utf-8") == "x = 1\n"

    def test_run_ruff_fix_skips_missing_file(self, tmp_path: Path) -> None:
        target = tmp_path / "missing.py"

        u.Infra.run_ruff_fix(target)

        assert target.exists() is False
