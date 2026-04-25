"""Behavior contract for FlextInfraUtilitiesGuardGates.guard_gates_run.

Per-file ruff/pyrefly check + on-failure restore from in-memory snapshot.
Returns a ``GuardGateReport`` listing every restored path and per-gate
failure messages. Out-of-scope file (gate touches a path not in the
snapshot set) returns ``r.fail`` so the orchestrator can surface scope
leaks instead of silently rolling back unrelated edits.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from pathlib import Path

from flext_infra._models.guard import FlextInfraModelsGuard
from tests import u


class TestsFlextInfraUtilitiesGuardGates:
    """Behavior contract for the per-file guard-gate runner."""

    @staticmethod
    def _scaffold(tmp_path: Path, name: str, content: str) -> Path:
        target = tmp_path / name
        target.write_text(content, encoding="utf-8")
        return target

    def test_clean_files_pass_and_no_restores(self, tmp_path: Path) -> None:
        target = self._scaffold(tmp_path, "alpha.py", "x = 1\n")
        snap_result = u.Infra.snapshot_files((target,))
        report_result = u.Infra.guard_gates_run(
            workspace_root=tmp_path,
            snapshots=snap_result.value,
            gates=(),
        )
        assert report_result.success, report_result.error
        report = report_result.value
        assert isinstance(report, FlextInfraModelsGuard.GuardGateReport)
        assert tuple(report.restored_paths) == ()
        assert tuple(report.gate_failures) == ()

    def test_gate_failure_restores_from_snapshot(self, tmp_path: Path) -> None:
        target = self._scaffold(tmp_path, "alpha.py", "x = 1\n")
        snap_result = u.Infra.snapshot_files((target,))
        target.write_text("BROKEN??\n", encoding="utf-8")

        def _fake_lint(
            path: Path, *, workspace: Path, gates: tuple[str, ...]
        ) -> Mapping[str, Sequence[str]]:
            del workspace, gates
            if path == target.resolve():
                return {"ruff": (f"E001: {path.name} has bad content",)}
            return {}

        report_result = u.Infra.guard_gates_run(
            workspace_root=tmp_path,
            snapshots=snap_result.value,
            gates=("ruff",),
            lint_callback=_fake_lint,
        )
        assert report_result.success, report_result.error
        report = report_result.value
        assert tuple(report.restored_paths) == (target.resolve(),)
        assert any("E001" in failure for failure in report.gate_failures)
        assert target.read_text(encoding="utf-8") == "x = 1\n"

    def test_out_of_scope_failure_returns_fail(self, tmp_path: Path) -> None:
        in_scope = self._scaffold(tmp_path, "alpha.py", "x = 1\n")
        out_of_scope = self._scaffold(tmp_path, "beta.py", "y = 2\n")
        snap_result = u.Infra.snapshot_files((in_scope,))

        def _fake_lint(
            path: Path, *, workspace: Path, gates: tuple[str, ...]
        ) -> Mapping[str, Sequence[str]]:
            del workspace, gates
            if path == out_of_scope.resolve():
                return {"ruff": ("boom",)}
            return {}

        report_result = u.Infra.guard_gates_run(
            workspace_root=tmp_path,
            snapshots=snap_result.value,
            gates=("ruff",),
            lint_callback=_fake_lint,
            additional_paths=(out_of_scope,),
        )
        assert report_result.success is False
        assert report_result.error
        assert "out-of-scope" in report_result.error
