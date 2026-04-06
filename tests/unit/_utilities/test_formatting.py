from __future__ import annotations

from collections.abc import MutableSequence
from pathlib import Path

import pytest
from tests import c, r, t, u


class TestFormattingRunRuffFix:
    def test_run_ruff_fix_runs_check_and_format(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        target = tmp_path / "sample.py"
        target.write_text("x=1\n", encoding="utf-8")
        calls: MutableSequence[t.StrSequence] = []

        def _fake_run_checked(
            cmd: t.StrSequence,
        ) -> r[bool]:
            calls.append(cmd)
            return r[bool].ok(True)

        monkeypatch.setattr(u.Cli, "run_checked", _fake_run_checked)

        u.Infra.run_ruff_fix(target)

        assert calls[0] == [
            c.Infra.RUFF,
            c.Infra.CHECK,
            "--fix",
            str(target),
        ]
        assert calls[1] == [
            c.Infra.RUFF,
            c.Infra.FORMAT,
            str(target),
        ]

    def test_run_ruff_fix_quiet_adds_flag_and_suppresses_missing_binary(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        target = tmp_path / "sample.py"
        target.write_text("x=1\n", encoding="utf-8")
        calls: MutableSequence[t.StrSequence] = []

        def _raise_missing(
            cmd: t.StrSequence,
        ) -> r[bool]:
            calls.append(cmd)
            return r[bool].fail("ruff not found")

        monkeypatch.setattr(u.Cli, "run_checked", _raise_missing)

        u.Infra.run_ruff_fix(target, include_format=False, quiet=True)

        assert calls == [
            [
                c.Infra.RUFF,
                c.Infra.CHECK,
                "--fix",
                "--quiet",
                str(target),
            ],
        ]
