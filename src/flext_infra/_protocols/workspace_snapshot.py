"""Structural read contracts of the per-run workspace snapshot.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, runtime_checkable

if TYPE_CHECKING:
    from collections.abc import MutableMapping
    from pathlib import Path

    from flext_infra import m, p, t


@runtime_checkable
class FlextInfraProtocolsWorkspaceSnapshot(Protocol):
    """Workspace snapshot protocols exposed through ``p.Infra``."""

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
        def exports(self) -> MutableMapping[Path, t.StrSequence]:
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
