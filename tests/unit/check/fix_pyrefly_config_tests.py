"""Tests for flext_infra.deps.fix_pyrefly_config module.

Tests the real CLI entry point.
"""

from __future__ import annotations

import pytest

from flext_infra import main as infra_main


def test_fix_pyrefly_config_main_executes_real_cli_help(
    capsys: pytest.CaptureFixture[str],
) -> None:
    with pytest.raises(SystemExit) as exc_info:
        infra_main(["check", "fix-pyrefly-config", "--help"])
    captured = capsys.readouterr()
    assert exc_info.value.code == 0
    assert "usage:" in captured.out
