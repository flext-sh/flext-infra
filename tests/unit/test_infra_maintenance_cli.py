"""CLI contract tests for workspace maintenance entry point."""

from __future__ import annotations

from tests import t, u

from flext_infra import main as infra_main


def main(argv: t.StrSequence | None = None) -> int:
    args = ["maintenance"]
    if argv is not None:
        args.extend(argv)
    return infra_main(args)


def test_maintenance_rejects_apply_flag() -> None:
    assert u.Infra.run_cli(main, ["--apply"]) == 2
