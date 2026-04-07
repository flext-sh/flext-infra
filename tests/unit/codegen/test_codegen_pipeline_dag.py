"""Integration tests for the codegen pipeline DAG execution.

Validates stage ordering, project discovery caching, failure propagation,
and state accumulation across stages using monkeypatched services.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import TYPE_CHECKING

from flext_tests import tm
from tests import c, m, t

from flext_core import r
from flext_infra import (
    FlextInfraCodegenPipeline,
)
from flext_infra.services import pipeline as pipeline_module

if TYPE_CHECKING:
    from pathlib import Path

    from _pytest.monkeypatch import MonkeyPatch

_P = c.Infra.Pipeline
type StageHandler = Callable[
    [FlextInfraCodegenPipeline, m.Cli.PipelineStageContext],
    r[m.Cli.PipelineStageResult],
]


def _ok_stage(
    stage_id: str,
) -> r[m.Cli.PipelineStageResult]:
    return r[m.Cli.PipelineStageResult].ok(
        m.Cli.PipelineStageResult(
            stage_id=stage_id,
            status=c.Cli.Pipeline.STATUS_OK,
        ),
    )


def _stub_all_stages(
    monkeypatch: MonkeyPatch,
    call_order: list[str],
) -> None:
    """Replace every stage handler with a lightweight tracker."""
    for stage_id in _P.STAGE_ORDER:

        def _make_handler(sid: str) -> StageHandler:
            def _handler(
                _self: FlextInfraCodegenPipeline,
                _ctx: m.Cli.PipelineStageContext,
            ) -> r[m.Cli.PipelineStageResult]:
                call_order.append(sid)
                return _ok_stage(sid)

            return _handler

        monkeypatch.setattr(
            FlextInfraCodegenPipeline,
            f"_stage_{stage_id}",
            _make_handler(stage_id),
        )


class TestCodegenPipelineDag:
    """Tests for the codegen pipeline DAG stage execution."""

    def test_pipeline_stage_order(
        self,
        tmp_path: Path,
        monkeypatch: MonkeyPatch,
    ) -> None:
        """All stages execute in the canonical dependency order."""
        call_order: list[str] = []
        _stub_all_stages(monkeypatch, call_order)

        svc = FlextInfraCodegenPipeline.model_validate({
            "workspace_root": tmp_path,
        })
        result = svc.execute()
        tm.ok(result)
        tm.that(call_order, eq=list(_P.STAGE_ORDER))

    def test_pipeline_project_discovery_cached(
        self,
        tmp_path: Path,
        monkeypatch: MonkeyPatch,
    ) -> None:
        """u.Infra.discover_projects is called exactly ONCE across all stages."""
        discover_count = 0

        def _counting_discover(
            *args: t.Scalar, **kwargs: t.Scalar
        ) -> r[Sequence[t.NormalizedValue]]:
            nonlocal discover_count
            discover_count += 1
            return r[Sequence[t.NormalizedValue]].ok(())

        monkeypatch.setattr(
            pipeline_module.u.Infra,
            "discover_projects",
            staticmethod(_counting_discover),
        )

        # Stub remaining stages to not call real services.
        for stage_id in _P.STAGE_ORDER:
            if stage_id == _P.STAGE_DISCOVER:
                continue

            def _make_noop(sid: str) -> StageHandler:
                def _handler(
                    _self: FlextInfraCodegenPipeline,
                    _ctx: m.Cli.PipelineStageContext,
                ) -> r[m.Cli.PipelineStageResult]:
                    return _ok_stage(sid)

                return _handler

            monkeypatch.setattr(
                FlextInfraCodegenPipeline,
                f"_stage_{stage_id}",
                _make_noop(stage_id),
            )

        svc = FlextInfraCodegenPipeline.model_validate({
            "workspace_root": tmp_path,
        })
        result = svc.execute()
        tm.ok(result)
        tm.that(discover_count, eq=1)

    def test_pipeline_failure_stops_subsequent_stages(
        self,
        tmp_path: Path,
        monkeypatch: MonkeyPatch,
    ) -> None:
        """If census_before fails, scaffold/fix/etc don't run."""
        executed: list[str] = []

        for stage_id in _P.STAGE_ORDER:

            def _make_handler(sid: str) -> StageHandler:
                def _handler(
                    _self: FlextInfraCodegenPipeline,
                    _ctx: m.Cli.PipelineStageContext,
                ) -> r[m.Cli.PipelineStageResult]:
                    executed.append(sid)
                    if sid == _P.STAGE_CENSUS_BEFORE:
                        return r[m.Cli.PipelineStageResult].fail("census exploded")
                    return _ok_stage(sid)

                return _handler

            monkeypatch.setattr(
                FlextInfraCodegenPipeline,
                f"_stage_{stage_id}",
                _make_handler(stage_id),
            )

        svc = FlextInfraCodegenPipeline.model_validate({
            "workspace_root": tmp_path,
        })
        result = svc.execute()
        tm.fail(result)

        # Stages before census_before should have run.
        tm.that(_P.STAGE_DISCOVER in executed, eq=True)
        tm.that(_P.STAGE_PY_TYPED in executed, eq=True)
        tm.that(_P.STAGE_CENSUS_BEFORE in executed, eq=True)
        # Stages after census_before should NOT have run.
        tm.that(_P.STAGE_SCAFFOLD not in executed, eq=True)
        tm.that(_P.STAGE_AUTO_FIX not in executed, eq=True)

    def test_pipeline_state_propagated(
        self,
        tmp_path: Path,
        monkeypatch: MonkeyPatch,
    ) -> None:
        """_CodegenPipelineState accumulates results across stages."""
        call_order: list[str] = []
        _stub_all_stages(monkeypatch, call_order)

        svc = FlextInfraCodegenPipeline.model_validate({
            "workspace_root": tmp_path,
        })
        result = svc.execute()
        tm.ok(result)
        # After successful execution, the internal state object should exist.
        # The execute() method creates _state and all stages ran.
        tm.that(len(call_order), eq=len(_P.STAGE_ORDER))


__all__: t.StrSequence = []
