"""Beads projection models.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path
from typing import Annotated, Literal, Self

from flext_cli import m

from flext_infra import t
from flext_infra._models._config.contract import FlextInfraModelsConfigContract


class FlextInfraModelsConfigBeads:
    """Beads projection models."""

    class BeadsProjectSpec(FlextInfraModelsConfigContract.ConfigContract):
        """Repository-local Beads identity from ``config/beads.yaml``."""

        version: Annotated[
            Literal[1],
            m.Field(description="Beads project configuration schema version"),
        ]
        workspace: Annotated[
            t.NonEmptyStr,
            m.Field(description="Stable workspace identity"),
        ]
        database: Annotated[
            t.NonEmptyStr,
            m.Field(description="Repository-owned Dolt database"),
        ]
        issue_prefix: Annotated[
            t.NonEmptyStr,
            m.Field(description="Repository-owned issue prefix"),
        ]
        ownership_command_prefix: Annotated[
            tuple[t.NonEmptyStr, ...],
            m.Field(description="Declared public wrapper for ownership reads"),
        ] = ()
        ownership_command_cwd: Annotated[
            Path | None,
            m.Field(description="Declared city/rig scope of ownership reads"),
        ] = None
        custom_issue_types: Annotated[
            tuple[t.NonEmptyStr, ...],
            m.Field(
                description=(
                    "Repository-owned custom types beyond the Gas City baseline"
                ),
            ),
        ] = ()

        @m.model_validator(mode="after")
        def _validate_custom_issue_types(self) -> Self:
            """Reject duplicate project extensions before projection.

            Returns:
                The resulting ``Self``.

            Raises:
                ValueError: If beads custom_issue_types must be unique.

            """
            if len(set(self.custom_issue_types)) != len(self.custom_issue_types):
                msg = "beads custom_issue_types must be unique"
                raise ValueError(msg)
            return self

    class BeadsConfigRenderSpec(FlextInfraModelsConfigContract.ConfigContract):
        """Field-only render input for the generated Beads ledger config."""

        issue_prefix: Annotated[
            t.NonEmptyStr,
            m.Field(description="Issue prefix from local config/beads.yaml"),
        ]
        endpoint_origin: Annotated[
            Literal["inherited_city"],
            m.Field(description="Gas City endpoint ownership projection"),
        ]
        endpoint_status: Annotated[
            Literal["verified"],
            m.Field(description="Gas City inherited endpoint status"),
        ]
        gascity_enabled: Annotated[
            bool,
            m.Field(
                description=(
                    "Gas City runtime-contract participation; False drops the "
                    "gc endpoint keys and makes Beads own a repository-local "
                    "Dolt server (dolt.auto-start: true)."
                ),
            ),
        ] = True
        custom_issue_types: Annotated[
            tuple[t.NonEmptyStr, ...],
            m.Field(description="Union of project and required custom bead types"),
        ] = ()
        dolt_mode: Annotated[
            t.NonEmptyStr,
            m.Field(description="From toolchain.beads.dolt_mode"),
        ]
        export_auto: Annotated[
            bool,
            m.Field(description="From toolchain.beads.export_auto"),
        ]
        backup_enabled: Annotated[
            bool,
            m.Field(description="From toolchain.beads.backup_enabled"),
        ]
        dolt_disable_event_flush: Annotated[
            bool,
            m.Field(description="From toolchain.beads.dolt_disable_event_flush"),
        ]

    class BeadsMetadataRenderSpec(FlextInfraModelsConfigContract.ConfigContract):
        """Field-only render input for the generated Beads ledger marker.

        The marker carries portable storage and database identity plus the
        checkout's ledger identity. ``project_id`` is NOT invented here: it is
        read back from the checkout's own ``.beads/identity.toml`` so a
        regeneration preserves it. Omitting it made every ``make gen`` strip the
        key, and Beads then minted a fresh identity on next access — observed in
        a consumer rig, where the ledger identity changed on regeneration.
        ``None`` means the checkout has no ledger
        identity yet, and Beads mints the first one.
        """

        database: Annotated[
            t.NonEmptyStr,
            m.Field(description="Dolt database from local config/beads.yaml"),
        ]
        dolt_mode: Annotated[
            t.NonEmptyStr,
            m.Field(description="Storage mode from toolchain.beads.dolt_mode"),
        ]
        project_id: Annotated[
            t.NonEmptyStr | None,
            m.Field(
                default=None,
                description=(
                    "Ledger identity read back from .beads/identity.toml; "
                    "None only before Beads has minted one"
                ),
            ),
        ] = None


__all__: list[str] = ["FlextInfraModelsConfigBeads"]
