"""Typed, config-derived pytest timeout policy contracts."""

from __future__ import annotations

import pytest

from flext_infra import config
from flext_tests import tm


class TestsFlextInfraPytestTimeoutConfig:
    def test_timeout_policy_round_trips_through_its_typed_ssot(self) -> None:
        """Consume arbitrary configured values through the production model."""
        policy = config.Infra.tooling.tools.pytest

        round_tripped = type(policy).model_validate(policy.model_dump())

        tm.that(round_tripped, eq=policy)
        tm.that(policy.enforcement_plugin, empty=False)

    def test_timeout_policy_has_a_valid_fail_closed_order(self) -> None:
        """Validate relational invariants without freezing configured values."""
        policy = config.Infra.tooling.tools.pytest

        tm.that(policy.case_timeout_seconds < policy.run_timeout_seconds, eq=True)
        tm.that(policy.termination_grace_seconds < policy.run_timeout_seconds, eq=True)

    @pytest.mark.parametrize(
        ("field", "invalid_value"),
        (
            (
                "case_timeout_seconds",
                config.Infra.tooling.tools.pytest.case_timeout_seconds + 1,
            ),
            (
                "run_timeout_seconds",
                config.Infra.tooling.tools.pytest.run_timeout_seconds + 1,
            ),
        ),
    )
    def test_timeout_policy_rejects_values_above_operator_caps(
        self, field: str, invalid_value: int
    ) -> None:
        """Reject config drift above the hard external execution contract."""
        policy = config.Infra.tooling.tools.pytest
        payload = policy.model_dump()
        payload[field] = invalid_value

        with pytest.raises(ValueError):
            type(policy).model_validate(payload)
