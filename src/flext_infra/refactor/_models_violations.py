"""Violation and helper classification models for the refactor subpackage."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Annotated, ClassVar

from pydantic import ConfigDict, Field

from flext_core import m
from flext_infra import t


class FlextInfraRefactorModelsViolations:
    """Class-nesting violation, helper classification, and analysis report models."""

    class ClassNestingMapping(m.ArbitraryTypesModel):
        """Unified mapping contract for class-nesting rewrite planning."""

        model_config: ClassVar[ConfigDict] = ConfigDict(extra="ignore", frozen=True)

        loose_name: Annotated[
            str,
            Field(default="", description="Original loose class name"),
        ] = ""
        current_file: Annotated[
            str,
            Field(default="", description="File containing class"),
        ] = ""
        target_namespace: Annotated[
            t.NonEmptyStr,
            Field(description="Target namespace class name"),
        ]
        target_name: Annotated[
            str,
            Field(default="", description="Target class name"),
        ] = ""
        confidence: Annotated[t.NonEmptyStr, Field(description="Confidence level")]
        reason: Annotated[
            str,
            Field(default="", description="Optional mapping rationale"),
        ] = ""
        rewrite_scope: Annotated[
            str | None,
            Field(default=None, description="Rewrite scope (file/project/workspace)"),
        ] = None

    class ClassNestingViolation(m.ArbitraryTypesModel):
        """Normalized class-nesting violation with rewrite metadata."""

        model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True)

        file: Annotated[t.NonEmptyStr, Field(description="Source module path")]
        line: Annotated[t.PositiveInt, Field(description="Line number")]
        class_name: Annotated[t.NonEmptyStr, Field(description="Class name")]
        target_namespace: Annotated[
            str,
            Field(default="", description="Expected namespace class"),
        ] = ""
        confidence: Annotated[
            str,
            Field(default="low", description="Confidence level"),
        ] = "low"
        rewrite_scope: Annotated[
            str,
            Field(default="file", description="Rewrite scope"),
        ] = "file"

    class ClassNestingPolicy(m.FrozenStrictModel):
        """Validated policy contract used by class-nesting transformers."""

        model_config: ClassVar[ConfigDict] = ConfigDict(extra="ignore", frozen=True)

        family_name: Annotated[t.NonEmptyStr, Field(description="Module family name")]
        allowed_operations: Annotated[
            t.StrSequence,
            Field(description="Enabled operation identifiers for this family"),
        ] = Field(default_factory=list)
        forbidden_operations: Annotated[
            t.StrSequence,
            Field(description="Disabled operation identifiers for this family"),
        ] = Field(default_factory=list)
        forbidden_targets: Annotated[
            t.StrSequence,
            Field(description="Target namespaces forbidden for this family"),
        ] = Field(default_factory=list)
        enable_class_nesting: Annotated[
            bool,
            Field(
                default=True,
                description="Allow moving top-level classes under a namespace",
            ),
        ]
        allow_namespace_creation: Annotated[
            bool,
            Field(
                default=True,
                description="Allow creating a target namespace when absent",
            ),
        ]
        allow_existing_namespace_merge: Annotated[
            bool,
            Field(
                default=True,
                description="Allow merging nested classes into existing namespace",
            ),
        ]
        enable_helper_consolidation: Annotated[
            bool,
            Field(
                default=True,
                description="Allow consolidating helper functions into namespaces",
            ),
        ]
        allow_helper_call_rewrite: Annotated[
            bool,
            Field(
                default=True,
                description="Allow rewriting helper call sites to namespaced calls",
            ),
        ]
        require_signature_validation: Annotated[
            bool,
            Field(
                default=False,
                description="Require signature checks before helper migration",
            ),
        ]
        required_parameters: Annotated[
            t.StrSequence,
            Field(
                description="Function parameters that must exist in helper signatures"
            ),
        ] = Field(default_factory=list)
        forbidden_parameters: Annotated[
            t.StrSequence,
            Field(
                description="Function parameters that must not exist in helper signatures"
            ),
        ] = Field(default_factory=list)
        allow_vararg: Annotated[
            bool,
            Field(
                default=True, description="Allow variadic positional parameter usage"
            ),
        ]
        allow_kwarg: Annotated[
            bool,
            Field(default=True, description="Allow variadic keyword parameter usage"),
        ]
        allow_positional_only_params: Annotated[
            bool,
            Field(default=True, description="Allow positional-only parameters"),
        ]
        allow_keyword_only_params: Annotated[
            bool,
            Field(default=True, description="Allow keyword-only parameters"),
        ]
        propagate_imports: Annotated[
            bool,
            Field(default=True, description="Allow propagating import rewrite rules"),
        ]
        propagate_name_references: Annotated[
            bool,
            Field(
                default=True,
                description="Allow propagating direct name reference rewrites",
            ),
        ]
        propagate_attribute_references: Annotated[
            bool,
            Field(
                default=True,
                description="Allow propagating attribute reference rewrites",
            ),
        ]
        blocked_reference_prefixes: Annotated[
            t.StrSequence,
            Field(description="Name prefixes blocked from rewrite propagation"),
        ] = Field(default_factory=list)
        allowed_targets: Annotated[
            t.StrSequence,
            Field(description="Explicitly allowed target namespaces"),
        ] = Field(default_factory=list)

    class ClassNestingReport(m.ArbitraryTypesModel):
        """Aggregated class-nesting analysis report."""

        violations_count: Annotated[
            t.NonNegativeInt,
            Field(description="Total violations"),
        ]
        confidence_counts: Annotated[
            t.IntMapping,
            Field(description="Confidence histogram"),
        ] = Field(default_factory=dict)
        violations: Annotated[
            Sequence[FlextInfraRefactorModelsViolations.ClassNestingViolation],
            Field(description="Violation details"),
        ] = Field(default_factory=lambda: ())
        per_file_counts: Annotated[
            t.IntMapping,
            Field(description="Violation counts per file"),
        ] = Field(default_factory=dict)

    class HelperClassification(m.ArbitraryTypesModel):
        """Classification result for a helper function."""

        file: Annotated[t.NonEmptyStr, Field(description="Source file")]
        function: Annotated[t.NonEmptyStr, Field(description="Function name")]
        category: Annotated[t.NonEmptyStr, Field(description="Assigned category")]
        target_namespace: Annotated[
            t.NonEmptyStr,
            Field(description="Target namespace path"),
        ]
        dependencies: Annotated[
            t.StrSequence,
            Field(description="Imported dependencies used by function"),
        ] = Field(default_factory=list)
        manual_review: Annotated[
            bool,
            Field(default=False, description="Whether manual review is required"),
        ]
        review_reason: Annotated[
            str,
            Field(default="", description="Manual review rationale"),
        ]

    class HelperClassificationReport(m.ArbitraryTypesModel):
        """Aggregated helper-function classification payload."""

        totals: Annotated[
            t.IntMapping,
            Field(description="Category totals"),
        ] = Field(default_factory=dict)
        suggestions: Annotated[
            Sequence[FlextInfraRefactorModelsViolations.HelperClassification],
            Field(description="Classification suggestions"),
        ] = Field(default_factory=lambda: ())
        manual_review: Annotated[
            Sequence[FlextInfraRefactorModelsViolations.HelperClassification],
            Field(description="Manual-review candidates"),
        ] = Field(default_factory=lambda: ())

    class HelperFileAnalysis(m.ArbitraryTypesModel):
        suggestions: Annotated[
            Sequence[FlextInfraRefactorModelsViolations.HelperClassification],
            Field(description="Helper classifications from one file"),
        ] = Field(default_factory=lambda: ())
        totals: Annotated[
            t.IntMapping,
            Field(description="Category totals for file helpers"),
        ] = Field(default_factory=dict)
        manual_review: Annotated[
            Sequence[FlextInfraRefactorModelsViolations.HelperClassification],
            Field(description="Helpers requiring manual review"),
        ] = Field(default_factory=lambda: ())

    class ViolationTopFileSection(m.ArbitraryTypesModel):
        """One ranked hotspot entry in violation analysis output."""

        file: Annotated[t.NonEmptyStr, Field(description="File path")]
        total: Annotated[
            t.NonNegativeInt,
            Field(description="Total violations in file"),
        ]
        counts: Annotated[
            t.IntMapping,
            Field(description="Per-pattern counts"),
        ] = Field(default_factory=dict)

    class ViolationAnalysisReport(m.ArbitraryTypesModel):
        """Full violation analysis report for refactor diagnostics."""

        totals: Annotated[
            t.IntMapping,
            Field(description="Aggregate counts by pattern"),
        ] = Field(default_factory=dict)
        files: Annotated[
            Mapping[str, t.IntMapping],
            Field(description="Per-file per-pattern counts"),
        ] = Field(default_factory=dict)
        top_files: Annotated[
            Sequence[FlextInfraRefactorModelsViolations.ViolationTopFileSection],
            Field(description="Top hotspot files"),
        ] = Field(default_factory=lambda: ())
        files_scanned: Annotated[t.NonNegativeInt, Field(description="Files scanned")]
        helper_classification: Annotated[
            FlextInfraRefactorModelsViolations.HelperClassificationReport,
            Field(description="Helper classification summary"),
        ]
        class_nesting: Annotated[
            FlextInfraRefactorModelsViolations.ClassNestingReport,
            Field(description="Class nesting analysis summary"),
        ]


__all__ = ["FlextInfraRefactorModelsViolations"]
