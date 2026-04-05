"""Phase: Ensure pyright/mypy extra paths are synchronized."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from flext_infra import t

if TYPE_CHECKING:
    from flext_infra import FlextInfraExtraPathsManager


class FlextInfraEnsureExtraPathsPhase:
    """Ensure pyright/mypy extra paths are synchronized.

    Modifies the in-memory doc directly (like all other phases) so the
    modernizer writes a single consistent file at the end.
    """

    def apply(
        self,
        doc: t.Cli.TomlDocument,
        *,
        path: Path,
        is_root: bool,
        dry_run: bool = False,
        paths_manager: FlextInfraExtraPathsManager | None = None,
    ) -> t.StrSequence:
        _ = dry_run
        if paths_manager is None:
            return []
        return paths_manager.sync_doc(
            doc,
            project_dir=path.parent,
            is_root=is_root,
        )


__all__ = ["FlextInfraEnsureExtraPathsPhase"]
