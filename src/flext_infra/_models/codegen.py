"""Domain models for the codegen subpackage."""

from __future__ import annotations

from collections.abc import MutableSequence, MutableSet
from typing import Annotated

from pydantic import Field

from flext_core import FlextModels
from flext_infra import (
    FlextInfraCodegenDeduplicationModels,
    t,
)


class FlextInfraCodegenModels(FlextInfraCodegenDeduplicationModels):
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
        violations: list[FlextInfraCodegenModels.CensusViolation] = Field(
            default_factory=list,
            description="Detected violations",
        )
        total: Annotated[t.NonNegativeInt, Field(description="Total violation count")]
        fixable: Annotated[
            t.NonNegativeInt,
            Field(description="Count of auto-fixable violations"),
        ]

    class ScaffoldResult(FlextModels.ArbitraryTypesModel):
        """Result of scaffolding base modules for a project."""

        project: Annotated[t.NonEmptyStr, Field(description="Project name")]
        files_created: t.StrSequence = Field(
            default_factory=list,
            description="Newly created file paths",
        )
        files_skipped: t.StrSequence = Field(
            default_factory=list,
            description="Skipped (already existing) file paths",
        )

    class AutoFixResult(FlextModels.ArbitraryTypesModel):
        """Result of auto-fixing namespace violations for a project."""

        project: Annotated[t.NonEmptyStr, Field(description="Project name")]
        violations_fixed: list[FlextInfraCodegenModels.CensusViolation] = Field(
            default_factory=list,
            description="Fixed violations",
        )
        violations_skipped: list[FlextInfraCodegenModels.CensusViolation] = Field(
            default_factory=list,
            description="Skipped violations (not auto-fixable)",
        )
        files_modified: t.StrSequence = Field(
            default_factory=list,
            description="Modified file paths",
        )

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
            t.NonNegativeInt,
            Field(description="Total violations"),
        ]
        fixable_violations: Annotated[
            t.NonNegativeInt,
            Field(description="Auto-fixable violations"),
        ]
        validator_passed: Annotated[bool, Field(description="Whether validator passed")]
        mro_failures: Annotated[
            t.NonNegativeInt,
            Field(description="MRO failure count"),
        ]
        layer_violations: Annotated[
            t.NonNegativeInt,
            Field(description="Layer violation count"),
        ]
        cross_project_reference_violations: Annotated[
            t.NonNegativeInt,
            Field(description="Cross-project reference violation count"),
        ]

    class BulkFixItem(FlextModels.ArbitraryTypesModel):
        """Shared line-addressable item used by bulk codegen fixes."""

        name: Annotated[t.NonEmptyStr, Field(description="Item identifier")]
        file_path: Annotated[
            t.NonEmptyStr,
            Field(description="Absolute file path"),
        ]
        line: Annotated[t.PositiveInt, Field(description="Line number")]

    class ConstantDefinition(BulkFixItem):
        """A single constant extracted from a constants.py file."""

        value_repr: Annotated[
            str,
            Field(description="Source repr (e.g., '30', '\"localhost\"')"),
        ]
        type_annotation: Annotated[
            str,
            Field(default="", description="Type annotation string"),
        ]
        class_path: Annotated[
            str,
            Field(
                default="",
                description="Nested class path (e.g., 'OracleWms.Connection')",
            ),
        ]
        project: Annotated[t.NonEmptyStr, Field(description="Project name")]

    class DuplicateConstantGroup(FlextModels.ArbitraryTypesModel):
        """Cross-project duplicate group with consolidation metadata."""

        constant_name: t.NonEmptyStr = Field(description="Constant identifier")
        definitions: list[FlextInfraCodegenModels.ConstantDefinition] = Field(
            description="Definitions across projects",
        )
        is_value_identical: bool = Field(description="Whether all values match")
        canonical_ref: str = Field(default="", description="Canonical parent reference")

    class UnusedConstant(BulkFixItem):
        """Constant declared but never referenced in workspace."""

        class_path: Annotated[str, Field(default="", description="Nested class path")]
        project: Annotated[t.NonEmptyStr, Field(description="Project name")]

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
        value: t.Infra.CanonicalValue = Field(description="Canonical value")
        type: str = Field(description="Canonical type")
        canonical_ref: str = Field(description="Canonical reference")
        semantic_names: t.StrSequence = Field(
            default_factory=list, description="semantic_names"
        )

    class NsRule(FlextModels.ArbitraryTypesModel):
        id: str = Field(description="Rule ID")
        description: str = Field(description="Rule description")
        fixable: bool = Field(description="Whether the rule is fixable")
        fixable_exclusion: str | None = Field(
            default=None, description="Fixable exclusion reason"
        )

    class ConstantsGovernanceConfig(FlextModels.ArbitraryTypesModel):
        version: str = Field(description="Config version")
        rules: list[FlextInfraCodegenModels.NsRule] = Field(
            description="Governance rules"
        )
        canonical_values: list[FlextInfraCodegenModels.CanonicalValueRule] = Field(
            description="Canonical values config"
        )
        constants_class_pattern: str = Field(
            description="Constants class pattern regex"
        )

    class FixContext(FlextModels.ArbitraryTypesModel):
        """Mutable accumulation context for fix operations."""

        violations_fixed: MutableSequence[FlextInfraCodegenModels.CensusViolation] = (
            Field(
                default_factory=list,
                description="List of violations that were fixed",
            )
        )
        violations_skipped: MutableSequence[FlextInfraCodegenModels.CensusViolation] = (
            Field(
                default_factory=list,
                description="List of violations that were skipped",
            )
        )
        files_modified: MutableSet[str] = Field(
            default_factory=set,
            description="Set of unique modified file paths",
        )

        def skip(self, *, module: str, rule: str, line: int, message: str) -> None:
            self.violations_skipped.append(
                FlextInfraCodegenModels.CensusViolation(
                    module=module, rule=rule, line=line, message=message, fixable=False
                ),
            )

        def fix(self, *, module: str, rule: str, line: int, message: str) -> None:
            self.violations_fixed.append(
                FlextInfraCodegenModels.CensusViolation(
                    module=module, rule=rule, line=line, message=message, fixable=True
                ),
            )


__all__ = ["FlextInfraCodegenModels"]
