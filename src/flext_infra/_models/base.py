"""Base models for flext-infra project.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

from flext_cli import m
from flext_infra import FlextInfraModelsMixins as mm, c, t


class FlextInfraModelsBase:
    """Base models for flext-infra project."""

    class SummaryStats(m.ContractModel):
        """Bundled stats for summary output."""

        verb: str = m.Field(description="Verb label for the summary block")
        total: int = m.Field(description="Total processed items")
        success: int = m.Field(description="Successful items")
        failed: int = m.Field(description="Failed items")
        skipped: int = m.Field(description="Skipped items")
        elapsed: float = m.Field(description="Elapsed time in seconds")

    class ProjectFailureInfo(
        mm.ProjectNameMixin,
        m.ContractModel,
    ):
        """Bundled info for project failure output."""

        elapsed: Annotated[float, m.Field(description="Elapsed time in seconds")]
        log_path: Annotated[Path, m.Field(description="Path to the project log")]
        error_count: Annotated[int, m.Field(description="Total project errors")]
        errors: Annotated[
            t.StrSequence,
            m.Field(description="Rendered error excerpt lines"),
        ]
        max_show: Annotated[int, m.Field(description="Maximum errors to render")] = 3

    class SafeExecutionResult(m.ContractModel):
        """Result of a safe execution pipeline run."""

        mode: Annotated[
            c.Infra.ExecutionMode,
            m.Field(description="Execution mode used"),
        ]
        files_backed_up: Annotated[
            t.StrSequence,
            m.Field(description="Paths of files backed up before transform"),
        ]
        gate_results: Annotated[
            t.StrSequence,
            m.Field(description="Gate validation outcome summaries"),
        ]
        rolled_back: Annotated[
            bool,
            m.Field(description="Whether rollback was performed"),
        ]

    class TransformStep(m.ContractModel):
        """Declarative step for enforcement pipeline."""

        detector: Annotated[
            str,
            m.Field(description="Detector rule_id to run"),
        ]
        transformer: Annotated[
            str,
            m.Field(description="Transformer class name to apply"),
        ]
        gates: Annotated[
            str,
            m.Field(description="Comma-separated gate names for post-validation"),
        ] = c.Infra.SAFE_EXECUTION_DEFAULT_GATES
