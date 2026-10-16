"""Protocol for workspace check outcomes.

Defines the structural contract for workspace gate loop outcome
objects with results, failure counts, and timing information.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, runtime_checkable

if TYPE_CHECKING:
    from flext_cli import p

    from flext_infra import m, t


@runtime_checkable
class FlextInfraProtocolsCheck(Protocol):
    """Check-domain protocol definitions."""

    class NativeStorageSlot[ValueT](Protocol):
        """Read one interpreter-owned slot with its precise native result."""

        def __get__(
            self,
            instance: t.Infra.NativeOperand,
            owner: t.Infra.NativeType,
            /,
        ) -> ValueT: ...

    @runtime_checkable
    class NativeModuleSpec(Protocol):
        """Physical source fields supplied by the native import finder."""

        @property
        def origin(self) -> str | None: ...

        @property
        def loader(self) -> p.AttributeProbe | None: ...

        @property
        def submodule_search_locations(self) -> t.SequenceOf[str] | None: ...

    @runtime_checkable
    class PytestRunContextReceiver(Protocol):
        """Receive the runner's immutable Pydantic receipt through explicit DI."""

        def __call__(self, context: m.Infra.PytestRunContext) -> None: ...

    @runtime_checkable
    class WorkspaceLoopOutcome(Protocol):
        """Public structural view of the workspace gate loop outcome."""

        results: tuple[m.Infra.ProjectResult, ...]
        failed: int
        total_elapsed: float


__all__: list[str] = ["FlextInfraProtocolsCheck"]
