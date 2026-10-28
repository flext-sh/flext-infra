# AUTO-GENERATED FILE — Regenerate with: make gen
"""Protocol definitions for flext-infra utilities and services.

Defines structural contracts (runtime-checkable Protocols) for orchestration,
command execution, validation, and reporting services used across the
infrastructure layer.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import (
    Iterable,
    Iterator,
    Mapping,
    MutableMapping,
    MutableSequence,
    Sequence,
)

from flext_cli import FlextCliProtocols

from flext_infra._protocols import (
    FlextInfraProtocolsBase,
    FlextInfraProtocolsCheck,
    FlextInfraProtocolsDeps,
    FlextInfraProtocolsDocs,
    FlextInfraProtocolsPromoted,
    FlextInfraProtocolsRope,
    FlextInfraProtocolsRopeRuntime,
    FlextInfraProtocolsWorkspaceSnapshot,
)


class FlextInfraProtocols(FlextCliProtocols):
    """Structural contracts for flext-infra utilities and services.

    All parent protocols (Result, Config, DI, Service, etc.) are inherited
    transparently from ``FlextProtocols`` via FLEXT. Infra-specific utility
    protocols live as nested classes below.
    """

    class Infra(
        FlextInfraProtocolsCheck,
        FlextInfraProtocolsDeps,
        FlextInfraProtocolsDocs,
        FlextInfraProtocolsPromoted,
        FlextInfraProtocolsRopeRuntime,
        FlextInfraProtocolsRope,
        FlextInfraProtocolsBase,
        FlextInfraProtocolsWorkspaceSnapshot,
    ):
        """Infra-specific structural protocol definitions."""


p = FlextInfraProtocols
__all__: list[str] = ["FlextInfraProtocols", "FlextInfraProtocolsBase", "p"]
