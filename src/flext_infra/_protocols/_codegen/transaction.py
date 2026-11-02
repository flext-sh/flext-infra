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

if TYPE_CHECKING:
    from flext_infra import p
    from flext_infra._protocols import FlextInfraProtocolsWorkspaceSnapshot


class FlextInfraProtocolsCodegenTransaction:
    """Own the structural contracts declared by its model source."""

    @runtime_checkable
    class CodegenFilePlan(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def path(self) -> Path: ...
        @property
        def before(self) -> p.Cli.AtomicFileState: ...
        @property
        def desired_content(self) -> bytes | None: ...
        @property
        def desired_mode(self) -> int | None: ...
        @property
        def inputs(self) -> tuple[p.Cli.AtomicFileState, ...]: ...
        @property
        def project(self) -> Path: ...
        @property
        def move_source(self) -> Path | None: ...
        @property
        def owner(self) -> str: ...
        @property
        def policy(self) -> Literal["full", "merge"] | None: ...
        @property
        def tracking(self) -> Literal["versioned", "runtime-local"]: ...
        @property
        def index_before(self) -> p.Infra.GitWorktreeIndexEntry | None: ...
        @property
        def tracking_dependencies(self) -> tuple[Path, ...]: ...

    @runtime_checkable
    class StageSourceOptions(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def workspaces(self) -> tuple[Path, ...]: ...
        @property
        def modes(self) -> Mapping[Path, int] | None: ...
        @property
        def declared_files(self) -> tuple[p.Infra.CodegenFilePlan, ...]: ...
        @property
        def inputs(self) -> tuple[p.Cli.AtomicFileState, ...]: ...
        @property
        def import_edges(
            self,
        ) -> Mapping[Path, tuple[frozenset[str], frozenset[str]]]: ...
        @property
        def snapshot(
            self,
        ) -> FlextInfraProtocolsWorkspaceSnapshot.WorkspaceSnapshot | None: ...

    @runtime_checkable
    class StageSourcePlan(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def workspace(self) -> Path: ...
        @property
        def workspaces(self) -> tuple[Path, ...]: ...
        @property
        def roots(self) -> tuple[Path, ...]: ...
        @property
        def inputs(self) -> tuple[p.Cli.AtomicFileState, ...]: ...
        @property
        def updates(self) -> Mapping[Path, str | None]: ...
        @property
        def modes(self) -> Mapping[Path, int]: ...
        @property
        def declared_files(self) -> tuple[p.Infra.CodegenFilePlan, ...]: ...
        @property
        def layouts(self) -> tuple[p.Infra.RopeProjectLayout, ...]: ...
        @property
        def workspace_packages(self) -> tuple[str, ...]: ...
        @property
        def candidate_layouts(self) -> tuple[p.Infra.RopeProjectLayout, ...]: ...
        @property
        def candidate_workspace_packages(self) -> tuple[str, ...]: ...

    @runtime_checkable
    class SemanticSourcePlan(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def candidate(self) -> p.Infra.StageSourcePlan: ...
        @property
        def consumer_roots(self) -> tuple[Path, ...]: ...


__all__: list[str] = [
    "FlextInfraProtocolsCodegenTransaction",
]
