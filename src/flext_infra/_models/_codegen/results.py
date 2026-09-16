"""Result and accumulator models for the codegen fix pipeline domain."""

from __future__ import annotations

from collections.abc import MutableSet
from typing import Annotated, ClassVar, Literal

from flext_cli import m, u

from ... import t
from .. import FlextInfraModelsMixins as mm
from .census import FlextInfraModelsCodegenCensus


class FlextInfraModelsCodegenResults:
    """Private codegen results model domain partial."""

    class ScaffoldResult(mm.ProjectNameMixin, m.ArbitraryTypesModel):
        """Result of scaffolding base modules for a project.

        Enforcement exemption: internal tooling model with intentional
        mutable state.
        """

        files_created: t.StrSequence = m.Field(
            default_factory=tuple, description="Newly created file paths"
        )
        files_skipped: t.StrSequence = m.Field(
            default_factory=tuple, description="Skipped (already existing) file paths"
        )

    class AutoFixResult(mm.ProjectNameMixin, m.ArbitraryTypesModel):
        """Result of auto-fixing namespace violations for a project."""

        @staticmethod
        def _violations_default() -> t.SequenceOf[
            FlextInfraModelsCodegenCensus.CensusViolation
        ]:
            """Violations default."""
            return []

        violations_fixed: Annotated[
            t.SequenceOf[FlextInfraModelsCodegenCensus.CensusViolation],
            m.Field(
                default_factory=_violations_default, description="Fixed violations"
            ),
        ]
        violations_skipped: Annotated[
            t.SequenceOf[FlextInfraModelsCodegenCensus.CensusViolation],
            m.Field(
                default_factory=_violations_default,
                description="Skipped violations (not auto-fixable)",
            ),
        ]
        files_modified: t.StrSequence = m.Field(
            default_factory=tuple, description="Modified file paths"
        )

    class ConsolidatorFileResult(m.ContractModel):
        """Per-file result emitted by the constants consolidator."""

        file: Annotated[
            t.NonEmptyStr, m.Field(description="Workspace-relative file path")
        ]
        status: Annotated[
            Literal["applied", "reverted"],
            m.Field(description="File processing status"),
        ]
        changes: Annotated[
            t.StrSequence,
            m.Field(default_factory=tuple, description="Applied replacements"),
        ]

    class ConsolidatorReport(m.ContractModel):
        """JSON report emitted by the constants consolidator."""

        total_found: Annotated[
            t.NonNegativeInt, m.Field(description="Total replacements found")
        ] = 0
        total_applied: Annotated[
            t.NonNegativeInt, m.Field(description="Total replacements applied")
        ] = 0
        total_failed: Annotated[
            t.NonNegativeInt, m.Field(description="Total files reverted")
        ] = 0
        files: Annotated[
            t.SequenceOf[FlextInfraModelsCodegenResults.ConsolidatorFileResult],
            m.Field(default_factory=tuple, description="Per-file processing results"),
        ]

    class QualityGateCheck(m.ArbitraryTypesModel):
        """A single quality gate check result entry."""

        name: Annotated[t.NonEmptyStr, m.Field(description="Check identifier")]
        passed: Annotated[bool, m.Field(description="Whether check passed")]
        detail: Annotated[str, m.Field(description="Human-readable check detail")] = ""
        critical: Annotated[bool, m.Field(description="Whether failure is critical")]

    class QualityGateProjectFinding(mm.ProjectNameMixin, m.ArbitraryTypesModel):
        """Per-project quality gate findings."""

        violations_total: Annotated[
            t.NonNegativeInt, m.Field(description="Total violations")
        ]
        fixable_violations: Annotated[
            t.NonNegativeInt, m.Field(description="Auto-fixable violations")
        ]
        validator_passed: Annotated[
            bool, m.Field(description="Whether validator passed")
        ]
        flext_failures: Annotated[
            t.NonNegativeInt, m.Field(description="FLEXT failure count")
        ]
        layer_violations: Annotated[
            t.NonNegativeInt, m.Field(description="Layer violation count")
        ]
        cross_project_reference_violations: Annotated[
            t.NonNegativeInt,
            m.Field(description="Cross-project reference violation count"),
        ]

    class BulkFixItem(
        mm.AbsoluteFilePathTextMixin, mm.PositiveLineMixin, m.ArbitraryTypesModel
    ):
        """Shared line-addressable item used by bulk codegen fixes."""

        name: Annotated[t.NonEmptyStr, m.Field(description="Item identifier")]

    class ConstantDefinition(mm.ProjectNameMixin, mm.NestedClassPathMixin, BulkFixItem):
        """A single constant extracted from a constants.py file."""

        value_repr: Annotated[
            str, m.Field(description="Source repr (e.g., '30', '\"localhost\"')")
        ]
        type_annotation: Annotated[
            str, m.Field(description="Type annotation string")
        ] = ""

    class DuplicateConstantGroup(m.ArbitraryTypesModel):
        """Cross-project duplicate group with consolidation metadata."""

        constant_name: t.NonEmptyStr = m.Field(description="Constant identifier")
        definitions: t.SequenceOf[FlextInfraModelsCodegenResults.ConstantDefinition] = (
            m.Field(description="Definitions across projects")
        )
        is_value_identical: bool = m.Field(description="Whether all values match")
        canonical_ref: Annotated[
            str, m.Field(description="Canonical parent reference")
        ] = ""

    class DirectConstantRef(mm.ProjectNameMixin, m.ArbitraryTypesModel):
        """Direct FlextXConstants.Y.Z reference that should use c.* alias."""

        full_ref: Annotated[
            t.NonEmptyStr,
            m.Field(description="e.g., FlextAuthConstants.Auth.DEFAULT_TIMEOUT"),
        ]
        alias_ref: Annotated[
            t.NonEmptyStr, m.Field(description="e.g., c.Auth.DEFAULT_TIMEOUT")
        ]
        file_path: Annotated[
            t.NonEmptyStr, m.Field(description="File containing the reference")
        ]
        line: Annotated[t.PositiveInt, m.Field(description="Line number")]

    class FixContext(m.ArbitraryTypesModel):
        """Mutable accumulation context for fix operations.

        Enforcement exemption: MutableSequence/MutableSet accumulators are
        appended/added to as fixes proceed; fresh per-instance — no shared
        state.
        """

        @staticmethod
        def _violations_default() -> list[
            FlextInfraModelsCodegenCensus.CensusViolation
        ]:
            """Violations default."""
            return []

        violations_fixed: Annotated[
            t.MutableSequenceOf[FlextInfraModelsCodegenCensus.CensusViolation],
            m.Field(
                default_factory=_violations_default,
                description="List of violations that were fixed",
            ),
        ] = m.Field(
            default_factory=_violations_default,
            description="List of violations that were fixed",
        )
        violations_skipped: Annotated[
            t.MutableSequenceOf[FlextInfraModelsCodegenCensus.CensusViolation],
            m.Field(
                default_factory=_violations_default,
                description="List of violations that were skipped",
            ),
        ] = m.Field(
            default_factory=_violations_default,
            description="List of violations that were skipped",
        )
        files_modified: Annotated[
            MutableSet[str],
            m.Field(
                default_factory=set, description="Set of unique modified file paths"
            ),
        ] = m.Field(
            default_factory=set, description="Set of unique modified file paths"
        )

        @property
        def has_changes(self) -> bool:
            """Whether at least one file was modified."""
            return bool(self.files_modified)

        def skip(self, *, module: str, rule: str, line: int, message: str) -> None:
            """Skip."""
            self.violations_skipped.append(
                FlextInfraModelsCodegenCensus.CensusViolation(
                    module=module, rule=rule, line=line, message=message, fixable=False
                )
            )

        def fix(self, *, module: str, rule: str, line: int, message: str) -> None:
            """Fix."""
            self.violations_fixed.append(
                FlextInfraModelsCodegenCensus.CensusViolation(
                    module=module, rule=rule, line=line, message=message, fixable=True
                )
            )

    class ViolationKey(m.ContractModel):
        """Content-stable violation identifier — resilient to line shifts."""

        model_config: ClassVar[m.ConfigDict] = m.ConfigDict(frozen=True, extra="forbid")

        module: Annotated[str, m.Field(description="Module containing the violation")]
        rule: Annotated[str, m.Field(description="Rule that was violated")]
        content_hash: Annotated[
            str, m.Field(description="SHA256 of surrounding context lines")
        ]

        def __hash__(self) -> int:
            """Hash by stable business identity so keys work in sets and frozensets."""
            return hash((self.module, self.rule, self.content_hash))

        @staticmethod
        def from_violation(
            violation: FlextInfraModelsCodegenCensus.CensusViolation,
            source_lines: t.StrSequence,
        ) -> FlextInfraModelsCodegenResults.ViolationKey:
            """Build key from violation and source context (+-2 lines)."""
            ctx_start = max(0, violation.line - 2)
            ctx_end = min(len(source_lines), violation.line + 3)
            context = "\n".join(source_lines[ctx_start:ctx_end])
            content_hash = u.Cli.sha256_content(context)
            return FlextInfraModelsCodegenResults.ViolationKey(
                module=violation.module, rule=violation.rule, content_hash=content_hash
            )
