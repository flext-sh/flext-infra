"""Typed source associations and immutable plan-collection receipts."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated, Literal

from flext_cli import m as cli_m

from flext_core import m
from flext_infra import t

from .config import FlextInfraConfigModels


class FlextInfraModelsDocsCollection:
    """Collection describes provenance, never semantic execution status."""

    class PlanCollectionTimestamp(m.ContractModel):
        """Native YAML timestamp ingress without a JSON-shaped conversion."""

        value: t.Infra.PlanSourceTimestamp = m.Field(
            description="Native YAML date, instant, or explicitly quoted timestamp"
        )

    class PlanCollectionSource(m.ContractModel):
        """One explicitly associated provider source."""

        id: Annotated[
            str,
            m.Field(
                pattern=r"^[a-z][a-z0-9-]*$",
                description="Stable source association identity",
            ),
        ]
        provider: t.NonEmptyStr = m.Field(description="Declared source provider")
        root: Path = m.Field(description="Declared physical source root")
        adapter: Literal["files", "private-inventory"] = m.Field(
            description="Selected deterministic source adapter"
        )
        driver: t.NonEmptyStr = m.Field(description="Source driver provenance")
        driver_version: t.NonEmptyStr = m.Field(
            description="Declared source driver version"
        )
        plan_globs: Annotated[
            tuple[str, ...],
            m.Field(min_length=1, description="Explicit plan discovery patterns"),
        ]
        exclude_globs: tuple[str, ...] = m.Field(
            default=(), description="Explicit source exclusions"
        )
        updated_fields: tuple[str, ...] = m.Field(
            default=("source_updated_at",),
            description="Source-owned substantive update fields in priority order",
        )
        companion_directory: bool = m.Field(
            default=True, description="Collect the same-basename artifact directory"
        )
        publication: Literal["plan-artifacts", "private"] = m.Field(
            description="Authorized publication classification"
        )

    class PlanCollectionConfig(m.ContractModel):
        """Repository-owned associations; projection is separately authorized."""

        canonical_dir: Path = m.Field(
            description="Repository-relative canonical plan destination"
        )
        projection_root: Path | None = m.Field(
            default=None, description="Separately authorized absolute projection owner"
        )
        sources: Annotated[
            tuple[FlextInfraModelsDocsCollection.PlanCollectionSource, ...],
            m.Field(
                min_length=1,
                description="Complete explicitly associated source inventory",
            ),
        ]

    class PlanCollectionRevision(m.ContractModel):
        """Immutable source revision, including companion artifact digests."""

        identity: t.NonEmptyStr = m.Field(description="Stable collected plan identity")
        provider: t.NonEmptyStr = m.Field(
            description="Provider supplying this revision"
        )
        source_id: t.NonEmptyStr = m.Field(
            description="Source association supplying this revision"
        )
        source_path: Path = m.Field(
            description="Source-association-relative locator without private root disclosure"
        )
        driver: t.NonEmptyStr = m.Field(description="Source driver provenance")
        driver_version: t.NonEmptyStr = m.Field(description="Source driver version")
        digest: t.NonEmptyStr = m.Field(
            description="Content digest including attachments"
        )
        canonical_path: Path = m.Field(
            description="Canonical-owner-relative stable plan destination"
        )
        source_updated_at: str | None = m.Field(
            default=None,
            description="Source update in UTC or original incomplete precision",
        )
        source_updated_at_original: str | None = m.Field(
            default=None, description="Declared source timestamp before UTC conversion"
        )
        source_updated_at_utc: str | None = m.Field(
            default=None,
            description="UTC instant only when the source declares a timezone",
        )
        collected_at: t.NonEmptyStr = m.Field(
            description="First collection timestamp for this immutable revision"
        )
        attachments: tuple[str, ...] = m.Field(
            default=(), description="Companion-relative attachment identities"
        )

    class PlanCollectionSourceInventory(m.ContractModel):
        """Exact discovery topology, including private paths but no contents."""

        source_id: t.NonEmptyStr = m.Field(description="Source association identity")
        paths: tuple[Path, ...] = m.Field(
            description="Exact discovered plan and attachment paths"
        )

    class PlanCollectionOwnedArtifact(m.ContractModel):
        """Exact generated bytes that authorize ignoring a discovery output."""

        relative_path: Path = m.Field(
            description="Destination-relative generated artifact path"
        )
        digest: t.NonEmptyStr = m.Field(description="Exact generated byte digest")

    class PlanCollectionManifest(m.ContractModel):
        """Generated artifact ownership and provenance, never execution state."""

        revisions: tuple[FlextInfraModelsDocsCollection.PlanCollectionRevision, ...] = (
            m.Field(
                default=(), description="Immutable observed source revision history"
            )
        )
        artifacts: tuple[
            FlextInfraModelsDocsCollection.PlanCollectionOwnedArtifact, ...
        ] = m.Field(
            default=(), description="Digest-attested generated artifact ownership"
        )

    class PlanCollectionCoverage(m.ContractModel):
        """Observed source coverage, explicitly distinct from reconciliation."""

        source_id: t.NonEmptyStr = m.Field(description="Source association identity")
        provider: t.NonEmptyStr = m.Field(description="Declared provider")
        adapter: Literal["files", "private-inventory"] = m.Field(
            description="Executed adapter"
        )
        files: t.NonNegativeInt = m.Field(
            description="Number of discovered source files"
        )
        status: Literal["collected", "private-inventory", "empty"] = m.Field(
            description="Observed collection coverage, not reconciliation status"
        )
        private_paths: tuple[Path, ...] = m.Field(
            default=(),
            description="Private source references without transcript contents",
        )

    class PlanCollectionBundle(m.ArbitraryTypesModel):
        """Read-only planning result consumed by the existing publisher."""

        files: tuple[FlextInfraConfigModels.CodegenFilePlan, ...] = m.Field(
            description="Effects for the existing docs transaction"
        )
        source_states: tuple[cli_m.Cli.AtomicFileState, ...] = m.Field(
            description="Authenticated inputs and ownership reads including absence"
        )
        required_directories: tuple[Path, ...] = m.Field(
            description="Required destination parent chains"
        )
        revisions: tuple[FlextInfraModelsDocsCollection.PlanCollectionRevision, ...] = (
            m.Field(description="Latest newly observed revision per plan")
        )
        coverage: tuple[FlextInfraModelsDocsCollection.PlanCollectionCoverage, ...] = (
            m.Field(description="Explicit per-source collection coverage")
        )
        inventories: tuple[
            FlextInfraModelsDocsCollection.PlanCollectionSourceInventory, ...
        ] = m.Field(description="Authenticated discovery topology")
        excluded_outputs: tuple[Path, ...] = m.Field(
            description="Unchanged owned output paths excluded from source discovery"
        )


__all__: list[str] = ["FlextInfraModelsDocsCollection"]
