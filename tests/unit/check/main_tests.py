"""Tests for the centralized check CLI group."""

from __future__ import annotations

from _pytest.capture import CaptureFixture

from flext_infra import main as infra_main


def test_check_main_executes_real_cli(capsys: CaptureFixture[str]) -> None:
    exit_code = infra_main(["check", "run", "--help"])
    captured = capsys.readouterr()
    assert exit_code == 0
    assert "usage:" in captured.out.lower()
