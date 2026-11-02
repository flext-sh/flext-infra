# AUTO-GENERATED FILE — Regenerate with: make gen
"""Source-derived structural model contracts."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Literal, Protocol, runtime_checkable

from flext_infra import t


class FlextInfraProtocolsDuplication:
    """Own the structural model contracts declared by this module."""

    @runtime_checkable
    class ProjectDuplicationOverrides(Protocol):
        """Structural data contract projected from the owning model."""

        min_lines: t.PositiveInt = ...
        min_tokens: t.PositiveInt = ...
        threshold_percent: t.Percentage = ...
        mode: t.NonEmptyStr = ...
        scope: Sequence[str] = ...
        fleet: t.StrictBool = ...
        comparison_roots: Sequence[str] = ...

    @runtime_checkable
    class JscpdProjectOverlay(Protocol):
        """Structural data contract projected from the owning model."""

        ignore: Sequence[str] = ...

    @runtime_checkable
    class JscpdConfig(Protocol):
        """Structural data contract projected from the owning model."""

        absolute: t.StrictBool
        formats_exts: Mapping[str, Sequence[str]] = ...
        ignore: Sequence[str]
        ignore_pattern: Sequence[str] = ...
        min_lines: t.PositiveInt = ...
        min_tokens: t.PositiveInt = ...
        mode: t.NonEmptyStr
        no_colors: t.StrictBool = ...
        no_tips: t.StrictBool = ...
        reporters: Sequence[str]
        threshold: t.Percentage
        similarity: float
        semantic: FlextInfraProtocolsDuplication.JscpdSemantic | None = ...

    @runtime_checkable
    class JscpdSemantic(Protocol):
        """Structural data contract projected from the owning model."""

        enabled: t.StrictBool = ...
        provider: t.NonEmptyStr
        url: t.NonEmptyStr
        model: t.NonEmptyStr

    @runtime_checkable
    class JscpdLocation(Protocol):
        """Structural data contract projected from the owning model."""

        column: t.NonNegativeInt
        line: t.PositiveInt
        position: t.NonNegativeInt

    @runtime_checkable
    class JscpdFile(Protocol):
        """Structural data contract projected from the owning model."""

        end: t.PositiveInt
        end_location: FlextInfraProtocolsDuplication.JscpdLocation
        name: t.NonEmptyStr
        nodes: t.NonNegativeInt | None = ...
        start: t.NonNegativeInt
        start_location: FlextInfraProtocolsDuplication.JscpdLocation

    @runtime_checkable
    class JscpdDuplicate(Protocol):
        """Structural data contract projected from the owning model."""

        first_file: FlextInfraProtocolsDuplication.JscpdFile
        format_name: t.NonEmptyStr
        fragment: t.NonEmptyStr
        is_new: t.StrictBool = ...
        kind: t.NonEmptyStr = ...
        lines: t.PositiveInt
        second_file: FlextInfraProtocolsDuplication.JscpdFile
        tokens: t.PositiveInt
        similarity: float | None = ...
        method: t.NonEmptyStr | None = ...

    @runtime_checkable
    class JscpdStatisticsSummary(Protocol):
        """Structural data contract projected from the owning model."""

        clones: t.NonNegativeInt
        duplicated_lines: t.NonNegativeInt
        duplicated_tokens: t.NonNegativeInt
        lines: t.NonNegativeInt
        new_clones: t.NonNegativeInt
        new_duplicated_lines: t.NonNegativeInt
        percentage: t.Percentage
        percentage_tokens: t.Percentage
        sources: t.NonNegativeInt
        tokens: t.NonNegativeInt

    @runtime_checkable
    class JscpdStatistics(Protocol):
        """Structural data contract projected from the owning model."""

        detection_date: t.NonEmptyStr
        formats: Mapping[str, FlextInfraProtocolsDuplication.JscpdStatisticsSummary]
        total: FlextInfraProtocolsDuplication.JscpdStatisticsSummary

    @runtime_checkable
    class JscpdReport(Protocol):
        """Structural data contract projected from the owning model."""

        duplicates: Sequence[FlextInfraProtocolsDuplication.JscpdDuplicate]
        statistics: FlextInfraProtocolsDuplication.JscpdStatistics

    @runtime_checkable
    class DuplicationSpanMeasure(Protocol):
        """Structural data contract projected from the owning model."""

        source: str = ...
        sha256: str = ...
        lines: t.NonNegativeInt = ...
        tokens: t.NonNegativeInt = ...
        runs: tuple[tuple[int, int, int], ...] = ...
        removed: tuple[str, ...] = ...
        uncertainty: str = ...

    @runtime_checkable
    class DuplicationClassification(Protocol):
        """Structural data contract projected from the owning model."""

        disposition: Literal[
            "non_behavioral_only",
            "below_existing_behavior_floor",
            "behavioral_candidate",
            "authority_data_candidate",
            "unresolved",
            "analysis_error",
        ] = ...
        reason: t.NonEmptyStr = ...

    @runtime_checkable
    class DuplicationCandidateEvidence(Protocol):
        """Structural data contract projected from the owning model."""

        disposition: Literal[
            "non_behavioral_only",
            "below_existing_behavior_floor",
            "behavioral_candidate",
            "authority_data_candidate",
            "unresolved",
            "analysis_error",
        ] = ...
        reason: t.NonEmptyStr = ...
        index: t.NonNegativeInt = ...
        canonical_index: t.NonNegativeInt = ...
        candidate: FlextInfraProtocolsDuplication.JscpdDuplicate = ...
        owned: bool = ...
        self_span: bool = ...
        measures: tuple[
            FlextInfraProtocolsDuplication.DuplicationSpanMeasure, ...
        ] = ...

    @runtime_checkable
    class DuplicationAssessment(Protocol):
        """Structural data contract projected from the owning model."""

        policy: Literal["structural-evidence-v1-raw-hard"] = ...
        raw_sha256: str = ...
        report: FlextInfraProtocolsDuplication.JscpdReport = ...
        candidates: tuple[
            FlextInfraProtocolsDuplication.DuplicationCandidateEvidence, ...
        ] = ...
        min_lines: t.PositiveInt = ...
        min_tokens: t.PositiveInt = ...
        duration_seconds: float = ...
        source_count: t.NonNegativeInt = ...
        counts: Mapping[str, int] = ...
        execution: str = ...
        source_provenance: str = ...
        budget_status: str = ...

    @runtime_checkable
    class JscpdScan(Protocol):
        """Structural data contract projected from the owning model."""

        exit_code: t.NonNegativeInt
        report: FlextInfraProtocolsDuplication.JscpdReport
        stderr: str
        stdout: str


__all__: list[str] = [
    "FlextInfraProtocolsDuplication",
]
