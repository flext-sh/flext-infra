"""Unified census pipeline models — accessed via m.Infra.Census.*."""

from __future__ import annotations

from types import MappingProxyType
from typing import Annotated, ClassVar

from flext_core import m

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
            m.ArbitraryTypesModel,
        ):
            """Single discovered Python object with tier and classification metadata."""

            model_config: ClassVar[m.ConfigDict] = m.ConfigDict(frozen=True)

            name: Annotated[t.NonEmptyStr, m.Field(description="Object identifier")]
            kind: Annotated[
                str,
                m.Field(
                    description="Object kind (class/function/method/constant/local/...)"
                ),
            ]
            module_name: Annotated[
                str,
                m.Field(
                    description="Fully-qualified module name for the object",
                ),
            ] = ""
            scope_path: Annotated[
                str,
                m.Field(
                    description="Canonical owner/scope path for the object",
                ),
            ] = ""
            actual_tier: Annotated[
                str,
                m.Field(
                    description="Tier derived from file location",
                ),
            ] = ""
            expected_tier: Annotated[
                str,
                m.Field(
                    description="Tier determined by classifier",
                ),
            ] = ""
            is_facade_member: Annotated[
                bool,
                m.Field(
                    description="Whether object is exposed via facade MRO",
                ),
            ] = False
            references_count: Annotated[
                t.NonNegativeInt,
                m.Field(
                    description="Number of cross-file references",
                ),
            ] = 0
            fingerprint: Annotated[
                str,
                m.Field(
                    description="Normalized Rope-derived semantic fingerprint",
                ),
            ] = ""

        class Violation(
            FlextInfraModelsMixins.ProjectNameMixin,
            m.ArbitraryTypesModel,
        ):
            """Detected census violation with fix metadata."""

            model_config: ClassVar[m.ConfigDict] = m.ConfigDict(frozen=True)

            object_name: Annotated[
                t.NonEmptyStr,
                m.Field(description="Name of the violating object"),
            ]
            object_kind: Annotated[
                str,
                m.Field(
                    description="Object kind (constant/type/protocol/model/utility)"
                ),
            ]
            kind: Annotated[
                str,
                m.Field(
                    description="Violation kind (misplaced/duplicate/unused/missing_mro_base/flat_alias/wrong_tier)",
                ),
            ]
            severity: Annotated[
                str,
                m.Field(
                    description="Severity level",
                ),
            ] = c.Infra.GateSeverity.WARNING.value
            file_path: Annotated[str, m.Field(description="File containing violation")]
            line: Annotated[t.NonNegativeInt, m.Field(description="Line number")] = 0
            fixable: Annotated[
                bool, m.Field(description="Whether auto-fix is available")
            ] = False
            fix_action: Annotated[
                str, m.Field(description="Recommended fix action identifier")
            ] = ""
            description: Annotated[
                str, m.Field(description="Human-readable violation description")
            ] = ""

        class Fix(m.ArbitraryTypesModel):
            """Applied or proposed auto-fix operation."""

            model_config: ClassVar[m.ConfigDict] = m.ConfigDict(frozen=True)

            object_name: Annotated[
                t.NonEmptyStr,
                m.Field(description="Name of the fixed object"),
            ]
            action: Annotated[
                str,
                m.Field(
                    description="Fix action applied (move_to_tier/deduplicate/...)"
                ),
            ]
            source_file: Annotated[str, m.Field(description="Original file path")]
            target_file: Annotated[
                str, m.Field(description="Destination file path (for moves)")
            ] = ""
            files_changed: Annotated[
                t.NonNegativeInt, m.Field(description="Number of files modified")
            ] = 0
            applied: Annotated[
                bool, m.Field(description="Whether fix was actually applied")
            ] = False
            dry_run_diff: Annotated[
                str, m.Field(description="Unified diff preview (dry-run mode)")
            ] = ""

        class DuplicateGroup(m.ArbitraryTypesModel):
            """Cross-project duplicate object cluster."""

            model_config: ClassVar[m.ConfigDict] = m.ConfigDict(frozen=True)

            name: Annotated[
                t.NonEmptyStr,
                m.Field(description="Shared object name across projects"),
            ]
            kind: Annotated[str, m.Field(description="Object kind")]
            definitions: list[FlextInfraModelsCensus.Census.Object] = m.Field(
                description="All definitions of this object"
            )
            canonical: Annotated[
                str,
                m.Field(
                    description="Most-upstream project (canonical source)",
                ),
            ] = ""
            value_identical: Annotated[
                bool,
                m.Field(
                    description="Whether all definitions have identical values",
                ),
            ] = False

        class ProjectReport(
            FlextInfraModelsMixins.ProjectNameMixin,
            m.ArbitraryTypesModel,
        ):
            """Per-project census summary."""

            model_config: ClassVar[m.ConfigDict] = m.ConfigDict(frozen=True)

            objects: tuple[FlextInfraModelsCensus.Census.Object, ...] = m.Field(
                default_factory=tuple,
                description="Objects discovered for this project",
            )
            objects_total: Annotated[
                t.NonNegativeInt, m.Field(description="Total objects discovered")
            ] = 0
            objects_by_kind: Annotated[
                t.IntMapping,
                m.Field(
                    description="Object count per kind",
                ),
            ] = m.Field(default_factory=lambda: MappingProxyType({}))
            violations: tuple[FlextInfraModelsCensus.Census.Violation, ...] = m.Field(
                default_factory=tuple, description="Detected violations"
            )
            fixes: tuple[FlextInfraModelsCensus.Census.Fix, ...] = m.Field(
                default_factory=tuple,
                description="Proposed or applied fixes",
            )
            violations_total: Annotated[
                t.NonNegativeInt, m.Field(description="Total violation count")
            ] = 0
            fixes_applied: Annotated[
                t.NonNegativeInt, m.Field(description="Fixes applied count")
            ] = 0

        class WorkspaceReport(m.ArbitraryTypesModel):
            """Workspace-wide census summary."""

            projects: tuple[FlextInfraModelsCensus.Census.ProjectReport, ...] = m.Field(
                default_factory=tuple, description="Per-project reports"
            )
            total_objects: Annotated[
                t.NonNegativeInt, m.Field(description="Total objects across workspace")
            ] = 0
            total_violations: Annotated[
                t.NonNegativeInt,
                m.Field(description="Total violations across workspace"),
            ] = 0
            total_fixable: Annotated[
                t.NonNegativeInt, m.Field(description="Total fixable violations")
            ] = 0
            fixes_total: Annotated[
                t.NonNegativeInt, m.Field(description="Total proposed or applied fixes")
            ] = 0
            duplicates: tuple[FlextInfraModelsCensus.Census.DuplicateGroup, ...] = (
                m.Field(
                    default_factory=tuple, description="Cross-project duplicate groups"
                )
            )
            unused_count: Annotated[
                t.NonNegativeInt, m.Field(description="Total unused objects")
            ] = 0
            scan_duration_seconds: Annotated[
                float, m.Field(description="Wall-clock scan duration")
            ] = 0.0
            parse_errors: Annotated[
                t.NonNegativeInt, m.Field(description="Files that failed to parse")
            ] = 0


__all__: list[str] = ["FlextInfraModelsCensus"]
