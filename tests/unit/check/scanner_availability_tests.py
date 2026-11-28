"""Native scanner absence remains distinct from applicability and findings.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

from flext_infra.check import FlextInfraGateRegistry
from tests import c, m, tm, u


class TestsFlextInfraScannerAvailability:
    """Exercise missing scanners through the real registry and gate owners."""

    @staticmethod
    @c.Tests.MARK.parametrize("gate_id", (c.Infra.CUBIC, c.Infra.SMELLS))
    def test_missing_applicable_scanner_is_an_operational_error(
        tmp_path: Path, gate_id: str
    ) -> None:
        """A selected scanner that cannot execute never reports quality findings."""
        registry = FlextInfraGateRegistry.default()
        gate = tm.not_none(registry.create(gate_id, tmp_path))
        context = m.Infra.GateContext(
            repository_root=tmp_path, reports_dir=tmp_path / "reports"
        )
        with u.Tests.env_vars_context({
            "PATH": str(tmp_path),
            c.Infra.CUBIC_API_KEY_ENV: "missing-scanner-fixture",
        }):
            tm.that(
                registry.applicable_gate_ids((gate_id,), tmp_path, context),
                eq=(gate_id,),
            )
            execution = gate.check(tmp_path, context)

        message = f"{gate.scanner_binary} binary not found on PATH"
        tm.fail(execution.result.passed)
        tm.that(execution.outcome, eq=c.Infra.ToolOutcome.ERROR)
        tm.that(tuple(issue.message for issue in execution.issues), eq=(message,))
        receipt = tm.not_none(execution.raw_receipt)
        tm.that(receipt.read_text(encoding=c.DEFAULT_ENCODING), has=message)

    @staticmethod
    def test_missing_cubic_without_credentials_is_not_selected(tmp_path: Path) -> None:
        """Offline applicability does not invent an execution or a passing gate."""
        registry = FlextInfraGateRegistry.default()
        gate = tm.not_none(registry.get(c.Infra.CUBIC))
        context = m.Infra.GateContext(
            repository_root=tmp_path, reports_dir=tmp_path / "reports"
        )
        with u.Tests.env_vars_context({
            "PATH": str(tmp_path),
            c.Infra.CUBIC_API_KEY_ENV: "",
        }):
            tm.that(gate.resolve_binary(), none=True)
            tm.that(
                registry.applicable_gate_ids((c.Infra.CUBIC,), tmp_path, context),
                eq=(),
            )
