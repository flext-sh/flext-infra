"""Protocol for workspace check outcomes.

Defines the structural contract for workspace gate loop outcome
objects with results, failure counts, and timing information.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, runtime_checkable

if TYPE_CHECKING:
    from pathlib import Path

    from flext_cli import p, t

    from flext_infra import m


@runtime_checkable
class FlextInfraProtocolsCheck(Protocol):
    """Check-domain protocol definitions."""

    class NativeModuleSourceResolver(Protocol):
        """Resolve an elected physical supplier without importing its module."""

        def __call__(self, module_name: str) -> p.Result[Path]: ...

    class NativeSourceObserver(Protocol):
        """Provide callback-free native observation to the source proof owner."""

        def _is_class(self, value: p.AttributeProbe) -> bool: ...

        def _class_namespace(
            self,
            value: p.AttributeProbe,
        ) -> t.MappingKV[str, p.AttributeProbe]: ...

        def _value(
            self,
            value: p.AttributeProbe | None,
            seen: frozenset[int] = frozenset(),
            *,
            construction: bool = False,
        ) -> str: ...

        def _native_wrapper_kind(self, value: p.AttributeProbe) -> str | None: ...

        def _native_wrapper_function(
            self,
            value: p.AttributeProbe,
            kind: str,
        ) -> p.Result[p.AttributeProbe]: ...

    @runtime_checkable
    class NativeCodeIdentity(Protocol):
        """Immutable native code metadata consumed by source provenance."""

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
