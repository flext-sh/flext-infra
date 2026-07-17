"""Structural contracts for complete-worktree transaction models.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, runtime_checkable

from flext_cli import p

if TYPE_CHECKING:
    from pathlib import Path

    from flext_infra import t


@runtime_checkable
class FlextInfraProtocolsWorktree(Protocol):
    """Protocol-of-model contracts for isolated workspace transactions."""

    @runtime_checkable
    class LintSnapshot(p.BaseModel, Protocol):
        """Captured diagnostics from one lint invocation."""

        @property
        def tool(self) -> str: ...

        @property
        def exit_code(self) -> int: ...

        @property
        def errors(self) -> int: ...

        @property
        def warnings(self) -> int: ...

        @property
        def output(self) -> str: ...

    @runtime_checkable
    class RepositoryWorktree(p.BaseModel, Protocol):
        """Source repository paired with its isolated checkpoint."""

        @property
        def relative_path(self) -> str: ...

        @property
        def source_root(self) -> Path: ...

        @property
        def worktree_root(self) -> Path: ...

        @property
        def checkpoint_sha(self) -> str: ...

    @runtime_checkable
    class RepositoryDelta(p.BaseModel, Protocol):
        """Binary patch captured for one repository."""

        @property
        def relative_path(self) -> str: ...

        @property
        def source_root(self) -> Path: ...

        @property
        def worktree_root(self) -> Path: ...

        @property
        def checkpoint_sha(self) -> str: ...

        @property
        def changed_files(self) -> t.StrSequence: ...

        @property
        def patch(self) -> bytes: ...

    @runtime_checkable
    class WorktreeTransactionRequest(p.BaseModel, Protocol):
        """Validated request for one complete-worktree transaction."""

        @property
        def workspace_root(self) -> Path: ...

        @property
        def command(self) -> t.StrSequence: ...

        @property
        def selected_repositories(self) -> t.StrSequence: ...

        @property
        def apply_patch(self) -> bool: ...

        @property
        def timeout_seconds(self) -> int: ...

    @runtime_checkable
    class WorktreeTransactionReport(p.BaseModel, Protocol):
        """Complete evidence emitted by one workspace transaction."""

        @property
        def transaction_id(self) -> str: ...

        @property
        def command(self) -> t.StrSequence: ...

        @property
        def worktree_root(self) -> Path: ...

        @property
        def command_output(self) -> p.Cli.CommandOutput: ...

        @property
        def import_probe(self) -> p.Cli.CommandOutput: ...

        @property
        def lint_before(
            self,
        ) -> tuple[FlextInfraProtocolsWorktree.LintSnapshot, ...]: ...

        @property
        def lint_after(
            self,
        ) -> tuple[FlextInfraProtocolsWorktree.LintSnapshot, ...]: ...

        @property
        def repositories(
            self,
        ) -> tuple[FlextInfraProtocolsWorktree.RepositoryDelta, ...]: ...

        @property
        def breakage_detected(self) -> bool: ...

        @property
        def applied(self) -> bool: ...

        @property
        def summary(self) -> str: ...


__all__: tuple[str, ...] = ("FlextInfraProtocolsWorktree",)
