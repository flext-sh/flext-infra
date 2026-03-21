"""Typing census and violation detection models for flext-infra refactor."""

from __future__ import annotations

from typing import Annotated

from pydantic import ConfigDict, Field

from flext_core import FlextModels
from flext_infra.typings import FlextInfraTypes as t


class FlextInfraTypingCensusModels:
    """Mixin containing typing census and violation detection model contracts."""

    class TypingAnnotationViolation(FlextModels.FrozenStrictModel):
        """Detected typing annotation violation in source code."""

        model_config = ConfigDict(frozen=True)

        file: Annotated[t.NonEmptyStr, Field(description="Source file path")]
        line: Annotated[t.PositiveInt, Field(description="Line number")]
        column: Annotated[t.NonNegativeInt, Field(description="Column offset")]
        annotation_text: Annotated[
            t.NonEmptyStr, Field(description="Original annotation text")
        ]
        violation_kind: Annotated[
            str,
            Field(
                min_length=1,
                description=(
                    "Violation category: bare_object, container_object,"
                    " mapping_object, list_object, sequence_object,"
                    " typeadapter_object"
                ),
            ),
        ]
        context: Annotated[
            str,
            Field(
                min_length=1,
                description=(
                    "Annotation context: param, return, field, variable, typeadapter"
                ),
            ),
        ]
        suggested_replacement: Annotated[
            str, Field(description="Suggested replacement text")
        ]

    class TypingCensusReport(FlextModels.ArbitraryTypesModel):
        """Comprehensive typing census report with violation summary."""

        violations: Annotated[
            list[FlextInfraTypingCensusModels.TypingAnnotationViolation],
            Field(
                default_factory=list,
                description="All detected typing violations",
            ),
        ]
        total_violations: Annotated[
            t.NonNegativeInt, Field(description="Total violation count")
        ]
        violations_by_kind: Annotated[
            dict[str, int],
            Field(
                default_factory=dict,
                description="Violation counts by kind",
            ),
        ]
        files_scanned: Annotated[t.NonNegativeInt, Field(description="Files scanned")]
        parse_errors: Annotated[
            t.NonNegativeInt, Field(description="Files that failed to parse")
        ]

    class UnusedModelViolation(FlextModels.FrozenStrictModel):
        """Detected unused model class in source code."""

        model_config = ConfigDict(frozen=True)

        file: Annotated[t.NonEmptyStr, Field(description="Source file path")]
        line: Annotated[t.PositiveInt, Field(description="Line number")]
        class_name: Annotated[
            t.NonEmptyStr, Field(description="Unused model class name")
        ]
        reason: Annotated[
            str,
            Field(
                min_length=1,
                description="Reason: no_imports or no_references",
            ),
        ]

    class UnusedModelReport(FlextModels.ArbitraryTypesModel):
        """Report of unused model classes detected in codebase."""

        unused_models: Annotated[
            list[FlextInfraTypingCensusModels.UnusedModelViolation],
            Field(
                default_factory=list,
                description="Unused model violations",
            ),
        ]
        models_scanned: Annotated[
            t.NonNegativeInt, Field(description="Total models scanned")
        ]

    class ViolationCensusRecord(FlextModels.FrozenStrictModel):
        """Single violation record in census."""

        model_config = ConfigDict(frozen=True)

        file: Annotated[t.NonEmptyStr, Field(description="Source file path")]
        line: Annotated[t.PositiveInt, Field(description="Line number")]
        kind: Annotated[t.NonEmptyStr, Field(description="Violation kind identifier")]
        detail: Annotated[
            str,
            Field(default="", description="Human-readable detail"),
        ]

    class ViolationCensusReport(FlextModels.ArbitraryTypesModel):
        """Aggregated violation census report across codebase."""

        records: Annotated[
            list[FlextInfraTypingCensusModels.ViolationCensusRecord],
            Field(
                default_factory=list,
                description="All violation records",
            ),
        ]
        totals_by_kind: Annotated[
            dict[str, int],
            Field(
                default_factory=dict,
                description="Counts by violation kind",
            ),
        ]
        files_scanned: Annotated[t.NonNegativeInt, Field(description="Files scanned")]


__all__ = ["FlextInfraTypingCensusModels"]
