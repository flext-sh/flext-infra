"""Behavior contract for FlextInfraWorkspacePropagator.propagate.

Sequences make-verb invocations under a typed report envelope:
  * one ``run_make_verb_callback`` call per verb
  * after each verb, ``guard_gates_run`` is invoked over the snapshots the
    verb accumulated (delivered by ``snapshot_provider``)
  * verb whose guard report flagged a restored path is marked
    ``success=False`` but the propagation continues to the next verb
  * the envelope reports UTC start/end + per-verb status + per-verb guard
    report so consumers never have to re-derive that state
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from pathlib import Path

from flext_infra._models.guard import FlextInfraModelsGuard
from flext_infra._models.workspace import FlextInfraModelsWorkspace
from flext_infra.workspace.propagate import FlextInfraWorkspacePropagator


class TestsFlextInfraWorkspacePropagator:
    """Behavior contract for the workspace propagator."""

    @staticmethod
    def _scaffold(tmp_path: Path, name: str, content: str = "x = 1\n") -> Path:
        target = tmp_path / name
        target.write_text(content, encoding="utf-8")
        return target

    @staticmethod
    def _make_propagator(tmp_path: Path) -> FlextInfraWorkspacePropagator:
        return FlextInfraWorkspacePropagator(workspace_root=tmp_path)

    def test_runs_each_verb_in_sequence(self, tmp_path: Path) -> None:
        invoked: list[str] = []

        def _run(verb: str, *, workspace_root: Path) -> bool:
            del workspace_root
            invoked.append(verb)
            return True

        result = self._make_propagator(tmp_path).propagate(
            verbs=("docs", "refactor", "check"),
            run_make_verb_callback=_run,
            snapshot_provider=lambda _verb: (),
        )
        assert result.success, result.error
        assert invoked == ["docs", "refactor", "check"]
        assert tuple(s.verb for s in result.value.verb_statuses) == (
            "docs",
            "refactor",
            "check",
        )

    def test_marks_verb_failed_when_guard_restores_paths(self, tmp_path: Path) -> None:
        target = self._scaffold(tmp_path, "alpha.py")

        def _snapshots(_verb: str) -> Sequence[FlextInfraModelsGuard.FileSnapshot]:
            return (
                FlextInfraModelsGuard.FileSnapshot(
                    path=target.resolve(),
                    original_bytes=target.read_bytes(),
                    original_mtime=target.stat().st_mtime,
                ),
            )

        def _fake_lint(
            path: Path, *, workspace: Path, gates: tuple[str, ...]
        ) -> Mapping[str, Sequence[str]]:
            del workspace, gates
            return {"ruff": ("E001 boom",)} if path == target.resolve() else {}

        result = self._make_propagator(tmp_path).propagate(
            verbs=("docs",),
            run_make_verb_callback=lambda verb, *, workspace_root: True,
            snapshot_provider=_snapshots,
            lint_callback=_fake_lint,
            guard_gates=("ruff",),
        )
        assert result.success, result.error
        report = result.value
        assert len(report.verb_statuses) == 1
        status = report.verb_statuses[0]
        assert status.verb == "docs"
        assert status.success is False
        assert tuple(status.guard_report.restored_paths) == (target.resolve(),)

    def test_run_callback_failure_marks_verb_and_continues(
        self, tmp_path: Path
    ) -> None:
        def _run(verb: str, *, workspace_root: Path) -> bool:
            del workspace_root
            return verb != "refactor"

        result = self._make_propagator(tmp_path).propagate(
            verbs=("docs", "refactor", "check"),
            run_make_verb_callback=_run,
            snapshot_provider=lambda _verb: (),
        )
        assert result.success, result.error
        statuses = {s.verb: s.success for s in result.value.verb_statuses}
        assert statuses == {"docs": True, "refactor": False, "check": True}

    def test_report_records_utc_start_end_window(self, tmp_path: Path) -> None:
        result = self._make_propagator(tmp_path).propagate(
            verbs=("docs",),
            run_make_verb_callback=lambda verb, *, workspace_root: True,
            snapshot_provider=lambda _verb: (),
        )
        report = result.value
        assert report.started_at <= report.ended_at
        assert report.started_at.tzinfo is not None

    def test_empty_verb_sequence_is_a_clean_noop(self, tmp_path: Path) -> None:
        result = self._make_propagator(tmp_path).propagate(
            verbs=(),
            run_make_verb_callback=lambda verb, *, workspace_root: True,
            snapshot_provider=lambda _verb: (),
        )
        assert result.success, result.error
        assert tuple(result.value.verb_statuses) == ()

    def test_propagator_is_idempotent_under_same_inputs(self, tmp_path: Path) -> None:
        prop = self._make_propagator(tmp_path)
        kwargs = {
            "verbs": ("docs", "check"),
            "run_make_verb_callback": lambda verb, *, workspace_root: True,
            "snapshot_provider": lambda _verb: (),
        }
        first = prop.propagate(**kwargs)  # type: ignore[arg-type]
        second = prop.propagate(**kwargs)  # type: ignore[arg-type]
        assert tuple(s.verb for s in first.value.verb_statuses) == tuple(
            s.verb for s in second.value.verb_statuses
        )
        assert tuple(s.success for s in first.value.verb_statuses) == tuple(
            s.success for s in second.value.verb_statuses
        )

    def test_verb_status_carries_guard_report_even_on_pass(
        self, tmp_path: Path
    ) -> None:
        result = self._make_propagator(tmp_path).propagate(
            verbs=("docs",),
            run_make_verb_callback=lambda verb, *, workspace_root: True,
            snapshot_provider=lambda _verb: (),
        )
        status = result.value.verb_statuses[0]
        assert isinstance(status.guard_report, FlextInfraModelsGuard.GuardGateReport)
        assert tuple(status.guard_report.restored_paths) == ()
        assert tuple(status.guard_report.gate_failures) == ()

    def test_verb_status_model_is_part_of_workspace_namespace(self) -> None:
        # PropagateReport / VerbStatus live under m.Infra.Workspace... but
        # the model module exposes them directly so static consumers don't
        # need to traverse the lazy facade — important for IDE / pyrefly.
        assert hasattr(FlextInfraModelsWorkspace, "PropagateReport")
        assert hasattr(FlextInfraModelsWorkspace, "VerbStatus")
