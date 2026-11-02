# AUTO-GENERATED FILE — Regenerate with: make gen
"""Source-derived structural model contracts."""

from __future__ import annotations

from collections.abc import MutableMapping, MutableSequence, Sequence
from pathlib import Path
from typing import Protocol, runtime_checkable

from flext_infra import p, t


class FlextInfraProtocolsCensus:
    """Own the structural model contracts declared by this module."""

    @runtime_checkable
    class CensusOptions(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def consumer_roots(self) -> tuple[Path, ...]: ...

        @property
        def source_plan_output(self) -> Path | None: ...

        @property
        def json_output(self) -> str | None: ...

        @property
        def impact_map_output(self) -> str | None: ...

        @property
        def kinds(self) -> Sequence[str] | None: ...

        @property
        def rules(self) -> Sequence[str] | None: ...

        @property
        def families(self) -> Sequence[str] | None: ...

        @property
        def include_local_scopes(self) -> bool: ...

    @runtime_checkable
    class ReferenceSite(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def surface(self) -> str: ...

        @property
        def offset(self) -> t.NonNegativeInt | None: ...

    @runtime_checkable
    class Object(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def name(self) -> t.NonEmptyStr: ...

        @property
        def kind(self) -> str: ...

        @property
        def module_name(self) -> str: ...

        @property
        def scope_path(self) -> str: ...

        @property
        def actual_tier(self) -> str: ...

        @property
        def expected_tier(self) -> str: ...

        @property
        def is_facade_member(self) -> bool: ...

        @property
        def references_count(self) -> t.NonNegativeInt: ...

        @property
        def runtime_references_count(self) -> t.NonNegativeInt: ...

        @property
        def script_references_count(self) -> t.NonNegativeInt: ...

        @property
        def runtime_reference_sites(self) -> tuple[p.Infra.ReferenceSite, ...]: ...

        @property
        def script_reference_sites(self) -> tuple[p.Infra.ReferenceSite, ...]: ...

        @property
        def all_reference_sites(self) -> tuple[p.Infra.ReferenceSite, ...]: ...

        @property
        def reference_evidence_collected(self) -> bool: ...

        @property
        def fingerprint(self) -> str: ...

        @property
        def payload_fingerprint(self) -> str: ...

    @runtime_checkable
    class RemovalPreviewOptions(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def gates(self) -> Sequence[str]: ...

        @property
        def source_cache(self) -> MutableMapping[Path, str] | None: ...

    @runtime_checkable
    class RemovalCandidate(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def object_name(self) -> t.NonEmptyStr: ...

        @property
        def object_kind(self) -> str: ...

        @property
        def scope_path(self) -> str: ...

        @property
        def reason(self) -> str: ...

        @property
        def suggested_action(self) -> str: ...

        @property
        def runtime_reference_sites(self) -> tuple[p.Infra.ReferenceSite, ...]: ...

        @property
        def script_reference_sites(self) -> tuple[p.Infra.ReferenceSite, ...]: ...

    @runtime_checkable
    class Violation(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def object_name(self) -> t.NonEmptyStr: ...

        @property
        def object_kind(self) -> str: ...

        @property
        def kind(self) -> str: ...

        @property
        def severity(self) -> str: ...

        @property
        def file_path(self) -> str: ...

        @property
        def line(self) -> t.NonNegativeInt: ...

        @property
        def description(self) -> str: ...

    @runtime_checkable
    class ScanConfig(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def kind_names(self) -> Sequence[str] | None: ...

        @property
        def rule_names(self) -> Sequence[str] | None: ...

        @property
        def selected_families(self) -> frozenset[str]: ...

        @property
        def selected_kinds(self) -> frozenset[str] | None: ...

        @property
        def selected_rules(self) -> frozenset[str] | None: ...

        @property
        def include_object_references(self) -> bool: ...

        @property
        def include_local_scopes(self) -> bool: ...

    @runtime_checkable
    class DuplicateDefinition(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def item(self) -> p.Infra.Object: ...

        @property
        def path(self) -> Path: ...

        @property
        def source(self) -> str: ...

        @property
        def statement(self) -> p.Infra.LogicalStatement | None: ...

        @property
        def body(self) -> str: ...

        @property
        def consumers(self) -> int: ...

        @property
        def layer(self) -> int: ...

    @runtime_checkable
    class DuplicateCopyCure(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def definition(self) -> p.Infra.DuplicateDefinition: ...

        @property
        def consumer_files(self) -> tuple[Path, ...]: ...

        @property
        def in_module_uses(self) -> int: ...

    @runtime_checkable
    class DuplicateGroupCure(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def owner(self) -> p.Infra.DuplicateCopyCure: ...

        @property
        def copies(self) -> tuple[p.Infra.DuplicateCopyCure, ...]: ...

        @property
        def edits(self) -> tuple[p.Infra.SemanticMigrationEdit, ...]: ...

    @runtime_checkable
    class DuplicateDeletion(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def path(self) -> Path: ...

        @property
        def name(self) -> str: ...

        @property
        def line(self) -> int: ...

        @property
        def project(self) -> str: ...

    @runtime_checkable
    class DuplicateGroup(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def name(self) -> t.NonEmptyStr: ...

        @property
        def kind(self) -> str: ...

        @property
        def definitions(self) -> MutableSequence[p.Infra.Object]: ...

        @property
        def canonical(self) -> str: ...

        @property
        def value_identical(self) -> bool: ...

        @property
        def semantic_candidate(self) -> bool: ...

    @runtime_checkable
    class DuplicateCureEdit(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def file_path(self) -> Path: ...

        @property
        def line(self) -> t.PositiveInt: ...

        @property
        def action(self) -> t.NonEmptyStr: ...

        @property
        def detail(self) -> t.NonEmptyStr: ...

    @runtime_checkable
    class DuplicateCurePlan(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def name(self) -> t.NonEmptyStr: ...

        @property
        def kind(self) -> str: ...

        @property
        def origin(self) -> t.NonEmptyStr: ...

        @property
        def reason(self) -> t.NonEmptyStr: ...

        @property
        def owner_file_path(self) -> Path: ...

        @property
        def owner_line(self) -> t.PositiveInt: ...

        @property
        def owner_project(self) -> str: ...

        @property
        def edits(self) -> tuple[p.Infra.DuplicateCureEdit, ...]: ...

    @runtime_checkable
    class DuplicateCureOutcome(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def edits(self) -> tuple[p.Infra.SemanticMigrationEdit, ...]: ...

        @property
        def plans(self) -> tuple[p.Infra.DuplicateCurePlan, ...]: ...

        @property
        def files_changed(self) -> t.NonNegativeInt: ...

        @property
        def copies_removed(self) -> t.NonNegativeInt: ...

        @property
        def bindings_rewired(self) -> t.NonNegativeInt: ...

    @runtime_checkable
    class ProjectReport(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def objects(self) -> tuple[p.Infra.Object, ...]: ...

        @property
        def objects_total(self) -> t.NonNegativeInt: ...

        @property
        def objects_by_kind(self) -> t.IntMapping: ...

        @property
        def violations(self) -> tuple[p.Infra.Violation, ...]: ...

        @property
        def violations_total(self) -> t.NonNegativeInt: ...

        @property
        def unused_count(self) -> t.NonNegativeInt: ...

        @property
        def removal_candidate_count(self) -> t.NonNegativeInt: ...

        @property
        def removal_candidates(self) -> tuple[p.Infra.RemovalCandidate, ...]: ...


__all__: list[str] = [
    "FlextInfraProtocolsCensus",
]
