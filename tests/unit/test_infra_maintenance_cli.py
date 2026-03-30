"""CLI contract tests for workspace maintenance entry point."""

from __future__ import annotations

from flext_infra import u
from flext_infra.workspace.maintenance.__main__ import main


def test_maintenance_rejects_apply_flag() -> None:
    assert u.Infra.run_cli(main, ["--apply"]) == 2
