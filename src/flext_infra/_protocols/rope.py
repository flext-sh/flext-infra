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
    class RopeProjectRootLike(Protocol):
        """Minimal contract for rope project's root resource."""

        real_path: str
        """Absolute filesystem path for the project root."""

    @runtime_checkable
    class RopeResourceLike(Protocol):
        """Minimal contract for rope Resource objects."""

        path: str
        """Relative path within the rope project."""

        real_path: str
        """Absolute filesystem path."""

        def read(self) -> str:
            """Read file contents as string."""
            ...

    @runtime_checkable
    class RopeProjectLike(Protocol):
        """Minimal contract for rope Project objects."""

        root: FlextInfraProtocolsRope.RopeProjectRootLike
        """Project root resource."""

        pycore: object
        """Rope's dynamic PyCore object."""

        def get_resource(self, resource_path: str) -> object:
            """Resolve one resource path inside the project."""
            ...

        def get_pymodule(
            self,
            resource: FlextInfraProtocolsRope.RopeResourceLike,
        ) -> FlextInfraProtocolsRope.RopePyModuleLike:
            """Return the PyModule for one resource."""
            ...

        def do(self, changes: object) -> None:
            """Apply one rope change set."""
            ...

        def close(self) -> None:
            """Close project resources."""
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
    class RopeChangesLike(Protocol):
        """Structural contract for rope ChangeSet-like objects."""

        @property
        def changes(self) -> Sequence[FlextInfraProtocolsRope.RopeChangeLike]:
            """Return nested changes carried by this change set."""
            ...

    @runtime_checkable
    class RopeMutableChangesLike(RopeChangesLike, Protocol):
        """ChangeSet-like object that can receive child changes."""

        def add_change(
            self,
            change: FlextInfraProtocolsRope.RopeChangeLike,
        ) -> None:
            """Append one child change."""
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

        @property
        def source_code(self) -> str:
            """Return module source text."""
            ...

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
    class RopeAbstractClassLike(Protocol):
        """Structural contract for rope class-like objects."""

        def get_attributes(self) -> dict[str, FlextInfraProtocolsRope.RopePyNameLike]:
            """Return class attributes."""
            ...

        def get_module(self) -> FlextInfraProtocolsRope.RopePyModuleLike | None:
            """Return the module containing this class."""
            ...

        def get_name(self) -> str | None:
            """Return the class name, or None."""
            ...

        def get_superclasses(
            self,
        ) -> Sequence[FlextInfraProtocolsRope.RopeAbstractClassLike]:
            """Return direct superclasses."""
            ...

    @runtime_checkable
    class RopePyFunctionLike(Protocol):
        """Structural contract for rope function-like objects."""

        def get_kind(self) -> str:
            """Return function kind: method/classmethod/staticmethod/function."""
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
    class RopeLocationLike(Protocol):
        """Structural contract for rope occurrence search results."""

        resource: FlextInfraProtocolsRope.RopeResourceLike
        """Resource containing the occurrence."""

        lineno: int
        """1-based line number."""

        region: tuple[int, int]
        """Byte-offset region."""

    @runtime_checkable
    class RopeImportInfoLike(Protocol):
        """Structural contract for rope import descriptors."""

        names_and_aliases: Sequence[tuple[str, str | None]]
        """Imported names and optional aliases."""

    @runtime_checkable
    class RopeFromImportLike(RopeImportInfoLike, Protocol):
        """Structural contract for ``from x import y`` descriptors."""

        module_name: str
        """Imported module path."""

        level: int
        """Relative import level, 0 for absolute."""

    @runtime_checkable
    class RopeImportStatementLike(Protocol):
        """Structural contract for one import statement wrapper."""

        import_info: object
        """Underlying import descriptor."""

    @runtime_checkable
    class RopeModuleImportsLike(Protocol):
        """Structural contract for rope's ModuleImports helper."""

        imports: Sequence[FlextInfraProtocolsRope.RopeImportStatementLike]
        """Discovered import statements."""

        def add_import(self, import_info: object) -> None:
            """Append one import descriptor."""
            ...

        def remove_duplicates(self) -> None:
            """Deduplicate imports in-place."""
            ...

        def sort_imports(self) -> None:
            """Sort imports in-place."""
            ...

        def get_changed_source(self) -> str:
            """Render the updated module source."""
            ...

    @runtime_checkable
    class RopeRenameLike(Protocol):
        """Structural contract for rope Rename refactor objects."""

        def get_changes(self, new_name: str) -> FlextInfraProtocolsRope.RopeChangesLike:
            """Build rename changes for the requested symbol."""
            ...

    @runtime_checkable
    class RopeImportOrganizerLike(Protocol):
        """Structural contract for rope import organizers."""

        def organize_imports(
            self,
            resource: FlextInfraProtocolsRope.RopeResourceLike,
            offset: int | None = None,
        ) -> FlextInfraProtocolsRope.RopeChangesLike | None:
            """Return one change set that rewrites imports."""
            ...

    class RopeGetModuleImportsFn(Protocol):
        """Callable signature for ``rope.refactor.importutils.get_module_imports``."""

        def __call__(
            self,
            project: FlextInfraProtocolsRope.RopeProjectLike,
            pymodule: FlextInfraProtocolsRope.RopePyModuleLike,
        ) -> FlextInfraProtocolsRope.RopeModuleImportsLike:
            """Build one module-import helper for the given module."""
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
