"""Phase: Ensure pyright/mypy extra paths are synchronized."""

from __future__ import annotations

from pathlib import Path

from flext_infra import FlextInfraExtraPathsManager, t


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
    ) -> t.StrSequence:
        _ = dry_run
        manager = FlextInfraExtraPathsManager()
        return manager.sync_doc(
            doc,
            project_dir=path.parent,
            is_root=is_root,
        )


__all__ = ["FlextInfraEnsureExtraPathsPhase"]
