"""Direct codegen pipeline command service."""

from __future__ import annotations

from collections.abc import (
    Callable,
)
from typing import override

from flext_infra import (
    FlextInfraCodegenCensus,
    FlextInfraCodegenFixer,
    FlextInfraCodegenLazyInit,
    FlextInfraCodegenPyTyped,
    FlextInfraCodegenScaffolder,
    c,
    m,
    p,
    r,
    s,
    t,
    u,
)

_log = u.fetch_logger(__name__)


class FlextInfraCodegenPipeline(s[str]):
    """Run the full codegen pipeline directly from the validated CLI model."""

    _state: m.Infra.CodegenPipelineState = u.PrivateAttr(
        default_factory=lambda: m.Infra.CodegenPipelineState(),
    )

    @override
    def execute(self) -> p.Result[str]:
        """Execute the end-to-end codegen pipeline via DAG engine."""
        self._state = m.Infra.CodegenPipelineState()
        ctx = m.Cli.PipelineStageContext(
            workspace_root=self.workspace_root,
            shared={},
            settings={
                c.Infra.PIPELINE_KEY_DRY_RUN: self.dry_run or not self.apply_changes,
            },
        )

        stages = self._build_codegen_stages()

        pipeline_result = u.Cli.execute_pipeline(
            stages,
            ctx,
            fail_fast=True,
            logger=_log,
        )
        if pipeline_result.failure:
            return r[str].fail(pipeline_result.error or "pipeline execution failed")

        result = pipeline_result.value
        if not result.success:
            failed = result.failed_stages
            error_msg = failed[0].error if failed else "pipeline failed"
            return r[str].fail(error_msg or "pipeline failed")

        return self._collect_pipeline_output()

    # ------------------------------------------------------------------
    # Stage builder
    # ------------------------------------------------------------------

    def _build_codegen_stages(self) -> t.SequenceOf[m.Cli.PipelineStageSpec]:
        """Build DAG stage specs with linear dependency chain."""
        handlers: t.MappingKV[
            str,
            Callable[[m.Cli.PipelineStageContext], p.Result[m.Cli.PipelineStageResult]],
        ] = {
            c.Infra.PipelineStage.DISCOVER: self._stage_discover,
            c.Infra.PipelineStage.PY_TYPED: self._stage_py_typed,
            c.Infra.PipelineStage.CENSUS_BEFORE: self._stage_census_before,
            c.Infra.PipelineStage.SCAFFOLD: self._stage_scaffold,
            c.Infra.PipelineStage.AUTO_FIX: self._stage_auto_fix,
            c.Infra.PipelineStage.LAZY_INIT: self._stage_lazy_init,
            c.Infra.PipelineStage.CENSUS_AFTER: self._stage_census_after,
        }
        stage_list: t.MutableSequenceOf[m.Cli.PipelineStageSpec] = []
        prev: str | None = None
        for stage_id in c.Infra.PIPELINE_STAGE_ORDER:
            handler = handlers[stage_id]
            deps: frozenset[str] = (
                frozenset((prev,)) if prev is not None else frozenset()
            )
            retry = 1 if stage_id == c.Infra.PipelineStage.AUTO_FIX else 0
            stage_list.append(
                m.Cli.PipelineStageSpec(
                    stage_id=stage_id,
                    depends_on=deps,
                    handler=handler,
                    retry=retry,
                ),
            )
            prev = stage_id
        return stage_list

    # ------------------------------------------------------------------
    # Stage harness — single fail-fast boundary, no per-stage duplication
    # ------------------------------------------------------------------

    def _run_stage[V](
        self,
        stage_id: str,
        action: Callable[[], V],
        emit: Callable[[V], t.JsonMapping],
    ) -> p.Result[m.Cli.PipelineStageResult]:
        """Run one pipeline stage with a single try-boundary.

        ``action`` performs the work and may mutate ``self._state``; ``emit``
        builds the output payload from the action's return value. Any
        exception is captured and returned as ``r.fail_op(stage_id, exc)``
        so the DAG engine can fail-fast — never silenced, never demoted.
        """
        return r[m.Cli.PipelineStageResult].create_from_callable(
            lambda: m.Cli.PipelineStageResult(
                stage_id=stage_id,
                status=c.Cli.PipelineStageStatus.OK,
                output=emit(action()),
            ),
            error_code=stage_id,
        )

    # ------------------------------------------------------------------
    # Stage handlers
    # ------------------------------------------------------------------

    def _stage_discover(
        self,
        ctx: m.Cli.PipelineStageContext,
    ) -> p.Result[m.Cli.PipelineStageResult]:
        """Discover workspace projects once for reuse across all stages.

        Failure to enumerate projects propagates as a stage failure — no
        silent empty-tuple fallback, since downstream stages depend on the
        actual workspace inventory.
        """

        def _action() -> tuple[m.Infra.ProjectInfo, ...]:
            projects_result = u.Infra.projects(ctx.workspace_root)
            if projects_result.failure:
                msg = projects_result.error or "project discovery failed"
                raise RuntimeError(msg)
            return tuple(projects_result.unwrap())

        def _emit(discovered: tuple[m.Infra.ProjectInfo, ...]) -> t.JsonMapping:
            self._state.discovered_projects = discovered
            return {"projects_discovered": len(discovered)}

        return self._run_stage(c.Infra.PipelineStage.DISCOVER, _action, _emit)

    def _stage_py_typed(
        self,
        ctx: m.Cli.PipelineStageContext,
    ) -> p.Result[m.Cli.PipelineStageResult]:
        """Run PEP 561 py.typed marker generation."""

        def _action() -> int:
            return FlextInfraCodegenPyTyped.model_validate({
                "workspace_root": ctx.workspace_root,
            }).run()

        return self._run_stage(
            c.Infra.PipelineStage.PY_TYPED,
            _action,
            lambda count: {"markers_updated": count},
        )

    def _stage_census_before(
        self,
        ctx: m.Cli.PipelineStageContext,
    ) -> p.Result[m.Cli.PipelineStageResult]:
        """Run census (before fixes) and cache reports in typed state."""

        def _action() -> tuple[
            FlextInfraCodegenCensus, t.SequenceOf[m.Infra.CensusReport]
        ]:
            census = FlextInfraCodegenCensus.model_validate({
                "workspace_root": ctx.workspace_root,
            })
            projects = self._state.discovered_projects or None
            return census, census.run(projects=projects)

        def _emit(
            payload: tuple[FlextInfraCodegenCensus, t.SequenceOf[m.Infra.CensusReport]],
        ) -> t.JsonMapping:
            census, reports = payload
            self._state.census_service = census
            self._state.reports_before = reports
            return {
                "total_violations": sum(report.total for report in reports),
                "total_fixable": sum(report.fixable for report in reports),
            }

        return self._run_stage(c.Infra.PipelineStage.CENSUS_BEFORE, _action, _emit)

    def _stage_scaffold(
        self,
        ctx: m.Cli.PipelineStageContext,
    ) -> p.Result[m.Cli.PipelineStageResult]:
        """Run scaffold stage and cache results."""

        def _action() -> t.SequenceOf[m.Infra.ScaffoldResult]:
            dry_run = bool(ctx.settings.get(c.Infra.PIPELINE_KEY_DRY_RUN, False))
            projects = self._state.discovered_projects or None
            return FlextInfraCodegenScaffolder.model_validate({
                "workspace_root": ctx.workspace_root,
            }).run(dry_run=dry_run, projects=projects)

        def _emit(results: t.SequenceOf[m.Infra.ScaffoldResult]) -> t.JsonMapping:
            self._state.scaffold_results = results
            return {
                "total_created": sum(len(rsl.files_created) for rsl in results),
                "total_skipped": sum(len(rsl.files_skipped) for rsl in results),
            }

        return self._run_stage(c.Infra.PipelineStage.SCAFFOLD, _action, _emit)

    def _stage_auto_fix(
        self,
        ctx: m.Cli.PipelineStageContext,
    ) -> p.Result[m.Cli.PipelineStageResult]:
        """Run auto-fix stage and cache results."""

        def _action() -> t.SequenceOf[m.Infra.AutoFixResult]:
            dry_run = bool(ctx.settings.get(c.Infra.PIPELINE_KEY_DRY_RUN, False))
            projects = self._state.discovered_projects or None
            return FlextInfraCodegenFixer.model_validate({
                "workspace_root": ctx.workspace_root,
                "dry_run": dry_run,
            }).fix_workspace(projects=projects)

        def _emit(results: t.SequenceOf[m.Infra.AutoFixResult]) -> t.JsonMapping:
            self._state.fix_results = results
            return {
                "total_fixed": sum(len(rsl.violations_fixed) for rsl in results),
                "total_skipped": sum(len(rsl.violations_skipped) for rsl in results),
            }

        return self._run_stage(c.Infra.PipelineStage.AUTO_FIX, _action, _emit)

    def _stage_lazy_init(
        self,
        ctx: m.Cli.PipelineStageContext,
    ) -> p.Result[m.Cli.PipelineStageResult]:
        """Run lazy-init __init__.py generation."""

        def _action() -> int:
            dry_run = bool(ctx.settings.get(c.Infra.PIPELINE_KEY_DRY_RUN, False))
            return FlextInfraCodegenLazyInit.model_validate({
                "workspace_root": ctx.workspace_root,
            }).generate_inits(check_only=dry_run)

        return self._run_stage(
            c.Infra.PipelineStage.LAZY_INIT,
            _action,
            lambda count: {"unmapped_count": count},
        )

    def _stage_census_after(
        self,
        ctx: m.Cli.PipelineStageContext,
    ) -> p.Result[m.Cli.PipelineStageResult]:
        """Run census (after fixes) and cache reports."""

        def _action() -> t.SequenceOf[m.Infra.CensusReport]:
            census = (
                self._state.census_service
                or FlextInfraCodegenCensus.model_validate({
                    "workspace_root": ctx.workspace_root,
                })
            )
            projects = self._state.discovered_projects or None
            return census.run(projects=projects)

        def _emit(reports: t.SequenceOf[m.Infra.CensusReport]) -> t.JsonMapping:
            self._state.reports_after = reports
            return {
                "total_violations": sum(report.total for report in reports),
                "total_fixable": sum(report.fixable for report in reports),
            }

        return self._run_stage(c.Infra.PipelineStage.CENSUS_AFTER, _action, _emit)

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
            ]),
        )


__all__: list[str] = ["FlextInfraCodegenPipeline"]
