"""Deduplication models for codegen constant consolidation."""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
from typing import Annotated

from pydantic import Field

from flext_core import FlextModels
from flext_infra import t
from flext_infra._models.mixins import FlextInfraModelsMixins


class FlextInfraCodegenDeduplicationModels:
    """Typed contracts for constant deduplication workflows."""

    class DeduplicationCandidate(FlextModels.ArbitraryTypesModel):
        """One constant candidate grouped by shared value."""

        name: Annotated[t.NonEmptyStr, Field(description="Constant name")]
        type_annotation: Annotated[
            str,
            Field(default="", description="Original type annotation"),
        ]
        usages: Annotated[
            t.NonNegativeInt,
            Field(default=0, description="Observed usage count"),
        ] = 0

        def render_text(self) -> str:
            """Render a compact CLI-facing summary line."""
            return f"{self.name} ({self.usages} uses)"

    class DeduplicationFixProposal(FlextModels.ArbitraryTypesModel):
        """One deduplication plan for a duplicated constant value."""

        value_repr: Annotated[
            str,
            Field(default="", description="Normalized source representation"),
        ]
        canonical: FlextInfraCodegenDeduplicationModels.DeduplicationCandidate = Field(
            description="Canonical constant kept after replacement",
        )
        duplicates: tuple[
            FlextInfraCodegenDeduplicationModels.DeduplicationCandidate, ...
        ] = Field(
            default_factory=tuple,
            description="Duplicate constants replaced by canonical",
        )
        total_occurrences: Annotated[
            t.PositiveInt,
            Field(description="Total constants that shared the same value"),
        ]

        def impact_score(self) -> int:
            """Rank proposals by likely benefit."""
            return self.canonical.usages * len(self.duplicates)

        def preview_value(self, *, limit: int = 50) -> str:
            """Return a short preview suitable for CLI output."""
            return self.value_repr[:limit]

        def render_header(self, *, index: int) -> str:
            """Render the proposal headline for CLI output."""
            return (
                f"{index}. Value: {self.preview_value()}"
                f" | Keep: {self.canonical.render_text()}"
                f" | Replace {len(self.duplicates)} others"
            )

        def render_duplicate_lines(self) -> Sequence[str]:
            """Render duplicate detail lines for CLI output."""
            return tuple(
                f"   - {duplicate.render_text()}" for duplicate in self.duplicates
            )

    class DeduplicationReplacement(FlextModels.ArbitraryTypesModel):
        """One concrete replacement emitted while applying a proposal."""

        file_path: Annotated[
            t.NonEmptyStr,
            Field(description="Changed file path"),
        ]
        line: Annotated[
            t.NonNegativeInt,
            Field(default=0, description="Best-known affected line"),
        ] = 0
        old_name: Annotated[
            t.NonEmptyStr,
            Field(description="Replaced constant name"),
        ]

    class DeduplicationApplyResult(
        FlextInfraModelsMixins.DryRunTrueMixin,
        FlextModels.ArbitraryTypesModel,
    ):
        """Effect of applying one deduplication proposal."""

        canonical_name: Annotated[
            t.NonEmptyStr,
            Field(description="Canonical constant kept after rename"),
        ]
        replaced_names: t.StrSequence = Field(
            default_factory=tuple,
            description="Duplicate constant names replaced by canonical",
        )
        replacements: tuple[
            FlextInfraCodegenDeduplicationModels.DeduplicationReplacement, ...
        ] = Field(default_factory=tuple, description="Concrete per-file replacements")
        files_modified: t.NonNegativeInt = Field(
            default=0,
            description="Touched files count",
        )

        def render_summary(self) -> str:
            """Render the per-proposal application summary."""
            return (
                f"  {self.canonical_name}: replaced {len(self.replaced_names)}"
                f" in {self.files_modified} files"
            )

    class DeduplicationRunOptions(
        FlextInfraModelsMixins.DryRunTrueMixin,
        FlextModels.ArbitraryTypesModel,
    ):
        """Validated options for the deduplication workflow."""

        class_path: Annotated[
            t.NonEmptyStr,
            Field(description="Fully qualified constants facade path"),
        ]
        root_path: Annotated[
            Path,
            Field(description="Workspace root used for scanning and renames"),
        ]
        max_files: t.NonNegativeInt = Field(
            default=2000,
            description="Maximum files scanned for usages",
        )
        exclude_patterns: frozenset[str] = Field(
            default_factory=frozenset,
            description="Directory names excluded from usage scanning",
        )

    class DeduplicationRunReport(
        FlextInfraModelsMixins.DryRunTrueMixin,
        FlextModels.ArbitraryTypesModel,
    ):
        """Typed report emitted by the deduplication workflow."""

        class_path: Annotated[
            t.NonEmptyStr,
            Field(description="Analyzed constants facade path"),
        ]
        proposals: tuple[
            FlextInfraCodegenDeduplicationModels.DeduplicationFixProposal, ...
        ] = Field(
            default_factory=tuple, description="Identified deduplication proposals"
        )
        applied: tuple[
            FlextInfraCodegenDeduplicationModels.DeduplicationApplyResult,
            ...,
        ] = Field(
            default_factory=tuple,
            description="Application results for each proposal",
        )
        total_files_modified: t.NonNegativeInt = Field(
            default=0,
            description="Total files touched across proposals",
        )

        def render_text(self) -> str:
            """Render a concise CLI-oriented report."""
            if not self.proposals:
                return "No duplicates found"

            lines: list[str] = [
                f"Found {len(self.proposals)} groups of duplicate constants",
                "",
            ]
            for index, proposal in enumerate(self.proposals, 1):
                lines.append(proposal.render_header(index=index))
                lines.extend(proposal.render_duplicate_lines())

            if self.applied:
                lines.extend((
                    "",
                    f"Applying {len(self.applied)} deduplication fixes...",
                ))
                lines.extend(result.render_summary() for result in self.applied)

            lines.append("")
            if self.dry_run:
                lines.append(
                    f"[DRY-RUN] Would modify {self.total_files_modified} files"
                )
            else:
                lines.append(f"Modified {self.total_files_modified} files")
            return "\n".join(lines)


__all__ = ["FlextInfraCodegenDeduplicationModels"]
