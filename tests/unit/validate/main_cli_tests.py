"""CLI contract tests for flext_infra.validate.__main__."""

from __future__ import annotations

import pytest
from flext_tests import tm

from flext_infra import t, u
from flext_infra.validate import __main__ as validate_main
from flext_infra.validate.__main__ import FlextInfraValidateCommand


def test_stub_validate_uses_all_flag(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: list[bool] = []

    def _run_stub_validate(
        cli: u.Infra.CliArgs,
        project: t.StrSequence | None,
    ) -> int:
        del cli
        captured.append(project is None)
        return 0

    monkeypatch.setattr(
        FlextInfraValidateCommand,
        "run_stub_validate",
        staticmethod(_run_stub_validate),
    )
    tm.that(validate_main._main_inner(["stub-validate", "--all"]), eq=0)
    tm.that(captured, eq=[True])


def test_stub_validate_rejects_all_with_project() -> None:
    with pytest.raises(SystemExit) as exc_info:
        validate_main._main_inner(["stub-validate", "--all", "--project", "flext-core"])
    tm.that(exc_info.value.code, eq=2)
