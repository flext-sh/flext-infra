# AUTO-GENERATED FILE — Regenerate with: make gen
"""Source-derived structural model contracts.

Copyright (c) 2026 FLEXT Team. All rights reserved.
src/flext_infra/_protocols/codegen_toolchain
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Protocol, runtime_checkable

from flext_cli import FlextCliProtocols

if TYPE_CHECKING:
    from flext_cli import p

    from flext_infra import t


class FlextInfraProtocolsCodegenToolchain:
    """Own the structural contracts declared by its model source."""

    @runtime_checkable
    class MiseToolchainProjectLayout(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def selector(self) -> t.NonEmptyStr:
            """Workspace-relative project selector."""
            ...

        @property
        def root(self) -> Path:
            """Resolved project root."""
            ...

        @property
        def transaction_root(self) -> Path | None:
            """Persistent transaction root on this project filesystem."""
            ...

        @property
        def config(self) -> Path:
            """Generated Mise configuration destination."""
            ...

    @runtime_checkable
    class CodegenFileParticipant(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def selector(self) -> str:
            """File capability identity."""
            ...

        @property
        def root(self) -> Path:
            """Exact authorized destination root."""
            ...

        @property
        def device(self) -> int:
            """Authenticated root device."""
            ...

        @property
        def inode(self) -> int:
            """Authenticated root inode."""
            ...

        @property
        def transaction_root(self) -> Path:
            """Destination-local staging for this transaction."""
            ...

    @runtime_checkable
    class MiseToolchainWorkspaceLayout(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def scope_root(self) -> Path:
            """Resolved transaction scope."""
            ...

        @property
        def state_root(self) -> Path:
            """Persistent scope transaction staging directory."""
            ...

        @property
        def journal_path(self) -> Path:
            """Direct journal under the authenticated scope Git directory."""
            ...

        @property
        def transaction_id(self) -> str | None:
            """Current unpredictable transaction identity, if mutating."""
            ...

        @property
        def projects(
            self,
        ) -> tuple[FlextInfraProtocolsCodegenToolchain.MiseToolchainProjectLayout, ...]:
            """Ordered Mise workspace participants."""
            ...

        @property
        def file_participants(
            self,
        ) -> tuple[FlextInfraProtocolsCodegenToolchain.CodegenFileParticipant, ...]:
            """Explicit non-Mise publication capabilities."""
            ...

    @runtime_checkable
    class MiseToolchainConfigState(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def before(self) -> p.Cli.AtomicFileState:
            """Exact preflight state of the live configuration."""
            ...

        @property
        def replacement_content(self) -> bytes:
            """Exact rendered bytes to stage and publish."""
            ...

        @property
        def replacement_mode(self) -> int:
            """Exact permission mode to stage and publish."""
            ...

        @property
        def sources(self) -> tuple[p.Cli.AtomicFileState, ...]:
            """Ordered YAML states that produced the replacement."""
            ...

    @runtime_checkable
    class MiseToolchainProjectState(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def layout(
            self,
        ) -> FlextInfraProtocolsCodegenToolchain.MiseToolchainProjectLayout:
            """Stable project layout owning this snapshot."""
            ...

        @property
        def config(
            self,
        ) -> FlextInfraProtocolsCodegenToolchain.MiseToolchainConfigState:
            """Planned generated Mise configuration state."""
            ...

    @runtime_checkable
    class MiseToolchainWorkspacePlan(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def layout(
            self,
        ) -> FlextInfraProtocolsCodegenToolchain.MiseToolchainWorkspaceLayout:
            """Stable workspace topology."""
            ...

        @property
        def projects(
            self,
        ) -> tuple[FlextInfraProtocolsCodegenToolchain.MiseToolchainProjectState, ...]:
            """Ordered complete workspace topology."""
            ...

        @property
        def sources(self) -> tuple[p.Cli.AtomicFileState, ...]:
            """Every state the publication reads: the planned declarations."""
            ...


__all__: list[str] = [
    "FlextInfraProtocolsCodegenToolchain",
]
