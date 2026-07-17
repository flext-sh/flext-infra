"""Result models for the enforcement fix orchestrator.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Annotated

from flext_cli import FlextCliModels as m

if TYPE_CHECKING:
    from flext_infra import t


class FlextInfraFixersResult:
    """Result containers returned by enforcement fix adapters."""

    class FixedViolation(m.ArbitraryTypesModel):
        """One violation that was fixed."""

        rule_id: Annotated[str, m.Field(description="Enforcement rule ID")]
        file_path: Annotated[str, m.Field(description="File that was modified")]
        message: Annotated[str, m.Field(description="Human-readable fix summary")]

    class PreviewedViolation(m.ArbitraryTypesModel):
        """One violation with a non-mutating dry-run fix preview."""

        rule_id: Annotated[str, m.Field(description="Enforcement rule ID")]
        file_path: Annotated[str, m.Field(description="File that would change")]
        message: Annotated[str, m.Field(description="Human-readable preview summary")]

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
            default_factory=tuple, description="Fixed violations"
        )
        previewed: t.SequenceOf[FlextInfraFixersResult.PreviewedViolation] = m.Field(
            default_factory=tuple, description="Dry-run previews"
        )
        skipped: t.SequenceOf[FlextInfraFixersResult.SkippedViolation] = m.Field(
            default_factory=tuple, description="Skipped violations"
        )
        failed: t.SequenceOf[FlextInfraFixersResult.FailedFix] = m.Field(
            default_factory=tuple, description="Failed fix attempts"
        )
        files_modified: t.StrSequence = m.Field(
            default_factory=tuple, description="Modified file paths"
        )


__all__: list[str] = ["FlextInfraFixersResult"]
