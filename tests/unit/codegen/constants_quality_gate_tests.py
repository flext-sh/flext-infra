"""Tests for constants-quality-gate CLI wiring.

Validates CLI dispatch, argument parsing, and verdict classification
using real service instances with temporary workspaces.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_tests import tm

from flext_infra import m, main, u
from flext_infra.codegen.constants_quality_gate import FlextInfraCodegenQualityGate
from flext_infra.refactor.census import FlextInfraRefactorCensus

if TYPE_CHECKING:
    from pathlib import Path

    import pytest

    from tests.typings import t


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
            FlextInfraCodegenQualityGate.successful_verdict("PASS"),
            eq=True,
        )

    def test_success_verdict_rejects_conditional_pass(self) -> None:
        """successful_verdict returns False for removed conditional verdicts."""
        tm.that(
            not FlextInfraCodegenQualityGate.successful_verdict("CONDITIONAL_PASS"),
            eq=True,
        )

    def test_success_verdict_rejects_fail(self) -> None:
        """successful_verdict returns False for FAIL."""
        tm.that(
            not FlextInfraCodegenQualityGate.successful_verdict("FAIL"),
            eq=True,
        )

    def test_real_workspace_run_returns_report(self, tmp_path: Path) -> None:
        """Quality gate runs on real empty workspace without errors."""
        gate = FlextInfraCodegenQualityGate(workspace_root=tmp_path)
        report_result = gate.build_report()
        tm.ok(report_result)
        assert "verdict" in report_result.value

    def test_build_report_uses_canonical_census_duplicates(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
    ) -> None:
        """Duplicate groups are sourced from the canonical refactor census."""
        census_report = m.Infra.Census.WorkspaceReport.model_validate({
            "duplicates": (
                {
                    "name": "SHARED_TIMEOUT",
                    "kind": "constant",
                    "definitions": (
                        {
                            "name": "SHARED_TIMEOUT",
                            "kind": "constant",
                            "file_path": str(
                                (
                                    tmp_path / "flext-core" / "src" / "sample.py"
                                ).resolve(),
                            ),
                            "line": 1,
                            "project": "flext-core",
                        },
                        {
                            "name": "SHARED_TIMEOUT",
                            "kind": "constant",
                            "file_path": str(
                                (
                                    tmp_path / "flext-cli" / "src" / "sample.py"
                                ).resolve(),
                            ),
                            "line": 1,
                            "project": "flext-cli",
                        },
                    ),
                    "canonical": "flext-core",
                    "value_identical": True,
                },
            ),
        })

        monkeypatch.setattr(
            FlextInfraRefactorCensus,
            "build_report",
            lambda self: census_report,
        )

        gate = FlextInfraCodegenQualityGate(workspace_root=tmp_path)
        report_result = gate.build_report()
        tm.ok(report_result)
        report = report_result.value
        after = u.Cli.json_deep_mapping(report, "after")
        duplicate_groups = u.Cli.json_deep_mapping_list(
            report,
            "duplicate_constant_groups",
        )

        assert u.Cli.json_pick_int(after, "duplicate_groups") == 1
        assert u.Cli.json_pick_str(duplicate_groups[0], "name") == "SHARED_TIMEOUT"
        assert u.Cli.json_pick_str(duplicate_groups[0], "canonical") == "flext-core"


__all__: t.StrSequence = []
