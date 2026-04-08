"""CLI contract tests for the centralized validate CLI group."""

from __future__ import annotations

import pytest
from flext_tests import tm
from tests import m, r, t

from flext_infra import FlextInfraStubSupplyChain, main as infra_main


def test_stub_validate_uses_all_flag(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: t.MutableSequenceOf[bool] = []

    def _mock_handler(
        _self: FlextInfraStubSupplyChain,
        params: m.Infra.ValidateStubValidateInput,
    ) -> r[bool]:
        captured.append(params.all_projects)
        return r[bool].ok(True)

    monkeypatch.setattr(
        FlextInfraStubSupplyChain,
        "execute_command",
        _mock_handler,
    )
    infra_main(["validate", "stub-validate", "--all"])
    # The call captured whether --all was passed
    tm.that(len(captured), eq=1)
    tm.that(captured[0], eq=True)


def test_stub_validate_help_returns_zero() -> None:
    """--help for stub-validate returns 0."""
    tm.that(infra_main(["validate", "stub-validate", "--help"]), eq=0)
