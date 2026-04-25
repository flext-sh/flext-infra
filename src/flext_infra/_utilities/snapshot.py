"""Per-file in-memory snapshot helper (Task 0.5).

``snapshot_files(paths)`` captures byte content + mtime for each path so
``restore_files(snapshots)`` can put the workspace back exactly as it was
without invoking ``git``. Missing-file inputs surface as ``r.fail`` so
the orchestrator never silently drops an entry.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import os
from collections.abc import Sequence
from pathlib import Path

from flext_core import FlextResult as r

from flext_infra._models.guard import FlextInfraModelsGuard


class FlextInfraUtilitiesSnapshot:
    """Frozen snapshot + restore helpers (no git, no .bak files)."""

    @classmethod
    def snapshot_files(
        cls, paths: Sequence[Path]
    ) -> r[Sequence[FlextInfraModelsGuard.FileSnapshot]]:
        """Capture (bytes, mtime) for each existing path.

        Missing or unreadable paths abort the snapshot with ``r.fail`` —
        the consumer must surface the gap, never silently drop coverage.
        """
        captured: list[FlextInfraModelsGuard.FileSnapshot] = []
        missing: list[str] = []
        for path in paths:
            if not path.exists():
                missing.append(str(path))
                continue
            try:
                data = path.read_bytes()
                stat = path.stat()
            except OSError as exc:
                return r[Sequence[FlextInfraModelsGuard.FileSnapshot]].fail(
                    f"snapshot read failed for {path}: {exc}",
                    exception=exc,
                )
            captured.append(
                FlextInfraModelsGuard.FileSnapshot(
                    path=path,
                    original_bytes=data,
                    original_mtime=stat.st_mtime,
                ),
            )
        if missing:
            joined = ", ".join(sorted(missing))
            return r[Sequence[FlextInfraModelsGuard.FileSnapshot]].fail(
                f"snapshot rejected missing files: {joined}",
            )
        return r[Sequence[FlextInfraModelsGuard.FileSnapshot]].ok(tuple(captured))

    @classmethod
    def restore_snapshots(
        cls, snapshots: Sequence[FlextInfraModelsGuard.FileSnapshot]
    ) -> r[Sequence[Path]]:
        """Restore each snapshot's bytes + mtime, return the touched paths.

        Distinct name (vs ``FlextInfraUtilitiesSafety.restore_files``) so the
        two restore surfaces stay unambiguous on the ``u.Infra`` facade —
        ``restore_files`` rolls back ``.bak`` paths, ``restore_snapshots``
        rolls back in-memory snapshot objects.
        """
        restored: list[Path] = []
        for snapshot in snapshots:
            try:
                snapshot.path.write_bytes(snapshot.original_bytes)
                os.utime(
                    snapshot.path,
                    (snapshot.original_mtime, snapshot.original_mtime),
                )
            except OSError as exc:
                return r[Sequence[Path]].fail(
                    f"restore failed for {snapshot.path}: {exc}",
                    exception=exc,
                )
            restored.append(snapshot.path)
        return r[Sequence[Path]].ok(tuple(restored))
