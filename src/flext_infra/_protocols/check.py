"""Protocol for workspace check outcomes.

Defines the structural contract for workspace gate loop outcome
objects with results, failure counts, and timing information.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, runtime_checkable

if TYPE_CHECKING:
    from flext_cli import p, t

    from flext_infra import m


@runtime_checkable
class FlextInfraProtocolsCheck(Protocol):
    """Check-domain protocol definitions."""

    @runtime_checkable
    class NativeCodeIdentity(Protocol):
        """Immutable native code metadata consumed by source provenance."""

        co_argcount: int
        co_posonlyargcount: int
        co_kwonlyargcount: int
        co_filename: str
        co_qualname: str
        co_firstlineno: int
        co_consts: tuple[p.AttributeProbe | None, ...]
        co_names: tuple[str, ...]
        co_varnames: tuple[str, ...]
        co_freevars: tuple[str, ...]
        co_cellvars: tuple[str, ...]
        co_code: bytes
        co_linetable: bytes
        co_exceptiontable: bytes
        co_flags: int

        def replace(
            self,
            **changes: p.AttributeProbe | None,
        ) -> FlextInfraProtocolsCheck.NativeCodeIdentity: ...

    class NativeClosureCell(Protocol):
        """Expose the interpreter-owned contents of one closure cell."""

        @property
        def cell_contents(self) -> p.AttributeProbe | None: ...

    class NativePythonFunction(Protocol):
        """Read an elected native Python function through precise contracts."""

        @property
        def __code__(self) -> FlextInfraProtocolsCheck.NativeCodeIdentity: ...

        @property
        def __defaults__(self) -> tuple[p.AttributeProbe | None, ...] | None: ...

        @property
        def __kwdefaults__(
            self,
        ) -> t.MappingKV[str, p.AttributeProbe | None] | None: ...

        @property
        def __globals__(self) -> t.MappingKV[str, p.AttributeProbe | None]: ...

        @property
        def __closure__(
            self,
        ) -> tuple[FlextInfraProtocolsCheck.NativeClosureCell, ...] | None: ...

        __name__: str
        __module__: str
        __qualname__: str

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
