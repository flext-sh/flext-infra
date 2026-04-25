"""In-memory file snapshot helper for handler rollback (Lane A-CH Task 0.5).

Captures (bytes, mtime) per file before a refactor mutation. ``restore_files``
returns each captured file to its snapshot state. Used by
``u.Infra.guard_gates_run`` to roll back per-file failures **without** any
git invocation (per AGENTS.md §3.5 "Git is IMMUTABLE").

Per AGENT_COORDINATION.md §2.2, A-CH owns this surface.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import os
from collections.abc import Sequence
from pathlib import Path

from flext_core.result import FlextResult

from flext_infra._models.guard import FlextInfraModelsGuard


class FlextInfraUtilitiesSnapshot:
    """Capture and restore in-memory file snapshots."""

    @staticmethod
    def snapshot_files(
        paths: Sequence[Path],
    ) -> FlextResult[tuple[FlextInfraModelsGuard.FileSnapshot, ...]]:
        """Snapshot each path's bytes + mtime.

        Returns ``r.fail(...)`` if any path is missing or unreadable. Either
        all snapshots succeed or none — partial captures are not returned.
        """
        snapshots: list[FlextInfraModelsGuard.FileSnapshot] = []
        for raw in paths:
            path = raw.resolve()
            if not path.exists():
                return FlextResult[
                    tuple[FlextInfraModelsGuard.FileSnapshot, ...]
                ].fail(f"snapshot target missing: {path}")
            try:
                data = path.read_bytes()
                mtime = path.stat().st_mtime
            except OSError as exc:
                return FlextResult[
                    tuple[FlextInfraModelsGuard.FileSnapshot, ...]
                ].fail(f"snapshot read failed for {path}: {exc}")
            snapshots.append(
                FlextInfraModelsGuard.FileSnapshot(
                    path=path,
                    original_bytes=data,
                    original_mtime=mtime,
                )
            )
        return FlextResult[
            tuple[FlextInfraModelsGuard.FileSnapshot, ...]
        ].ok(tuple(snapshots))

    @staticmethod
    def restore_snapshots(
        snapshots: Sequence[FlextInfraModelsGuard.FileSnapshot],
    ) -> FlextResult[tuple[Path, ...]]:
        """Restore each in-memory snapshot to disk byte-for-byte and reset mtime.

        Distinct from ``u.Infra.restore_files(bak_paths)`` (in
        ``FlextInfraUtilitiesSafety``) which restores from on-disk ``.bak``
        files. This method works against the typed ``FileSnapshot`` model
        captured by ``snapshot_files``.
        """
        restored: list[Path] = []
        for snap in snapshots:
            try:
                snap.path.write_bytes(snap.original_bytes)
                os.utime(snap.path, (snap.original_mtime, snap.original_mtime))
            except OSError as exc:
                return FlextResult[tuple[Path, ...]].fail(
                    f"restore failed for {snap.path}: {exc}",
                )
            restored.append(snap.path)
        return FlextResult[tuple[Path, ...]].ok(tuple(restored))


__all__: list[str] = ["FlextInfraUtilitiesSnapshot"]
