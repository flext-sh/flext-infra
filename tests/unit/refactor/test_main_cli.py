from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path

import pytest
from flext_core import r
from flext_tests import tm

from flext_infra import m
from flext_infra.refactor import __main__ as refactor_main
from flext_infra.refactor.__main__ import FlextInfraRefactorCli


def test_refactor_census_rejects_apply_before_subcommand() -> None:
    tm.that(refactor_main.main(["--apply", "census"]), eq=2)


def test_refactor_centralize_accepts_apply_before_subcommand(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    captured_apply = False
    captured_workspace = Path()
    captured_normalize_remaining = False

    @staticmethod  # type: ignore[misc]
    def _mock_handler(
        params: m.Infra.RefactorCentralizeInput,
    ) -> r[Mapping[str, int]]:
        nonlocal captured_apply, captured_workspace, captured_normalize_remaining
        captured_apply = params.apply
        captured_workspace = Path(params.workspace).resolve()
        captured_normalize_remaining = params.normalize_remaining
        return r[Mapping[str, int]].ok({"files": 0})

    monkeypatch.setattr(
        FlextInfraRefactorCli,
        "_handle_centralize_pydantic",
        _mock_handler,
    )
    result = refactor_main.main(
        ["--workspace", str(tmp_path), "--apply", "centralize-pydantic"],
    )
    tm.that(result, eq=0)
    tm.that(captured_apply, eq=True)
    tm.that(captured_workspace, eq=tmp_path.resolve())
    tm.that(captured_normalize_remaining, eq=False)
