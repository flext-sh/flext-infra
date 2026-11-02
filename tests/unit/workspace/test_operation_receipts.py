"""Original Infra reports round-trip through the public CLI evidence projection.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

import pytest

from flext_infra.workspace import FlextInfraWorkspaceDetector
from tests import c, m, tm, u


class TestsWorkspaceOperationReceipts:
    """Domain fields remain owned by Infra while CLI consumes its evidence view."""

    @staticmethod
    def test_persisted_protocol_evidence_retains_native_schema() -> None:
        """Real captured state retains its validation and complete JSON schema."""
        source = Path(__file__).resolve()
        observed = u.Cli.atomic_read_binary_file_state(source, required=True).unwrap()
        elected = FlextInfraWorkspaceDetector.runtime_election(
            source.parents[3]
        ).unwrap()
        original = m.Infra.WorkspaceRuntimeContext.model_validate(
            elected, from_attributes=True
        )
        payload = original.model_dump()
        payload["installation_inputs"] = (observed,)
        context = m.Infra.WorkspaceRuntimeContext.model_validate(payload)

        tm.that(context.installation_inputs[0] is observed, eq=True)
        restored = m.Infra.WorkspaceRuntimeContext.model_validate_json(
            context.model_dump_json()
        )
        state = restored.installation_inputs[0]
        tm.that(type(state) is type(observed), eq=True)
        tm.that(state.path, eq=observed.path)
        tm.that(state.content, eq=observed.content)
        tm.that(
            m.Infra.WorkspaceRuntimeContext.model_json_schema()["$defs"][
                m.Cli.AtomicFileState.__name__
            ],
            eq=m.Cli.AtomicFileState.model_json_schema(),
        )

        payload["installation_inputs"] = (
            {
                "path": observed.path,
                "content": observed.content,
            },
        )
        with pytest.raises(c.ValidationError):
            m.Infra.WorkspaceRuntimeContext.model_validate(payload)

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
