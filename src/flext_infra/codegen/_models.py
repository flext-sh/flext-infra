"""Domain models for the codegen subpackage."""

from __future__ import annotations

from typing import Annotated

from pydantic import Field

from flext_core import FlextModels
from flext_infra.typings import FlextInfraTypes as t


class FlextInfraCodegenModels:
    """Models for codegen census, scaffold, and auto-fix pipelines."""

    class CensusViolation(FlextModels.ArbitraryTypesModel):
        """A single namespace violation detected by the census service."""

        module: Annotated[t.NonEmptyStr, Field(description="Module file path")]
        rule: Annotated[
            t.NonEmptyStr,
            Field(description="Violated rule identifier (e.g. NS-001)"),
        ]
        line: Annotated[t.NonNegativeInt, Field(description="Line number of violation")]
        message: Annotated[
            t.NonEmptyStr,
            Field(description="Human-readable violation message"),
        ]
        fixable: Annotated[
            bool,
            Field(description="Whether this violation can be auto-fixed"),
        ]

    class CensusReport(FlextModels.ArbitraryTypesModel):
        """Aggregated census report for a single project."""

        project: Annotated[t.NonEmptyStr, Field(description="Project name")]
        violations: Annotated[
            list[FlextInfraCodegenModels.CensusViolation],
            Field(
                default_factory=list,
                description="Detected violations",
            ),
        ]
        total: Annotated[t.NonNegativeInt, Field(description="Total violation count")]
        fixable: Annotated[
            t.NonNegativeInt,
            Field(description="Count of auto-fixable violations"),
        ]

    class ScaffoldResult(FlextModels.ArbitraryTypesModel):
        """Result of scaffolding base modules for a project."""

        project: Annotated[t.NonEmptyStr, Field(description="Project name")]
        files_created: Annotated[
            list[str],
            Field(
                default_factory=list,
                description="Newly created file paths",
            ),
        ]
        files_skipped: Annotated[
            list[str],
            Field(
                default_factory=list,
                description="Skipped (already existing) file paths",
            ),
        ]

    class AutoFixResult(FlextModels.ArbitraryTypesModel):
        """Result of auto-fixing namespace violations for a project."""

        project: Annotated[t.NonEmptyStr, Field(description="Project name")]
        violations_fixed: Annotated[
            list[FlextInfraCodegenModels.CensusViolation],
            Field(
                default_factory=list,
                description="Fixed violations",
            ),
        ]
        violations_skipped: Annotated[
            list[FlextInfraCodegenModels.CensusViolation],
            Field(
                default_factory=list,
                description="Skipped violations (not auto-fixable)",
            ),
        ]
        files_modified: Annotated[
            list[str],
            Field(
                default_factory=list,
                description="Modified file paths",
            ),
        ]

    class CodegenPipelineResult(FlextModels.ArbitraryTypesModel):
        """Full pipeline result combining census, scaffold, auto-fix phases."""

        census_before: Annotated[
            FlextInfraCodegenModels.CensusReport,
            Field(
                description="Census report before transformations",
            ),
        ]
        scaffold: Annotated[
            FlextInfraCodegenModels.ScaffoldResult,
            Field(
                description="Scaffold phase result",
            ),
        ]
        auto_fix: Annotated[
            FlextInfraCodegenModels.AutoFixResult,
            Field(
                description="Auto-fix phase result",
            ),
        ]
        census_after: Annotated[
            FlextInfraCodegenModels.CensusReport,
            Field(
                description="Census report after transformations",
            ),
        ]

    class QualityGateCheck(FlextModels.ArbitraryTypesModel):
        """A single quality gate check result entry."""

        name: Annotated[t.NonEmptyStr, Field(description="Check identifier")]
        passed: Annotated[bool, Field(description="Whether check passed")]
        detail: Annotated[
            str,
            Field(default="", description="Human-readable check detail"),
        ]
        critical: Annotated[bool, Field(description="Whether failure is critical")]

    class QualityGateProjectFinding(FlextModels.ArbitraryTypesModel):
        """Per-project quality gate findings."""

        project: Annotated[t.NonEmptyStr, Field(description="Project name")]
        violations_total: Annotated[
            t.NonNegativeInt, Field(description="Total violations")
        ]
        fixable_violations: Annotated[
            t.NonNegativeInt,
            Field(description="Auto-fixable violations"),
        ]
        validator_passed: Annotated[bool, Field(description="Whether validator passed")]
        mro_failures: Annotated[
            t.NonNegativeInt, Field(description="MRO failure count")
        ]
        layer_violations: Annotated[
            t.NonNegativeInt,
            Field(description="Layer violation count"),
        ]
        cross_project_reference_violations: Annotated[
            t.NonNegativeInt,
            Field(description="Cross-project reference violation count"),
        ]

    class ConstantDefinition(FlextModels.ArbitraryTypesModel):
        """A single constant extracted from a constants.py file."""

        name: Annotated[t.NonEmptyStr, Field(description="Constant identifier")]
        value_repr: Annotated[
            str,
            Field(description="Source repr (e.g., '30', '\"localhost\"')"),
        ]
        type_annotation: Annotated[
            str,
            Field(default="", description="Type annotation string"),
        ]
        file_path: Annotated[
            t.NonEmptyStr,
            Field(description="Absolute file path"),
        ]
        class_path: Annotated[
            str,
            Field(
                default="",
                description="Nested class path (e.g., 'OracleWms.Connection')",
            ),
        ]
        project: Annotated[t.NonEmptyStr, Field(description="Project name")]
        line: Annotated[t.PositiveInt, Field(description="Line number")]

    class DuplicateConstantGroup(FlextModels.ArbitraryTypesModel):
        """Cross-project duplicate group with consolidation metadata."""

        constant_name: Annotated[
            t.NonEmptyStr,
            Field(description="Constant identifier"),
        ]
        definitions: Annotated[
            list[FlextInfraCodegenModels.ConstantDefinition],
            Field(description="Definitions across projects"),
        ]
        is_value_identical: Annotated[
            bool,
            Field(description="Whether all values match"),
        ]
        canonical_ref: Annotated[
            str,
            Field(default="", description="Canonical parent reference"),
        ]

    class UnusedConstant(FlextModels.ArbitraryTypesModel):
        """Constant declared but never referenced in workspace."""

        name: Annotated[t.NonEmptyStr, Field(description="Constant identifier")]
        file_path: Annotated[
            t.NonEmptyStr,
            Field(description="Declaration file path"),
        ]
        class_path: Annotated[str, Field(default="", description="Nested class path")]
        project: Annotated[t.NonEmptyStr, Field(description="Project name")]
        line: Annotated[t.PositiveInt, Field(description="Line number")]

    class DirectConstantRef(FlextModels.ArbitraryTypesModel):
        """Direct FlextXConstants.Y.Z reference that should use c.* alias."""

        full_ref: Annotated[
            t.NonEmptyStr,
            Field(description="e.g., FlextAuthConstants.Auth.DEFAULT_TIMEOUT"),
        ]
        alias_ref: Annotated[
            t.NonEmptyStr,
            Field(description="e.g., c.Auth.DEFAULT_TIMEOUT"),
        ]
        file_path: Annotated[
            t.NonEmptyStr,
            Field(description="File containing the reference"),
        ]
        project: Annotated[t.NonEmptyStr, Field(description="Project name")]
        line: Annotated[t.PositiveInt, Field(description="Line number")]

    class CanonicalValueRule(FlextModels.ArbitraryTypesModel):
        value: int | str = Field(...)
        type: str = Field(...)
        canonical_ref: str = Field(...)
        semantic_names: list[str] = Field(default_factory=list)

    class NsRule(FlextModels.ArbitraryTypesModel):
        id: str = Field(...)
        description: str = Field(...)
        fixable: bool = Field(...)
        fixable_exclusion: str | None = Field(default=None)

    class ConstantsGovernanceConfig(FlextModels.ArbitraryTypesModel):
        version: str = Field(...)
        rules: list[FlextInfraCodegenModels.NsRule] = Field(...)
        canonical_values: list[FlextInfraCodegenModels.CanonicalValueRule] = Field(...)
        constants_class_pattern: str = Field(...)


__all__ = ["FlextInfraCodegenModels"]
