"""Structural read contracts of the per-run workspace snapshot.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Iterator, MutableMapping, Sequence
from contextlib import AbstractContextManager
from typing import TYPE_CHECKING, Literal, Protocol, Self, runtime_checkable

if TYPE_CHECKING:
    from pathlib import Path

    from flext_infra import m, p, t


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

        def add(self, key: str, value: str) -> None: ...

        def set(self, key: str, value: bool | Sequence[str]) -> None: ...

    @runtime_checkable
    class RopeChangeSet(Protocol):
        """Rope change set shape."""

        changes: list[p.AttributeProbe]

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
        def source_plans(self) -> tuple[m.Infra.CodegenFilePlan, ...]: ...

        def source_view(
            self,
            *,
            declared_files: tuple[m.Infra.CodegenFilePlan, ...] | None = (),
            additional_source_folders: tuple[str, ...] | None = (),
        ) -> AbstractContextManager[Self]: ...

        def source_state(
            self, path: Path, *, required: bool = True
        ) -> m.Cli.AtomicFileState: ...

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
            folder: FlextInfraProtocolsWorkspaceSnapshot.RopeRoot | None = None,
        ) -> FlextInfraProtocolsWorkspaceSnapshot.RopeResource | None: ...

        def get_module(
            self,
            name: str,
            folder: FlextInfraProtocolsWorkspaceSnapshot.RopeRoot | None = None,
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
            folder: FlextInfraProtocolsWorkspaceSnapshot.RopeRoot | None = None,
        ) -> None: ...

        def close(self) -> None: ...

        def get_prefs(self) -> FlextInfraProtocolsWorkspaceSnapshot.RopePreferences: ...

        def frozen_layout(self) -> AbstractContextManager[Self]: ...

    @runtime_checkable
    class WorkspaceSnapshotSource(Protocol):
        """One workspace file as the run read it."""

        @property
        def path(self) -> Path:
            """Resolved file path."""
            ...

        @property
        def state(self) -> m.Cli.AtomicFileState:
            """Authenticated state the run reads and publishes."""
            ...

        @property
        def digest(self) -> str:
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
    class WorkspaceBootstrapDependencies(Protocol):
        """Bootstrap closure and the native source epoch that established it."""

        @property
        def namespace(self) -> str: ...

        @property
        def modules(self) -> tuple[t.Infra.RopeNativeParsedModule, ...]: ...

        @property
        def source_folders(self) -> tuple[str, ...]: ...

        @property
        def python_path_folders(self) -> tuple[str, ...]: ...

        @property
        def source_digests(self) -> tuple[str, ...]: ...

        @property
        def dependencies(self) -> frozenset[str]: ...

    @runtime_checkable
    class WorkspaceSnapshot(Protocol):
        """Read surface of the one Rope model a workspace run shares.

        Stages depend on this surface, never on the concrete model; the run's
        composition root builds the snapshot once and injects it. Queries go
        through the ``u.Infra`` snapshot owner, which fills these memos.
        """

        @property
        def workspace_root(self) -> Path:
            """Resolved root of the workspace."""
            ...

        @property
        def members(self) -> tuple[Path, ...]:
            """Resolved member roots."""
            ...

        @property
        def engine(self) -> p.Infra.RopeProject:
            """The one source engine project; planned effects enter its overlay."""
            ...

        @property
        def python_files(self) -> MutableMapping[Path, tuple[Path, ...]]:
            """Python sources of each member, listed on first query."""
            ...

        @property
        def directory_facts(
            self,
        ) -> MutableMapping[Path, tuple[Path | None, str]]:
            """Physical directory owner and package name."""
            ...

        @property
        def python_module_facts(
            self,
        ) -> MutableMapping[t.Infra.RopeNativeParsedModule, m.Infra.PythonModuleFacts]:
            """Static facts keyed by the original engine's parsed module."""
            ...

        @property
        def sources(
            self,
        ) -> MutableMapping[
            Path, FlextInfraProtocolsWorkspaceSnapshot.WorkspaceSnapshotSource
        ]:
            """Authenticated reads of this run, made on first query."""
            ...

        @property
        def packages(self) -> MutableMapping[Path, str]:
            """Dotted package of each queried directory."""
            ...

        @property
        def import_edges(
            self,
        ) -> MutableMapping[Path, tuple[frozenset[str], frozenset[str]]]:
            """Runtime and typing-only imported modules per queried source."""
            ...

        @property
        def bootstrap_dependencies(
            self,
        ) -> MutableMapping[
            Path, FlextInfraProtocolsWorkspaceSnapshot.WorkspaceBootstrapDependencies
        ]:
            """Bootstrap closure bound to native modules and resolver roots."""
            ...

        @property
        def absolute_import_roots(self) -> MutableMapping[Path, t.StrTuple]:
            """Absolute imported package roots per captured member."""
            ...

        @property
        def import_namespaces(
            self,
        ) -> MutableMapping[tuple[Path, Path], tuple[Path, str] | None]:
            """Import-law namespace election per consumer and source."""
            ...

        @property
        def class_ancestors(self) -> MutableMapping[str, t.StrTuple]:
            """C3 method order per qualified class identity."""
            ...

        @property
        def exports(self) -> MutableMapping[Path, Sequence[str]]:
            """Declared public names per module."""
            ...

        @property
        def bindings(self) -> MutableMapping[Path, dict[str, str]]:
            """Module-level name to bound qualified source per module."""
            ...

        @property
        def initializer_aliases(self) -> MutableMapping[Path, dict[str, str]]:
            """Aliases each initializer publishes."""
            ...

        @property
        def receiver_bindings(self) -> MutableMapping[tuple[Path, str], Path | None]:
            """Module each source binds a facade letter from."""
            ...

        @property
        def facade_paths(self) -> MutableMapping[tuple[Path, str], Path]:
            """Facade module per package and letter."""
            ...

        @property
        def pyproject_texts(self) -> MutableMapping[tuple[Path, str], str]:
            """Recovered pyproject text per path and digest."""
            ...

        @property
        def codemod_renderings(
            self,
        ) -> MutableMapping[tuple[Path, str], m.Infra.CodemodNativeGenerated]:
            """Native codemod rendering per member root and render-input digest."""
            ...


__all__: list[str] = ["FlextInfraProtocolsWorkspaceSnapshot"]
