"""Base models for flext-infra project.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

from pydantic import Field

from flext_cli import m
from flext_infra import c, t
from flext_infra._models.mixins import FlextInfraModelsMixins


class FlextInfraModelsBase:
    """Base models for flext-infra project."""

    class SummaryStats(m.ContractModel):
        """Bundled stats for summary output."""

        verb: str = Field(description="Verb label for the summary block")
        total: int = Field(description="Total processed items")
        success: int = Field(description="Successful items")
        failed: int = Field(description="Failed items")
        skipped: int = Field(description="Skipped items")
        elapsed: float = Field(description="Elapsed time in seconds")

    class ProjectFailureInfo(
        FlextInfraModelsMixins.ProjectNameMixin,
        m.ContractModel,
    ):
        """Bundled info for project failure output."""

        elapsed: Annotated[float, Field(description="Elapsed time in seconds")]
        log_path: Annotated[Path, Field(description="Path to the project log")]
        error_count: Annotated[int, Field(description="Total project errors")]
        errors: Annotated[
            t.StrSequence,
            Field(description="Rendered error excerpt lines"),
        ]
        max_show: Annotated[int, Field(description="Maximum errors to render")] = 3

    class SafeExecutionResult(m.ContractModel):
        """Result of a safe execution pipeline run."""

        mode: Annotated[
            c.Infra.ExecutionMode,
            Field(description="Execution mode used"),
        ]
        files_backed_up: Annotated[
            t.StrSequence,
            Field(description="Paths of files backed up before transform"),
        ]
        gate_results: Annotated[
            t.StrSequence,
            Field(description="Gate validation outcome summaries"),
        ]
        rolled_back: Annotated[
            bool,
            Field(description="Whether rollback was performed"),
        ]

    class TransformStep(m.ContractModel):
        """Declarative step for enforcement pipeline."""

        detector: Annotated[
            str,
            Field(description="Detector rule_id to run"),
        ]
        transformer: Annotated[
            str,
            Field(description="Transformer class name to apply"),
        ]
        gates: Annotated[
            str,
            Field(description="Comma-separated gate names for post-validation"),
        ] = c.Infra.SAFE_EXECUTION_DEFAULT_GATES
