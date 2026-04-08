"""Protocols for rope library interop — structural typing for untyped rope APIs.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from pathlib import Path
from typing import TYPE_CHECKING, Protocol, runtime_checkable

if TYPE_CHECKING:
    from flext_infra import m, t


class FlextInfraProtocolsRope(Protocol):
    """Structural contracts layered on top of Rope's concrete runtime classes."""

    @runtime_checkable
    class RopeProjectRootLike(Protocol):
        """Minimal contract for rope project's root resource."""

        @property
        def real_path(self) -> str:
            """Absolute filesystem path for the project root."""
            ...

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
    class RopeApiResourceLike(Protocol):
        """Minimal contract for rope resources used by refactor APIs."""

        @property
        def path(self) -> str:
            """Relative path within the rope project."""
            ...

        @property
        def real_path(self) -> str:
            """Absolute filesystem path."""
            ...

    @runtime_checkable
    class RopeProjectLike(Protocol):
        """Minimal contract for rope Project objects."""

        @property
        def root(self) -> FlextInfraProtocolsRope.RopeProjectRootLike:
            """Project root resource."""
            ...

        @property
        def pycore(self) -> t.OpaqueValue:
            """Rope's dynamic PyCore object."""
            ...

        def get_resource(self, resource_name: str) -> t.OpaqueValue:
            """Resolve one resource path inside the project."""
            ...

        def get_pymodule(
            self,
            resource: t.Infra.RopeApiResource,
            *,
            force_errors: bool = False,
        ) -> t.OpaqueValue:
            """Return the PyModule for one resource."""
            ...

        def do(
            self,
            changes: t.Infra.RopeChanges,
            task_handle: t.OpaqueValue | None = None,
        ) -> None:
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
        def resource(self) -> t.Infra.RopeApiResource:
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
        def changes(self) -> Sequence[t.Infra.RopeChange]:
            """Return nested changes carried by this change set."""
            ...

    @runtime_checkable
    class RopeMutableChangesLike(RopeChangesLike, Protocol):
        """ChangeSet-like object that can receive child changes."""

        def add_change(
            self,
            change: t.Infra.RopeChange,
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
            resource: t.Infra.RopeResource,
            *,
            force_errors: bool = False,
        ) -> t.Infra.RopePyModule:
            """Convert a resource to its PyModule representation."""
            ...

    @runtime_checkable
    class RopePyModuleLike(Protocol):
        """Structural contract for rope PyModule objects."""

        def get_attributes(self) -> t.MappingKV[str, t.Infra.RopePyName]:
            """Return module-level attributes as a name → pyname mapping."""
            ...

        def get_name(self) -> str | None:
            """Return the module name, or None."""
            ...

        def get_resource(self) -> t.Infra.RopeResource | None:
            """Return the resource backing this module, or None for builtins."""
            ...

    @runtime_checkable
    class RopePyNameLike(Protocol):
        """Structural contract for rope PyName objects."""

        def get_object(self) -> t.Infra.RopePyObject:
            """Return the Python object this name refers to."""
            ...

        def get_definition_location(
            self,
        ) -> t.Pair[t.Infra.RopePyModule | None, int | None]:
            """Return (module, line_number) of this name's definition."""
            ...

    @runtime_checkable
    class RopeAbstractClassLike(Protocol):
        """Structural contract for rope class-like objects."""

        def get_attributes(self) -> t.MappingKV[str, t.Infra.RopePyName]:
            """Return class attributes."""
            ...

        def get_module(self) -> t.Infra.RopePyModule | None:
            """Return the module containing this class."""
            ...

        def get_name(self) -> str | None:
            """Return the class name, or None."""
            ...

        def get_superclasses(
            self,
        ) -> Sequence[t.Infra.RopeAbstractClass]:
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

        def get_module(self) -> t.Infra.RopePyModule | None:
            """Return the module containing this object, or None."""
            ...

    @runtime_checkable
    class RopeNamedObjectLike(Protocol):
        """Structural contract for Rope objects that expose ``get_name``."""

        def get_name(self) -> str | None:
            """Return the name of this object, or None."""
            ...

    @runtime_checkable
    class RopeLocationLike(Protocol):
        """Structural contract for rope occurrence search results."""

        resource: t.Infra.RopeApiResource
        """Resource containing the occurrence."""

        lineno: int
        """1-based line number."""

        region: t.IntPair
        """Byte-offset region."""

    @runtime_checkable
    class RopeImportInfoLike(Protocol):
        """Structural contract for rope import descriptors."""

        names_and_aliases: t.MutableSequenceOf[t.Pair[str, str | None]]
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

        @property
        def import_info(self) -> t.Infra.RopeImportInfo:
            """Underlying import descriptor."""
            ...

        @import_info.setter
        def import_info(self, value: t.Infra.RopeImportInfo) -> None:
            """Replace the underlying import descriptor."""
            ...

    @runtime_checkable
    class RopeModuleImportsLike(Protocol):
        """Structural contract for rope's ModuleImports helper."""

        @property
        def imports(
            self,
        ) -> (
            Sequence[t.Infra.RopeImportStatement]
            | Callable[[], Sequence[t.Infra.RopeImportStatement]]
        ):
            """Discovered import statements."""
            ...

        def add_import(
            self,
            import_info: t.Infra.RopeImportInfo,
        ) -> None:
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

        def get_changes(self, new_name: str) -> t.Infra.RopeChanges:
            """Build rename changes for the requested symbol."""
            ...

    @runtime_checkable
    class RopeImportOrganizerLike(Protocol):
        """Structural contract for rope import organizers."""

        def organize_imports(
            self,
            resource: FlextInfraProtocolsRope.RopeApiResourceLike,
            offset: int | None = None,
        ) -> FlextInfraProtocolsRope.RopeChangesLike | None:
            """Return one change set that rewrites imports."""
            ...

    @runtime_checkable
    class RopeImportUtilsModuleLike(Protocol):
        """Structural contract for the rope.refactor.importutils module."""

        def get_module_imports(
            self,
            project: t.Infra.RopeProject,
            pymodule: t.Infra.RopePyModule,
        ) -> t.Infra.RopeModuleImports:
            """Build one module-import helper for the given module."""
            ...

    @runtime_checkable
    class RopeFindItModuleLike(Protocol):
        """Structural contract for the rope.contrib.findit module."""

        def find_occurrences(
            self,
            project: t.Infra.RopeProject,
            resource: t.Infra.RopeApiResource,
            offset: int,
            *,
            unsure: bool = False,
            resources: t.SequenceOf[t.Infra.RopeApiResource] | None = None,
            in_hierarchy: bool = False,
            task_handle: t.OpaqueValue | None = None,
        ) -> t.SequenceOf[t.Infra.RopeLocation]:
            """Return occurrences for the symbol at the given offset."""
            ...

    class RopeGetModuleImportsFn(Protocol):
        """Callable signature for ``rope.refactor.importutils.get_module_imports``."""

        def __call__(
            self,
            project: t.Infra.RopeProject,
            pymodule: t.Infra.RopePyModule,
        ) -> t.Infra.RopeModuleImports:
            """Build one module-import helper for the given module."""
            ...

    class RopeFindOccurrencesFn(Protocol):
        """Callable signature for ``rope.contrib.findit.find_occurrences``."""

        def __call__(
            self,
            project: t.Infra.RopeProject,
            resource: t.Infra.RopeApiResource,
            offset: int,
            *,
            unsure: bool = False,
            resources: t.SequenceOf[t.Infra.RopeApiResource] | None = None,
            in_hierarchy: bool = False,
            task_handle: t.OpaqueValue | None = None,
        ) -> t.SequenceOf[t.Infra.RopeLocation]:
            """Return occurrences for the symbol at the given offset."""
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
        ) -> t.SequenceOf[m.Infra.Result]:
            """Execute the hook and return results."""
            ...

    class RopeAnalysisMethods(Protocol):
        """Structural contract for Rope analysis class helpers."""

        @staticmethod
        def get_module_classes(
            rope_project: t.Infra.RopeProject,
            resource: t.Infra.RopeResource,
        ) -> t.StrSequence: ...

        @staticmethod
        def get_class_methods(
            rope_project: t.Infra.RopeProject,
            resource: t.Infra.RopeResource,
            class_name: str,
            *,
            include_private: bool = False,
        ) -> t.StrMapping: ...

        @staticmethod
        def method_kind_label(method_kind: str) -> str: ...

        @staticmethod
        def discover_project_root_from_file(file_path: Path) -> Path | None: ...

        @staticmethod
        def init_rope_project(
            workspace_root: Path,
            *,
            project_prefix: str = "",
            src_dir: str = "",
            ignored_resources: t.VariadicTuple[str] = (),
        ) -> t.Infra.RopeProject: ...

        @staticmethod
        def get_resource_from_path(
            rope_project: t.Infra.RopeProject,
            file_path: Path,
        ) -> t.Infra.RopeResource | None: ...


__all__ = ["FlextInfraProtocolsRope"]
