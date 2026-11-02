# AUTO-GENERATED FILE — Regenerate with: make gen
"""Source-derived structural model contracts.

Copyright (c) 2026 FLEXT Team. All rights reserved.
src/flext_infra/_protocols/_config/beads
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path
from typing import Literal, Protocol, runtime_checkable

from flext_infra import t


class FlextInfraProtocolsConfigBeads:
    """Own the structural contracts declared by its model source."""

    @runtime_checkable
    class BeadsProjectSpec(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def version(self) -> Literal[1]: ...
        @property
        def workspace(self) -> t.NonEmptyStr: ...
        @property
        def database(self) -> t.NonEmptyStr: ...
        @property
        def issue_prefix(self) -> t.NonEmptyStr: ...
        @property
        def ownership_command_prefix(self) -> tuple[t.NonEmptyStr, ...]: ...
        @property
        def ownership_command_cwd(self) -> Path | None: ...
        @property
        def custom_issue_types(self) -> tuple[t.NonEmptyStr, ...]: ...

    @runtime_checkable
    class BeadsConfigRenderSpec(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def issue_prefix(self) -> t.NonEmptyStr: ...
        @property
        def endpoint_origin(self) -> Literal["inherited_city"]: ...
        @property
        def endpoint_status(self) -> Literal["verified"]: ...
        @property
        def gascity_enabled(self) -> bool: ...
        @property
        def custom_issue_types(self) -> tuple[t.NonEmptyStr, ...]: ...
        @property
        def dolt_mode(self) -> t.NonEmptyStr: ...
        @property
        def export_auto(self) -> bool: ...
        @property
        def backup_enabled(self) -> bool: ...
        @property
        def dolt_disable_event_flush(self) -> bool: ...

    @runtime_checkable
    class BeadsMetadataRenderSpec(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def database(self) -> t.NonEmptyStr: ...
        @property
        def dolt_mode(self) -> t.NonEmptyStr: ...
        @property
        def project_id(self) -> t.NonEmptyStr | None: ...


__all__: list[str] = [
    "FlextInfraProtocolsConfigBeads",
]
