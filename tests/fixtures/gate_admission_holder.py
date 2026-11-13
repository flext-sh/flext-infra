"""Process fixture: one heavy gate that holds its admitted slot until released.

Run as ``python -m tests.fixtures.gate_admission_holder <name> <root> <mode>
<budget_seconds> [repeat]``. The process admits itself through the public
``u.Infra`` owner, records ``<name>.started``, waits for ``<name>.release`` and
records ``<name>.ended`` (FLEXT ADR-032). With ``repeat`` it is a full-weight
run under the declared check repeat window: refused inside the window, and
recorded when it succeeds.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import sys
import time
from collections.abc import Sequence
from enum import StrEnum, unique
from pathlib import Path

from flext_infra import config, m, u


class TestsFlextInfraGateAdmissionHolder:
    """Hold one admitted slot the way a heavy route does."""

    @unique
    class Mode(StrEnum):
        """What the holder does once it is released."""

        HOLD = "hold"
        FAIL = "fail"
        NESTED = "nested"

    FAILURE_STATUS = 7

    @classmethod
    def main(cls, arguments: Sequence[str]) -> int:
        """Admit, hold until released, and leave with the mode's status.

        Returns:
            Zero, or ``FAILURE_STATUS`` in fail mode.

        """
        name, root_text, mode_text, budget_text, *repeat = arguments
        root, mode = Path(root_text), cls.Mode(mode_text)
        budget = m.Infra.RouteBudgetSpec(
            budget_seconds=int(budget_text), grace_seconds=1
        )
        if repeat:
            u.Infra.gate_repeat_refuse(
                name, root, config.Infra.gate_admission.repeat.check
            )
        with u.Infra.gate_admitted_budget(name, root, budget) as ticket:
            (root / f"{name}.started").write_text(str(time.time()), encoding="utf-8")
            while not (root / f"{name}.release").exists():
                time.sleep(0.1)
            if mode is cls.Mode.NESTED:
                with u.Infra.gate_admitted(f"{name}-inner", root):
                    (root / f"{name}.nested").write_text("", encoding="utf-8")
            (root / f"{name}.ended").write_text(str(time.time()), encoding="utf-8")
        if mode is cls.Mode.FAIL:
            return cls.FAILURE_STATUS
        if repeat:
            u.Infra.gate_repeat_record(ticket)
        return 0


if __name__ == "__main__":
    sys.exit(TestsFlextInfraGateAdmissionHolder.main(sys.argv[1:]))

__all__ = ["TestsFlextInfraGateAdmissionHolder"]
