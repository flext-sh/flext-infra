# AUTO-GENERATED FILE — Regenerate with: make gen
"""Source-derived structural model contracts.

Copyright (c) 2026 FLEXT Team. All rights reserved.
src/flext_infra/_protocols/_git/identity
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Protocol, runtime_checkable

from flext_cli import FlextCliProtocols

if TYPE_CHECKING:
    from flext_infra import t


class FlextInfraProtocolsGitIdentity:
    """Own the structural contracts declared by its model source."""

    @runtime_checkable
    class GitIdentityReport(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def repo_root(self) -> Path:
            """Repository worktree root."""
            ...

        @property
        def primary_root(self) -> Path:
            """Canonical primary worktree root."""
            ...

        @property
        def head_oid(self) -> t.NonEmptyStr | None:
            """HEAD commit hex SHA, absent for an unborn branch."""
            ...

        @property
        def porcelain(self) -> str:
            """Raw git status --porcelain output."""
            ...

        @property
        def dirty(self) -> bool:
            """Whether the worktree is dirty."""
            ...

        @property
        def git_dir(self) -> Path:
            """Absolute .git directory."""
            ...

        @property
        def common_dir(self) -> Path:
            """Git common directory (shared across linked worktrees)."""
            ...

        @property
        def branch(self) -> t.NonEmptyStr | None:
            """Active branch name, None if detached HEAD."""
            ...

        @property
        def origin_remote(self) -> t.NonEmptyStr | None:
            """Origin remote URL."""
            ...

        @property
        def upstream_remote(self) -> t.NonEmptyStr | None:
            """Upstream remote URL."""
            ...

        @property
        def superproject_root(self) -> Path | None:
            """Superproject root if nested, None if standalone."""
            ...

        @property
        def requested_path(self) -> Path | None:
            """Filesystem path submitted to the identity probe, if any."""
            ...

        @property
        def is_worktree(self) -> bool:
            """Whether the checkout uses a linked (non-primary) Git dir."""
            ...

        @property
        def is_submodule(self) -> bool:
            """Whether the primary repository is a Git submodule."""
            ...

        @property
        def is_attached_submodule(self) -> bool:
            """Whether this checkout is physically nested in its superproject."""
            ...

        @property
        def has_submodules(self) -> bool:
            """Whether the repository declares any submodules."""
            ...

        @property
        def is_inside_work_tree(self) -> bool:
            """Whether the path is inside a Git work tree."""
            ...


__all__: list[str] = [
    "FlextInfraProtocolsGitIdentity",
]
