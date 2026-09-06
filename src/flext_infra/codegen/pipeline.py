"""Direct codegen pipeline command service."""

from __future__ import annotations

from typing import TYPE_CHECKING, override

from flext_cli import cli
from flext_infra import c, m, p, r, t, u
from flext_infra.base import FlextInfraServiceBase
from flext_infra.codegen._pipeline_stages import FlextInfraCodegenPipelineStagesMixin

if TYPE_CHECKING:
    from collections.abc import Callable

_log = u.fetch_logger(__name__)


class FlextInfraCodegenPipeline(
    FlextInfraCodegenPipelineStagesMixin, FlextInfraServiceBase[str]
):
    """Run the full codegen pipeline directly from the validated CLI model."""

    _state: m.Infra.CodegenPipelineState = u.PrivateAttr(
        default_factory=m.Infra.CodegenPipelineState
    )

    @override
    def execute(self) -> p.Result[str]:
        """Execute the end-to-end codegen pipeline via DAG runner."""
        self._state = m.Infra.CodegenPipelineState()
        stages = self._build_codegen_stages()

        pipeline_result = cli.pipeline(
            stages,
            context=cli.stage_context(
                self.repository_root,
                settings={
                    c.Infra.PIPELINE_KEY_DRY_RUN: self.dry_run or not self.apply_changes
                },
            ),
            logger=_log,
        )
        if pipeline_result.failure:
            return r[str].from_failure(pipeline_result)
        # cli.pipeline already maps failed_stages to r.fail; value is always success.
        return self._collect_pipeline_output()

    # ------------------------------------------------------------------
    # Stage builder
    # ------------------------------------------------------------------

    def _build_codegen_stages(self) -> t.SequenceOf[m.Cli.PipelineStageSpec]:
        """Build DAG stage specs with linear dependency chain."""
        handlers: dict[str, p.Cli.PipelineStage] = {
            c.Infra.PipelineStage.DISCOVER: lambda ctx, /: self._stage_discover(ctx),
            c.Infra.PipelineStage.TOOLCHAIN: lambda ctx, /: self._stage_toolchain(ctx),
            c.Infra.PipelineStage.PY_TYPED: lambda ctx, /: self._stage_py_typed(ctx),
            c.Infra.PipelineStage.CENSUS_BEFORE: lambda ctx, /: self._stage_census_before(ctx),
            c.Infra.PipelineStage.SCAFFOLD: lambda ctx, /: self._stage_scaffold(ctx),
            c.Infra.PipelineStage.AUTO_FIX: lambda ctx, /: self._stage_auto_fix(ctx),
            c.Infra.PipelineStage.DEPS: lambda ctx, /: self._stage_deps(ctx),
            c.Infra.PipelineStage.LAZY_INIT: lambda ctx, /: self._stage_lazy_init(ctx),
            c.Infra.PipelineStage.CENSUS_AFTER: lambda ctx, /: self._stage_census_after(ctx),
        }
        return cli.linear_pipeline(c.Infra.PIPELINE_STAGE_ORDER, handlers)

    # ------------------------------------------------------------------
    # Stage harness — single fail-fast boundary, no per-stage duplication
    # ------------------------------------------------------------------

    @override
    def _run_stage[V](
        self, stage_id: str, action: Callable[[], V], emit: Callable[[V], t.JsonMapping]
    ) -> p.Result[m.Cli.PipelineStageResult]:
        """Run one pipeline stage and preserve the first exception.

        ``action`` performs the work and may mutate ``self._state``; ``emit``
        builds the output payload from the action's return value.
        """
        return r[m.Cli.PipelineStageResult].ok(
            cli.stage_result(stage_id, output=emit(action()))
        )

    # ------------------------------------------------------------------
    # Output collection
    # ------------------------------------------------------------------

    def _collect_pipeline_output(self) -> p.Result[str]:
        """Convert typed pipeline state into the original output format."""
        reports_before = self._state.reports_before
        reports_after = self._state.reports_after
        scaffold_results = self._state.scaffold_results
        fix_results = self._state.fix_results

        before_violations = sum(report.total for report in reports_before)
        before_fixable = sum(report.fixable for report in reports_before)
        after_violations = sum(report.total for report in reports_after)
        after_fixable = sum(report.fixable for report in reports_after)
        scaffold_created = sum(len(result.files_created) for result in scaffold_results)
        scaffold_skipped = sum(len(result.files_skipped) for result in scaffold_results)
        fixed = sum(len(result.violations_fixed) for result in fix_results)
        skipped = sum(len(result.violations_skipped) for result in fix_results)

        if self.output_format == c.Cli.OutputFormats.JSON:
            payload: t.Infra.MutableInfraMapping = {
                "census_before": {
                    "total_violations": before_violations,
                    "total_fixable": before_fixable,
                },
                "scaffold": {
                    "total_created": scaffold_created,
                    "total_skipped": scaffold_skipped,
                },
                "auto_fix": {"total_fixed": fixed, "total_skipped": skipped},
                "census_after": {
                    "total_violations": after_violations,
                    "total_fixable": after_fixable,
                },
            }
            return r[str].ok(t.Infra.INFRA_MAPPING_ADAPTER.dump_json(payload).decode())
        return r[str].ok(
            "\n".join([
                f"Census before: {before_violations} violations",
                f"Scaffold: {scaffold_created} files created",
                f"Auto-fix: {fixed} violations fixed",
                f"Census after: {after_violations} violations",
                f"Improvement: {before_violations - after_violations} violations resolved",
            ])
        )


__all__: list[str] = ["FlextInfraCodegenPipeline"]
