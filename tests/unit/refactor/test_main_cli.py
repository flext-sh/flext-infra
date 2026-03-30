from __future__ import annotations

from pathlib import Path

import pytest
from flext_tests import tm

from flext_infra.refactor import __main__ as refactor_main


def test_refactor_census_rejects_apply_before_subcommand() -> None:
    tm.that(refactor_main.main(["--apply", "census"]), eq=2)


def test_refactor_centralize_accepts_apply_before_subcommand(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    captured_apply = False
    captured_workspace = Path()
    captured_normalize_remaining = False

    def _run_centralize(
        cli: object,
        *,
        normalize_remaining: bool,
    ) -> int:
        nonlocal captured_apply, captured_workspace, captured_normalize_remaining
        captured_apply = bool(getattr(cli, "apply", False))
        workspace_value = getattr(cli, "workspace", Path())
        captured_workspace = (
            workspace_value if isinstance(workspace_value, Path) else Path()
        )
        captured_normalize_remaining = normalize_remaining
        return 0

    monkeypatch.setattr(
        refactor_main.FlextInfraRefactorCommand,
        "run_centralize_pydantic",
        staticmethod(_run_centralize),
    )
    result = refactor_main.main(
        ["--workspace", str(tmp_path), "--apply", "centralize-pydantic"],
    )
    tm.that(result, eq=0)
    tm.that(captured_apply, eq=True)
    tm.that(captured_workspace, eq=tmp_path.resolve())
    tm.that(captured_normalize_remaining, eq=False)
