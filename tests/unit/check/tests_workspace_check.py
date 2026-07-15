"""Tests for flext_infra.check.workspace_check module.

Tests the real entry-point behavior.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from flext_tests import tm

from flext_infra import main


def test_workspace_check_main_returns_error_without_projects() -> None:
    """Return failure when no workspace projects can be selected."""
    exit_code = main(["check", "run"])
    tm.that(exit_code, eq=1)
