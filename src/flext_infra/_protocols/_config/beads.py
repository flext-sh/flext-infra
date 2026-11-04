# AUTO-GENERATED FILE — Regenerate with: make gen
"""Source-derived structural model contracts.

Copyright (c) 2026 FLEXT Team. All rights reserved.
src/flext_infra/_protocols/_config/beads
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Literal, Protocol, runtime_checkable

from flext_infra._protocols._config import FlextInfraProtocolsConfigContract

if TYPE_CHECKING:
    from flext_infra import t


class FlextInfraProtocolsConfigBeads:
    """Own the structural contracts declared by its model source."""

    @runtime_checkable
    class BeadsProjectSpec(FlextInfraProtocolsConfigContract.ConfigContract, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def version(self) -> Literal[1]:
            """Beads project configuration schema version."""
            ...

        @property
        def workspace(self) -> t.NonEmptyStr:
            """Stable workspace identity."""
            ...

        @property
        def database(self) -> t.NonEmptyStr:
            """Repository-owned Dolt database."""
            ...

        @property
        def issue_prefix(self) -> t.NonEmptyStr:
            """Repository-owned issue prefix."""
            ...

        @property
        def ownership_command_prefix(self) -> tuple[t.NonEmptyStr, ...]:
            """Declared public wrapper for ownership reads."""
            ...

        @property
        def ownership_command_cwd(self) -> Path | None:
            """Declared city/rig scope of ownership reads."""
            ...

        @property
        def custom_issue_types(self) -> tuple[t.NonEmptyStr, ...]:
            """Repository-owned custom types beyond the Gas City baseline."""
            ...

    @runtime_checkable
    class BeadsConfigRenderSpec(
        FlextInfraProtocolsConfigContract.ConfigContract, Protocol
    ):
        """Structural data contract projected from the owning model."""

        @property
        def issue_prefix(self) -> t.NonEmptyStr:
            """Issue prefix from local config/beads.yaml."""
            ...

        @property
        def endpoint_origin(self) -> Literal["inherited_city"]:
            """Gas City endpoint ownership projection."""
            ...

        @property
        def endpoint_status(self) -> Literal["verified"]:
            """Gas City inherited endpoint status."""
            ...

        @property
        def gascity_enabled(self) -> bool:
            """Structural member projected from the owning model.

            Gas City runtime-contract participation; False drops the gc endpoint
            keys and makes Beads own a repository-local Dolt server (dolt.auto-
            start: true).
            """
            ...

        @property
        def custom_issue_types(self) -> tuple[t.NonEmptyStr, ...]:
            """Union of project and required custom bead types."""
            ...

        @property
        def dolt_mode(self) -> t.NonEmptyStr:
            """From toolchain.beads.dolt_mode."""
            ...

        @property
        def export_auto(self) -> bool:
            """From toolchain.beads.export_auto."""
            ...

        @property
        def backup_enabled(self) -> bool:
            """From toolchain.beads.backup_enabled."""
            ...

        @property
        def dolt_disable_event_flush(self) -> bool:
            """From toolchain.beads.dolt_disable_event_flush."""
            ...

    @runtime_checkable
    class BeadsMetadataRenderSpec(
        FlextInfraProtocolsConfigContract.ConfigContract, Protocol
    ):
        """Structural data contract projected from the owning model."""

        @property
        def database(self) -> t.NonEmptyStr:
            """Dolt database from local config/beads.yaml."""
            ...

        @property
        def dolt_mode(self) -> t.NonEmptyStr:
            """Storage mode from toolchain.beads.dolt_mode."""
            ...

        @property
        def project_id(self) -> t.NonEmptyStr | None:
            """Structural member projected from the owning model.

            Ledger identity read back from .beads/identity.toml; None only before
            Beads has minted one.
            """
            ...


__all__: list[str] = [
    "FlextInfraProtocolsConfigBeads",
]
