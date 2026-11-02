# AUTO-GENERATED FILE — Regenerate with: make gen
"""Source-derived structural model contracts.

Copyright (c) 2026 FLEXT Team. All rights reserved.
src/flext_infra/_protocols/_config/make_clean
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from flext_infra import t


class FlextInfraProtocolsConfigMakeClean:
    """Own the structural contracts declared by its model source."""

    @runtime_checkable
    class MakeCleanSpec(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def cache_dirs(self) -> tuple[t.NonEmptyStr, ...]: ...
        @property
        def root_dirs(self) -> tuple[t.NonEmptyStr, ...]: ...
        @property
        def root_files(self) -> tuple[t.NonEmptyStr, ...]: ...
        @property
        def trace_globs(self) -> tuple[t.NonEmptyStr, ...]: ...


__all__: list[str] = [
    "FlextInfraProtocolsConfigMakeClean",
]
