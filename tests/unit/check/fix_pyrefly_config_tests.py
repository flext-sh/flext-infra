"""Tests for flext_infra.deps.fix_pyrefly_config module.

Tests the real CLI entry point.
"""

from __future__ import annotations

from _pytest.capture import CaptureFixture

from flext_infra import main as infra_main


def test_fix_pyrefly_config_main_executes_real_cli_help(
    capsys: CaptureFixture[str],
) -> None:
    exit_code = infra_main(["check", "fix-pyrefly-config", "--help"])
    captured = capsys.readouterr()
    assert exit_code == 0
    assert "usage:" in captured.out.lower()
