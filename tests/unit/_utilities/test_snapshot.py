"""Behavior contract for FlextInfraUtilitiesSnapshot snapshot_files / restore_files.

Round-trip semantics: snapshot captures bytes + mtime exactly; mutating the
file then restoring brings the bytes back identical. Missing-file inputs
return ``r.fail(...)`` so callers can surface the broken contract instead
of silently dropping the entry.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from flext_infra._models.guard import FlextInfraModelsGuard
from tests import u


class TestsFlextInfraUtilitiesSnapshot:
    """Behavior contract for the file-snapshot utility."""

    @staticmethod
    def _write(path: Path, content: bytes) -> Path:
        path.write_bytes(content)
        return path

    def test_snapshot_captures_bytes_and_mtime(self, tmp_path: Path) -> None:
        target = self._write(tmp_path / "alpha.py", b"x = 1\n")
        original_mtime = target.stat().st_mtime
        result = u.Infra.snapshot_files((target,))
        assert result.success, result.error
        snapshots = result.value
        assert len(snapshots) == 1
        assert isinstance(snapshots[0], FlextInfraModelsGuard.FileSnapshot)
        assert snapshots[0].path == target
        assert snapshots[0].original_bytes == b"x = 1\n"
        assert snapshots[0].original_mtime == pytest.approx(original_mtime)

    def test_snapshot_then_restore_is_byte_identical(self, tmp_path: Path) -> None:
        target = self._write(tmp_path / "alpha.py", b"original\n")
        snapshots_result = u.Infra.snapshot_files((target,))
        target.write_bytes(b"mutated\n")
        restore_result = u.Infra.restore_snapshots(snapshots_result.value)
        assert restore_result.success, restore_result.error
        assert tuple(restore_result.value) == (target,)
        assert target.read_bytes() == b"original\n"

    def test_snapshot_rejects_missing_file(self, tmp_path: Path) -> None:
        absent = tmp_path / "ghost.py"
        result = u.Infra.snapshot_files((absent,))
        assert result.success is False
        assert result.error
        assert "ghost.py" in result.error

    def test_snapshot_preserves_multiple_files_in_order(self, tmp_path: Path) -> None:
        first = self._write(tmp_path / "a.py", b"A\n")
        second = self._write(tmp_path / "b.py", b"B\n")
        result = u.Infra.snapshot_files((first, second))
        assert result.success, result.error
        captured = tuple(snap.path for snap in result.value)
        assert captured == (first, second)

    def test_restore_with_empty_snapshots_is_a_noop(self) -> None:
        result = u.Infra.restore_snapshots(())
        assert result.success, result.error
        assert tuple(result.value) == ()
