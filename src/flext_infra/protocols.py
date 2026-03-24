"""Protocol definitions for flext-infra utilities and services.

Defines structural contracts (runtime-checkable Protocols) for orchestration,
command execution, validation, and reporting services used across the
infrastructure layer.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import argparse
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import TYPE_CHECKING, Protocol, runtime_checkable

from flext_core import FlextProtocols, r
from pydantic import JsonValue
from flext_infra import FlextInfraProtocolsBase

if TYPE_CHECKING:
    from flext_infra import m, t, u


class FlextInfraProtocols(FlextProtocols):
    """Structural contracts for flext-infra utilities and services.

    All parent protocols (Result, Config, DI, Service, etc.) are inherited
    transparently from ``FlextProtocols`` via MRO. Infra-specific utility
    protocols live as nested classes below.
    """

    class Infra(FlextInfraProtocolsBase):
        """Infra-specific structural protocol definitions."""


p = FlextInfraProtocols
__all__ = ["FlextInfraProtocols", "p"]
