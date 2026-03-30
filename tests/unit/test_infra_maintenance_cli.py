"""CLI contract tests for workspace maintenance entry point."""

from __future__ import annotations

from collections.abc import Sequence

from flext_infra import u
from flext_infra.cli import main as infra_main


def main(argv: Sequence[str] | None = None) -> int:
    args = ["maintenance"]
    if argv is not None:
        args.extend(argv)
    return infra_main(args)


def test_maintenance_rejects_apply_flag() -> None:
    assert u.Infra.run_cli(main, ["--apply"]) == 2
