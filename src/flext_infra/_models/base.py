"""Base models for flext-infra project.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

from pydantic import Field

from flext_core import FlextModels
from flext_infra import t
from flext_infra._models.mixins import FlextInfraModelsMixins


class FlextInfraModelsBase:
    """Base models for flext-infra project."""

    class SummaryStats(FlextModels.ContractModel):
        """Bundled stats for summary output."""

        verb: Annotated[str, Field(description="Verb label for the summary block")]
        total: Annotated[int, Field(description="Total processed items")]
        success: Annotated[int, Field(description="Successful items")]
        failed: Annotated[int, Field(description="Failed items")]
        skipped: Annotated[int, Field(description="Skipped items")]
        elapsed: Annotated[float, Field(description="Elapsed time in seconds")]

    class ProjectFailureInfo(
        FlextInfraModelsMixins.ProjectNameMixin,
        FlextModels.ContractModel,
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
