# AUTO-GENERATED FILE — Regenerate with: make gen
"""Source-derived structural model contracts.

Copyright (c) 2026 FLEXT Team. All rights reserved.
src/flext_infra/_protocols/census
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import MutableMapping, MutableSequence, MutableSet, Sequence
from pathlib import Path
from typing import TYPE_CHECKING, Protocol, runtime_checkable

from flext_cli import FlextCliProtocols

from flext_infra._protocols import FlextInfraProtocolsBase, FlextInfraProtocolsMixins

if TYPE_CHECKING:
    from flext_infra import t
    from flext_infra._protocols import (
        FlextInfraProtocolsRope,
        FlextInfraProtocolsTransformers,
    )


class FlextInfraProtocolsCensus:
    """Own the structural contracts declared by its model source."""

    @runtime_checkable
    class ReferenceSite(
        FlextInfraProtocolsMixins.AbsoluteFilePathTextMixin,
        FlextInfraProtocolsMixins.RequiredNonNegativeLineMixin,
        FlextInfraProtocolsBase.FrozenArbitrary,
        Protocol,
    ):
        """Structural data contract projected from the owning model."""

        @property
        def surface(self) -> str:
            """Reference surface (src/tests/examples/scripts)."""
            ...

        @property
        def offset(self) -> t.NonNegativeInt | None:
            """Rope character offset for exact occurrence evidence."""
            ...

    @runtime_checkable
    class Object(
        FlextInfraProtocolsMixins.AbsoluteFilePathTextMixin,
        FlextInfraProtocolsMixins.RequiredNonNegativeLineMixin,
        FlextInfraProtocolsMixins.ProjectNameMixin,
        FlextInfraProtocolsMixins.NestedClassPathMixin,
        FlextInfraProtocolsBase.FrozenArbitrary,
        Protocol,
    ):
        """Structural data contract projected from the owning model."""

        @property
        def name(self) -> t.NonEmptyStr:
            """Object identifier."""
            ...

        @property
        def kind(self) -> str:
            """Object kind (class/function/method/constant/local/...)."""
            ...

        @property
        def module_name(self) -> str:
            """Fully-qualified module name for the object."""
            ...

        @property
        def scope_path(self) -> str:
            """Canonical owner/scope path for the object."""
            ...

        @property
        def actual_tier(self) -> str:
            """Tier derived from file location."""
            ...

        @property
        def expected_tier(self) -> str:
            """Tier determined by classifier."""
            ...

        @property
        def is_facade_member(self) -> bool:
            """Whether object is exposed via facade FLEXT."""
            ...

        @property
        def references_count(self) -> t.NonNegativeInt:
            """Number of references excluding the definition site."""
            ...

        @property
        def runtime_references_count(self) -> t.NonNegativeInt:
            """Number of references from runtime/source modules."""
            ...

        @property
        def script_references_count(self) -> t.NonNegativeInt:
            """Number of references from script modules."""
            ...

        @property
        def runtime_reference_sites(
            self,
        ) -> tuple[FlextInfraProtocolsCensus.ReferenceSite, ...]:
            """Runtime/source reference sites."""
            ...

        @property
        def script_reference_sites(
            self,
        ) -> tuple[FlextInfraProtocolsCensus.ReferenceSite, ...]:
            """Script reference sites."""
            ...

        @property
        def all_reference_sites(
            self,
        ) -> tuple[FlextInfraProtocolsCensus.ReferenceSite, ...]:
            """Structural member projected from the owning model.

            Qualified indexed occurrences on all surfaces, including reexports; not
            reachability.
            """
            ...

        @property
        def reference_evidence_collected(self) -> bool:
            """Whether the indexed Rope occurrence search was performed."""
            ...

        @property
        def fingerprint(self) -> str:
            """Normalized Rope-derived semantic fingerprint."""
            ...

        @property
        def payload_fingerprint(self) -> str:
            """Structural member projected from the owning model.

            Diagnostic native Pydantic declaration fingerprint, retaining bases,
            fields, literal defaults, configuration, generics and
            validation/serialization code; never an equivalence proof.
            """
            ...

    @runtime_checkable
    class RemovalPreviewOptions(FlextInfraProtocolsBase.FrozenArbitrary, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def gates(self) -> Sequence[str]:
            """Configured dry-run gate names the preview runs."""
            ...

        @property
        def source_cache(self) -> MutableMapping[Path, str] | None:
            """Live source cache reused across candidates."""
            ...

    @runtime_checkable
    class RemovalCandidate(
        FlextInfraProtocolsMixins.AbsoluteFilePathTextMixin,
        FlextInfraProtocolsMixins.RequiredNonNegativeLineMixin,
        FlextInfraProtocolsMixins.ProjectNameMixin,
        FlextInfraProtocolsBase.FrozenArbitrary,
        Protocol,
    ):
        """Structural data contract projected from the owning model."""

        @property
        def object_name(self) -> t.NonEmptyStr:
            """Candidate object name."""
            ...

        @property
        def object_kind(self) -> str:
            """Candidate object kind."""
            ...

        @property
        def scope_path(self) -> str:
            """Canonical owner/scope path for the candidate."""
            ...

        @property
        def reason(self) -> str:
            """Candidate reason (unused)."""
            ...

        @property
        def suggested_action(self) -> str:
            """Suggested removal action for this candidate."""
            ...

        @property
        def runtime_reference_sites(
            self,
        ) -> tuple[FlextInfraProtocolsCensus.ReferenceSite, ...]:
            """Runtime/source references blocking full deletion."""
            ...

        @property
        def script_reference_sites(
            self,
        ) -> tuple[FlextInfraProtocolsCensus.ReferenceSite, ...]:
            """Script references supporting this candidate."""
            ...

    @runtime_checkable
    class Violation(
        FlextInfraProtocolsMixins.ProjectNameMixin,
        FlextInfraProtocolsBase.FrozenArbitrary,
        Protocol,
    ):
        """Structural data contract projected from the owning model."""

        @property
        def object_name(self) -> t.NonEmptyStr:
            """Name of the violating object."""
            ...

        @property
        def object_kind(self) -> str:
            """Object kind (constant/type/protocol/model/utility)."""
            ...

        @property
        def kind(self) -> str:
            """Analysis kind (duplicate/unused/wrong_tier)."""
            ...

        @property
        def severity(self) -> str:
            """Severity level."""
            ...

        @property
        def file_path(self) -> str:
            """File containing violation."""
            ...

        @property
        def line(self) -> t.NonNegativeInt:
            """Line number."""
            ...

        @property
        def description(self) -> str:
            """Human-readable violation description."""
            ...

    @runtime_checkable
    class ScanConfig(FlextInfraProtocolsBase.FrozenArbitrary, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def kind_names(self) -> Sequence[str] | None:
            """Symbol-kind filters."""
            ...

        @property
        def rule_names(self) -> Sequence[str] | None:
            """Violation-rule filters."""
            ...

        @property
        def selected_families(self) -> frozenset[str]:
            """Resolved namespace families."""
            ...

        @property
        def selected_kinds(self) -> frozenset[str] | None:
            """Precomputed kind set."""
            ...

        @property
        def selected_rules(self) -> frozenset[str] | None:
            """Precomputed rule set."""
            ...

        @property
        def include_object_references(self) -> bool:
            """Whether to resolve object references."""
            ...

        @property
        def include_local_scopes(self) -> bool:
            """Whether to include local/nested scopes."""
            ...

    @runtime_checkable
    class ScanFindings(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def project_objects(
            self,
        ) -> MutableMapping[str, MutableSequence[FlextInfraProtocolsCensus.Object]]:
            """Object inventory accumulated per project."""
            ...

        @property
        def report_projects(self) -> MutableSet[str]:
            """Projects whose modules produced a census outcome."""
            ...

    @runtime_checkable
    class AliasCensus(FlextInfraProtocolsBase.FrozenArbitrary, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def name(self) -> t.NonEmptyStr:
            """Alias declaration name."""
            ...

        @property
        def canonical(self) -> str:
            """Canonical target name."""
            ...

        @property
        def owner_module(self) -> str:
            """Module owning the alias declaration."""
            ...

        @property
        def kind(self) -> str:
            """Alias kind (assignment/import-alias/all-entry)."""
            ...

        @property
        def users(self) -> tuple[FlextInfraProtocolsCensus.ReferenceSite, ...]:
            """Reference sites using alias."""
            ...

        @property
        def fixable(self) -> bool:
            """Whether the existing cutover can cure it."""
            ...

        @property
        def reason(self) -> str:
            """Why the row is review-only, when it is."""
            ...

        @property
        def cure(self) -> str:
            """Canonical cure owner or command."""
            ...

    @runtime_checkable
    class DuplicateCensus(FlextInfraProtocolsBase.FrozenArbitrary, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def name(self) -> t.NonEmptyStr:
            """Duplicate declaration name."""
            ...

        @property
        def kind(self) -> str:
            """Duplicate object kind."""
            ...

        @property
        def canonical_owner(self) -> str:
            """Elected canonical owner module."""
            ...

        @property
        def modules(self) -> tuple[str, ...]:
            """Modules declaring the name."""
            ...

        @property
        def payload_fingerprint(self) -> str:
            """Diagnostic declaration fingerprint."""
            ...

        @property
        def users(self) -> tuple[FlextInfraProtocolsCensus.ReferenceSite, ...]:
            """Reference sites using copies."""
            ...

        @property
        def fixable(self) -> bool:
            """Whether the duplicate cure can apply it."""
            ...

        @property
        def reason(self) -> str:
            """Why the row is review-only, when it is."""
            ...

        @property
        def cure(self) -> str:
            """Canonical cure owner or command."""
            ...

    @runtime_checkable
    class ShortestFormCensus(FlextInfraProtocolsBase.FrozenArbitrary, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def target(self) -> t.NonEmptyStr:
            """Declaration or use."""
            ...

        @property
        def current_form(self) -> str:
            """Current longer form."""
            ...

        @property
        def canonical_form(self) -> str:
            """Canonical shortest form."""
            ...

        @property
        def kind(self) -> str:
            """Shortest-form kind (wrapper/ceremony/all-entry)."""
            ...

        @property
        def users(self) -> tuple[FlextInfraProtocolsCensus.ReferenceSite, ...]:
            """Reference sites using form."""
            ...

        @property
        def fixable(self) -> bool:
            """Whether the existing owner can cure it."""
            ...

        @property
        def reason(self) -> str:
            """Why the row is review-only, when it is."""
            ...

        @property
        def cure(self) -> str:
            """Canonical cure owner or command."""
            ...

    @runtime_checkable
    class CensusFixPlan(FlextInfraProtocolsBase.FrozenArbitrary, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def alias(self) -> tuple[FlextInfraProtocolsCensus.AliasCensus, ...]:
            """Fixable alias rows."""
            ...

        @property
        def duplicate(self) -> tuple[FlextInfraProtocolsCensus.DuplicateCensus, ...]:
            """Fixable duplicate rows."""
            ...

        @property
        def shortest_form(
            self,
        ) -> tuple[FlextInfraProtocolsCensus.ShortestFormCensus, ...]:
            """Fixable shortest-form rows."""
            ...

        @property
        def commands(self) -> tuple[str, ...]:
            """Canonical cure commands per owner."""
            ...

        @property
        def expected_rescan(self) -> t.NonNegativeInt:
            """Rows expected to disappear after cure."""
            ...

    @runtime_checkable
    class DuplicateDefinition(FlextInfraProtocolsBase.FrozenArbitrary, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def item(self) -> FlextInfraProtocolsCensus.Object:
            """Canonical census object."""
            ...

        @property
        def path(self) -> Path:
            """Definition source path."""
            ...

        @property
        def source(self) -> str:
            """Captured module source."""
            ...

        @property
        def statement(self) -> FlextInfraProtocolsRope.LogicalStatement | None:
            """Original Rope definition region."""
            ...

        @property
        def body(self) -> str:
            """Definition source span."""
            ...

        @property
        def consumers(self) -> int:
            """Proven consumer count."""
            ...

        @property
        def layer(self) -> int:
            """Discovered project layer."""
            ...

    @runtime_checkable
    class DuplicateCopyCure(FlextInfraProtocolsBase.FrozenArbitrary, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def definition(self) -> FlextInfraProtocolsCensus.DuplicateDefinition:
            """Verified duplicate definition."""
            ...

        @property
        def consumer_files(self) -> tuple[Path, ...]:
            """Consumers requiring import rebindings."""
            ...

        @property
        def in_module_uses(self) -> int:
            """References within the definition module."""
            ...

    @runtime_checkable
    class DuplicateGroupCure(FlextInfraProtocolsBase.FrozenArbitrary, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def owner(self) -> FlextInfraProtocolsCensus.DuplicateCopyCure:
            """Elected definition and its bindings."""
            ...

        @property
        def copies(self) -> tuple[FlextInfraProtocolsCensus.DuplicateCopyCure, ...]:
            """Copies with proven removal contracts."""
            ...

        @property
        def edits(
            self,
        ) -> tuple[FlextInfraProtocolsTransformers.SemanticMigrationEdit, ...]:
            """Complete proposed source edits."""
            ...

    @runtime_checkable
    class DuplicateDeletion(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def path(self) -> Path:
            """Copy source path."""
            ...

        @property
        def name(self) -> str:
            """Duplicate object name."""
            ...

        @property
        def line(self) -> int:
            """Copy definition line."""
            ...

        @property
        def project(self) -> str:
            """Discovered project identity."""
            ...

    @runtime_checkable
    class DuplicateGroup(FlextInfraProtocolsBase.FrozenArbitrary, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def name(self) -> t.NonEmptyStr:
            """Shared object name across projects."""
            ...

        @property
        def kind(self) -> str:
            """Object kind."""
            ...

        @property
        def definitions(self) -> MutableSequence[FlextInfraProtocolsCensus.Object]:
            """All definitions of this object."""
            ...

        @property
        def canonical(self) -> str:
            """Most-upstream project (canonical source)."""
            ...

        @property
        def value_identical(self) -> bool:
            """Whether all definitions have identical values."""
            ...

        @property
        def semantic_candidate(self) -> bool:
            """Structural member projected from the owning model.

            Diagnostic Pydantic declarations sharing native structure across names
            or holders; automatic cure requires independent identity and complete
            consumer proof.
            """
            ...

    @runtime_checkable
    class DuplicateCureEdit(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def file_path(self) -> Path:
            """File the cure edit touches."""
            ...

        @property
        def line(self) -> t.PositiveInt:
            """One-based definition or import line of the edit."""
            ...

        @property
        def action(self) -> t.NonEmptyStr:
            """Cure action: keep-owner, delete-copy, rebind-import or bind-owner."""
            ...

        @property
        def detail(self) -> t.NonEmptyStr:
            """Human-readable cure step for review."""
            ...

    @runtime_checkable
    class DuplicateCurePlan(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def name(self) -> t.NonEmptyStr:
            """Duplicated object name."""
            ...

        @property
        def kind(self) -> str:
            """Duplicated object kind."""
            ...

        @property
        def origin(self) -> t.NonEmptyStr:
            """Plan origin: census group or jscpd clone."""
            ...

        @property
        def reason(self) -> t.NonEmptyStr:
            """Why the engine did not auto-unify this duplicate."""
            ...

        @property
        def owner_file_path(self) -> Path:
            """Elected owner definition file."""
            ...

        @property
        def owner_line(self) -> t.PositiveInt:
            """Elected owner definition line."""
            ...

        @property
        def owner_project(self) -> str:
            """Project of the elected owner."""
            ...

        @property
        def edits(self) -> tuple[FlextInfraProtocolsCensus.DuplicateCureEdit, ...]:
            """Proposed manual edits, owner first."""
            ...

    @runtime_checkable
    class DuplicateCureOutcome(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def edits(
            self,
        ) -> tuple[FlextInfraProtocolsTransformers.SemanticMigrationEdit, ...]:
            """Applied source rewrites."""
            ...

        @property
        def plans(self) -> tuple[FlextInfraProtocolsCensus.DuplicateCurePlan, ...]:
            """Manual assisted-cure plans for structural duplicates."""
            ...

        @property
        def files_changed(self) -> t.NonNegativeInt:
            """Files the applied cure rewrote."""
            ...

        @property
        def copies_removed(self) -> t.NonNegativeInt:
            """Duplicate definitions the applied cure deleted."""
            ...

        @property
        def bindings_rewired(self) -> t.NonNegativeInt:
            """Consumer imports the applied cure rebound."""
            ...

    @runtime_checkable
    class ProjectReport(
        FlextInfraProtocolsMixins.ProjectNameMixin,
        FlextInfraProtocolsBase.FrozenArbitrary,
        Protocol,
    ):
        """Structural data contract projected from the owning model."""

        @property
        def objects(self) -> tuple[FlextInfraProtocolsCensus.Object, ...]:
            """Objects discovered for this project."""
            ...

        @property
        def objects_total(self) -> t.NonNegativeInt:
            """Total objects discovered."""
            ...

        @property
        def objects_by_kind(self) -> t.IntMapping:
            """Object count per kind."""
            ...

        @property
        def violations(self) -> tuple[FlextInfraProtocolsCensus.Violation, ...]:
            """Detected violations."""
            ...

        @property
        def violations_total(self) -> t.NonNegativeInt:
            """Total violation count."""
            ...

        @property
        def unused_count(self) -> t.NonNegativeInt:
            """Objects with no non-definition references."""
            ...

        @property
        def removal_candidate_count(self) -> t.NonNegativeInt:
            """Objects eligible for aggressive removal review."""
            ...

        @property
        def removal_candidates(
            self,
        ) -> tuple[FlextInfraProtocolsCensus.RemovalCandidate, ...]:
            """Explicit aggressive-removal candidates for this project."""
            ...

    @runtime_checkable
    class WorkspaceReport(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        constant_consumer_files: t.NonNegativeInt
        constant_consumer_bindings: t.NonNegativeInt
        duplicate_cure_files: t.NonNegativeInt
        duplicate_cure_copies: t.NonNegativeInt
        duplicate_cure_bindings: t.NonNegativeInt
        projects: tuple[FlextInfraProtocolsCensus.ProjectReport, ...]
        total_objects: t.NonNegativeInt
        total_violations: t.NonNegativeInt
        duplicates: tuple[FlextInfraProtocolsCensus.DuplicateGroup, ...]
        duplicate_cure_plans: tuple[FlextInfraProtocolsCensus.DuplicateCurePlan, ...]
        unused_count: t.NonNegativeInt
        removal_candidate_count: t.NonNegativeInt
        removal_candidates: tuple[FlextInfraProtocolsCensus.RemovalCandidate, ...]
        alias_census: tuple[FlextInfraProtocolsCensus.AliasCensus, ...]
        duplicate_census: tuple[FlextInfraProtocolsCensus.DuplicateCensus, ...]
        shortest_form_census: tuple[FlextInfraProtocolsCensus.ShortestFormCensus, ...]
        census_fix_plan: FlextInfraProtocolsCensus.CensusFixPlan
        scan_duration_seconds: float
        parse_errors: t.NonNegativeInt


__all__: list[str] = [
    "FlextInfraProtocolsCensus",
]
