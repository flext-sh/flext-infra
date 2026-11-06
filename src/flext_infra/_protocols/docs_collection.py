# AUTO-GENERATED FILE — Regenerate with: make gen
"""Source-derived structural model contracts.

Copyright (c) 2026 FLEXT Team. All rights reserved.
src/flext_infra/_protocols/docs_collection
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Literal, Protocol, runtime_checkable

from flext_cli import FlextCliProtocols

if TYPE_CHECKING:
    from flext_infra import t
    from flext_infra._protocols._codegen import FlextInfraProtocolsCodegenTransaction


class FlextInfraProtocolsDocsCollection:
    """Own the structural contracts declared by its model source."""

    @runtime_checkable
    class PlanCollectionTimestamp(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def value(self) -> t.Infra.PlanSourceTimestamp:
            """Native YAML date, instant, or explicitly quoted timestamp."""
            ...

    @runtime_checkable
    class PlanCollectionSource(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def id(self) -> str:
            """Stable source association identity."""
            ...

        @property
        def provider(self) -> t.NonEmptyStr:
            """Declared source provider."""
            ...

        @property
        def root(self) -> Path:
            """Declared physical source root."""
            ...

        @property
        def adapter(self) -> Literal["files", "private-inventory"]:
            """Selected deterministic source adapter."""
            ...

        @property
        def driver(self) -> t.NonEmptyStr:
            """Source driver provenance."""
            ...

        @property
        def driver_version(self) -> t.NonEmptyStr:
            """Declared source driver version."""
            ...

        @property
        def plan_globs(self) -> tuple[str, ...]:
            """Explicit plan discovery patterns."""
            ...

        @property
        def exclude_globs(self) -> tuple[str, ...]:
            """Explicit source exclusions."""
            ...

        @property
        def updated_fields(self) -> tuple[str, ...]:
            """Source-owned substantive update fields in priority order."""
            ...

        @property
        def companion_directory(self) -> bool:
            """Collect the same-basename artifact directory."""
            ...

        @property
        def publication(self) -> Literal["plan-artifacts", "private"]:
            """Authorized publication classification."""
            ...

    @runtime_checkable
    class PlanCollectionConfig(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def enabled(self) -> bool:
            """Explicit authorization for plan source publication."""
            ...

        @property
        def canonical_dir(self) -> Path:
            """Repository-relative canonical plan destination."""
            ...

        @property
        def projection_root(self) -> Path | None:
            """Separately authorized absolute projection owner."""
            ...

        @property
        def sources(
            self,
        ) -> tuple[FlextInfraProtocolsDocsCollection.PlanCollectionSource, ...]:
            """Complete explicitly associated source inventory."""
            ...

    @runtime_checkable
    class PlanCollectionRevision(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def identity(self) -> t.NonEmptyStr:
            """Stable collected plan identity."""
            ...

        @property
        def provider(self) -> t.NonEmptyStr:
            """Provider supplying this revision."""
            ...

        @property
        def source_id(self) -> t.NonEmptyStr:
            """Source association supplying this revision."""
            ...

        @property
        def source_path(self) -> Path:
            """Structural member projected from the owning model.

            Source-association-relative locator without private root disclosure.
            """
            ...

        @property
        def driver(self) -> t.NonEmptyStr:
            """Source driver provenance."""
            ...

        @property
        def driver_version(self) -> t.NonEmptyStr:
            """Source driver version."""
            ...

        @property
        def digest(self) -> t.NonEmptyStr:
            """Content digest including attachments."""
            ...

        @property
        def canonical_path(self) -> Path:
            """Canonical-owner-relative stable plan destination."""
            ...

        @property
        def source_updated_at(self) -> str | None:
            """Source update in UTC or original incomplete precision."""
            ...

        @property
        def source_updated_at_original(self) -> str | None:
            """Declared source timestamp before UTC conversion."""
            ...

        @property
        def source_updated_at_utc(self) -> str | None:
            """UTC instant only when the source declares a timezone."""
            ...

        @property
        def collected_at(self) -> t.NonEmptyStr:
            """First collection timestamp for this immutable revision."""
            ...

        @property
        def attachments(self) -> tuple[str, ...]:
            """Companion-relative attachment identities."""
            ...

    @runtime_checkable
    class PlanCollectionOwnedArtifact(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def relative_path(self) -> Path:
            """Destination-relative generated artifact path."""
            ...

        @property
        def digest(self) -> t.NonEmptyStr:
            """Exact generated byte digest."""
            ...

    @runtime_checkable
    class PlanCollectionManifest(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def configuration_sha256(self) -> t.NonEmptyStr | None:
            """Structural member projected from the owning model.

            Typed source association digest; None only before first collection.
            """
            ...

        @property
        def coverage(
            self,
        ) -> tuple[FlextInfraProtocolsDocsCollection.PlanCollectionCoverage, ...]:
            """Complete source coverage from the published collection."""
            ...

        @property
        def revisions(
            self,
        ) -> tuple[FlextInfraProtocolsDocsCollection.PlanCollectionRevision, ...]:
            """Immutable observed source revision history."""
            ...

        @property
        def artifacts(
            self,
        ) -> tuple[FlextInfraProtocolsDocsCollection.PlanCollectionOwnedArtifact, ...]:
            """Digest-attested generated artifact ownership."""
            ...

    @runtime_checkable
    class PlanCollectionCoverage(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def source_id(self) -> t.NonEmptyStr:
            """Source association identity."""
            ...

        @property
        def provider(self) -> t.NonEmptyStr:
            """Declared provider."""
            ...

        @property
        def adapter(self) -> Literal["files", "private-inventory"]:
            """Executed adapter."""
            ...

        @property
        def files(self) -> t.NonNegativeInt:
            """Number of discovered source files."""
            ...

        @property
        def source_revisions(self) -> tuple[tuple[Path, t.NonEmptyStr], ...]:
            """Source-relative plans and revision digests observed in this run."""
            ...

        @property
        def status(self) -> Literal["collected", "private-inventory", "empty"]:
            """Observed collection coverage, not reconciliation status."""
            ...

        @property
        def private_paths(self) -> tuple[Path, ...]:
            """Private source references without transcript contents."""
            ...

    @runtime_checkable
    class PlanCollectionBundle(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def files(
            self,
        ) -> tuple[FlextInfraProtocolsCodegenTransaction.CodegenFilePlan, ...]:
            """Effects published through the shared publisher."""
            ...

        prunable_directories: tuple[Path, ...]

        @property
        def revisions(
            self,
        ) -> tuple[FlextInfraProtocolsDocsCollection.PlanCollectionRevision, ...]:
            """Latest newly observed revision per plan."""
            ...

        @property
        def coverage(
            self,
        ) -> tuple[FlextInfraProtocolsDocsCollection.PlanCollectionCoverage, ...]:
            """Explicit per-source collection coverage."""
            ...


__all__: list[str] = [
    "FlextInfraProtocolsDocsCollection",
]
