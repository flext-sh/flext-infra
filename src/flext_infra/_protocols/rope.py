"""Protocols for rope library interop — structural typing for untyped rope APIs.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
from typing import TYPE_CHECKING, Protocol, runtime_checkable

if TYPE_CHECKING:
    from flext_infra import m


class FlextInfraProtocolsRope:
    """Structural contracts for rope objects lacking type stubs."""

    @runtime_checkable
    class RopeResourceLike(Protocol):
        """Minimal contract for rope Resource objects."""

        @property
        def path(self) -> str:
            """Relative path within the rope project."""
            ...

        @property
        def real_path(self) -> str:
            """Absolute filesystem path."""
            ...

        def read(self) -> str:
            """Read file contents as string."""
            ...

    @runtime_checkable
    class RopeChangeLike(Protocol):
        """Structural contract for rope ChangeContents / ChangeSet.changes elements.

        Rope's Change hierarchy is untyped — this protocol bridges the gap so
        utilities can access .resource and .new_contents without type: ignore.
        """

        @property
        def resource(self) -> FlextInfraProtocolsRope.RopeResourceLike:
            """The resource affected by this change."""
            ...

        @property
        def new_contents(self) -> str | None:
            """New file contents after the change, or None for deletions."""
            ...

    @runtime_checkable
    class RopePyCoreLike(Protocol):
        """Structural contract for rope PyCore.

        Rope's pycore property is dynamically typed — this protocol provides
        a typed facade for resource_to_pyobject.
        """

        def resource_to_pyobject(
            self,
            resource: FlextInfraProtocolsRope.RopeResourceLike,
        ) -> FlextInfraProtocolsRope.RopePyModuleLike:
            """Convert a resource to its PyModule representation."""
            ...

    @runtime_checkable
    class RopePyModuleLike(Protocol):
        """Structural contract for rope PyModule objects."""

        def get_attributes(self) -> dict[str, FlextInfraProtocolsRope.RopePyNameLike]:
            """Return module-level attributes as a name → pyname mapping."""
            ...

        def get_name(self) -> str | None:
            """Return the module name, or None."""
            ...

        def get_resource(self) -> FlextInfraProtocolsRope.RopeResourceLike | None:
            """Return the resource backing this module, or None for builtins."""
            ...

    @runtime_checkable
    class RopePyNameLike(Protocol):
        """Structural contract for rope PyName objects."""

        def get_object(self) -> FlextInfraProtocolsRope.RopePyObjectLike:
            """Return the Python object this name refers to."""
            ...

        def get_definition_location(
            self,
        ) -> tuple[FlextInfraProtocolsRope.RopePyModuleLike | None, int | None]:
            """Return (module, line_number) of this name's definition."""
            ...

    @runtime_checkable
    class RopePyObjectLike(Protocol):
        """Structural contract for rope PyObject hierarchy."""

        def get_module(self) -> FlextInfraProtocolsRope.RopePyModuleLike | None:
            """Return the module containing this object, or None."""
            ...

        def get_name(self) -> str | None:
            """Return the name of this object, or None."""
            ...

    @runtime_checkable
    class RopePostHook(Protocol):
        """Contract for post-processing hooks invoked after rope refactoring.

        Implementations receive a workspace path and dry_run flag,
        and return rope-compatible Result objects.
        """

        def __call__(
            self,
            path: Path,
            *,
            dry_run: bool,
        ) -> Sequence[m.Infra.Result]:
            """Execute the hook and return results."""
            ...


__all__ = ["FlextInfraProtocolsRope"]
