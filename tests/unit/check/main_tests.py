"""Tests for the centralized check CLI group."""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_infra import main as infra_main
from flext_tests import tm

from _pytest.capture import CaptureFixture



def test_check_main_executes_real_cli(capsys: CaptureFixture[str]) -> None:
    exit_code = infra_main(["check", "run", "--help"])
    captured = capsys.readouterr()
    tm.that(exit_code, eq=0)
    tm.that(captured.out.lower(), has="usage:")
