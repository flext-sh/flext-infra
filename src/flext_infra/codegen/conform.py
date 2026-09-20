"""Unified, fail-closed conformance for new and existing repositories.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from ._conform import FlextInfraCodegenConformBase


class FlextInfraCodegenConform(FlextInfraCodegenConformBase):
    """Plan every selected output, then atomically write only a clean plan."""


__all__: list[str] = ["FlextInfraCodegenConform"]
