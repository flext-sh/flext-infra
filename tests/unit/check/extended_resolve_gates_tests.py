"""Tests for workspace checker gate resolution and CSV parsing.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import pytest

from flext_infra import config
from flext_infra.check.workspace_check import FlextInfraWorkspaceChecker
from flext_tests import tm


class TestWorkspaceCheckerResolveGates:
    """Test FlextInfraWorkspaceChecker.resolve_gates."""

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


class TestWorkspaceCheckerCiGateSkips:
    """Test FlextInfraWorkspaceChecker.apply_ci_gate_skips."""

    def test_without_ci_token_keeps_all_gates(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        ci = config.Infra.codegen.make.ci
        monkeypatch.delenv(ci.variable, raising=False)
        gates = ["lint", "format", "pyrefly", "mypy", "pyright"]
        tm.that(
            FlextInfraWorkspaceChecker.apply_ci_gate_skips(gates),
            eq=gates,
        )

    def test_github_ci_true_does_not_skip_gates(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        ci = config.Infra.codegen.make.ci
        monkeypatch.setenv(ci.variable, "true")
        gates = ["lint", "format", "pyrefly", "pyright"]
        tm.that(
            FlextInfraWorkspaceChecker.apply_ci_gate_skips(gates),
            eq=gates,
        )

    def test_ci_token_omits_ruff_and_pyrefly(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        ci = config.Infra.codegen.make.ci
        monkeypatch.setenv(ci.variable, ci.value)
        gates = ["lint", "format", "pyrefly", "mypy", "pyright", "security"]
        expected = [gate for gate in gates if gate not in ci.check_gates_skip]
        tm.that(expected, eq=["mypy", "pyright", "security"])
        tm.that(
            FlextInfraWorkspaceChecker.apply_ci_gate_skips(gates),
            eq=expected,
        )
        tm.that(set(ci.check_gates_skip), eq={"lint", "format", "pyrefly"})
