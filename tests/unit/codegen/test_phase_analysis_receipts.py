"""Verify native failed-target receipts at the phase model boundary.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError

from tests import c, m, tm


class TestsPhaseAnalysisReceipts:
    """Rejected targets retain native analyses, not broader source receipts."""

    @staticmethod
    def test_failed_target_preserves_original_analysis(tmp_path: Path) -> None:
        """A validated native receipt crosses the boundary by reference."""
        original = m.Infra.CodegenPhaseAnalysis(
            phase=c.Infra.CodegenStagedFilePhase.LAZY_INIT,
            files=(),
            inputs=(),
        )
        analysis = m.Infra.CodegenPhaseAnalysis(
            phase=c.Infra.CodegenStagedFilePhase.LAZY_INIT,
            files=(),
            inputs=(),
            failed_targets=((tmp_path, original),),
        )

        tm.that(analysis.failed_targets[0][0], eq=tmp_path)
        tm.that(analysis.failed_targets[0][1], where=lambda value: value is original)

    @staticmethod
    def test_failed_target_rejects_non_analysis_receipt(tmp_path: Path) -> None:
        """A source-only receipt cannot masquerade as a failed phase analysis."""
        source = m.Infra.CodegenSourceReceipt(
            phase=c.Infra.CodegenStagedFilePhase.LAZY_INIT,
            inputs=(),
        )

        with pytest.raises(ValidationError, match="failed_targets"):
            m.Infra.CodegenPhaseAnalysis.model_validate({
                "phase": c.Infra.CodegenStagedFilePhase.LAZY_INIT,
                "files": (),
                "inputs": (),
                "failed_targets": ((tmp_path, source),),
            })
