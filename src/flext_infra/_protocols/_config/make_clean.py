# AUTO-GENERATED FILE — Regenerate with: make gen
"""Source-derived structural model contracts.

Copyright (c) 2026 FLEXT Team. All rights reserved.
src/flext_infra/_protocols/_config/make_clean
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from flext_infra import t
from flext_infra._protocols._config import FlextInfraProtocolsConfigContract


class FlextInfraProtocolsConfigMakeClean:
    """Own the structural contracts declared by its model source."""

    @runtime_checkable
    class MakeCleanSpec(FlextInfraProtocolsConfigContract.ConfigContract, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def cache_dirs(self) -> tuple[t.NonEmptyStr, ...]:
            """Cache directory names removed anywhere in the tree."""
            ...

        @property
        def root_dirs(self) -> tuple[t.NonEmptyStr, ...]:
            """Directories removed at the project root only."""
            ...

        @property
        def root_files(self) -> tuple[t.NonEmptyStr, ...]:
            """Files removed at the project root only."""
            ...

        @property
        def trace_globs(self) -> tuple[t.NonEmptyStr, ...]:
            """Trace/profile globs removed anywhere in the tree."""
            ...


__all__: list[str] = [
    "FlextInfraProtocolsConfigMakeClean",
]
