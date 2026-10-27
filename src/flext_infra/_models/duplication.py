"""Typed jscpd report contracts for the duplication gate.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path
from typing import Annotated, ClassVar, Literal, Self

from flext_core import m

from flext_infra import c, t


class FlextInfraModelsDuplication:
    """Strict external-boundary models for jscpd 5 reports."""

    class ProjectDuplicationOverrides(m.ContractModel):
        """Validated ``[tool.flext.project.duplication]`` overrides.

        One project's pyproject.toml may narrow the workspace-wide jscpd
        defaults; every field defaults to the canonical constant so a project
        with no overrides table gets the same behavior as the workspace scan.
        """

        model_config: ClassVar[m.ConfigDict] = m.ConfigDict(
            extra="forbid",
            frozen=True,
            populate_by_name=True,
        )

        min_lines: Annotated[
            t.PositiveInt,
            m.Field(alias="min-lines", description="Minimum duplicated line count"),
        ] = c.Infra.JSCPD_MIN_LINES
        min_tokens: Annotated[
            t.PositiveInt,
            m.Field(alias="min-tokens", description="Minimum duplicated token count"),
        ] = c.Infra.JSCPD_MIN_TOKENS
        threshold_percent: Annotated[
            t.Percentage,
            m.Field(
                alias="threshold-percent",
                description="Maximum allowed duplication percentage",
            ),
        ] = c.Infra.JSCPD_THRESHOLD_PERCENT
        mode: Annotated[t.NonEmptyStr, m.Field(description="jscpd detection mode")] = (
            c.Infra.JSCPD_MODE
        )
        scope: Annotated[
            t.StrSequence,
            m.Field(description="Scope directory names"),
        ] = c.Infra.JSCPD_SCOPE_DIRNAMES
        fleet: Annotated[
            t.StrictBool,
            m.Field(
                description=(
                    "Scan this governed workspace's declared members together in "
                    "one cross-project jscpd run; the member set is derived from "
                    "the workspace composition and is never listed here. Default "
                    "on: a clone shared between two projects is a finding, never "
                    "a per-project blind spot; a standalone checkout degrades to "
                    "its own scope"
                ),
            ),
        ] = True
        comparison_roots: Annotated[
            t.StrSequence,
            m.Field(
                description=(
                    "External comparison checkout roots joined into this "
                    "project's scan scope, analogous to mod consumer_roots. A "
                    "clone stays a finding of THIS project only when one side "
                    "remains under the invoking project root; clones wholly "
                    "inside an external root belong to that root's owner. An "
                    "absent root degrades: it is skipped and recorded in the "
                    "gate output, like a standalone fleet checkout"
                ),
            ),
        ] = ()

    class JscpdConfig(m.ContractModel):
        """Complete generated jscpd invocation configuration."""

        model_config: ClassVar[m.ConfigDict] = m.ConfigDict(
            extra="forbid",
            frozen=True,
            populate_by_name=True,
        )

        absolute: Annotated[t.StrictBool, m.Field(description="Emit absolute paths")]
        formats_exts: t.MappingKV[str, t.StrSequence] = m.Field(
            alias="formatsExts",
            description="Extensions by parser format",
        )
        ignore: Annotated[t.StrSequence, m.Field(description="Ignored path patterns")]
        ignore_pattern: t.StrSequence = m.Field(
            alias="ignorePattern",
            description="Code-level regexes whose tokens jscpd skips",
        )
        min_lines: t.PositiveInt = m.Field(
            alias="minLines",
            description="Minimum duplicated line count",
        )
        min_tokens: t.PositiveInt = m.Field(
            alias="minTokens",
            description="Minimum duplicated token count",
        )
        mode: Annotated[t.NonEmptyStr, m.Field(description="jscpd detection mode")]
        no_colors: t.StrictBool = m.Field(
            alias="noColors",
            description="Disable color output",
        )
        no_tips: t.StrictBool = m.Field(
            alias="noTips",
            description="Disable tip output",
        )
        reporters: Annotated[
            t.StrSequence,
            m.Field(description="Required report formats"),
        ]
        threshold: Annotated[
            t.Percentage,
            m.Field(description="Maximum allowed duplication percentage"),
        ]
        similarity: Annotated[
            float,
            m.Field(gt=0, le=1, description="Structural near-miss pass ratio"),
        ]
        semantic: Annotated[
            FlextInfraModelsDuplication.JscpdSemantic | None,
            m.Field(description="Embedding pass; absent where it is not executed"),
        ] = None

    class JscpdSemantic(m.ContractModel):
        """Enabled embedding pass of the generated jscpd configuration."""

        enabled: Annotated[t.StrictBool, m.Field(description="Run the pass")] = True
        provider: Annotated[t.NonEmptyStr, m.Field(description="Embedding provider")]
        url: Annotated[t.NonEmptyStr, m.Field(description="Embeddings API URL")]
        model: Annotated[t.NonEmptyStr, m.Field(description="Embedding model name")]

    class JscpdLocation(m.ContractModel):
        """One required source coordinate in a jscpd report."""

        column: Annotated[
            t.NonNegativeInt,
            m.Field(description="Zero-based UTF-8 byte column reported by jscpd"),
        ]
        line: Annotated[
            t.PositiveInt,
            m.Field(description="One-based source line reported by jscpd"),
        ]
        position: Annotated[
            t.NonNegativeInt,
            m.Field(description="Zero-based source offset reported by jscpd"),
        ]

    class JscpdFile(m.ContractModel):
        """One side of a detected clone."""

        model_config: ClassVar[m.ConfigDict] = m.ConfigDict(
            extra="forbid",
            frozen=True,
            populate_by_name=True,
        )

        end: Annotated[t.PositiveInt, m.Field(description="Exclusive clone end offset")]
        end_location: Annotated[
            FlextInfraModelsDuplication.JscpdLocation,
            m.Field(alias="endLoc", description="Clone end coordinate"),
        ]
        name: Annotated[
            t.NonEmptyStr,
            m.Field(description="Absolute scanned source path"),
        ]
        nodes: Annotated[
            t.NonNegativeInt | None,
            m.Field(description="Scanner AST node count for semantic spans"),
        ] = None
        start: Annotated[
            t.NonNegativeInt,
            m.Field(description="Inclusive clone start offset"),
        ]
        start_location: Annotated[
            FlextInfraModelsDuplication.JscpdLocation,
            m.Field(alias="startLoc", description="Clone start coordinate"),
        ]

    class JscpdDuplicate(m.ContractModel):
        """One complete two-sided clone from jscpd."""

        model_config: ClassVar[m.ConfigDict] = m.ConfigDict(
            extra="forbid",
            frozen=True,
            populate_by_name=True,
        )

        first_file: Annotated[
            FlextInfraModelsDuplication.JscpdFile,
            m.Field(alias="firstFile", description="First clone source"),
        ]
        format_name: Annotated[
            t.NonEmptyStr,
            m.Field(alias="format", description="jscpd parser format name"),
        ]
        fragment: Annotated[
            t.NonEmptyStr,
            m.Field(description="Duplicated source fragment"),
        ]
        is_new: Annotated[
            t.StrictBool,
            m.Field(
                alias="isNew",
                description=(
                    "Whether jscpd marked the clone new; the flag is absent from "
                    "some jscpd report versions and defaults to False"
                ),
            ),
        ] = False
        kind: Annotated[
            t.NonEmptyStr,
            m.Field(
                description=(
                    "jscpd clone classification; the field is absent from some "
                    "jscpd report versions and defaults to 'exact'"
                ),
            ),
        ] = "exact"
        lines: Annotated[
            t.PositiveInt,
            m.Field(description="Duplicated logical line count"),
        ]
        second_file: Annotated[
            FlextInfraModelsDuplication.JscpdFile,
            m.Field(alias="secondFile", description="Second clone source"),
        ]
        tokens: Annotated[t.PositiveInt, m.Field(description="Duplicated token count")]
        similarity: Annotated[
            float | None,
            m.Field(description="Score of a similar or semantic clone"),
        ] = None
        method: Annotated[
            t.NonEmptyStr | None,
            m.Field(description="Near-miss mechanism of a similar clone"),
        ] = None

    class JscpdStatisticsSummary(m.ContractModel):
        """Complete aggregate emitted for one format or the whole scan."""

        model_config: ClassVar[m.ConfigDict] = m.ConfigDict(
            extra="forbid",
            frozen=True,
            populate_by_name=True,
        )

        clones: Annotated[t.NonNegativeInt, m.Field(description="Detected clone count")]
        duplicated_lines: Annotated[
            t.NonNegativeInt,
            m.Field(alias="duplicatedLines", description="Duplicated line count"),
        ]
        duplicated_tokens: Annotated[
            t.NonNegativeInt,
            m.Field(alias="duplicatedTokens", description="Duplicated token count"),
        ]
        lines: Annotated[
            t.NonNegativeInt,
            m.Field(description="Scanned logical line count"),
        ]
        new_clones: Annotated[
            t.NonNegativeInt,
            m.Field(alias="newClones", description="New clone count"),
        ]
        new_duplicated_lines: Annotated[
            t.NonNegativeInt,
            m.Field(
                alias="newDuplicatedLines",
                description="New duplicated line count",
            ),
        ]
        percentage: Annotated[
            t.Percentage,
            m.Field(description="Duplicated line percentage"),
        ]
        percentage_tokens: Annotated[
            t.Percentage,
            m.Field(
                alias="percentageTokens",
                description="Duplicated token percentage",
            ),
        ]
        sources: Annotated[
            t.NonNegativeInt,
            m.Field(description="Scanned source file count"),
        ]
        tokens: Annotated[t.NonNegativeInt, m.Field(description="Scanned token count")]

    class JscpdStatistics(m.ContractModel):
        """Per-format and total statistics proving non-empty collection."""

        model_config: ClassVar[m.ConfigDict] = m.ConfigDict(
            extra="forbid",
            frozen=True,
            populate_by_name=True,
        )

        detection_date: Annotated[
            t.NonEmptyStr,
            m.Field(alias="detectionDate", description="jscpd detection timestamp"),
        ]
        formats: Annotated[
            t.MappingKV[str, FlextInfraModelsDuplication.JscpdStatisticsSummary],
            m.Field(description="Statistics keyed by parsed source format"),
        ]
        total: Annotated[
            FlextInfraModelsDuplication.JscpdStatisticsSummary,
            m.Field(description="Aggregate scan statistics"),
        ]

    class JscpdReport(m.ContractModel):
        """Validated complete jscpd JSON report."""

        duplicates: Annotated[
            t.SequenceOf[FlextInfraModelsDuplication.JscpdDuplicate],
            m.Field(description="Complete detected clone records"),
        ]
        statistics: Annotated[
            FlextInfraModelsDuplication.JscpdStatistics,
            m.Field(description="Validated scan statistics"),
        ]

        @m.model_validator(mode="after")
        def _validate_complete_report(self) -> Self:
            format_summaries = tuple(self.statistics.formats.values())
            if not format_summaries or self.statistics.total.sources == 0:
                msg = "jscpd report collected zero source files"
                raise ValueError(msg)
            if (
                sum(item.sources for item in format_summaries)
                != self.statistics.total.sources
            ):
                msg = "jscpd per-format source count does not match total"
                raise ValueError(msg)
            if (
                sum(item.clones for item in format_summaries)
                != self.statistics.total.clones
            ):
                msg = "jscpd per-format clone count does not match total"
                raise ValueError(msg)
            if self.statistics.total.clones != len(self.duplicates):
                msg = "jscpd duplicate records do not match the reported clone total"
                raise ValueError(msg)
            for duplicate in self.duplicates:
                for source in (duplicate.first_file, duplicate.second_file):
                    if not Path(source.name).is_absolute():
                        msg = (
                            f"jscpd reported a non-absolute source path: {source.name}"
                        )
                        raise ValueError(msg)
            return self

    class DuplicationSpanMeasure(m.ContractModel):
        """Structural measurement, never a semantic exemption or oracle proof."""

        source: str = m.Field(description="Physical source path")
        sha256: str = m.Field(description="Digest of the complete bytes read")
        lines: t.NonNegativeInt = m.Field(
            description="Physical lines with retained tokens"
        )
        tokens: t.NonNegativeInt = m.Field(description="Retained Python lexical tokens")
        runs: tuple[tuple[int, int, int], ...] = m.Field(
            description="Contiguous retained line runs: start, end, token count",
        )
        removed: tuple[str, ...] = m.Field(description="Removed structural categories")
        uncertainty: str = m.Field(description="Unproven import or annotation effects")

    class DuplicationClassification(m.ContractModel):
        """Typed disposition vocabulary with a mandatory evidence reason."""

        disposition: Literal[
            "non_behavioral_only",
            "below_existing_behavior_floor",
            "behavioral_candidate",
            "authority_data_candidate",
            "unresolved",
            "analysis_error",
        ] = m.Field(description="Conservative explanation, not a gate exemption")
        reason: t.NonEmptyStr = m.Field(
            description="Evidence or causal analysis failure"
        )

    class DuplicationCandidateEvidence(DuplicationClassification):
        """One immutable-index link to every scanner candidate, including mirrors."""

        index: t.NonNegativeInt = m.Field(description="Zero-based raw inventory index")
        canonical_index: t.NonNegativeInt = m.Field(
            description="First unordered span pair index"
        )
        candidate: FlextInfraModelsDuplication.JscpdDuplicate = m.Field(
            description="Unmodified typed scanner candidate",
        )
        owned: bool = m.Field(description="At least one side belongs to the project")
        self_span: bool = m.Field(description="Both sides name the identical span")
        measures: tuple[FlextInfraModelsDuplication.DuplicationSpanMeasure, ...] = (
            m.Field(
                description="Both measured spans when analysis succeeds",
            )
        )

    class DuplicationAssessment(m.ContractModel):
        """Lossless sidecar; raw-hard remains the only acceptance contract."""

        policy: Literal["structural-evidence-v1-raw-hard"] = m.Field(
            description="Versioned non-promoting policy"
        )
        raw_sha256: str = m.Field(description="Digest of the exact published receipt")
        report: FlextInfraModelsDuplication.JscpdReport = m.Field(
            description="Complete raw typed inventory and counters"
        )
        candidates: tuple[
            FlextInfraModelsDuplication.DuplicationCandidateEvidence, ...
        ] = m.Field(description="One explanation per raw candidate")
        min_lines: t.PositiveInt = m.Field(description="Selected existing line floor")
        min_tokens: t.PositiveInt = m.Field(description="Selected existing token floor")
        duration_seconds: float = m.Field(
            ge=0, description="Measured analysis wall time"
        )
        source_count: t.NonNegativeInt = m.Field(
            description="Unique complete sources read"
        )
        counts: t.MappingKV[str, int] = m.Field(
            description="Disposition and ownership counters"
        )
        execution: str = m.Field(
            description="Scanner status, timeout, signal and pass availability"
        )
        source_provenance: str = m.Field(
            description="Limits of source binding to the scanner snapshot",
        )
        budget_status: str = m.Field(
            description="Budget verification status; absence never authorizes promotion"
        )

        @m.model_validator(mode="after")
        def _validate_inventory(self) -> Self:
            if tuple(item.index for item in self.candidates) != tuple(
                range(len(self.report.duplicates))
            ):
                msg = "assessment must preserve every raw candidate in order"
                raise ValueError(msg)
            if any(
                item.candidate != self.report.duplicates[item.index]
                for item in self.candidates
            ):
                msg = "assessment candidate differs from raw inventory"
                raise ValueError(msg)
            return self

    class JscpdScan(m.ContractModel):
        """Fresh command evidence plus its validated report."""

        exit_code: Annotated[
            t.NonNegativeInt,
            m.Field(le=255, description="Raw jscpd process exit code"),
        ]
        report: Annotated[
            FlextInfraModelsDuplication.JscpdReport,
            m.Field(description="Validated report from this exact scan"),
        ]
        stderr: Annotated[str, m.Field(description="Raw jscpd standard error")]
        stdout: Annotated[str, m.Field(description="Raw jscpd standard output")]


__all__: list[str] = ["FlextInfraModelsDuplication"]
