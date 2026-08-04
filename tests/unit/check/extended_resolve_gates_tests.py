"""Tests for workspace checker gate resolution and CSV parsing.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import pytest

from flext_infra import c, config
from flext_infra.check.workspace_check import FlextInfraWorkspaceChecker
from flext_tests import tm


class TestWorkspaceCheckerResolveGates:
    """Test FlextInfraWorkspaceChecker.resolve_gates."""

    @pytest.fixture(autouse=True)
    def _clear_make_ci_token(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Gate resolution assumes CI unset unless a test sets CI=Y."""
        monkeypatch.delenv(c.Infra.PYTEST_ENV_CI, raising=False)

    def test_resolve_gates_type_is_rejected(self) -> None:
        result = FlextInfraWorkspaceChecker.resolve_gates(["type"])
        tm.fail(result, has="unknown gate")

    def test_resolve_gates_skips_empty_strings(self) -> None:
        result = FlextInfraWorkspaceChecker.resolve_gates(["lint", "", "format"])
        tm.ok(result)
        tm.that("" not in result.value, eq=True)

    def test_resolve_gates_deduplicates_entries(self) -> None:
        result = FlextInfraWorkspaceChecker.resolve_gates([
            "lint",
            "lint",
            "format",
            "lint",
        ])
        tm.ok(result)
        tm.that(result.value.count("lint"), eq=1)

    def test_resolve_gates_invalid_gate_fails(self) -> None:
        result = FlextInfraWorkspaceChecker.resolve_gates(["invalid"])
        tm.fail(result, has="unknown gate")

    def test_resolve_gates_all_valid_types(self) -> None:
        gates = [
            "lint",
            "format",
            "pyrefly",
            "mypy",
            "pyright",
            "silent-failure",
            "security",
            "markdown",
        ]
        result = FlextInfraWorkspaceChecker.resolve_gates(gates)
        tm.ok(result)
        tm.that(len(result.value) > 0, eq=True)

    def test_resolve_gates_accepts_silent_failure(self) -> None:
        result = FlextInfraWorkspaceChecker.resolve_gates(["silent-failure"])
        tm.ok(result)
        tm.that(result.value, eq=["silent-failure"])

    def test_resolve_gates_under_ci_y_skips_lint_and_pyrefly(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """mro-v4p5: CI=Y make check omits ruff lint and pyrefly."""
        monkeypatch.setenv(c.Infra.PYTEST_ENV_CI, config.Infra.codegen.make.ci.value)
        result = FlextInfraWorkspaceChecker.resolve_gates([
            "lint",
            "pyrefly",
            "mypy",
            "pyright",
            "security",
        ])
        tm.ok(result)
        tm.that(result.value, eq=["mypy", "pyright", "security"])
        tm.that(result.value, lacks="lint")
        tm.that(result.value, lacks="pyrefly")
