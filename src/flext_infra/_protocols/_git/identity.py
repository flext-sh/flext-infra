# AUTO-GENERATED FILE — Regenerate with: make gen
"""Source-derived structural model contracts."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated, Protocol, runtime_checkable

from flext_infra import t


class FlextInfraProtocolsGitIdentity:
    """Own the structural model contracts declared by this module."""

    @runtime_checkable
    class GitIdentityReport(Protocol):
        """Structural data contract projected from the owning model."""

        repo_root: Path
        primary_root: Path
        head_oid: t.NonEmptyStr | None
        porcelain: Annotated[str, t.StringConstraints(strip_whitespace=False)]
        dirty: bool
        git_dir: Path
        common_dir: Path
        branch: t.NonEmptyStr | None = ...
        origin_remote: t.NonEmptyStr | None = ...
        upstream_remote: t.NonEmptyStr | None = ...
        superproject_root: Path | None = ...
        requested_path: Path | None = ...
        is_worktree: bool = ...
        is_submodule: bool = ...
        is_attached_submodule: bool = ...
        has_submodules: bool = ...
        is_inside_work_tree: bool = ...


__all__: list[str] = [
    "FlextInfraProtocolsGitIdentity",
]
