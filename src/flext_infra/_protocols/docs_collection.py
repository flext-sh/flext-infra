# AUTO-GENERATED FILE — Regenerate with: make gen
"""Source-derived structural model contracts.

Copyright (c) 2026 FLEXT Team. All rights reserved.
src/flext_infra/_protocols/docs_collection
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Literal, Protocol, runtime_checkable

from flext_infra import t

if TYPE_CHECKING:
    from flext_infra import p


class FlextInfraProtocolsDocsCollection:
    """Own the structural contracts declared by its model source."""

    @runtime_checkable
    class PlanCollectionTimestamp(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def value(self) -> t.Infra.PlanSourceTimestamp: ...

    @runtime_checkable
    class PlanCollectionSource(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def id(self) -> str: ...
        @property
        def provider(self) -> t.NonEmptyStr: ...
        @property
        def root(self) -> Path: ...
        @property
        def adapter(self) -> Literal["files", "private-inventory"]: ...
        @property
        def driver(self) -> t.NonEmptyStr: ...
        @property
        def driver_version(self) -> t.NonEmptyStr: ...
        @property
        def plan_globs(self) -> tuple[str, ...]: ...
        @property
        def exclude_globs(self) -> tuple[str, ...]: ...
        @property
        def updated_fields(self) -> tuple[str, ...]: ...
        @property
        def companion_directory(self) -> bool: ...
        @property
        def publication(self) -> Literal["plan-artifacts", "private"]: ...

    @runtime_checkable
    class PlanCollectionConfig(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def enabled(self) -> bool: ...
        @property
        def canonical_dir(self) -> Path: ...
        @property
        def projection_root(self) -> Path | None: ...
        @property
        def sources(self) -> tuple[p.Infra.PlanCollectionSource, ...]: ...

    @runtime_checkable
    class PlanCollectionRevision(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def identity(self) -> t.NonEmptyStr: ...
        @property
        def provider(self) -> t.NonEmptyStr: ...
        @property
        def source_id(self) -> t.NonEmptyStr: ...
        @property
        def source_path(self) -> Path: ...
        @property
        def driver(self) -> t.NonEmptyStr: ...
        @property
        def driver_version(self) -> t.NonEmptyStr: ...
        @property
        def digest(self) -> t.NonEmptyStr: ...
        @property
        def canonical_path(self) -> Path: ...
        @property
        def source_updated_at(self) -> str | None: ...
        @property
        def source_updated_at_original(self) -> str | None: ...
        @property
        def source_updated_at_utc(self) -> str | None: ...
        @property
        def collected_at(self) -> t.NonEmptyStr: ...
        @property
        def attachments(self) -> tuple[str, ...]: ...

    @runtime_checkable
    class PlanCollectionOwnedArtifact(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def relative_path(self) -> Path: ...
        @property
        def digest(self) -> t.NonEmptyStr: ...

    @runtime_checkable
    class PlanCollectionManifest(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def configuration_sha256(self) -> t.NonEmptyStr | None: ...
        @property
        def coverage(self) -> tuple[p.Infra.PlanCollectionCoverage, ...]: ...
        @property
        def revisions(self) -> tuple[p.Infra.PlanCollectionRevision, ...]: ...
        @property
        def artifacts(self) -> tuple[p.Infra.PlanCollectionOwnedArtifact, ...]: ...

    @runtime_checkable
    class PlanCollectionCoverage(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def source_id(self) -> t.NonEmptyStr: ...
        @property
        def provider(self) -> t.NonEmptyStr: ...
        @property
        def adapter(self) -> Literal["files", "private-inventory"]: ...
        @property
        def files(self) -> t.NonNegativeInt: ...
        @property
        def source_revisions(self) -> tuple[tuple[Path, t.NonEmptyStr], ...]: ...
        @property
        def status(self) -> Literal["collected", "private-inventory", "empty"]: ...
        @property
        def private_paths(self) -> tuple[Path, ...]: ...

    @runtime_checkable
    class PlanCollectionBundle(Protocol):
        """Structural data contract projected from the owning model."""

        files: tuple[p.Infra.CodegenFilePlan, ...]
        prunable_directories: tuple[Path, ...]
        revisions: tuple[p.Infra.PlanCollectionRevision, ...]
        coverage: tuple[p.Infra.PlanCollectionCoverage, ...]


__all__: list[str] = [
    "FlextInfraProtocolsDocsCollection",
]
