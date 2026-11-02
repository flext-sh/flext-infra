# AUTO-GENERATED FILE — Regenerate with: make gen
"""Source-derived structural model contracts.

Copyright (c) 2026 FLEXT Team. All rights reserved.
src/flext_infra/_protocols/_git/identity
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path
from typing import Protocol, runtime_checkable

from flext_infra import t


class FlextInfraProtocolsGitIdentity:
    """Own the structural contracts declared by its model source."""

    @runtime_checkable
    class GitIdentityReport(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def repo_root(self) -> Path: ...
        @property
        def primary_root(self) -> Path: ...
        @property
        def head_oid(self) -> t.NonEmptyStr | None: ...
        @property
        def porcelain(self) -> str: ...
        @property
        def dirty(self) -> bool: ...
        @property
        def git_dir(self) -> Path: ...
        @property
        def common_dir(self) -> Path: ...
        @property
        def branch(self) -> t.NonEmptyStr | None: ...
        @property
        def origin_remote(self) -> t.NonEmptyStr | None: ...
        @property
        def upstream_remote(self) -> t.NonEmptyStr | None: ...
        @property
        def superproject_root(self) -> Path | None: ...
        @property
        def requested_path(self) -> Path | None: ...
        @property
        def is_worktree(self) -> bool: ...
        @property
        def is_submodule(self) -> bool: ...
        @property
        def is_attached_submodule(self) -> bool: ...
        @property
        def has_submodules(self) -> bool: ...
        @property
        def is_inside_work_tree(self) -> bool: ...


__all__: list[str] = [
    "FlextInfraProtocolsGitIdentity",
]
