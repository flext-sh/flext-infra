"""Tests for u.Infra.snapshot_files / restore_files (Lane A-CH Task 0.5).

Validates byte-for-byte and mtime preservation across snapshot/restore round
trips, and that missing-file snapshots return r.fail.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from tests import u


class TestsFlextInfraUtilitiesSnapshot:
    """Behavior contract for FileSnapshot capture and restore."""

    def test_snapshot_then_restore_round_trip_preserves_bytes(
        self, tmp_path: Path
    ) -> None:
        target = tmp_path / "x.py"
        original = b"VALUE = 1\n"
        target.write_bytes(original)
        snap_result = u.Infra.snapshot_files((target,))
        assert snap_result.success is True
        snapshots = snap_result.value

        target.write_bytes(b"VALUE = 999\n")
        assert target.read_bytes() != original

        restore_result = u.Infra.restore_snapshots(snapshots)
        assert restore_result.success is True
        assert target.read_bytes() == original

    def test_snapshot_then_restore_preserves_mtime(self, tmp_path: Path) -> None:
        target = tmp_path / "x.py"
        target.write_bytes(b"x = 1\n")
        # Force a known mtime
        os.utime(target, (1000.0, 1000.0))
        snap_result = u.Infra.snapshot_files((target,))
        assert snap_result.success is True

        # Touch the file (changes mtime)
        target.write_bytes(b"x = 2\n")
        os.utime(target, (5000.0, 5000.0))

        restore_result = u.Infra.restore_snapshots(snap_result.value)
        assert restore_result.success is True
        assert target.stat().st_mtime == pytest.approx(1000.0)

    def test_snapshot_missing_file_returns_fail(self, tmp_path: Path) -> None:
        result = u.Infra.snapshot_files((tmp_path / "missing.py",))
        assert result.success is False

    def test_snapshot_empty_set_returns_empty_tuple(self, tmp_path: Path) -> None:
        del tmp_path  # unused
        result = u.Infra.snapshot_files(())
        assert result.success is True
        assert result.value == ()
