"""Tests for u.Infra.guard_gates_run (Lane A-CH Task 0.5).

Validates: clean files pass; ruff-violating files are restored from snapshot;
report lists reverted files; out-of-scope gate failures return r.fail.
NEVER invokes git.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

from tests import u


class TestsFlextInfraUtilitiesGuardGates:
    """Behavior contract for guard_gates_run snapshot rollback."""

    def test_clean_files_pass_all_gates(self, tmp_path: Path) -> None:
        (tmp_path / "__init__.py").write_text("", encoding="utf-8")
        target = tmp_path / "x.py"
        target.write_text('"""Module."""\n\nx = 1\n', encoding="utf-8")
        snap_result = u.Infra.snapshot_files((target,))
        assert snap_result.success is True

        result = u.Infra.guard_gates_run(
            workspace_root=tmp_path,
            snapshots=snap_result.value,
            gates=("ruff",),
        )
        assert result.success is True
        report = result.value
        assert len(report.outcomes) == 1
        assert report.outcomes[0].passed is True
        assert report.files_reverted == ()

    def test_ruff_violation_restores_file_from_snapshot(
        self, tmp_path: Path
    ) -> None:
        (tmp_path / "__init__.py").write_text("", encoding="utf-8")
        target = tmp_path / "x.py"
        target.write_text('"""Module."""\n\nx = 1\n', encoding="utf-8")
        snap_result = u.Infra.snapshot_files((target,))
        assert snap_result.success is True

        # Mutate to a ruff E501-style violation
        target.write_text("x =       1\n" + "z = 1  " * 30 + "\n", encoding="utf-8")

        result = u.Infra.guard_gates_run(
            workspace_root=tmp_path,
            snapshots=snap_result.value,
            gates=("ruff",),
        )
        assert result.success is True
        report = result.value
        assert any(not o.passed for o in report.outcomes)
        assert target.resolve() in report.files_reverted
        # Snapshot restored
        assert target.read_text(encoding="utf-8") == '"""Module."""\n\nx = 1\n'

    def test_revert_disabled_keeps_dirty_state(self, tmp_path: Path) -> None:
        (tmp_path / "__init__.py").write_text("", encoding="utf-8")
        target = tmp_path / "x.py"
        target.write_text('"""Module."""\n\nx = 1\n', encoding="utf-8")
        snap_result = u.Infra.snapshot_files((target,))
        target.write_text('"""Module."""\n\nx =1\n', encoding="utf-8")  # ruff E225

        result = u.Infra.guard_gates_run(
            workspace_root=tmp_path,
            snapshots=snap_result.value,
            gates=("ruff",),
            revert_on_failure=False,
        )
        assert result.success is True
        # File NOT restored
        assert target.read_text(encoding="utf-8") == '"""Module."""\n\nx =1\n'
        assert result.value.files_reverted == ()
