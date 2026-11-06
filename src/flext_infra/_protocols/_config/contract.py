# AUTO-GENERATED FILE — Regenerate with: make gen
"""Source-derived structural model contracts.

Copyright (c) 2026 FLEXT Team. All rights reserved.
src/flext_infra/_protocols/_config/contract
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Protocol, runtime_checkable

from flext_infra._protocols import FlextInfraProtocolsMiseToolchainBase

if TYPE_CHECKING:
    from flext_infra import t


class FlextInfraProtocolsConfigContract:
    """Own the structural contracts declared by its model source."""

    @runtime_checkable
    class ConfigContract(FlextInfraProtocolsMiseToolchainBase.SchemaRecord, Protocol):
        """Structural data contract projected from the owning model."""

    @runtime_checkable
    class DocsAuditOverridesSpec(ConfigContract, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def stale_symbols(self) -> tuple[t.NonEmptyStr, ...]:
            """Public symbols retired from current documentation."""
            ...

        @property
        def stale_symbol_exempt_paths(self) -> tuple[t.NonEmptyStr, ...]:
            """Exact generated API paths retaining live symbols."""
            ...

        @property
        def forbidden_terms(self) -> tuple[t.NonEmptyStr, ...]:
            """Structural member projected from the owning model.

            Literal retired-surface names forbidden in current documentation, each
            superseded by a declared canonical owner.
            """
            ...

        @property
        def container_home_identities(self) -> tuple[t.NonEmptyStr, ...]:
            """Structural member projected from the owning model.

            Container/CI identities whose /home|/Users home is part of the declared
            image contract, never an operator machine path.
            """
            ...

        @property
        def historical_evidence_files(self) -> tuple[Path, ...]:
            """Exact dated Markdown records preserving observed paths."""
            ...

    @runtime_checkable
    class DocsAuditPolicySpec(DocsAuditOverridesSpec, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def placeholder_patterns(self) -> tuple[t.NonEmptyStr, ...]:
            """Regexes recognizing unfinished document markers."""
            ...


__all__: list[str] = [
    "FlextInfraProtocolsConfigContract",
]
