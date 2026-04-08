"""Violation and helper classification models for the refactor subpackage."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Annotated, ClassVar

from pydantic import ConfigDict, Field

from flext_core import m
from flext_infra import t
from flext_infra._models.mixins import FlextInfraModelsMixins


class FlextInfraRefactorModelsViolations:
    """Class-nesting violation, helper classification, and analysis report models."""

    class ClassNestingMapping(m.ArbitraryTypesModel):
        """Unified mapping contract for class-nesting rewrite planning."""

        model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True)

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

    class ClassNestingViolation(
        FlextInfraModelsMixins.ConfidenceLevelMixin,
        FlextInfraModelsMixins.RewriteScopeMixin,
        FlextInfraModelsMixins.FileLineViolationMixin,
        m.ArbitraryTypesModel,
    ):
        """Normalized class-nesting violation with rewrite metadata."""

        model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True)
        class_name: Annotated[t.NonEmptyStr, Field(description="Class name")]
        target_namespace: Annotated[
            str,
            Field(default="", description="Expected namespace class"),
        ] = ""

    class ClassNestingPolicy(m.ContractModel):
        """Validated policy contract used by class-nesting transformers."""

        model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True)

        family_name: Annotated[t.NonEmptyStr, Field(description="Module family name")]
        allowed_operations: t.StrSequence = Field(
            default_factory=list,
            description="Enabled operation identifiers for this family",
        )
        forbidden_operations: t.StrSequence = Field(
            default_factory=list,
            description="Disabled operation identifiers for this family",
        )
        forbidden_targets: t.StrSequence = Field(
            default_factory=list,
            description="Target namespaces forbidden for this family",
        )
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
        required_parameters: t.StrSequence = Field(
            default_factory=list,
            description="Function parameters that must exist in helper signatures",
        )
        forbidden_parameters: t.StrSequence = Field(
            default_factory=list,
            description="Function parameters that must not exist in helper signatures",
        )
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
        blocked_reference_prefixes: t.StrSequence = Field(
            default_factory=list,
            description="Name prefixes blocked from rewrite propagation",
        )
        allowed_targets: t.StrSequence = Field(
            default_factory=list, description="Explicitly allowed target namespaces"
        )

    class ClassNestingReport(m.ArbitraryTypesModel):
        """Aggregated class-nesting analysis report."""

        violations_count: Annotated[
            t.NonNegativeInt,
            Field(description="Total violations"),
        ]
        confidence_counts: t.IntMapping = Field(
            default_factory=dict, description="Confidence histogram"
        )
        violations: tuple[
            FlextInfraRefactorModelsViolations.ClassNestingViolation,
            ...,
        ] = Field(default_factory=tuple, description="Violation details")
        per_file_counts: t.IntMapping = Field(
            default_factory=dict, description="Violation counts per file"
        )

    class HelperClassification(m.ArbitraryTypesModel):
        """Classification result for a helper function."""

        file: Annotated[t.NonEmptyStr, Field(description="Source file")]
        function: Annotated[t.NonEmptyStr, Field(description="Function name")]
        category: Annotated[t.NonEmptyStr, Field(description="Assigned category")]
        target_namespace: Annotated[
            t.NonEmptyStr,
            Field(description="Target namespace path"),
        ]
        dependencies: t.StrSequence = Field(
            default_factory=list, description="Imported dependencies used by function"
        )
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

        totals: t.IntMapping = Field(
            default_factory=dict, description="Category totals"
        )
        suggestions: tuple[
            FlextInfraRefactorModelsViolations.HelperClassification,
            ...,
        ] = Field(default_factory=tuple, description="Classification suggestions")
        manual_review: tuple[
            FlextInfraRefactorModelsViolations.HelperClassification,
            ...,
        ] = Field(default_factory=tuple, description="Manual-review candidates")

    class HelperFileAnalysis(m.ArbitraryTypesModel):
        suggestions: tuple[
            FlextInfraRefactorModelsViolations.HelperClassification,
            ...,
        ] = Field(
            default_factory=tuple,
            description="Helper classifications from one file",
        )
        totals: t.IntMapping = Field(
            default_factory=dict, description="Category totals for file helpers"
        )
        manual_review: tuple[
            FlextInfraRefactorModelsViolations.HelperClassification,
            ...,
        ] = Field(default_factory=tuple, description="Helpers requiring manual review")

    class ViolationTopFileSection(m.ArbitraryTypesModel):
        """One ranked hotspot entry in violation analysis output."""

        file: Annotated[t.NonEmptyStr, Field(description="File path")]
        total: Annotated[
            t.NonNegativeInt,
            Field(description="Total violations in file"),
        ]
        counts: t.IntMapping = Field(
            default_factory=dict, description="Per-pattern counts"
        )

    class ViolationAnalysisReport(m.ArbitraryTypesModel):
        """Full violation analysis report for refactor diagnostics."""

        totals: t.IntMapping = Field(
            default_factory=dict, description="Aggregate counts by pattern"
        )
        files: Mapping[str, t.IntMapping] = Field(
            default_factory=dict, description="Per-file per-pattern counts"
        )
        top_files: tuple[
            FlextInfraRefactorModelsViolations.ViolationTopFileSection,
            ...,
        ] = Field(default_factory=tuple, description="Top hotspot files")
        files_scanned: Annotated[t.NonNegativeInt, Field(description="Files scanned")]
        helper_classification: FlextInfraRefactorModelsViolations.HelperClassificationReport = Field(
            description="Helper classification summary"
        )
        class_nesting: FlextInfraRefactorModelsViolations.ClassNestingReport = Field(
            description="Class nesting analysis summary"
        )


__all__ = ["FlextInfraRefactorModelsViolations"]
