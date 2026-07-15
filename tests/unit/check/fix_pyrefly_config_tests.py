"""Tests for flext_infra.deps.fix_pyrefly_config module.

Tests the real CLI entry point.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from _pytest.capture import CaptureFixture
from flext_tests import tm

from flext_infra import main as infra_main


def test_fix_pyrefly_config_main_executes_real_cli_help(
    capsys: CaptureFixture[str],
) -> None:
    """Execute the public CLI help path for Pyrefly configuration repair."""
    exit_code = infra_main(["check", "fix-pyrefly-settings", "--help"])
    captured = capsys.readouterr()
    tm.that(exit_code, eq=0)
    tm.that(captured.out.lower(), has="usage:")
