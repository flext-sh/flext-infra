"""Typed source associations and immutable plan-collection receipts.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import TYPE_CHECKING, Annotated, Literal, Self

from flext_cli import m

from flext_infra import t
from flext_infra._models._config.artifact import FlextInfraModelsConfigArtifact

if TYPE_CHECKING:
    from flext_infra import p


class FlextInfraModelsDocsCollection:
    """Collection describes provenance, never semantic execution status."""

    class PlanCollectionTimestamp(m.ContractModel):
        """Native YAML timestamp ingress without a JSON-shaped conversion."""

        value: t.Infra.PlanSourceTimestamp = m.Field(
            description="Native YAML date, instant, or explicitly quoted timestamp",
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
        root: Annotated[
            Path,
            m.BeforeValidator(
                lambda value: Path(value) if isinstance(value, str) else value,
            ),
            m.Field(description="Declared physical source root"),
        ]
        adapter: Literal["files", "private-inventory"] = m.Field(
            description="Selected deterministic source adapter",
        )
        driver: t.NonEmptyStr = m.Field(description="Source driver provenance")
        driver_version: t.NonEmptyStr = m.Field(
            description="Declared source driver version",
        )
        plan_globs: Annotated[
            tuple[str, ...],
            m.Field(
                strict=False,
                min_length=1,
                description="Explicit plan discovery patterns",
            ),
        ]
        exclude_globs: Annotated[
            tuple[str, ...],
            m.Field(strict=False, description="Explicit source exclusions"),
        ] = ()
        updated_fields: Annotated[
            tuple[str, ...],
            m.Field(
                strict=False,
                description="Source-owned substantive update fields in priority order",
            ),
        ] = ("source_updated_at",)
        companion_directory: bool = m.Field(
            default=True,
            description="Collect the same-basename artifact directory",
        )
        publication: Literal["plan-artifacts", "private"] = m.Field(
            description="Authorized publication classification",
        )

        @m.field_validator(
            "plan_globs",
            "exclude_globs",
            "updated_fields",
            mode="before",
        )
        @classmethod
        def _tuple_from_list(
            cls,
            value: t.JsonPayload,
        ) -> t.JsonPayload | tuple[t.JsonValue, ...]:
            """Convert lists from the canonical validation producer domain.

            Returns:
                A tuple for list input, otherwise the original validation value.

            """
            return tuple(value) if isinstance(value, list) else value

    class PlanCollectionConfig(m.ContractModel):
        """Repository-owned associations; projection is separately authorized."""

        enabled: bool = m.Field(
            description="Explicit authorization for plan source publication",
        )
        canonical_dir: Annotated[
            Path,
            m.BeforeValidator(
                lambda value: Path(value) if isinstance(value, str) else value,
            ),
            m.Field(description="Repository-relative canonical plan destination"),
        ]
        projection_root: Annotated[
            Path | None,
            m.BeforeValidator(
                lambda value: Path(value) if isinstance(value, str) else value,
            ),
            m.Field(description="Separately authorized absolute projection owner"),
        ] = None
        sources: Annotated[
            tuple[FlextInfraModelsDocsCollection.PlanCollectionSource, ...],
            m.Field(
                strict=False,
                description="Complete explicitly associated source inventory",
            ),
        ] = ()

        @m.field_validator("sources", mode="before")
        @classmethod
        def _tuple_from_list(
            cls,
            value: t.JsonPayload,
        ) -> t.JsonPayload | tuple[t.JsonValue, ...]:
            """Preserve native models and paths while converting source lists.

            Returns:
                A tuple for list input, otherwise the original validation value.

            """
            return tuple(value) if isinstance(value, list) else value

        @m.model_validator(mode="after")
        def _authorization_matches_sources(self) -> Self:
            if self.enabled and not self.sources:
                msg = "enabled plan collection requires at least one source"
                raise ValueError(msg)
            if not self.enabled and (self.sources or self.projection_root is not None):
                msg = "disabled plan collection cannot declare sources or projection"
                raise ValueError(msg)
            return self

    class PlanCollectionRevision(m.ContractModel):
        """Immutable source revision, including companion artifact digests."""

        identity: t.NonEmptyStr = m.Field(description="Stable collected plan identity")
        provider: t.NonEmptyStr = m.Field(
            description="Provider supplying this revision",
        )
        source_id: t.NonEmptyStr = m.Field(
            description="Source association supplying this revision",
        )
        source_path: Path = m.Field(
            description=(
                "Source-association-relative locator without private root disclosure"
            ),
        )
        driver: t.NonEmptyStr = m.Field(description="Source driver provenance")
        driver_version: t.NonEmptyStr = m.Field(description="Source driver version")
        digest: t.NonEmptyStr = m.Field(
            description="Content digest including attachments",
        )
        canonical_path: Path = m.Field(
            description="Canonical-owner-relative stable plan destination",
        )
        source_updated_at: str | None = m.Field(
            default=None,
            description="Source update in UTC or original incomplete precision",
        )
        source_updated_at_original: str | None = m.Field(
            default=None,
            description="Declared source timestamp before UTC conversion",
        )
        source_updated_at_utc: str | None = m.Field(
            default=None,
            description="UTC instant only when the source declares a timezone",
        )
        collected_at: t.NonEmptyStr = m.Field(
            description="First collection timestamp for this immutable revision",
        )
        attachments: tuple[str, ...] = m.Field(
            default=(),
            description="Companion-relative attachment identities",
        )

    class PlanCollectionOwnedArtifact(m.ContractModel):
        """Exact generated bytes that authorize ignoring a discovery output."""

        relative_path: Path = m.Field(
            description="Destination-relative generated artifact path",
        )
        digest: t.NonEmptyStr = m.Field(description="Exact generated byte digest")

    class PlanCollectionManifest(m.ContractModel):
        """Generated artifact ownership and provenance, never execution state."""

        configuration_sha256: t.NonEmptyStr | None = m.Field(
            description=(
                "Typed source association digest; None only before first collection"
            ),
        )
        coverage: tuple[
            FlextInfraModelsDocsCollection.PlanCollectionCoverage, ...
        ] = m.Field(
            description="Complete source coverage from the published collection",
        )

        revisions: tuple[FlextInfraModelsDocsCollection.PlanCollectionRevision, ...] = (
            m.Field(
                default=(),
                description="Immutable observed source revision history",
            )
        )
        artifacts: tuple[
            FlextInfraModelsDocsCollection.PlanCollectionOwnedArtifact, ...
        ] = m.Field(
            default=(),
            description="Digest-attested generated artifact ownership",
        )

        @m.model_validator(mode="before")
        @classmethod
        def _ownership_before_image(
            cls,
            value: t.JsonPayload,
            info: p.ValidationInfo,
        ) -> t.JsonPayload:
            """Admit typed legacy ownership only for local collection's before-image.

            Returns:
                The payload for complete native validation, not qualified evidence.

            Raises:
                ValueError: If published current-format proof is explicitly null.

            """
            context = info.context
            if (
                isinstance(context, Mapping)
                and context.get("manifest_before_image") is True
                and isinstance(value, dict)
            ):
                if "configuration_sha256" not in value and "coverage" not in value:
                    return {
                        **value,
                        "configuration_sha256": None,
                        "coverage": [],
                    }
                if (
                    "configuration_sha256" in value
                    and value["configuration_sha256"] is None
                ):
                    msg = "published collection manifest has null association proof"
                    raise ValueError(msg)
            return value

    class PlanCollectionCoverage(m.ContractModel):
        """Observed source coverage, explicitly distinct from reconciliation."""

        source_id: t.NonEmptyStr = m.Field(description="Source association identity")
        provider: t.NonEmptyStr = m.Field(description="Declared provider")
        adapter: Literal["files", "private-inventory"] = m.Field(
            description="Executed adapter",
        )
        files: t.NonNegativeInt = m.Field(
            description="Number of discovered source files",
        )
        source_revisions: tuple[tuple[Path, t.NonEmptyStr], ...] = m.Field(
            description="Source-relative plans and revision digests observed in this "
                        "run",
        )
        status: Literal["collected", "private-inventory", "empty"] = m.Field(
            description="Observed collection coverage, not reconciliation status",
        )
        private_paths: tuple[Path, ...] = m.Field(
            default=(),
            description="Private source references without transcript contents",
        )

        @m.model_validator(mode="before")
        @classmethod
        def _ownership_before_image(
            cls,
            value: t.JsonPayload,
            info: p.ValidationInfo,
        ) -> t.JsonPayload:
            """Admit counts-only coverage solely as unqualified local before-state.

            Returns:
                The payload for complete native validation before source recollection.

            """
            context = info.context
            if (
                isinstance(context, Mapping)
                and context.get("manifest_before_image") is True
                and isinstance(value, dict)
                and "source_revisions" not in value
            ):
                return {**value, "source_revisions": []}
            return value

    class PlanCollectionBundle(m.ArbitraryTypesModel):
        """Read-only planning result consumed by the existing publisher."""

        files: tuple[FlextInfraModelsConfigArtifact.CodegenFilePlan, ...] = m.Field(
            description="Effects published through the shared publisher"
        )
        prunable_directories: tuple[Path, ...] = m.Field(
            default=(),
            description="Owned empty directories removed after publication",
        )
        revisions: tuple[FlextInfraModelsDocsCollection.PlanCollectionRevision, ...] = (
            m.Field(description="Latest newly observed revision per plan")
        )
        coverage: tuple[FlextInfraModelsDocsCollection.PlanCollectionCoverage, ...] = (
            m.Field(description="Explicit per-source collection coverage")
        )


__all__: list[str] = ["FlextInfraModelsDocsCollection"]
