"""Original Infra reports round-trip through the public CLI evidence projection.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

from tests import c, m, tm


class TestsWorkspaceOperationReceipts:
    """Domain fields remain owned by Infra while CLI consumes its evidence view."""

    @staticmethod
    def test_unexecuted_receipt_preserves_its_original_report(tmp_path: Path) -> None:
        """An unattempted operation remains unattempted across both public models."""
        receipt = m.Infra.WorkspaceOperationReceipt(
            root=tmp_path,
            executed=False,
            outcome=None,
            completed=False,
            stage="environment",
            applicability="required installation has not completed",
        )
        report = m.Infra.WorkspaceOperationReport(
            root=tmp_path,
            operation="setup",
            scope=(tmp_path,),
            receipts=(receipt,),
        )
        serialized = report.model_dump_json()
        restored = m.Infra.WorkspaceOperationReport.model_validate_json(serialized)
        projected = m.Cli.ProcessNativeQualificationReport[
            m.Infra.WorkspaceRuntimeContext, m.Infra.Issue, c.Infra.ToolOutcome
        ].model_validate_json(serialized)
        tm.that(restored, eq=report)
        tm.fail(restored.receipts[0].executed)
        tm.that(restored.receipts[0].outcome, eq=None)
        tm.that(restored.receipts[0].completed, eq=False)
        tm.that(
            projected.receipts[0].native_tool_qualifications,
            eq=receipt.native_tool_qualifications,
        )
