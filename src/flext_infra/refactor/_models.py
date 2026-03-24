"""Domain models for the refactor subpackage."""

from __future__ import annotations

import ast
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
from pathlib import Path
from typing import Annotated, ClassVar

import libcst as cst
from flext_core import m
from pydantic import ConfigDict, Field

from flext_infra import (
    FlextInfraNamespaceEnforcerModels,
    FlextInfraRefactorAstGrepModels,
    t,
)


class FlextInfraRefactorModels(
    FlextInfraRefactorAstGrepModels,
    FlextInfraNamespaceEnforcerModels,
):
    """Models for the refactor engine and related tools.

    Canonical base policy:
    - ``FrozenStrictModel`` for configuration/policy contracts.
    - ``ArbitraryTypesModel`` for mutable engine/report/result payloads.
    """

    class Result(m.ArbitraryTypesModel):
        """Result of applying refactor rules to a single file."""

        file_path: Annotated[Path, Field(description="Target file path")]
        success: Annotated[bool, Field(description="Whether the operation succeeded")]
        modified: Annotated[
            bool,
            Field(description="Whether the file was actually modified"),
        ]
        error: Annotated[
            str | None,
            Field(default=None, description="Error message on failure"),
        ] = None
        changes: Annotated[
            t.StrSequence,
            Field(
                default_factory=list,
                description="Human-readable change descriptions",
            ),
        ]
        refactored_code: Annotated[
            str | None,
            Field(
                default=None,
                description="Resulting source code after transformation",
            ),
        ]

    class RefactorProjectInfo(m.ArbitraryTypesModel):
        name: Annotated[t.NonEmptyStr, Field(description="Project directory name")]
        path: Annotated[Path, Field(description="Absolute project path")]
        src_path: Annotated[Path, Field(description="Absolute src/ path")]
        package_roots: Annotated[
            t.Infra.StrSet,
            Field(
                default_factory=set,
                description="Top-level Python package roots in src/",
            ),
        ]

    class FileImportData(m.ArbitraryTypesModel):
        imported_modules: Annotated[
            t.Infra.StrSet,
            Field(
                default_factory=set,
                description="Imported module roots",
            ),
        ]
        imported_symbols: Annotated[
            t.Infra.StrSet,
            Field(
                default_factory=set,
                description="Imported symbol names",
            ),
        ]

    class MethodInfo(m.ArbitraryTypesModel):
        """Metadata about a method used for ordering inside classes."""

        name: Annotated[t.NonEmptyStr, Field(description="Method name")]
        category: Annotated[str, Field(description="Method category classification")]
        node: Annotated[
            cst.FunctionDef,
            Field(
                description="LibCST FunctionDef node",
                exclude=True,
            ),
        ]
        decorators: Annotated[
            t.StrSequence,
            Field(
                default_factory=list,
                description="Decorator names applied to this method",
            ),
        ]

    class Checkpoint(m.ArbitraryTypesModel):
        """Serialisable checkpoint state for refactor safety recovery."""

        workspace_root: Annotated[
            t.NonEmptyStr,
            Field(description="Workspace root path"),
        ]
        status: Annotated[
            str,
            Field(default="running", description="Checkpoint status"),
        ] = "running"
        stash_ref: Annotated[
            str,
            Field(default="", description="Git stash reference"),
        ] = ""
        processed_targets: Annotated[
            t.StrSequence,
            Field(
                default_factory=list,
                description="Already-processed file targets",
            ),
        ]
        updated_at: Annotated[
            str,
            Field(
                default_factory=lambda: datetime.now(UTC).isoformat(),
                description="ISO 8601 timestamp of last update",
            ),
        ]

    class ClassOccurrence(m.ArbitraryTypesModel):
        """A single class definition occurrence within a source file."""

        model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True)

        name: Annotated[t.NonEmptyStr, Field(description="Class name")]
        line: Annotated[
            t.NonNegativeInt,
            Field(description="Line number (0 = unknown)"),
        ]
        is_top_level: Annotated[
            bool,
            Field(description="Whether class is at module top level"),
        ]

    class LooseClassViolation(m.ArbitraryTypesModel):
        """A detected loose-class naming violation with confidence."""

        model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True)

        file: Annotated[t.NonEmptyStr, Field(description="Source file path")]
        line: Annotated[t.PositiveInt, Field(description="Line number")]
        class_name: Annotated[
            t.NonEmptyStr,
            Field(description="Violating class name"),
        ]
        expected_prefix: Annotated[str, Field(description="Expected namespace prefix")]
        rule: Annotated[t.NonEmptyStr, Field(description="Violated rule id")]
        reason: Annotated[str, Field(description="Human-readable reason")]
        confidence: Annotated[str, Field(description="Confidence level")]
        score: Annotated[t.DecimalFraction, Field(description="Confidence score")]

    class FamilyMROResolution(m.ArbitraryTypesModel):
        """Resolution payload for one facade family MRO."""

        model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True)

        family: Annotated[t.NonEmptyStr, Field(description="Facade family letter")]
        expected_bases: Annotated[
            t.Infra.VariadicTuple[str],
            Field(
                description="Expected base class names in order",
            ),
        ]
        resolved_mro: Annotated[
            t.Infra.VariadicTuple[str],
            Field(description="Resolved MRO class names"),
        ]
        accessible_namespaces: Annotated[
            t.Infra.VariadicTuple[str],
            Field(
                description="Namespaces accessible through the MRO",
            ),
        ]

    class ProjectClassification(m.ArbitraryTypesModel):
        """Result of classifying a project by kind and family chains."""

        model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True)

        project_kind: Annotated[
            t.NonEmptyStr,
            Field(
                description="Project kind (core, domain, platform, integration, app)",
            ),
        ]
        family_chains: Annotated[
            Mapping[str, t.StrSequence],
            Field(
                description="Family letter to MRO chain mapping",
            ),
        ]

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
            Field(
                default=None,
                description="Rewrite scope (file/project/workspace)",
            ),
        ] = None

    class ClassNestingViolation(m.ArbitraryTypesModel):
        """Normalized class-nesting violation with rewrite metadata."""

        model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True)

        file: Annotated[t.NonEmptyStr, Field(description="Source module path")]
        line: Annotated[t.PositiveInt, Field(description="Line number")]
        class_name: Annotated[t.NonEmptyStr, Field(description="Class name")]
        target_namespace: Annotated[
            str,
            Field(
                default="",
                description="Expected namespace class",
            ),
        ] = ""
        confidence: Annotated[
            str,
            Field(default="low", description="Confidence level"),
        ] = "low"
        rewrite_scope: Annotated[
            str,
            Field(
                default="file",
                description="Rewrite scope",
            ),
        ] = "file"

    class ClassNestingPolicy(m.FrozenStrictModel):
        """Validated policy contract used by class-nesting transformers."""

        model_config: ClassVar[ConfigDict] = ConfigDict(extra="ignore", frozen=True)

        family_name: Annotated[
            t.NonEmptyStr,
            Field(description="Module family name"),
        ]
        allowed_operations: Annotated[
            t.StrSequence,
            Field(
                default_factory=list,
                description="Enabled operation identifiers for this family",
            ),
        ]
        forbidden_operations: Annotated[
            t.StrSequence,
            Field(
                default_factory=list,
                description="Disabled operation identifiers for this family",
            ),
        ]
        forbidden_targets: Annotated[
            t.StrSequence,
            Field(
                default_factory=list,
                description="Target namespaces forbidden for this family",
            ),
        ]
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
                default_factory=list,
                description="Function parameters that must exist in helper signatures",
            ),
        ]
        forbidden_parameters: Annotated[
            t.StrSequence,
            Field(
                default_factory=list,
                description="Function parameters that must not exist in helper signatures",
            ),
        ]
        allow_vararg: Annotated[
            bool,
            Field(
                default=True,
                description="Allow variadic positional parameter usage",
            ),
        ]
        allow_kwarg: Annotated[
            bool,
            Field(
                default=True,
                description="Allow variadic keyword parameter usage",
            ),
        ]
        allow_positional_only_params: Annotated[
            bool,
            Field(
                default=True,
                description="Allow positional-only parameters",
            ),
        ]
        allow_keyword_only_params: Annotated[
            bool,
            Field(
                default=True,
                description="Allow keyword-only parameters",
            ),
        ]
        propagate_imports: Annotated[
            bool,
            Field(
                default=True,
                description="Allow propagating import rewrite rules",
            ),
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
            Field(
                default_factory=list,
                description="Name prefixes blocked from rewrite propagation",
            ),
        ]
        allowed_targets: Annotated[
            t.StrSequence,
            Field(
                default_factory=list,
                description="Explicitly allowed target namespaces",
            ),
        ]

    class ClassNestingReport(m.ArbitraryTypesModel):
        """Aggregated class-nesting analysis report."""

        violations_count: Annotated[
            t.NonNegativeInt,
            Field(description="Total violations"),
        ]
        confidence_counts: Annotated[
            Mapping[str, int],
            Field(
                default_factory=dict,
                description="Confidence histogram",
            ),
        ]
        violations: Annotated[
            Sequence[FlextInfraRefactorModels.ClassNestingViolation],
            Field(
                default_factory=lambda: (),
                description="Violation details",
            ),
        ]
        per_file_counts: Annotated[
            Mapping[str, int],
            Field(
                default_factory=dict,
                description="Violation counts per file",
            ),
        ]

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
            Field(
                default_factory=list,
                description="Imported dependencies used by function",
            ),
        ]
        manual_review: Annotated[
            bool,
            Field(
                default=False,
                description="Whether manual review is required",
            ),
        ]
        review_reason: Annotated[
            str,
            Field(
                default="",
                description="Manual review rationale",
            ),
        ]

    class HelperClassificationReport(m.ArbitraryTypesModel):
        """Aggregated helper-function classification payload."""

        totals: Annotated[
            Mapping[str, int],
            Field(
                default_factory=dict,
                description="Category totals",
            ),
        ]
        suggestions: Annotated[
            Sequence[FlextInfraRefactorModels.HelperClassification],
            Field(
                default_factory=lambda: (),
                description="Classification suggestions",
            ),
        ]
        manual_review: Annotated[
            Sequence[FlextInfraRefactorModels.HelperClassification],
            Field(
                default_factory=lambda: (),
                description="Manual-review candidates",
            ),
        ]

    class HelperFileAnalysis(m.ArbitraryTypesModel):
        suggestions: Annotated[
            Sequence[FlextInfraRefactorModels.HelperClassification],
            Field(
                default_factory=lambda: (),
                description="Helper classifications from one file",
            ),
        ]
        totals: Annotated[
            Mapping[str, int],
            Field(
                default_factory=dict,
                description="Category totals for file helpers",
            ),
        ]
        manual_review: Annotated[
            Sequence[FlextInfraRefactorModels.HelperClassification],
            Field(
                default_factory=lambda: (),
                description="Helpers requiring manual review",
            ),
        ]

    class ViolationTopFileSection(m.ArbitraryTypesModel):
        """One ranked hotspot entry in violation analysis output."""

        file: Annotated[t.NonEmptyStr, Field(description="File path")]
        total: Annotated[
            t.NonNegativeInt,
            Field(description="Total violations in file"),
        ]
        counts: Annotated[
            Mapping[str, int],
            Field(
                default_factory=dict,
                description="Per-pattern counts",
            ),
        ]

    class ViolationAnalysisReport(m.ArbitraryTypesModel):
        """Full violation analysis report for refactor diagnostics."""

        totals: Annotated[
            Mapping[str, int],
            Field(
                default_factory=dict,
                description="Aggregate counts by pattern",
            ),
        ]
        files: Annotated[
            Mapping[str, Mapping[str, int]],
            Field(
                default_factory=dict,
                description="Per-file per-pattern counts",
            ),
        ]
        top_files: Annotated[
            Sequence[FlextInfraRefactorModels.ViolationTopFileSection],
            Field(
                default_factory=lambda: (),
                description="Top hotspot files",
            ),
        ]
        files_scanned: Annotated[t.NonNegativeInt, Field(description="Files scanned")]
        helper_classification: Annotated[
            FlextInfraRefactorModels.HelperClassificationReport,
            Field(description="Helper classification summary"),
        ]
        class_nesting: Annotated[
            FlextInfraRefactorModels.ClassNestingReport,
            Field(
                description="Class nesting analysis summary",
            ),
        ]

    # -- MRO Target Specification -----------------------------------------------

    class MROTargetSpec(m.FrozenStrictModel):
        """Specification for an MRO target family."""

        family_alias: Annotated[
            t.NonEmptyStr,
            Field(description="Family alias letter"),
        ]
        file_names: Annotated[frozenset[str], Field(description="File name patterns")]
        package_directory: Annotated[
            t.NonEmptyStr,
            Field(description="Package directory name"),
        ]
        class_suffix: Annotated[t.NonEmptyStr, Field(description="Class suffix")]

    # -- Pydantic Centralizer Models -------------------------------------------

    class ClassMove(m.FrozenStrictModel):
        """Tracks a class definition being moved during centralization."""

        name: Annotated[t.NonEmptyStr, Field(description="Class name")]
        start: Annotated[t.NonNegativeInt, Field(description="Start line number")]
        end: Annotated[t.NonNegativeInt, Field(description="End line number")]
        source: Annotated[str, Field(description="Source code text")]
        kind: Annotated[
            t.NonEmptyStr,
            Field(description="Model kind classification"),
        ]

    class AliasMove(m.FrozenStrictModel):
        """Tracks a type alias being moved during centralization."""

        name: Annotated[t.NonEmptyStr, Field(description="Alias name")]
        start: Annotated[t.NonNegativeInt, Field(description="Start line number")]
        end: Annotated[t.NonNegativeInt, Field(description="End line number")]
        alias_expr: Annotated[str, Field(description="Alias expression text")]

    class CentralizerFailureStats(m.ArbitraryTypesModel):
        """Mutable statistics for centralizer parse failures."""

        parse_syntax_errors: Annotated[
            t.NonNegativeInt,
            Field(default=0, description="Syntax error count"),
        ] = 0
        parse_encoding_errors: Annotated[
            t.NonNegativeInt,
            Field(default=0, description="Encoding error count"),
        ] = 0
        parse_io_errors: Annotated[
            t.NonNegativeInt,
            Field(default=0, description="I/O error count"),
        ] = 0

    # -- Namespace Enforcer Models ---------------------------------------------

    class ParsedPythonModule(m.ArbitraryTypesModel):
        """Result of parsing a Python source file into AST."""

        model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True)

        source: Annotated[str, Field(description="Raw source text")]
        tree: Annotated[ast.Module, Field(description="Parsed AST module node")]

    # -- MRO Generic Models ----------------------------------------------------

    class MROFamilyTarget(m.ArbitraryTypesModel):
        """Parametrized target for an MRO family scan or operations.

        Defines which MRO family to scan (e.g. utilities, constants, models).
        """

        model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True)

        family: Annotated[
            t.NonEmptyStr,
            Field(description="Family alias letter (c/t/p/m/u)"),
        ]
        class_suffix: Annotated[
            str,
            Field(description="Class name suffix (e.g. 'Utilities')"),
        ]
        package_dir: Annotated[
            str,
            Field(
                description="Relative path to _xxx package dir (e.g. 'flext_core/_utilities')",
            ),
        ]
        facade_module: Annotated[
            str,
            Field(
                description="Relative path to facade (e.g. 'flext_core/utilities.py')",
            ),
        ]
        facade_class_prefix: Annotated[
            str,
            Field(
                default="Flext",
                description="Class name prefix for facade (e.g. 'Flext')",
            ),
        ] = "Flext"
        core_project: Annotated[
            str,
            Field(
                default="flext-core",
                description="Core project directory name",
            ),
        ] = "flext-core"

    # -- Census Models ---------------------------------------------------------

    class CensusMethodInfo(m.ArbitraryTypesModel):
        """A public method extracted from a _utilities class."""

        model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True)

        name: Annotated[t.NonEmptyStr, Field(description="Method name")]
        method_type: Annotated[
            str,
            Field(description="Method kind: static, class, instance"),
        ]
        source_file: Annotated[str, Field(description="Source filename")]

    class CensusUsageRecord(m.ArbitraryTypesModel):
        """A single method usage found via CST analysis."""

        model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True)

        class_name: Annotated[
            t.NonEmptyStr,
            Field(description="Utilities class name"),
        ]
        method_name: Annotated[t.NonEmptyStr, Field(description="Method name")]
        access_mode: Annotated[
            str,
            Field(description="Access mode: alias_flat, alias_namespaced, direct"),
        ]
        file_path: Annotated[str, Field(description="Source file path")]
        project: Annotated[str, Field(description="Project name")]

    class CensusMethodSummary(m.ArbitraryTypesModel):
        """Aggregated usage counts for a single method."""

        model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True)

        name: Annotated[t.NonEmptyStr, Field(description="Method name")]
        method_type: Annotated[str, Field(description="Method kind")]
        alias_flat: Annotated[t.NonNegativeInt, Field(description="u.method count")]
        alias_namespaced: Annotated[
            t.NonNegativeInt,
            Field(description="u.Class.method count"),
        ]
        direct: Annotated[
            t.NonNegativeInt,
            Field(description="Direct class.method count"),
        ]
        total: Annotated[t.NonNegativeInt, Field(description="Total usages")]

    class CensusClassSummary(m.ArbitraryTypesModel):
        """Aggregated census for one _utilities class."""

        model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True)

        class_name: Annotated[
            t.NonEmptyStr,
            Field(description="Utilities class name"),
        ]
        source_file: Annotated[str, Field(description="Source filename")]
        methods: Annotated[
            Sequence[FlextInfraRefactorModels.CensusMethodSummary],
            Field(
                default_factory=lambda: (),
                description="Method summaries",
            ),
        ]

    class CensusProjectMethodUsage(m.ArbitraryTypesModel):
        """Usage of a method within a specific project."""

        model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True)

        class_name: Annotated[
            t.NonEmptyStr,
            Field(description="Utilities class name"),
        ]
        method_name: Annotated[t.NonEmptyStr, Field(description="Method name")]
        access_mode: Annotated[str, Field(description="Access mode")]
        count: Annotated[t.NonNegativeInt, Field(description="Usage count")]

    class CensusProjectSummary(m.ArbitraryTypesModel):
        """Usage breakdown for one project."""

        model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True)

        project_name: Annotated[
            t.NonEmptyStr,
            Field(description="Project directory name"),
        ]
        usages: Annotated[
            Sequence[FlextInfraRefactorModels.CensusProjectMethodUsage],
            Field(
                default_factory=lambda: (),
                description="Per-method usages",
            ),
        ]
        total: Annotated[t.NonNegativeInt, Field(description="Total usages in project")]

    class UtilitiesCensusReport(m.ArbitraryTypesModel):
        """Full census report for _utilities method usage."""

        classes: Annotated[
            Sequence[FlextInfraRefactorModels.CensusClassSummary],
            Field(
                default_factory=lambda: (),
                description="Per-class summaries",
            ),
        ]
        projects: Annotated[
            Sequence[FlextInfraRefactorModels.CensusProjectSummary],
            Field(
                default_factory=lambda: (),
                description="Per-project breakdowns",
            ),
        ]
        total_classes: Annotated[
            t.NonNegativeInt,
            Field(description="Number of utility classes"),
        ]
        total_methods: Annotated[
            t.NonNegativeInt,
            Field(description="Number of public methods"),
        ]
        total_usages: Annotated[
            t.NonNegativeInt,
            Field(description="Total usage records"),
        ]
        total_unused: Annotated[
            t.NonNegativeInt,
            Field(description="Methods with zero usages"),
        ]
        files_scanned: Annotated[t.NonNegativeInt, Field(description="Files scanned")]
        parse_errors: Annotated[
            t.NonNegativeInt,
            Field(description="Files that failed to parse"),
        ]


__all__ = ["FlextInfraRefactorModels"]
