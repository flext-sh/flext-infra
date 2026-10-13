"""Native occurrence evidence shares complete authenticated source inputs.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

import pytest

from flext_infra import c, m
from flext_infra.codemod import FlextInfraModGateEngine
from tests import tm, u


class TestsFlextInfraModEvidenceInputs:
    """Validate public evidence round-trips without duplicated input bodies."""

    @staticmethod
    def test_native_occurrences_share_authenticated_inputs(mod_workspace: Path) -> None:
        """Every occurrence survives while each complete input is stored once."""
        source = mod_workspace / "consumer.py"
        marker = "descriptor evidence sentinel"
        source.write_text(
            f"# {marker}\nfrom __future__ import annotations\n"
            "def first(value: str) -> str:\n    return str(value)\n"
            "def second(value: str) -> str:\n    return str(value)\n",
            encoding="utf-8",
        )
        report = tm.ok(
            FlextInfraModGateEngine.scan(
                mod_workspace, fix=False, rule_ids=("ban-pass-through-wrapper",)
            )
        )
        tm.that(report.findings, eq=2)
        snapshot = u.Infra.codemod_binding_snapshot(
            mod_workspace, (tm.not_none(report.entries[0].source_state),)
        )
        report = report.model_copy(
            update={
                "entries": tuple(
                    entry.model_copy(update={"binding_states": snapshot.states})
                    for entry in report.entries
                )
            }
        )
        receipt = tm.ok(
            u.Infra.publish_mod_scan_evidence(
                mod_workspace,
                report,
                publication=m.Infra.ModScanPublication(
                    command=c.Infra.ModScanCommand.SCAN, scope=(str(source),)
                ),
            )
        )
        encoded = receipt.path.read_bytes()
        restored = m.Infra.ModScanEvidence.model_validate_json(encoded)
        tm.that(encoded.count(marker.encode("utf-8")), eq=1)
        tm.that(restored.entries, eq=report.entries)
        tm.that(
            len(restored.inputs.states),
            eq=len({
                state.path
                for state in (*tm.not_none(report.source_states), *snapshot.states)
            }),
        )
        tm.that(restored.entries[0].source_state is restored.entries[1].source_state)
        with pytest.raises(m.ValidationError):
            m.Infra.CodemodBindingSnapshot(
                states=(
                    snapshot.states[0],
                    snapshot.states[0].model_copy(update={"content": b"changed"}),
                )
            )
