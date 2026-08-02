"""Typed, config-derived pytest execution policy contracts."""

from __future__ import annotations

import pytest

from flext_infra import c, config
from flext_tests import tm


class TestsFlextInfraPytestTimeoutConfig:
    """Prove the operator caps and relational policy at the typed SSOT."""

    def test_policy_round_trips_through_its_production_model(self) -> None:
        """Validate the configured policy without freezing its current values."""
        policy = config.Infra.tooling.tools.pytest

        round_tripped = type(policy).model_validate(policy.model_dump(by_alias=True))

        tm.that(round_tripped, eq=policy)

    def test_configured_policy_orders_all_execution_deadlines(self) -> None:
        """Keep the case and shutdown budgets inside the invocation hard wall."""
        policy = config.Infra.tooling.tools.pytest

        tm.that(policy.case_timeout_seconds < policy.run_timeout_seconds, eq=True)
        tm.that(policy.termination_grace_seconds < policy.run_timeout_seconds, eq=True)
        tm.that(
            policy.case_timeout_seconds + policy.termination_grace_seconds
            <= policy.run_timeout_seconds,
            eq=True,
        )

    @pytest.mark.parametrize(
        ("field", "invalid_value"),
        [("case-timeout-seconds", 11), ("run-timeout-seconds", 61)],
    )
    def test_operator_caps_are_hard_typed_boundaries(
        self, field: str, invalid_value: int
    ) -> None:
        """Reject values beyond the immutable external 10s and 60s contracts."""
        policy = config.Infra.tooling.tools.pytest
        payload = policy.model_dump(by_alias=True)
        payload[field] = invalid_value

        with pytest.raises(c.ValidationError, match="less than or equal"):
            type(policy).model_validate(payload)

    def test_run_budget_must_include_item_and_termination_windows(self) -> None:
        policy = config.Infra.tooling.tools.pytest
        payload = policy.model_dump(by_alias=True)
        payload["run-timeout-seconds"] = (
            policy.case_timeout_seconds + policy.termination_grace_seconds - 1
        )

        with pytest.raises(
            c.ValidationError,
            match="pytest run timeout must include item and termination budgets",
        ):
            type(policy).model_validate(payload)

    @pytest.mark.parametrize(
        ("field", "invalid_value", "expected_error"),
        [
            (
                "progress-args",
                ["-q"],
                "pytest progress args must expose verbose item progress",
            ),
            (
                "standard-addopts",
                ["--timeout=999"],
                "pytest timeout options are derived from typed deadline fields",
            ),
            (
                "standard-addopts",
                ["--session-timeout=999"],
                "pytest timeout options are derived from typed deadline fields",
            ),
        ],
    )
    def test_derived_limits_and_live_progress_cannot_be_shadowed(
        self, field: str, invalid_value: list[str], expected_error: str
    ) -> None:
        policy = config.Infra.tooling.tools.pytest
        payload = policy.model_dump(by_alias=True)
        payload[field] = invalid_value

        with pytest.raises(c.ValidationError, match=expected_error):
            type(policy).model_validate(payload)
