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

    def test_ci_y_scopes_to_fast_gate_set(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """RULING 2: CI=Y runs the fast set -- the type checkers stay local.

        Runtime evidence (flext-ldap lane): `CI=Y make check WHAT=all` ran
        lint pyright security markdown smells; `CI=N make check WHAT=all`
        ran pyrefly mypy. The test states that observed contract.
        """
        ci = config.Infra.codegen.make.ci
        monkeypatch.setenv(ci.variable, ci.value)
        gates = ["lint", "pyrefly", "mypy", "pyright", "security"]
        expected = [gate for gate in gates if gate in ci.check_gates]
        tm.that(FlextInfraWorkspaceChecker.apply_ci_gate_rules(gates), eq=expected)
        tm.that(expected, eq=["lint", "pyright", "security"])


class TestWorkspaceCheckerCiGateRules:
    """Test FlextInfraWorkspaceChecker.apply_ci_gate_rules."""

    def test_without_ci_token_keeps_all_gates(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        ci = config.Infra.codegen.make.ci
        monkeypatch.delenv(ci.variable, raising=False)
        gates = ["lint", "format", "pyrefly", "mypy", "pyright"]
        tm.that(FlextInfraWorkspaceChecker.apply_ci_gate_rules(gates), eq=gates)

    def test_github_ci_true_does_not_filter_gates(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        ci = config.Infra.codegen.make.ci
        monkeypatch.setenv(ci.variable, "true")
        gates = ["lint", "format", "pyrefly", "pyright"]
        tm.that(FlextInfraWorkspaceChecker.apply_ci_gate_rules(gates), eq=gates)

    def test_ci_token_runs_positive_gate_set(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        ci = config.Infra.codegen.make.ci
        monkeypatch.setenv(ci.variable, ci.value)
        gates = ["lint", "format", "pyrefly", "mypy", "pyright", "security"]
        expected = [gate for gate in gates if gate in ci.check_gates]
        tm.that(expected, eq=["lint", "pyright", "security"])
        tm.that(FlextInfraWorkspaceChecker.apply_ci_gate_rules(gates), eq=expected)
        # CI=Y is the strict complement of the declared local set: fast gates
        # only, derived from the allowed vocabulary minus local_check_gates.
        tm.that(
            set(ci.check_gates),
            eq={"lint", "pyright", "security", "markdown", "smells"},
        )
        # CI=N is exactly the declared slow set -- the whole-program type
        # checkers -- and the two sets partition the check vocabulary.
        tm.that(set(ci.local_check_gates), eq={"pyrefly", "mypy"})
        tm.that(
            set(ci.check_gates) | set(ci.local_check_gates),
            eq=set(c.Infra.PROJECT_CHECK_GATES_ALLOWED_VALUES),
        )

    def test_ci_local_token_keeps_explicit_narrow_selection_as_noop_success(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """CI=N scopes ``make fix``'s fixable gates to a no-op success.

        ``make fix APPLY=Y`` asks only for the fixable gates (markdown,
        smells), disjoint from the CI=N slow set by design — pre-commit
        (CI=Y) owns that fixing stage. An empty intersection under the
        token is the verb's documented no-op, never a hard failure that
        would block the pre-push hook.
        """
        ci = config.Infra.codegen.make.ci
        monkeypatch.setenv(ci.variable, ci.local_value)
        fixable: list[str] = list(config.Infra.codegen.make.check_gates_fixable)
        tm.that(set(fixable) & set(ci.local_check_gates), eq=set())
        tm.that(FlextInfraWorkspaceChecker.apply_ci_gate_rules(fixable), eq=[])
        # The default full set is still scoped to the CI=N owner set.
        default = list(c.Infra.PROJECT_CHECK_GATES_DEFAULT_VALUES)
        tm.that(
            FlextInfraWorkspaceChecker.apply_ci_gate_rules(default),
            eq=list(ci.local_check_gates),
        )
