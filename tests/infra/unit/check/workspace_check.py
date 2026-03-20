"""Tests for flext_infra.check.workspace_check module.

Tests the real entry-point behavior.
"""

from __future__ import annotations

from tests.infra import m, t
from flext_infra.check.workspace_check import FlextInfraWorkspaceChecker


def test_workspace_check_main_returns_error_without_projects() -> None:
    exit_code = FlextInfraWorkspaceChecker.main([])
    assert exit_code == 1
