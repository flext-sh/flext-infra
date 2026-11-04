# AUTO-GENERATED FILE — Regenerate with: make gen
"""Source-derived structural model contracts.

Copyright (c) 2026 FLEXT Team. All rights reserved.
src/flext_infra/_protocols/duplication
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import TYPE_CHECKING, Literal, Protocol, runtime_checkable

from flext_cli import FlextCliProtocols

if TYPE_CHECKING:
    from flext_infra import t


class FlextInfraProtocolsDuplication:
    """Own the structural contracts declared by its model source."""

    @runtime_checkable
    class ProjectDuplicationOverrides(FlextCliProtocols.Model, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def min_lines(self) -> t.PositiveInt:
            """Minimum duplicated line count."""
            ...

        @property
        def min_tokens(self) -> t.PositiveInt:
            """Minimum duplicated token count."""
            ...

        @property
        def threshold_percent(self) -> t.Percentage:
            """Maximum allowed duplication percentage."""
            ...

        @property
        def mode(self) -> t.NonEmptyStr:
            """Jscpd detection mode."""
            ...

        @property
        def scope(self) -> Sequence[str]:
            """Scope directory names."""
            ...

        @property
        def fleet(self) -> t.StrictBool:
            """Structural member projected from the owning model.

            Scan this governed workspace's declared members together in one cross-
            project jscpd run; the member set is derived from the workspace
            composition and is never listed here. Default on: a clone shared between
            two projects is a finding, never a per-project blind spot; a standalone
            checkout degrades to its own scope.
            """
            ...

        @property
        def comparison_roots(self) -> Sequence[str]:
            """Structural member projected from the owning model.

            External comparison checkout roots joined into this project's scan
            scope, analogous to mod consumer_roots. A clone stays a finding of THIS
            project only when one side remains under the invoking project root;
            clones wholly inside an external root belong to that root's owner. An
            absent root degrades: it is skipped and recorded in the gate output,
            like a standalone fleet checkout.
            """
            ...

    @runtime_checkable
    class JscpdProjectOverlay(FlextCliProtocols.Model, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def ignore(self) -> Sequence[str]:
            """Structural member projected from the owning model.

            File globs jscpd skips; mandated generated and evidence surfaces named
            by an operator authorization.
            """
            ...

    @runtime_checkable
    class JscpdConfig(FlextCliProtocols.Model, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def absolute(self) -> t.StrictBool:
            """Emit absolute paths."""
            ...

        @property
        def formats_exts(self) -> Mapping[str, Sequence[str]]:
            """Extensions by parser format."""
            ...

        @property
        def ignore(self) -> Sequence[str]:
            """Ignored path patterns."""
            ...

        @property
        def ignore_pattern(self) -> Sequence[str]:
            """Code-level regexes whose tokens jscpd skips."""
            ...

        @property
        def min_lines(self) -> t.PositiveInt:
            """Minimum duplicated line count."""
            ...

        @property
        def min_tokens(self) -> t.PositiveInt:
            """Minimum duplicated token count."""
            ...

        @property
        def mode(self) -> t.NonEmptyStr:
            """Jscpd detection mode."""
            ...

        @property
        def no_colors(self) -> t.StrictBool:
            """Disable color output."""
            ...

        @property
        def no_tips(self) -> t.StrictBool:
            """Disable tip output."""
            ...

        @property
        def reporters(self) -> Sequence[str]:
            """Required report formats."""
            ...

        @property
        def threshold(self) -> t.Percentage:
            """Maximum allowed duplication percentage."""
            ...

        @property
        def similarity(self) -> float:
            """Structural near-miss pass ratio."""
            ...

        @property
        def semantic(self) -> FlextInfraProtocolsDuplication.JscpdSemantic | None:
            """Embedding pass; absent where it is not executed."""
            ...

    @runtime_checkable
    class JscpdSemantic(FlextCliProtocols.Model, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def enabled(self) -> t.StrictBool:
            """Run the pass."""
            ...

        @property
        def provider(self) -> t.NonEmptyStr:
            """Embedding provider."""
            ...

        @property
        def url(self) -> t.NonEmptyStr:
            """Embeddings API URL."""
            ...

        @property
        def model(self) -> t.NonEmptyStr:
            """Embedding model name."""
            ...

    @runtime_checkable
    class JscpdLocation(FlextCliProtocols.Model, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def column(self) -> t.NonNegativeInt:
            """Zero-based UTF-8 byte column reported by jscpd."""
            ...

        @property
        def line(self) -> t.PositiveInt:
            """One-based source line reported by jscpd."""
            ...

        @property
        def position(self) -> t.NonNegativeInt:
            """Zero-based source offset reported by jscpd."""
            ...

    @runtime_checkable
    class JscpdFile(FlextCliProtocols.Model, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def end(self) -> t.PositiveInt:
            """Exclusive clone end offset."""
            ...

        @property
        def end_location(self) -> FlextInfraProtocolsDuplication.JscpdLocation:
            """Clone end coordinate."""
            ...

        @property
        def name(self) -> t.NonEmptyStr:
            """Absolute scanned source path."""
            ...

        @property
        def nodes(self) -> t.NonNegativeInt | None:
            """Scanner AST node count for semantic spans."""
            ...

        @property
        def start(self) -> t.NonNegativeInt:
            """Inclusive clone start offset."""
            ...

        @property
        def start_location(self) -> FlextInfraProtocolsDuplication.JscpdLocation:
            """Clone start coordinate."""
            ...

    @runtime_checkable
    class JscpdDuplicate(FlextCliProtocols.Model, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def first_file(self) -> FlextInfraProtocolsDuplication.JscpdFile:
            """First clone source."""
            ...

        @property
        def format_name(self) -> t.NonEmptyStr:
            """Jscpd parser format name."""
            ...

        @property
        def fragment(self) -> t.NonEmptyStr:
            """Duplicated source fragment."""
            ...

        @property
        def is_new(self) -> t.StrictBool:
            """Structural member projected from the owning model.

            Whether jscpd marked the clone new; the flag is absent from some jscpd
            report versions and defaults to False.
            """
            ...

        @property
        def kind(self) -> t.NonEmptyStr:
            """Structural member projected from the owning model.

            jscpd clone classification; the field is absent from some jscpd report
            versions and defaults to 'exact'.
            """
            ...

        @property
        def lines(self) -> t.PositiveInt:
            """Duplicated logical line count."""
            ...

        @property
        def second_file(self) -> FlextInfraProtocolsDuplication.JscpdFile:
            """Second clone source."""
            ...

        @property
        def tokens(self) -> t.PositiveInt:
            """Duplicated token count."""
            ...

        @property
        def similarity(self) -> float | None:
            """Score of a similar or semantic clone."""
            ...

        @property
        def method(self) -> t.NonEmptyStr | None:
            """Near-miss mechanism of a similar clone."""
            ...

    @runtime_checkable
    class JscpdStatisticsSummary(FlextCliProtocols.Model, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def clones(self) -> t.NonNegativeInt:
            """Detected clone count."""
            ...

        @property
        def duplicated_lines(self) -> t.NonNegativeInt:
            """Duplicated line count."""
            ...

        @property
        def duplicated_tokens(self) -> t.NonNegativeInt:
            """Duplicated token count."""
            ...

        @property
        def lines(self) -> t.NonNegativeInt:
            """Scanned logical line count."""
            ...

        @property
        def new_clones(self) -> t.NonNegativeInt:
            """New clone count."""
            ...

        @property
        def new_duplicated_lines(self) -> t.NonNegativeInt:
            """New duplicated line count."""
            ...

        @property
        def percentage(self) -> t.Percentage:
            """Duplicated line percentage."""
            ...

        @property
        def percentage_tokens(self) -> t.Percentage:
            """Duplicated token percentage."""
            ...

        @property
        def sources(self) -> t.NonNegativeInt:
            """Scanned source file count."""
            ...

        @property
        def tokens(self) -> t.NonNegativeInt:
            """Scanned token count."""
            ...

    @runtime_checkable
    class JscpdStatistics(FlextCliProtocols.Model, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def detection_date(self) -> t.NonEmptyStr:
            """Jscpd detection timestamp."""
            ...

        @property
        def formats(
            self,
        ) -> Mapping[str, FlextInfraProtocolsDuplication.JscpdStatisticsSummary]:
            """Statistics keyed by parsed source format."""
            ...

        @property
        def total(self) -> FlextInfraProtocolsDuplication.JscpdStatisticsSummary:
            """Aggregate scan statistics."""
            ...

    @runtime_checkable
    class JscpdReport(FlextCliProtocols.Model, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def duplicates(self) -> Sequence[FlextInfraProtocolsDuplication.JscpdDuplicate]:
            """Complete detected clone records."""
            ...

        @property
        def statistics(self) -> FlextInfraProtocolsDuplication.JscpdStatistics:
            """Validated scan statistics."""
            ...

    @runtime_checkable
    class DuplicationSpanMeasure(FlextCliProtocols.Model, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def source(self) -> str:
            """Physical source path."""
            ...

        @property
        def sha256(self) -> str:
            """Digest of the complete bytes read."""
            ...

        @property
        def lines(self) -> t.NonNegativeInt:
            """Physical lines with retained tokens."""
            ...

        @property
        def tokens(self) -> t.NonNegativeInt:
            """Retained Python lexical tokens."""
            ...

        @property
        def runs(self) -> tuple[tuple[int, int, int], ...]:
            """Contiguous retained line runs: start, end, token count."""
            ...

        @property
        def removed(self) -> tuple[str, ...]:
            """Removed structural categories."""
            ...

        @property
        def uncertainty(self) -> str:
            """Unproven import or annotation effects."""
            ...

    @runtime_checkable
    class DuplicationClassification(FlextCliProtocols.Model, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def disposition(
            self,
        ) -> Literal[
            "non_behavioral_only",
            "below_existing_behavior_floor",
            "behavioral_candidate",
            "authority_data_candidate",
            "unresolved",
            "analysis_error",
        ]:
            """Conservative explanation, not a gate exemption."""
            ...

        @property
        def reason(self) -> t.NonEmptyStr:
            """Evidence or causal analysis failure."""
            ...

    @runtime_checkable
    class DuplicationCandidateEvidence(DuplicationClassification, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def index(self) -> t.NonNegativeInt:
            """Zero-based raw inventory index."""
            ...

        @property
        def canonical_index(self) -> t.NonNegativeInt:
            """First unordered span pair index."""
            ...

        @property
        def candidate(self) -> FlextInfraProtocolsDuplication.JscpdDuplicate:
            """Unmodified typed scanner candidate."""
            ...

        @property
        def owned(self) -> bool:
            """At least one side belongs to the project."""
            ...

        @property
        def self_span(self) -> bool:
            """Both sides name the identical span."""
            ...

        @property
        def measures(
            self,
        ) -> tuple[FlextInfraProtocolsDuplication.DuplicationSpanMeasure, ...]:
            """Both measured spans when analysis succeeds."""
            ...

    @runtime_checkable
    class DuplicationAssessment(FlextCliProtocols.Model, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def policy(self) -> Literal["structural-evidence-v1-raw-hard"]:
            """Versioned non-promoting policy."""
            ...

        @property
        def raw_sha256(self) -> str:
            """Digest of the exact published receipt."""
            ...

        @property
        def report(self) -> FlextInfraProtocolsDuplication.JscpdReport:
            """Complete raw typed inventory and counters."""
            ...

        @property
        def candidates(
            self,
        ) -> tuple[FlextInfraProtocolsDuplication.DuplicationCandidateEvidence, ...]:
            """One explanation per raw candidate."""
            ...

        @property
        def min_lines(self) -> t.PositiveInt:
            """Selected existing line floor."""
            ...

        @property
        def min_tokens(self) -> t.PositiveInt:
            """Selected existing token floor."""
            ...

        @property
        def duration_seconds(self) -> float:
            """Measured analysis wall time."""
            ...

        @property
        def source_count(self) -> t.NonNegativeInt:
            """Unique complete sources read."""
            ...

        @property
        def counts(self) -> Mapping[str, int]:
            """Disposition and ownership counters."""
            ...

        @property
        def execution(self) -> str:
            """Scanner status, timeout, signal and pass availability."""
            ...

        @property
        def source_provenance(self) -> str:
            """Limits of source binding to the scanner snapshot."""
            ...

        @property
        def budget_status(self) -> str:
            """Budget verification status; absence never authorizes promotion."""
            ...

    @runtime_checkable
    class JscpdScan(FlextCliProtocols.Model, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def exit_code(self) -> t.NonNegativeInt:
            """Raw jscpd process exit code."""
            ...

        @property
        def report(self) -> FlextInfraProtocolsDuplication.JscpdReport:
            """Validated report from this exact scan."""
            ...

        @property
        def stderr(self) -> str:
            """Raw jscpd standard error."""
            ...

        @property
        def stdout(self) -> str:
            """Raw jscpd standard output."""
            ...


__all__: list[str] = [
    "FlextInfraProtocolsDuplication",
]
