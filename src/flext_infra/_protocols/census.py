# AUTO-GENERATED FILE — Regenerate with: make gen
"""Source-derived structural model contracts."""

from __future__ import annotations

from collections.abc import MutableMapping, MutableSequence, Sequence
from pathlib import Path
from typing import Protocol, runtime_checkable

from flext_infra import t
from flext_infra._models import FlextInfraModelsRope, FlextInfraModelsTransformers


class FlextInfraProtocolsCensus:
    """Own the structural model contracts declared by this module."""

    @runtime_checkable
    class ReferenceSite(Protocol):
        """Structural data contract projected from the owning model."""

        surface: str = ...
        offset: t.NonNegativeInt | None = ...

    @runtime_checkable
    class Object(Protocol):
        """Structural data contract projected from the owning model."""

        name: t.NonEmptyStr
        kind: str
        module_name: str = ...
        scope_path: str = ...
        actual_tier: str = ...
        expected_tier: str = ...
        is_facade_member: bool = ...
        references_count: t.NonNegativeInt = ...
        runtime_references_count: t.NonNegativeInt = ...
        script_references_count: t.NonNegativeInt = ...
        runtime_reference_sites: tuple[FlextInfraModelsCensus.ReferenceSite, ...] = ...
        script_reference_sites: tuple[FlextInfraModelsCensus.ReferenceSite, ...] = ...
        all_reference_sites: tuple[FlextInfraModelsCensus.ReferenceSite, ...] = ...
        reference_evidence_collected: bool = ...
        fingerprint: str = ...
        payload_fingerprint: str = ...

    @runtime_checkable
    class RemovalPreviewOptions(Protocol):
        """Structural data contract projected from the owning model."""

        gates: Sequence[str]
        source_cache: MutableMapping[Path, str] | None = ...

    @runtime_checkable
    class RemovalCandidate(Protocol):
        """Structural data contract projected from the owning model."""

        object_name: t.NonEmptyStr
        object_kind: str
        scope_path: str = ...
        reason: str
        suggested_action: str
        runtime_reference_sites: tuple[FlextInfraModelsCensus.ReferenceSite, ...] = ...
        script_reference_sites: tuple[FlextInfraModelsCensus.ReferenceSite, ...] = ...

    @runtime_checkable
    class Violation(Protocol):
        """Structural data contract projected from the owning model."""

        object_name: t.NonEmptyStr
        object_kind: str
        kind: str
        severity: str = ...
        file_path: str
        line: t.NonNegativeInt = ...
        description: str = ...

    @runtime_checkable
    class ScanConfig(Protocol):
        """Structural data contract projected from the owning model."""

        kind_names: Sequence[str] | None
        rule_names: Sequence[str] | None
        selected_families: frozenset[str]
        selected_kinds: frozenset[str] | None
        selected_rules: frozenset[str] | None
        include_object_references: bool
        include_local_scopes: bool

    @runtime_checkable
    class DuplicateDefinition(Protocol):
        """Structural data contract projected from the owning model."""

        item: FlextInfraModelsCensus.Object
        path: Path
        source: str
        statement: FlextInfraModelsRope.LogicalStatement | None
        body: str
        consumers: int
        layer: int

    @runtime_checkable
    class DuplicateCopyCure(Protocol):
        """Structural data contract projected from the owning model."""

        definition: FlextInfraModelsCensus.DuplicateDefinition
        consumer_files: tuple[Path, ...]
        in_module_uses: int

    @runtime_checkable
    class DuplicateGroupCure(Protocol):
        """Structural data contract projected from the owning model."""

        owner: FlextInfraModelsCensus.DuplicateCopyCure
        copies: tuple[FlextInfraModelsCensus.DuplicateCopyCure, ...]
        edits: tuple[FlextInfraModelsTransformers.SemanticMigrationEdit, ...]

    @runtime_checkable
    class DuplicateDeletion(Protocol):
        """Structural data contract projected from the owning model."""

        path: Path
        name: str
        line: int
        project: str

    @runtime_checkable
    class DuplicateGroup(Protocol):
        """Structural data contract projected from the owning model."""

        name: t.NonEmptyStr
        kind: str
        definitions: MutableSequence[FlextInfraModelsCensus.Object] = ...
        canonical: str = ...
        value_identical: bool = ...
        semantic_candidate: bool = ...

    @runtime_checkable
    class DuplicateCureEdit(Protocol):
        """Structural data contract projected from the owning model."""

        file_path: Path
        line: t.PositiveInt
        action: t.NonEmptyStr
        detail: t.NonEmptyStr

    @runtime_checkable
    class DuplicateCurePlan(Protocol):
        """Structural data contract projected from the owning model."""

        name: t.NonEmptyStr
        kind: str
        origin: t.NonEmptyStr
        reason: t.NonEmptyStr
        owner_file_path: Path
        owner_line: t.PositiveInt
        owner_project: str = ...
        edits: tuple[FlextInfraModelsCensus.DuplicateCureEdit, ...] = ...

    @runtime_checkable
    class DuplicateCureOutcome(Protocol):
        """Structural data contract projected from the owning model."""

        edits: tuple[FlextInfraModelsTransformers.SemanticMigrationEdit, ...] = ...
        plans: tuple[FlextInfraModelsCensus.DuplicateCurePlan, ...] = ...
        files_changed: t.NonNegativeInt = ...
        copies_removed: t.NonNegativeInt = ...
        bindings_rewired: t.NonNegativeInt = ...

    @runtime_checkable
    class ProjectReport(Protocol):
        """Structural data contract projected from the owning model."""

        objects: tuple[FlextInfraModelsCensus.Object, ...] = ...
        objects_total: t.NonNegativeInt = ...
        objects_by_kind: t.IntMapping
        violations: tuple[FlextInfraModelsCensus.Violation, ...] = ...
        violations_total: t.NonNegativeInt = ...
        unused_count: t.NonNegativeInt = ...
        removal_candidate_count: t.NonNegativeInt = ...
        removal_candidates: tuple[FlextInfraModelsCensus.RemovalCandidate, ...] = ...


__all__: list[str] = [
    "FlextInfraProtocolsCensus",
]
