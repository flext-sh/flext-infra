"""Result models for the enforcement fix orchestrator.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import Annotated

from flext_cli.models import FlextCliModels as m
from flext_infra.typings import t


class FlextInfraFixersResult:
    """Result containers returned by enforcement fix adapters."""

    class FixedViolation(m.ArbitraryTypesModel):
        """One violation that was fixed."""

        rule_id: Annotated[str, m.Field(description="Enforcement rule ID")]
        file_path: Annotated[str, m.Field(description="File that was modified")]
        message: Annotated[str, m.Field(description="Human-readable fix summary")]

    class SkippedViolation(m.ArbitraryTypesModel):
        """One violation that was skipped."""

        rule_id: Annotated[str, m.Field(description="Enforcement rule ID")]
        file_path: Annotated[str, m.Field(description="File containing the violation")]
        reason: Annotated[str, m.Field(description="Why the fix was skipped")]

    class FailedFix(m.ArbitraryTypesModel):
        """One fix attempt that failed."""

        rule_id: Annotated[str, m.Field(description="Enforcement rule ID")]
        file_path: Annotated[str, m.Field(description="Target file when known")]
        error: Annotated[str, m.Field(description="Failure message")]

    class ProjectFixResult(m.ArbitraryTypesModel):
        """Aggregated fix result for a single project."""

        project: Annotated[str, m.Field(description="Project name")]
        fixed: t.SequenceOf[FlextInfraFixersResult.FixedViolation] = m.Field(
            default_factory=tuple,
            description="Fixed violations",
        )
        skipped: t.SequenceOf[FlextInfraFixersResult.SkippedViolation] = m.Field(
            default_factory=tuple,
            description="Skipped violations",
        )
        failed: t.SequenceOf[FlextInfraFixersResult.FailedFix] = m.Field(
            default_factory=tuple,
            description="Failed fix attempts",
        )
        files_modified: t.StrSequence = m.Field(
            default_factory=tuple,
            description="Modified file paths",
        )


__all__: list[str] = ["FlextInfraFixersResult"]
