"""CLI contract tests for maintenance entry point."""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_infra import main as infra_main
from flext_tests import tm

if TYPE_CHECKING:
    from tests import t


def _run_maintenance(argv: t.StrSequence | None = None) -> int:
    args = ["maintenance"]
    if argv is not None:
        args.extend(argv)
    return infra_main(args)


class TestsFlextInfraInfraMaintenanceCli:
    """Behavior contract for test_infra_maintenance_cli."""

    def test_maintenance_rejects_apply_flag(self) -> None:
        tm.that(_run_maintenance(["--apply"]), eq=2)
