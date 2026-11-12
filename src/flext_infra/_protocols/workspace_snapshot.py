"""Structural read contracts of the per-run workspace snapshot.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from flext_cli import p

    from flext_infra._protocols import FlextInfraProtocolsRefactorAstGrep
    from flext_infra._protocols._codegen import (
        FlextInfraProtocolsCodegenLazyInit,
        FlextInfraProtocolsCodegenTransaction,
    )


from collections.abc import Iterator, Mapping, Sequence
from contextlib import AbstractContextManager
from typing import Literal, Protocol, Self, runtime_checkable

from flext_cli import FlextCliProtocols

if TYPE_CHECKING:
    from pathlib import Path

    from flext_infra import t


@runtime_checkable
class FlextInfraProtocolsWorkspaceSnapshot(Protocol):
    """Workspace snapshot protocols exposed through ``p.Infra``."""

    @runtime_checkable
    class RopeProjectFiles(Protocol):
        """Filesystem observations consumed by native project construction."""

        def realpath(self, path: str) -> str: ...

        def exists(self, path: str) -> bool: ...

        def isfile(self, path: str) -> bool: ...

        def isdir(self, path: str) -> bool: ...

        def listdir(self, path: str) -> list[str]: ...

        def read(self, path: str) -> bytes: ...

    @runtime_checkable
    class RopeResource(Protocol):
        """Rope project resource shape shared by files and folders."""

        def is_folder(self) -> bool: ...

        def exists(self) -> bool: ...

        @property
        def name(self) -> str: ...

        @property
        def path(self) -> str: ...

        @property
        def real_path(self) -> str: ...

        @property
        def parent(self) -> FlextInfraProtocolsWorkspaceSnapshot.RopeRoot: ...

    @runtime_checkable
    class RopeRoot(RopeResource, Protocol):
        """Folder resource with the SDK's child lookup contract."""

        def get_children(
            self,
        ) -> Sequence[FlextInfraProtocolsWorkspaceSnapshot.RopeResource]: ...

        def get_child(
            self,
            name: str,
        ) -> FlextInfraProtocolsWorkspaceSnapshot.RopeResource: ...

        def has_child(self, name: str) -> bool: ...

    @runtime_checkable
    class RopeFile(RopeResource, Protocol):
        """Rope file resource with content access."""

        def read(self) -> str: ...

        def write(self, contents: str) -> None: ...

    @runtime_checkable
    class RopePreferences(Protocol):
        """Native preference updates required by project source election."""

        @property
        def imports(self) -> t.Infra.RopeNativeImportPrefs: ...

        def add(self, key: str, value: str) -> None: ...

        def set(self, key: str, *, value: bool | Sequence[str]) -> None: ...

    @runtime_checkable
    class RopeChange(Protocol):
        """One pending native resource update."""

        resource: FlextInfraProtocolsWorkspaceSnapshot.RopeResource
        new_contents: str

    @runtime_checkable
    class RopeChangeSet(Protocol):
        """Rope change set shape."""

        changes: list[FlextInfraProtocolsWorkspaceSnapshot.RopeChange]

        def do(self) -> None:
            """Apply the native change set."""
            ...

        def undo(self) -> None:
            """Undo the native change set."""
            ...

    @runtime_checkable
    class RopeModuleFinder(Protocol):
        """Native relative module lookup shared by every Rope project flavour."""

        def find_relative_module(
            self,
            modname: str,
            folder: FlextInfraProtocolsWorkspaceSnapshot.RopeRoot,
            level: int,
        ) -> FlextInfraProtocolsWorkspaceSnapshot.RopeResource | None: ...

    @runtime_checkable
    class RopeSourceAccess(Protocol):
        """Source reads through the project's overlaid filesystem view."""

        @property
        def source_plans(
            self,
        ) -> tuple[FlextInfraProtocolsCodegenTransaction.CodegenFilePlan, ...]: ...

        def source_view(
            self,
            *,
            declared_files: tuple[
                FlextInfraProtocolsCodegenTransaction.CodegenFilePlan, ...
            ]
            | None = (),
            additional_source_folders: tuple[str, ...] | None = (),
            analysis_files: Mapping[Path, str] | None = None,
        ) -> AbstractContextManager[Self]: ...

        def source_state(
            self, path: Path, *, required: bool = True
        ) -> p.Cli.AtomicFileState: ...

        def source_owned(self, path: Path) -> bool: ...

        def source_query(
            self, path: Path, predicate: Literal["exists", "isfile", "isdir"]
        ) -> bool: ...

        def source_children(self, path: Path) -> tuple[Path, ...]: ...

        def source_text(self, path: Path) -> str: ...

        def source_bytes(self, path: Path) -> bytes: ...

        def source_walk(
            self,
            path: Path,
        ) -> Iterator[tuple[Path, list[str], list[str]]]: ...

    @runtime_checkable
    class RopeProject(RopeModuleFinder, RopeSourceAccess, Protocol):
        """Compose native project lifecycle with authenticated source access."""

        @property
        def root(self) -> FlextInfraProtocolsWorkspaceSnapshot.RopeRoot: ...

        @property
        def fscommands(
            self,
        ) -> FlextInfraProtocolsWorkspaceSnapshot.RopeProjectFiles: ...

        def get_resource(
            self,
            resource_name: str,
        ) -> FlextInfraProtocolsWorkspaceSnapshot.RopeResource: ...

        def get_file(
            self,
            path: str,
        ) -> FlextInfraProtocolsWorkspaceSnapshot.RopeFile: ...

        def get_folder(
            self,
            path: str,
        ) -> FlextInfraProtocolsWorkspaceSnapshot.RopeRoot: ...

        def get_pymodule(
            self,
            resource: t.Infra.RopeNativeResource
            | FlextInfraProtocolsWorkspaceSnapshot.RopeResource,
            *,
            force_errors: bool = False,
        ) -> t.Infra.RopeNativeParsedModule: ...

        def get_pycore(self) -> p.AttributeProbe: ...

        def get_source_folders(
            self,
        ) -> Sequence[FlextInfraProtocolsWorkspaceSnapshot.RopeResource]: ...

        def get_python_path_folders(
            self,
        ) -> Sequence[FlextInfraProtocolsWorkspaceSnapshot.RopeResource]: ...

        def find_module(
            self,
            modname: str,
            folder: FlextInfraProtocolsWorkspaceSnapshot.RopeRoot
            | FlextInfraProtocolsWorkspaceSnapshot.RopeResource
            | None = None,
        ) -> FlextInfraProtocolsWorkspaceSnapshot.RopeResource | None: ...

        def get_module(
            self,
            name: str,
            folder: FlextInfraProtocolsWorkspaceSnapshot.RopeRoot
            | FlextInfraProtocolsWorkspaceSnapshot.RopeResource
            | None = None,
        ) -> t.Infra.RopeNativeSemanticModule: ...

        def get_relative_module(
            self,
            name: str,
            folder: FlextInfraProtocolsWorkspaceSnapshot.RopeRoot,
            level: int,
        ) -> t.Infra.RopeNativeParsedModule: ...

        def get_python_files(
            self,
        ) -> Sequence[FlextInfraProtocolsWorkspaceSnapshot.RopeFile]: ...

        def do(
            self, changes: FlextInfraProtocolsWorkspaceSnapshot.RopeChangeSet
        ) -> None: ...

        def validate(
            self,
            folder: FlextInfraProtocolsWorkspaceSnapshot.RopeRoot
            | FlextInfraProtocolsWorkspaceSnapshot.RopeResource
            | None = None,
        ) -> None: ...

        def close(self) -> None: ...

        def get_prefs(self) -> FlextInfraProtocolsWorkspaceSnapshot.RopePreferences: ...

        def frozen_layout(self) -> AbstractContextManager[Self]: ...

    @runtime_checkable
    class WorkspaceSnapshotSource(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def path(self) -> Path:
            """Resolved file path."""
            ...

        @property
        def state(self) -> p.Cli.AtomicFileState:
            """Authenticated state the run reads and publishes."""
            ...

        @property
        def digest(self) -> t.NonEmptyStr:
            """SHA-256 of the exact file bytes."""
            ...

        @property
        def module(self) -> str:
            """Dotted module name; empty outside a package."""
            ...

        @property
        def member(self) -> Path:
            """Resolved owning member root."""
            ...

        @property
        def text(self) -> str:
            """Exact decoded file text."""
            ...

    @runtime_checkable
    class WorkspaceBootstrapDependencies(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def namespace(self) -> str:
            """Publishing namespace."""
            ...

        @property
        def modules(self) -> tuple[t.Infra.RopeSourceModule, ...]:
            """Native modules of the source epoch."""
            ...

        @property
        def source_folders(self) -> tuple[str, ...]:
            """Native source folder election."""
            ...

        @property
        def python_path_folders(self) -> tuple[str, ...]:
            """Native Python path election."""
            ...

        @property
        def source_digests(self) -> tuple[str, ...]:
            """Digests of the elected source bytes."""
            ...

        @property
        def dependencies(self) -> frozenset[str]:
            """Runtime bootstrap dependencies."""
            ...

    @runtime_checkable
    class WorkspaceSnapshot(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def workspace_root(self) -> Path:
            """Resolved root of the workspace."""
            ...

        @property
        def members(self) -> tuple[Path, ...]:
            """Resolved member roots."""
            ...

        @property
        def engine(self) -> t.Infra.RopeProject:
            """The one source engine project; planned effects enter its overlay."""
            ...

        @property
        def python_files(self) -> dict[Path, tuple[Path, ...]]:
            """Python sources of each member."""
            ...

        @property
        def directory_facts(self) -> dict[Path, tuple[Path | None, str]]:
            """Physical directory owner and package name."""
            ...

        @property
        def python_module_facts(
            self,
        ) -> dict[
            t.Infra.RopeNativeParsedModule,
            FlextInfraProtocolsCodegenLazyInit.PythonModuleFacts,
        ]:
            """Shared static facts keyed by the original engine parse."""
            ...

        @property
        def sources(
            self,
        ) -> dict[Path, FlextInfraProtocolsWorkspaceSnapshot.WorkspaceSnapshotSource]:
            """Authenticated reads of this run."""
            ...

        @property
        def packages(self) -> dict[Path, str]:
            """Dotted package of each directory."""
            ...

        @property
        def import_edges(self) -> dict[Path, tuple[frozenset[str], frozenset[str]]]:
            """Runtime and typing-only imported modules per source."""
            ...

        @property
        def bootstrap_dependencies(
            self,
        ) -> dict[
            Path, FlextInfraProtocolsWorkspaceSnapshot.WorkspaceBootstrapDependencies
        ]:
            """Bootstrap facts per native source epoch."""
            ...

        @property
        def absolute_import_roots(self) -> dict[Path, t.StrTuple]:
            """Absolute imported package roots per captured member."""
            ...

        @property
        def import_namespaces(self) -> dict[tuple[Path, Path], tuple[Path, str] | None]:
            """Import-law namespace election per consumer and source."""
            ...

        @property
        def class_ancestors(self) -> dict[str, t.StrTuple]:
            """C3 method order per qualified class identity."""
            ...

        @property
        def exports(self) -> dict[Path, Sequence[str]]:
            """Declared public names per module."""
            ...

        @property
        def bindings(self) -> dict[Path, dict[str, str]]:
            """Module-level name to bound qualified source per module."""
            ...

        @property
        def initializer_aliases(self) -> dict[Path, dict[str, str]]:
            """Aliases each initializer publishes."""
            ...

        @property
        def receiver_bindings(self) -> dict[tuple[Path, str], Path | None]:
            """Module each source binds a facade letter from."""
            ...

        @property
        def facade_paths(self) -> dict[tuple[Path, str], Path]:
            """Facade module per package and letter."""
            ...

        @property
        def pyproject_texts(self) -> dict[tuple[Path, str], str]:
            """Recovered pyproject text per path and digest."""
            ...

        @property
        def codemod_renderings(
            self,
        ) -> dict[
            tuple[Path, str], FlextInfraProtocolsRefactorAstGrep.CodemodNativeGenerated
        ]:
            """Native codemod rendering per member root and render-input digest."""
            ...


__all__: list[str] = ["FlextInfraProtocolsWorkspaceSnapshot"]
