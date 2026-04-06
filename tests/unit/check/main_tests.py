"""Tests for the centralized check CLI group."""

from __future__ import annotations

import pytest
from _pytest.capture import CaptureFixture

from flext_infra import main as infra_main


def test_check_main_executes_real_cli(capsys: CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as exc_info:
        infra_main(["check", "run", "--help"])
    captured = capsys.readouterr()
    assert exc_info.value.code == 0
    assert "usage:" in captured.out
