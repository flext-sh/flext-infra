"""DAG pipeline execution engine backed by graphlib.TopologicalSorter."""

from __future__ import annotations

import time
from graphlib import CycleError, TopologicalSorter
from typing import ClassVar

from flext_cli import c, m, p, r, t
from flext_core import u


class FlextCliUtilitiesPipeline:
    """Pipeline execution utilities — exposed as u.Cli.execute_pipeline()."""

    _pipeline_logger: ClassVar[p.Logger] = u.fetch_logger(__name__)

    @staticmethod
    def execute_pipeline(
        stages: t.SequenceOf[m.Cli.PipelineStageSpec],
        context: m.Cli.PipelineStageContext,
        *,
        fail_fast: bool = c.Cli.PIPELINE_DEFAULT_FAIL_FAST,
        logger: p.Logger | None = None,
    ) -> p.Result[m.Cli.PipelineResult]:
        """Execute pipeline stages in topological order.

        Uses graphlib.TopologicalSorter for dependency resolution.
        Stages share state via context.shared mutable mapping.
        """
        log = logger or FlextCliUtilitiesPipeline._pipeline_logger
        pipeline_start = time.monotonic()
        results: t.MutableSequenceOf[m.Cli.PipelineStageResult] = []

        if not stages:
            return r[m.Cli.PipelineResult].ok(
                m.Cli.PipelineResult(stages=[], total_duration_ms=0.0)
            )

        # Build stage lookup and dependency graph.
        stage_map: dict[str, m.Cli.PipelineStageSpec] = {s.stage_id: s for s in stages}

        # Build TopologicalSorter graph.
        sorter: TopologicalSorter[str] = TopologicalSorter()
        for spec in stages:
            sorter.add(spec.stage_id, *spec.depends_on)

        try:
            order = tuple(sorter.static_order())
        except CycleError as exc:
            return r[m.Cli.PipelineResult].fail(f"pipeline cycle detected: {exc}")

        failed = False
        for stage_id in order:
            if stage_id not in stage_map:
                continue
            spec = stage_map[stage_id]

            if failed and fail_fast:
                results.append(
                    m.Cli.PipelineStageResult(
                        stage_id=stage_id,
                        status=c.Cli.PipelineStageStatus.SKIPPED,
                        error="skipped due to prior failure (fail_fast)",
                    )
                )
                continue

            stage_result = FlextCliUtilitiesPipeline._run_stage(spec, context, log)
            results.append(stage_result)

            if stage_result.status == c.Cli.PipelineStageStatus.FAILED:
                failed = True

        total_ms = (time.monotonic() - pipeline_start) * 1000
        pipeline_result = m.Cli.PipelineResult(
            stages=results, total_duration_ms=total_ms
        )

        log.info(
            "pipeline_complete",
            total_stages=len(results),
            failed=len(pipeline_result.failed_stages),
            skipped=len(pipeline_result.skipped_stages),
            duration_ms=round(total_ms, 2),
        )

        if pipeline_result.failed_stages:
            return r[m.Cli.PipelineResult].fail(
                "one or more pipeline stages failed"
            )
        return r[m.Cli.PipelineResult].ok(pipeline_result)

    @staticmethod
    def _run_stage(
        spec: m.Cli.PipelineStageSpec,
        context: m.Cli.PipelineStageContext,
        log: p.Logger,
    ) -> m.Cli.PipelineStageResult:
        """Execute a single stage with skip check and retry logic."""
        if spec.skip_if is not None and spec.skip_if(context):
            log.debug("stage_skipped", stage_id=spec.stage_id, reason="skip_if")
            return m.Cli.PipelineStageResult(
                stage_id=spec.stage_id, status=c.Cli.PipelineStageStatus.SKIPPED
            )

        max_attempts = 1 + min(spec.retry, c.Cli.PIPELINE_MAX_RETRY)
        last_error: str | None = None

        for attempt in range(1, max_attempts + 1):
            stage_start = time.monotonic()
            try:
                result = spec.handler(context)
            except c.Cli.CLI_SAFE_EXCEPTIONS as exc:
                last_error = f"stage {spec.stage_id} raised: {exc}"
                log.warning(
                    "stage_exception",
                    stage_id=spec.stage_id,
                    attempt=attempt,
                    error=str(exc),
                )
                continue

            duration_ms = (time.monotonic() - stage_start) * 1000

            if result.success:
                stage_result = result.value
                return stage_result.model_copy(update={"duration_ms": duration_ms})

            last_error = result.error or f"stage {spec.stage_id} failed"
            log.debug(
                "stage_retry", stage_id=spec.stage_id, attempt=attempt, error=last_error
            )

        log.warning(
            "stage_failed",
            stage_id=spec.stage_id,
            attempts=max_attempts,
            error=last_error or "",
        )
        return m.Cli.PipelineStageResult(
            stage_id=spec.stage_id,
            status=c.Cli.PipelineStageStatus.FAILED,
            error=last_error,
        )


__all__ = ("FlextCliUtilitiesPipeline",)
