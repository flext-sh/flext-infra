# AUTO-GENERATED FILE — Regenerate with: make gen
"""Source-derived structural model contracts.

Copyright (c) 2026 FLEXT Team. All rights reserved.
src/flext_infra/_protocols/_codegen/transaction
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import TYPE_CHECKING, Literal, Protocol, runtime_checkable

from flext_cli import FlextCliProtocols

from flext_infra._protocols import FlextInfraProtocolsBase

if TYPE_CHECKING:
    from flext_cli import p

    from flext_infra._protocols import FlextInfraProtocolsWorkspaceSnapshot
    from flext_infra._protocols._codegen import FlextInfraProtocolsCodegenLazyInit
    from flext_infra._protocols._git import FlextInfraProtocolsGitWorktreeState


class FlextInfraProtocolsCodegenTransaction:
    """Own the structural contracts declared by its model source."""

    @runtime_checkable
    class CodegenFilePlan(FlextCliProtocols.Model, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def path(self) -> Path:
            """Absolute destination path."""
            ...

        @property
        def before(self) -> p.Cli.AtomicFileState:
            """Destination state observed while planning."""
            ...

        @property
        def desired_content(self) -> bytes | None:
            """Desired bytes, or None to delete."""
            ...

        @property
        def desired_mode(self) -> int | None:
            """Desired mode, or None with deletion."""
            ...

        @property
        def inputs(self) -> tuple[p.Cli.AtomicFileState, ...]:
            """Original read-only observations consumed by this effect."""
            ...

        @property
        def project(self) -> Path:
            """Physical owning project root."""
            ...

        @property
        def move_source(self) -> Path | None:
            """Original source retired by this native resource move."""
            ...

        @property
        def owner(self) -> str:
            """Canonical artifact owner, empty for scaffold files."""
            ...

        @property
        def policy(self) -> Literal["full", "merge"] | None:
            """Governed root artifact policy."""
            ...

        @property
        def tracking(self) -> Literal["versioned", "runtime-local"]:
            """Declared persistence policy of this artifact."""
            ...

        @property
        def index_before(
            self,
        ) -> FlextInfraProtocolsGitWorktreeState.GitWorktreeIndexEntry | None:
            """Captured index entry scheduled for retirement."""
            ...

        @property
        def tracking_dependencies(self) -> tuple[Path, ...]:
            """Portable declaration destinations required before retirement."""
            ...

    @runtime_checkable
    class StageSourceOptions(FlextInfraProtocolsBase.FrozenArbitrary, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def workspaces(self) -> tuple[Path, ...]:
            """Explicit composition scopes of the staged view."""
            ...

        @property
        def modes(self) -> Mapping[Path, int] | None:
            """Declared source modes preserved during staging."""
            ...

        @property
        def declared_files(
            self,
        ) -> tuple[FlextInfraProtocolsCodegenTransaction.CodegenFilePlan, ...]:
            """Authenticated candidate file declarations."""
            ...

        @property
        def inputs(self) -> tuple[p.Cli.AtomicFileState, ...]:
            """Original source observations whose layouts join the closure."""
            ...

        @property
        def import_edges(self) -> Mapping[Path, tuple[frozenset[str], frozenset[str]]]:
            """Captured runtime and typing import facts retained by reference."""
            ...

        @property
        def snapshot(
            self,
        ) -> FlextInfraProtocolsWorkspaceSnapshot.WorkspaceSnapshot | None:
            """Structural member projected from the owning model.

            Run snapshot whose authenticated reads and import edges elect the
            closure instead of a second read and parse.
            """
            ...

    @runtime_checkable
    class StageSourcePlan(FlextInfraProtocolsBase.FrozenArbitrary, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def workspace(self) -> Path:
            """Canonical source workspace root."""
            ...

        @property
        def workspaces(self) -> tuple[Path, ...]:
            """Explicit composition scopes, never a parent-directory scan."""
            ...

        @property
        def roots(self) -> tuple[Path, ...]:
            """Discovered project roots covering the pinned source closure."""
            ...

        @property
        def inputs(self) -> tuple[p.Cli.AtomicFileState, ...]:
            """Exact source and configuration observations."""
            ...

        @property
        def updates(self) -> Mapping[Path, str | None]:
            """Structural member projected from the owning model.

            Desired sources keyed by live destination; None retires an artifact.
            """
            ...

        @property
        def modes(self) -> Mapping[Path, int]:
            """Desired file-effect modes derived from original move sources."""
            ...

        @property
        def declared_files(
            self,
        ) -> tuple[FlextInfraProtocolsCodegenTransaction.CodegenFilePlan, ...]:
            """Original file/absence witnesses with the current desired effects."""
            ...

        @property
        def layouts(
            self,
        ) -> tuple[FlextInfraProtocolsCodegenLazyInit.RopeProjectLayout, ...]:
            """Original project layouts in the desired import closure."""
            ...

        @property
        def workspace_packages(self) -> tuple[str, ...]:
            """Original elected workspace namespaces."""
            ...

        @property
        def candidate_layouts(
            self,
        ) -> tuple[FlextInfraProtocolsCodegenLazyInit.RopeProjectLayout, ...]:
            """Prospective import closure of the authenticated declarations."""
            ...

        @property
        def candidate_workspace_packages(self) -> tuple[str, ...]:
            """Prospective namespaces requiring sealed candidate origins."""
            ...

    @runtime_checkable
    class SemanticSourcePlan(FlextCliProtocols.Model, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def candidate(self) -> FlextInfraProtocolsCodegenTransaction.StageSourcePlan:
            """Authenticated complete source and runtime candidate closure."""
            ...

        @property
        def consumer_roots(self) -> tuple[Path, ...]:
            """External scopes elected before producer publication."""
            ...


__all__: list[str] = [
    "FlextInfraProtocolsCodegenTransaction",
]
