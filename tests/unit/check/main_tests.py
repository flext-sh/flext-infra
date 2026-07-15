"""Tests for the centralized check CLI group.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from _pytest.capture import CaptureFixture
from flext_tests import tm

from flext_infra import main as infra_main


def test_check_main_executes_real_cli(capsys: CaptureFixture[str]) -> None:
    """Verify that the public entry point exposes the real check CLI."""
    exit_code = infra_main(["check", "run", "--help"])
    captured = capsys.readouterr()
    tm.that(exit_code, eq=0)
    tm.that(captured.out.lower(), has="usage:")
