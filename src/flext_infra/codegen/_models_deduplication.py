"""Deduplication models for codegen constant consolidation."""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
from typing import Annotated

from pydantic import Field

from flext_core import FlextModels
from flext_infra import t


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
        canonical: Annotated[
            FlextInfraCodegenDeduplicationModels.DeduplicationCandidate,
            Field(description="Canonical constant kept after replacement"),
        ]
        duplicates: Annotated[
            Sequence[FlextInfraCodegenDeduplicationModels.DeduplicationCandidate],
            Field(description="Duplicate constants replaced by canonical"),
        ] = Field(default_factory=tuple)
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

    class DeduplicationApplyResult(FlextModels.ArbitraryTypesModel):
        """Effect of applying one deduplication proposal."""

        canonical_name: Annotated[
            t.NonEmptyStr,
            Field(description="Canonical constant kept after rename"),
        ]
        replaced_names: Annotated[
            t.StrSequence,
            Field(description="Duplicate constant names replaced by canonical"),
        ] = Field(default_factory=tuple)
        replacements: Annotated[
            Sequence[FlextInfraCodegenDeduplicationModels.DeduplicationReplacement],
            Field(description="Concrete per-file replacements"),
        ] = Field(default_factory=tuple)
        files_modified: Annotated[
            t.NonNegativeInt,
            Field(default=0, description="Touched files count"),
        ] = 0
        dry_run: Annotated[
            bool,
            Field(default=True, description="Whether no writes were performed"),
        ] = True

        def render_summary(self) -> str:
            """Render the per-proposal application summary."""
            return (
                f"  {self.canonical_name}: replaced {len(self.replaced_names)}"
                f" in {self.files_modified} files"
            )

    class DeduplicationRunOptions(FlextModels.ArbitraryTypesModel):
        """Validated options for the deduplication workflow."""

        class_path: Annotated[
            t.NonEmptyStr,
            Field(description="Fully qualified constants facade path"),
        ]
        root_path: Annotated[
            Path,
            Field(description="Workspace root used for scanning and renames"),
        ]
        dry_run: Annotated[
            bool,
            Field(default=True, description="Whether writes should be skipped"),
        ] = True
        max_files: Annotated[
            t.NonNegativeInt,
            Field(default=2000, description="Maximum files scanned for usages"),
        ] = 2000
        exclude_patterns: Annotated[
            frozenset[str],
            Field(description="Directory names excluded from usage scanning"),
        ] = Field(default_factory=frozenset)

    class DeduplicationRunReport(FlextModels.ArbitraryTypesModel):
        """Typed report emitted by the deduplication workflow."""

        class_path: Annotated[
            t.NonEmptyStr,
            Field(description="Analyzed constants facade path"),
        ]
        dry_run: Annotated[
            bool,
            Field(default=True, description="Whether writes were skipped"),
        ] = True
        proposals: Annotated[
            Sequence[FlextInfraCodegenDeduplicationModels.DeduplicationFixProposal],
            Field(description="Identified deduplication proposals"),
        ] = Field(default_factory=tuple)
        applied: Annotated[
            Sequence[FlextInfraCodegenDeduplicationModels.DeduplicationApplyResult],
            Field(description="Application results for each proposal"),
        ] = Field(default_factory=tuple)
        total_files_modified: Annotated[
            t.NonNegativeInt,
            Field(default=0, description="Total files touched across proposals"),
        ] = 0

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
