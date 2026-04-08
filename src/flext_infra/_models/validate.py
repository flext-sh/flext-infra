"""Domain models for the core subpackage."""

from __future__ import annotations

from typing import Annotated

from pydantic import Field

from flext_core import FlextModels
from flext_infra import FlextInfraModelsMixins, t


class FlextInfraModelsCore:
    """Models for core infrastructure services (subprocess, validation).

    Canonical base policy:
    - ``ArbitraryTypesModel`` for mutable report/result payloads.
    - ``ContractModel`` reserved for immutable settings/config contracts.
    """

    class ValidationReport(FlextModels.ArbitraryTypesModel):
        """Validation report model with violations and summary."""

        passed: Annotated[bool, Field(description="Validation status")]
        violations: Annotated[
            t.StrSequence,
            Field(
                description="Collected validation violations",
            ),
        ] = Field(default_factory=list)
        summary: Annotated[
            str,
            Field(
                default="",
                description="Human-readable validation summary",
            ),
        ]

    class StubAnalysisReport(
        FlextInfraModelsMixins.ProjectNameMixin,
        FlextModels.ArbitraryTypesModel,
    ):
        """Structured stub-chain analysis result for a project."""

        mypy_hints: Annotated[
            t.StrSequence,
            Field(
                description="types- package hints from mypy output",
            ),
        ] = Field(default_factory=list)
        internal_missing: Annotated[
            t.StrSequence,
            Field(
                description="Missing internal imports",
            ),
        ] = Field(default_factory=list)
        unresolved_missing: Annotated[
            t.StrSequence,
            Field(
                description="Missing external imports without stubs",
            ),
        ] = Field(default_factory=list)
        total_missing: Annotated[
            t.NonNegativeInt,
            Field(description="Total missing imports"),
        ]

    class PytestDiagnostics(FlextModels.ArbitraryTypesModel):
        """Extracted diagnostics summary from junit XML and pytest logs."""

        failed_count: Annotated[
            t.NonNegativeInt,
            Field(description="Failed test case count"),
        ]
        error_count: Annotated[t.NonNegativeInt, Field(description="Error trace count")]
        warning_count: Annotated[
            t.NonNegativeInt,
            Field(description="Warning line count"),
        ]
        skipped_count: Annotated[
            t.NonNegativeInt,
            Field(description="Skipped test case count"),
        ]
        failed_cases: Annotated[
            t.StrSequence,
            Field(
                description="Failed test labels",
            ),
        ] = Field(default_factory=list)
        error_traces: Annotated[
            t.StrSequence,
            Field(
                description="Collected error traces",
            ),
        ] = Field(default_factory=list)
        warning_lines: Annotated[
            t.StrSequence,
            Field(
                description="Captured warning lines",
            ),
        ] = Field(default_factory=list)
        skip_cases: Annotated[
            t.StrSequence,
            Field(
                description="Skipped test labels",
            ),
        ] = Field(default_factory=list)
        slow_entries: Annotated[
            t.StrSequence,
            Field(
                description="Slow test entries",
            ),
        ] = Field(default_factory=list)

    class DiagResult(FlextModels.ArbitraryTypesModel):
        """Internal container for extracted diagnostics."""

        failed_cases: t.StrSequence = Field(
            default_factory=list, description="Failed cases records"
        )
        error_traces: t.StrSequence = Field(
            default_factory=list, description="Error traces records"
        )
        skip_cases: t.StrSequence = Field(
            default_factory=list, description="Skipped cases records"
        )
        warning_lines: t.StrSequence = Field(
            default_factory=list, description="Warning lines records"
        )
        slow_entries: t.StrSequence = Field(
            default_factory=list, description="Slow entries records"
        )

    class InventoryReport(FlextModels.ArbitraryTypesModel):
        """Summary of written inventory report artifacts."""

        total_scripts: Annotated[
            t.NonNegativeInt,
            Field(description="Total discovered scripts"),
        ]
        reports_written: Annotated[
            t.StrSequence,
            Field(
                description="Written report file paths",
            ),
        ] = Field(default_factory=list)


__all__ = ["FlextInfraModelsCore"]
