"""Tests for constants-quality-gate CLI wiring.

Validates CLI dispatch, argument parsing, and verdict classification
using real service instances with temporary workspaces.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

from flext_tests import tm

from flext_infra import (
    FlextInfraConstantsCodegenQualityGate,
    main,
)
from tests import t


class TestConstantsQualityGateCLIDispatch:
    """CLI dispatch and argument parsing for constants-quality-gate."""

    def test_dispatch_returns_int(self, tmp_path: Path) -> None:
        """main() dispatches constants-quality-gate command to handler."""
        result = main([
            "codegen",
            "constants-quality-gate",
            "--workspace",
            str(tmp_path),
        ])
        tm.that(result, is_=int)

    def test_json_format_exits_with_int(self, tmp_path: Path) -> None:
        """JSON mode returns an integer exit code."""
        result = main([
            "codegen",
            "constants-quality-gate",
            "--workspace",
            str(tmp_path),
            "--format",
            "json",
        ])
        tm.that(result, is_=int)

    def test_text_format_exits_with_int(self, tmp_path: Path) -> None:
        """Text mode returns an integer exit code."""
        result = main([
            "codegen",
            "constants-quality-gate",
            "--workspace",
            str(tmp_path),
            "--format",
            "text",
        ])
        tm.that(result, is_=int)


class TestConstantsQualityGateVerdict:
    """Verdict classification and real workspace execution."""

    def test_success_verdict_accepts_pass(self) -> None:
        """successful_verdict returns True for PASS."""
        tm.that(
            FlextInfraConstantsCodegenQualityGate.successful_verdict("PASS"),
            eq=True,
        )

    def test_success_verdict_rejects_conditional_pass(self) -> None:
        """successful_verdict returns False for removed conditional verdicts."""
        tm.that(
            not FlextInfraConstantsCodegenQualityGate.successful_verdict(
                "CONDITIONAL_PASS"
            ),
            eq=True,
        )

    def test_success_verdict_rejects_fail(self) -> None:
        """successful_verdict returns False for FAIL."""
        tm.that(
            not FlextInfraConstantsCodegenQualityGate.successful_verdict("FAIL"),
            eq=True,
        )

    def test_real_workspace_run_returns_report(self, tmp_path: Path) -> None:
        """Quality gate runs on real empty workspace without errors."""
        gate = FlextInfraConstantsCodegenQualityGate(workspace=tmp_path)
        report = gate.build_report()
        assert isinstance(report, dict)
        assert "verdict" in report


__all__: t.StrSequence = []
