"""Protocol for workspace check outcomes.

Defines the structural contract for workspace gate loop outcome
objects with results, failure counts, and timing information.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, runtime_checkable

if TYPE_CHECKING:
    from collections.abc import Callable
    from contextlib import AbstractContextManager
    from pathlib import Path

    from flext_cli import t

    from flext_infra import m, p


@runtime_checkable
class FlextInfraProtocolsCheck(Protocol):
    """Check-domain protocol definitions."""

    class NativeModuleSourceResolver(Protocol):
        """Resolve an elected physical supplier without importing its module."""

        def __call__(self, module_name: str) -> p.Result[Path]: ...

    class NativeRopeSourceOperations(Protocol):
        """Required composed native SDK operations for one source-proof epoch."""

        def runtime_callable(
            self, module_name: str, attribute: str
        ) -> Callable[..., p.AttributeProbe]: ...

        def build_string_module(
            self,
            rope_project: p.Infra.RopeProject | None,
            source: str,
            *,
            resource: p.Infra.RopeResource | None = None,
        ) -> p.Infra.RopePyModule: ...

        def logical_statements(
            self, source: str
        ) -> t.SequenceOf[p.Infra.RopeSourceStatement]: ...

        def semantic_finder(
            self, module: p.Infra.RopePyModule
        ) -> p.Infra.RopeSimilarFinder: ...

        def semantic_capture_region(
            self, match: p.Infra.RopeContractMatch, variable: str
        ) -> t.Pair[int, int]: ...

        def expression_name(
            self, scope: p.Infra.RopeScope, expression: str
        ) -> p.Infra.RopePyName | None: ...

        def scope_at(
            self,
            pymodule: p.Infra.RopePyModule,
            offset: int,
            *,
            declaration_line: int | None = None,
        ) -> p.Infra.RopeScope: ...

        def same_name(
            self,
            expected: p.Infra.RopePyName,
            actual: p.Infra.RopePyName | None,
        ) -> bool: ...

        def open_import_project(
            self, source_root: Path
        ) -> AbstractContextManager[p.Infra.RopeProject]: ...

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
        def __kwdefaults__(self) -> t.MappingKV[str, p.AttributeProbe | None] | None: ...

        @property
        def __globals__(self) -> t.MappingKV[str, p.AttributeProbe | None]: ...

        @property
        def __closure__(
            self,
        ) -> tuple[FlextInfraProtocolsCheck.NativeClosureCell, ...] | None: ...

        @property
        def __name__(self) -> str: ...

        @property
        def __qualname__(self) -> str: ...

        @property
        def __module__(self) -> str | None: ...

        @property
        def __dict__(self) -> t.MappingKV[str, p.AttributeProbe | None]: ...

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
