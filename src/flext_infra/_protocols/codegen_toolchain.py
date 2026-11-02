# AUTO-GENERATED FILE — Regenerate with: make gen
"""Source-derived structural model contracts.

Copyright (c) 2026 FLEXT Team. All rights reserved.
src/flext_infra/_protocols/codegen_toolchain
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Protocol, runtime_checkable

from flext_infra import t

if TYPE_CHECKING:
    from flext_infra import p


class FlextInfraProtocolsCodegenToolchain:
    """Own the structural contracts declared by its model source."""

    @runtime_checkable
    class MiseToolchainProjectLayout(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def selector(self) -> t.NonEmptyStr: ...
        @property
        def root(self) -> Path: ...
        @property
        def transaction_root(self) -> Path | None: ...
        @property
        def config(self) -> Path: ...

    @runtime_checkable
    class CodegenFileParticipant(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def selector(self) -> str: ...
        @property
        def root(self) -> Path: ...
        @property
        def device(self) -> int: ...
        @property
        def inode(self) -> int: ...
        @property
        def transaction_root(self) -> Path: ...

    @runtime_checkable
    class MiseToolchainWorkspaceLayout(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def scope_root(self) -> Path: ...
        @property
        def state_root(self) -> Path: ...
        @property
        def journal_path(self) -> Path: ...
        @property
        def transaction_id(self) -> str | None: ...
        @property
        def projects(self) -> tuple[p.Infra.MiseToolchainProjectLayout, ...]: ...
        @property
        def file_participants(self) -> tuple[p.Infra.CodegenFileParticipant, ...]: ...

    @runtime_checkable
    class MiseToolchainConfigState(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def before(self) -> p.Cli.AtomicFileState: ...
        @property
        def replacement_content(self) -> bytes: ...
        @property
        def replacement_mode(self) -> int: ...
        @property
        def sources(self) -> tuple[p.Cli.AtomicFileState, ...]: ...

    @runtime_checkable
    class MiseToolchainProjectState(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def layout(self) -> p.Infra.MiseToolchainProjectLayout: ...
        @property
        def config(self) -> p.Infra.MiseToolchainConfigState: ...

    @runtime_checkable
    class MiseToolchainWorkspacePlan(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def layout(self) -> p.Infra.MiseToolchainWorkspaceLayout: ...
        @property
        def projects(self) -> tuple[p.Infra.MiseToolchainProjectState, ...]: ...
        @property
        def sources(self) -> tuple[p.Cli.AtomicFileState, ...]: ...


__all__: list[str] = [
    "FlextInfraProtocolsCodegenToolchain",
]
