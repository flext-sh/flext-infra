"""Pipeline DSL service exposed through the flext-cli public facade."""

from __future__ import annotations

from pathlib import Path

from flext_cli import c, m, p, r, s, t
from flext_cli._utilities.pipeline import FlextCliUtilitiesPipeline


class FlextCliPipeline(s, FlextCliUtilitiesPipeline):
    """Expose the canonical pipeline DSL through the service layer."""

    @staticmethod
    def stage_context(
        workspace_root: Path,
        *,
        shared: t.MutableJsonMapping | None = None,
        settings: t.JsonMapping | None = None,
    ) -> m.Cli.PipelineStageContext:
        """Build one validated stage context from the public DSL."""
        return m.Cli.PipelineStageContext.model_validate({
            "workspace_root": workspace_root,
            "shared": {} if shared is None else shared,
            "settings": {} if settings is None else settings,
        })

    @staticmethod
    def stage(
        stage_id: str,
        *,
        handler: t.Cli.PipelineHandler,
        depends_on: t.SequenceOf[str] | frozenset[str] = (),
        skip_if: t.Cli.PipelineSkipPredicate | None = None,
        retry: int = c.Cli.PIPELINE_DEFAULT_RETRY,
    ) -> m.Cli.PipelineStageSpec:
        """Build one declarative stage spec from the public DSL."""
        return m.Cli.PipelineStageSpec.model_validate({
            "stage_id": stage_id,
            "depends_on": frozenset(depends_on),
            "handler": handler,
            "skip_if": skip_if,
            "retry": retry,
        })

    @staticmethod
    def stage_result(
        stage_id: str,
        *,
        status: t.Cli.PipelineStageStatus = c.Cli.PipelineStageStatus.OK,
        output: t.JsonMapping | None = None,
        duration_ms: float = 0.0,
        error: str | None = None,
    ) -> m.Cli.PipelineStageResult:
        """Build one typed stage result payload."""
        return m.Cli.PipelineStageResult.model_validate({
            "stage_id": stage_id,
            "status": status,
            "output": {} if output is None else output,
            "duration_ms": duration_ms,
            "error": error,
        })

    @classmethod
    def ok_stage(
        cls,
        stage_id: str,
        *,
        output: t.JsonMapping | None = None,
        duration_ms: float = 0.0,
    ) -> p.Result[m.Cli.PipelineStageResult]:
        """Return one successful stage result via the canonical ``r`` API."""
        return r[m.Cli.PipelineStageResult].ok(
            cls.stage_result(
                stage_id,
                status=c.Cli.PipelineStageStatus.OK,
                output=output,
                duration_ms=duration_ms,
            )
        )

    @classmethod
    def linear_pipeline(
        cls,
        stage_order: t.StrSequence,
        handlers: t.Cli.PipelineHandlerMap,
        *,
        retry_by_stage: t.Cli.PipelineRetryMap | None = None,
        skip_by_stage: t.Cli.PipelineSkipMap | None = None,
    ) -> t.SequenceOf[m.Cli.PipelineStageSpec]:
        """Build a linear dependency chain from ordered stage handlers."""
        retries: t.Cli.PipelineRetryMap = (
            retry_by_stage if retry_by_stage is not None else {}
        )
        skips = skip_by_stage or {}
        stage_list: t.MutableSequenceOf[m.Cli.PipelineStageSpec] = []
        previous_stage_id: str | None = None
        for stage_id in stage_order:
            # NOTE (multi-agent): Typed retry map keeps ``get`` strictly integer.
            retry = retries.get(stage_id, c.Cli.PIPELINE_DEFAULT_RETRY)
            stage_list.append(
                cls.stage(
                    stage_id,
                    handler=handlers[stage_id],
                    depends_on=()
                    if previous_stage_id is None
                    else (previous_stage_id,),
                    skip_if=skips.get(stage_id),
                    retry=retry,
                )
            )
            previous_stage_id = stage_id
        return tuple(stage_list)

    def pipeline(
        self,
        stages: t.SequenceOf[m.Cli.PipelineStageSpec],
        *,
        context: m.Cli.PipelineStageContext,
        fail_fast: bool = c.Cli.PIPELINE_DEFAULT_FAIL_FAST,
        logger: p.Logger | None = None,
    ) -> p.Result[m.Cli.PipelineResult]:
        """Execute a pipeline through the public CLI DSL surface."""
        return self.execute_pipeline(
            stages, context, fail_fast=fail_fast, logger=logger or self.logger
        )


__all__: t.MutableSequenceOf[str] = ["FlextCliPipeline"]
