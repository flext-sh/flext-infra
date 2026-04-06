"""Protocol for refactor change tracking.

Defines the structural contract for objects that track applied
refactoring transformations via a mutable changes sequence.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import MutableSequence
from typing import Protocol, runtime_checkable


@runtime_checkable
class FlextInfraChangeTracker(Protocol):
    """Protocol for objects that track applied changes."""

    changes: MutableSequence[str]


class FlextInfraProtocolsRefactor(Protocol):
    """Refactor-domain protocol definitions."""


__all__ = [
    "FlextInfraChangeTracker",
    "FlextInfraProtocolsRefactor",
]
