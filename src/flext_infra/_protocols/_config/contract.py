# AUTO-GENERATED FILE — Regenerate with: make gen
"""Source-derived structural model contracts.

Copyright (c) 2026 FLEXT Team. All rights reserved.
src/flext_infra/_protocols/_config/contract
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path
from typing import Protocol, runtime_checkable

from flext_infra import t


class FlextInfraProtocolsConfigContract:
    """Own the structural contracts declared by its model source."""

    @runtime_checkable
    class ConfigContract(Protocol):
        """Structural data contract projected from the owning model."""

    @runtime_checkable
    class DocsAuditOverridesSpec(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def stale_symbols(self) -> tuple[t.NonEmptyStr, ...]: ...
        @property
        def stale_symbol_exempt_paths(self) -> tuple[t.NonEmptyStr, ...]: ...
        @property
        def forbidden_terms(self) -> tuple[t.NonEmptyStr, ...]: ...
        @property
        def container_home_identities(self) -> tuple[t.NonEmptyStr, ...]: ...
        @property
        def historical_evidence_files(self) -> tuple[Path, ...]: ...

    @runtime_checkable
    class DocsAuditPolicySpec(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def stale_symbols(self) -> tuple[t.NonEmptyStr, ...]: ...
        @property
        def stale_symbol_exempt_paths(self) -> tuple[t.NonEmptyStr, ...]: ...
        @property
        def forbidden_terms(self) -> tuple[t.NonEmptyStr, ...]: ...
        @property
        def container_home_identities(self) -> tuple[t.NonEmptyStr, ...]: ...
        @property
        def historical_evidence_files(self) -> tuple[Path, ...]: ...
        @property
        def placeholder_patterns(self) -> tuple[t.NonEmptyStr, ...]: ...


__all__: list[str] = [
    "FlextInfraProtocolsConfigContract",
]
