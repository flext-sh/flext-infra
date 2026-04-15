"""Unified census pipeline models — accessed via m.Infra.Census.*."""

from __future__ import annotations

from typing import Annotated, ClassVar

from pydantic import ConfigDict, Field

from flext_core import FlextModels
from flext_infra import FlextInfraModelsMixins, c, t


class FlextInfraModelsCensus:
    """Unified census pipeline models scoped under m.Infra.Census.*."""

    class Census:
        """Namespace for unified census pipeline data contracts."""

        class Object(
            FlextInfraModelsMixins.AbsoluteFilePathTextMixin,
            FlextInfraModelsMixins.RequiredNonNegativeLineMixin,
            FlextInfraModelsMixins.ProjectNameMixin,
            FlextInfraModelsMixins.NestedClassPathMixin,
            FlextModels.ArbitraryTypesModel,
        ):
            """Single discovered Python object with tier and classification metadata."""

            model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True)

            name: Annotated[t.NonEmptyStr, Field(description="Object identifier")]
            kind: Annotated[
                str,
                Field(
                    description="Object kind (class/function/method/constant/local/...)"
                ),
            ]
            module_name: Annotated[
                str,
                Field(
                    default="",
                    description="Fully-qualified module name for the object",
                ),
            ] = ""
            scope_path: Annotated[
                str,
                Field(
                    default="",
                    description="Canonical owner/scope path for the object",
                ),
            ] = ""
            actual_tier: Annotated[
                str,
                Field(
                    default="",
                    description="Tier derived from file location",
                ),
            ] = ""
            expected_tier: Annotated[
                str,
                Field(
                    default="",
                    description="Tier determined by classifier",
                ),
            ] = ""
            is_facade_member: Annotated[
                bool,
                Field(
                    default=False,
                    description="Whether object is exposed via facade MRO",
                ),
            ] = False
            references_count: Annotated[
                t.NonNegativeInt,
                Field(
                    default=0,
                    description="Number of cross-file references",
                ),
            ] = 0
            fingerprint: Annotated[
                str,
                Field(
                    default="",
                    description="Normalized Rope-derived semantic fingerprint",
                ),
            ] = ""

        class Violation(
            FlextInfraModelsMixins.ProjectNameMixin,
            FlextModels.ArbitraryTypesModel,
        ):
            """Detected census violation with fix metadata."""

            model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True)

            object_name: Annotated[
                t.NonEmptyStr,
                Field(description="Name of the violating object"),
            ]
            object_kind: Annotated[
                str,
                Field(description="Object kind (constant/type/protocol/model/utility)"),
            ]
            kind: Annotated[
                str,
                Field(
                    description="Violation kind (misplaced/duplicate/unused/missing_mro_base/flat_alias/wrong_tier)",
                ),
            ]
            severity: Annotated[
                str,
                Field(
                    default=c.Infra.GateSeverity.WARNING.value,
                    description="Severity level",
                ),
            ] = c.Infra.GateSeverity.WARNING.value
            file_path: Annotated[str, Field(description="File containing violation")]
            line: Annotated[
                t.NonNegativeInt,
                Field(default=0, description="Line number"),
            ] = 0
            fixable: Annotated[
                bool,
                Field(default=False, description="Whether auto-fix is available"),
            ] = False
            fix_action: Annotated[
                str,
                Field(default="", description="Recommended fix action identifier"),
            ] = ""
            description: Annotated[
                str,
                Field(default="", description="Human-readable violation description"),
            ] = ""

        class Fix(FlextModels.ArbitraryTypesModel):
            """Applied or proposed auto-fix operation."""

            model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True)

            object_name: Annotated[
                t.NonEmptyStr,
                Field(description="Name of the fixed object"),
            ]
            action: Annotated[
                str,
                Field(description="Fix action applied (move_to_tier/deduplicate/...)"),
            ]
            source_file: Annotated[str, Field(description="Original file path")]
            target_file: Annotated[
                str,
                Field(default="", description="Destination file path (for moves)"),
            ] = ""
            files_changed: Annotated[
                t.NonNegativeInt,
                Field(default=0, description="Number of files modified"),
            ] = 0
            applied: Annotated[
                bool,
                Field(default=False, description="Whether fix was actually applied"),
            ] = False
            dry_run_diff: Annotated[
                str,
                Field(default="", description="Unified diff preview (dry-run mode)"),
            ] = ""

        class DuplicateGroup(FlextModels.ArbitraryTypesModel):
            """Cross-project duplicate object cluster."""

            model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True)

            name: Annotated[
                t.NonEmptyStr,
                Field(description="Shared object name across projects"),
            ]
            kind: Annotated[str, Field(description="Object kind")]
            definitions: list[FlextInfraModelsCensus.Census.Object] = Field(
                description="All definitions of this object"
            )
            canonical: Annotated[
                str,
                Field(
                    default="",
                    description="Most-upstream project (canonical source)",
                ),
            ] = ""
            value_identical: Annotated[
                bool,
                Field(
                    default=False,
                    description="Whether all definitions have identical values",
                ),
            ] = False

        class ProjectReport(
            FlextInfraModelsMixins.ProjectNameMixin,
            FlextModels.ArbitraryTypesModel,
        ):
            """Per-project census summary."""

            model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True)

            objects: tuple[FlextInfraModelsCensus.Census.Object, ...] = Field(
                default_factory=tuple,
                description="Objects discovered for this project",
            )
            objects_total: Annotated[
                t.NonNegativeInt,
                Field(default=0, description="Total objects discovered"),
            ] = 0
            objects_by_kind: Annotated[
                t.IntMapping,
                Field(
                    description="Object count per kind",
                ),
            ] = Field(default_factory=dict)
            violations: tuple[FlextInfraModelsCensus.Census.Violation, ...] = Field(
                default_factory=tuple, description="Detected violations"
            )
            fixes: tuple[FlextInfraModelsCensus.Census.Fix, ...] = Field(
                default_factory=tuple,
                description="Proposed or applied fixes",
            )
            violations_total: Annotated[
                t.NonNegativeInt,
                Field(default=0, description="Total violation count"),
            ] = 0
            fixes_applied: Annotated[
                t.NonNegativeInt,
                Field(default=0, description="Fixes applied count"),
            ] = 0

        class WorkspaceReport(FlextModels.ArbitraryTypesModel):
            """Workspace-wide census summary."""

            projects: tuple[FlextInfraModelsCensus.Census.ProjectReport, ...] = Field(
                default_factory=tuple, description="Per-project reports"
            )
            total_objects: Annotated[
                t.NonNegativeInt,
                Field(default=0, description="Total objects across workspace"),
            ] = 0
            total_violations: Annotated[
                t.NonNegativeInt,
                Field(default=0, description="Total violations across workspace"),
            ] = 0
            total_fixable: Annotated[
                t.NonNegativeInt,
                Field(default=0, description="Total fixable violations"),
            ] = 0
            fixes_total: Annotated[
                t.NonNegativeInt,
                Field(default=0, description="Total proposed or applied fixes"),
            ] = 0
            duplicates: tuple[FlextInfraModelsCensus.Census.DuplicateGroup, ...] = (
                Field(
                    default_factory=tuple, description="Cross-project duplicate groups"
                )
            )
            unused_count: Annotated[
                t.NonNegativeInt,
                Field(default=0, description="Total unused objects"),
            ] = 0
            scan_duration_seconds: Annotated[
                float,
                Field(default=0.0, description="Wall-clock scan duration"),
            ] = 0.0
            parse_errors: Annotated[
                t.NonNegativeInt,
                Field(default=0, description="Files that failed to parse"),
            ] = 0


__all__: list[str] = ["FlextInfraModelsCensus"]
