"""A killed producer cannot clean its candidate tree; the next run must.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import os
import time
from pathlib import Path

from flext_infra.codegen.staged_package import FlextInfraStagedPackage


def _preview(parent: Path, name: str, age_seconds: int) -> Path:
    path = parent / f"flext-source-preview-{name}"
    path.mkdir()
    (path / "marker.py").write_text("# candidate\n", encoding="utf-8")
    stamp = time.time() - age_seconds
    os.utime(path, (stamp, stamp))
    return path


def test_stale_candidate_trees_are_removed_and_a_live_one_is_kept(
    tmp_path: Path,
) -> None:
    """Only the tree older than the live window is removed."""
    stale = _preview(tmp_path, "stale", 7200)
    live = _preview(tmp_path, "live", 60)
    unrelated = tmp_path / "other"
    unrelated.mkdir()

    FlextInfraStagedPackage.sweep_stale_previews(tmp_path)

    assert not stale.exists()
    assert live.exists()
    assert unrelated.exists()
