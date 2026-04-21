"""Protocol for refactor change tracking.

Defines the structural contract for objects that track applied
refactoring transformations via a mutable changes sequence.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import (
    MutableSequence,
)
from typing import Protocol, runtime_checkable


class FlextInfraProtocolsRefactor(Protocol):
    @runtime_checkable
    class ChangeTracker(Protocol):
        """Protocol for objects that track applied changes."""

        changes: MutableSequence[str]


__all__: list[str] = [
    "FlextInfraProtocolsRefactor",
]
