"""Protocol for workspace check outcomes.

Defines the structural contract for workspace gate loop outcome
objects with results, failure counts, and timing information.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, runtime_checkable

from flext_cli import p

if TYPE_CHECKING:
    from pathlib import Path

    from flext_infra import m, t


@runtime_checkable
class FlextInfraProtocolsCheck(Protocol):
    """Check-domain protocol definitions."""

    @runtime_checkable
    class SarifLocation(p.Model, Protocol):
        """Read a native source span without depending on its payload model."""

        @property
        def uri(self) -> str: ...

        @property
        def start_line(self) -> int | None: ...

        @property
        def start_column(self) -> int | None: ...

        @property
        def end_line(self) -> int | None: ...

        @property
        def end_column(self) -> int | None: ...

        @property
        def uri_base_id(self) -> str: ...

    @runtime_checkable
    class Issue(p.Model, Protocol):
        """Shared diagnostic contract for native parsers and gate aggregation."""

        @property
        def file(self) -> str: ...

        @property
        def line(self) -> int: ...

        @property
        def column(self) -> int: ...

        @property
        def code(self) -> str: ...

        @property
        def message(self) -> str: ...

        @property
        def severity(self) -> str: ...

        @property
        def formatted(self) -> str: ...

        @property
        def locations(
            self,
        ) -> t.SequenceOf[FlextInfraProtocolsCheck.SarifLocation]: ...

        @property
        def related_locations(
            self,
        ) -> t.SequenceOf[FlextInfraProtocolsCheck.SarifLocation]: ...

    @runtime_checkable
    class GitScopeFacts(Protocol):
        """Share one invocation's tracked Git scope inventory across consumers."""

        def tracked_scope_relative_paths(
            self,
            scope_root: Path,
        ) -> t.StrSequence | None: ...

    @runtime_checkable
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
