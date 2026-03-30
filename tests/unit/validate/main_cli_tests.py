"""CLI contract tests for flext_infra.validate.__main__."""

from __future__ import annotations

import pytest
from flext_core import r
from flext_tests import tm

from flext_infra import m
from flext_infra.validate import __main__ as validate_main
from flext_infra.validate.__main__ import FlextInfraValidateCli


def test_stub_validate_uses_all_flag(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: list[bool] = []

    @staticmethod  # type: ignore[misc]
    def _mock_handler(params: m.Infra.ValidateStubValidateInput) -> r[bool]:
        captured.append(params.all_projects)
        return r[bool].ok(True)

    monkeypatch.setattr(
        FlextInfraValidateCli,
        "_handle_stub_validate",
        _mock_handler,
    )
    validate_main.main(["stub-validate", "--all"])
    # The call captured whether --all was passed
    tm.that(len(captured), eq=1)
    tm.that(captured[0], eq=True)


def test_stub_validate_help_returns_zero() -> None:
    """--help for stub-validate returns 0."""
    with pytest.raises(SystemExit) as exc_info:
        validate_main.main(["stub-validate", "--help"])
    tm.that(exc_info.value.code, eq=0)
