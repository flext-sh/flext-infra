"""Direct codegen pipeline command service."""

from __future__ import annotations

from collections.abc import Callable, Mapping, MutableSequence, Sequence
from typing import Annotated, ClassVar, override

from pydantic import ConfigDict, Field

from flext_core import FlextLogger, FlextModels, r
from flext_infra import (
    FlextInfraCodegenCensus,
    FlextInfraCodegenFixer,
    FlextInfraCodegenLazyInit,
    FlextInfraCodegenPyTyped,
    FlextInfraCodegenScaffolder,
    c,
    m,
    p,
    s,
    t,
    u,
)


class _CodegenPipelineState(FlextModels.ArbitraryTypesModel):
    """Typed inter-stage state for the codegen pipeline — Pydantic v2 model."""

    _flext_enforcement_exempt: ClassVar[bool] = True

    model_config: ClassVar[ConfigDict] = ConfigDict(
        extra="forbid",
        arbitrary_types_allowed=True,
    )

    discovered_projects: Annotated[
        Sequence[p.Infra.ProjectInfo],
        Field(
            default_factory=tuple, description="Projects discovered at pipeline start"
        ),
    ]
    census_service: Annotated[
        FlextInfraCodegenCensus | None,
        Field(
            default=None, description="Cached census service for reuse across stages"
        ),
    ]
    reports_before: Annotated[
        Sequence[m.Infra.CensusReport],
        Field(
            default_factory=tuple, description="Census reports collected before fixes"
        ),
    ]
    reports_after: Annotated[
        Sequence[m.Infra.CensusReport],
        Field(
            default_factory=tuple, description="Census reports collected after fixes"
        ),
    ]
    scaffold_results: Annotated[
        Sequence[m.Infra.ScaffoldResult],
        Field(default_factory=tuple, description="Scaffolding stage results"),
    ]
    fix_results: Annotated[
        Sequence[m.Infra.AutoFixResult],
        Field(default_factory=tuple, description="Auto-fix stage results"),
    ]


_log = FlextLogger.create_module_logger(__name__)


class FlextInfraCodegenPipeline(s[str]):
    """Run the full codegen pipeline directly from the validated CLI model."""

    _state: _CodegenPipelineState

    @override
    def execute(self) -> r[str]:
        """Execute the end-to-end codegen pipeline via DAG engine."""
        self._state = _CodegenPipelineState()
        ctx = m.Cli.PipelineStageContext(
            workspace_root=self.workspace_root,
            shared={},
            config={
                c.Infra.Pipeline.KEY_DRY_RUN: self.dry_run or not self.apply_changes,
            },
        )

        stages = self._build_codegen_stages()

        pipeline_result = u.Cli.execute_pipeline(
            stages,
            ctx,
            fail_fast=True,
            logger=_log,
        )
        if pipeline_result.is_failure:
            return r[str].fail(pipeline_result.error or "pipeline execution failed")

        result = pipeline_result.value
        if not result.ok:
            failed = result.failed_stages
            error_msg = failed[0].error if failed else "pipeline failed"
            return r[str].fail(error_msg or "pipeline failed")

        return self._collect_pipeline_output()

    # ------------------------------------------------------------------
    # Stage builder
    # ------------------------------------------------------------------

    def _build_codegen_stages(self) -> Sequence[m.Cli.PipelineStageSpec]:
        """Build DAG stage specs with linear dependency chain."""
        handlers: Mapping[
            str,
            Callable[[m.Cli.PipelineStageContext], r[m.Cli.PipelineStageResult]],
        ] = {
            c.Infra.Pipeline.STAGE_DISCOVER: self._stage_discover,
            c.Infra.Pipeline.STAGE_PY_TYPED: self._stage_py_typed,
            c.Infra.Pipeline.STAGE_CENSUS_BEFORE: self._stage_census_before,
            c.Infra.Pipeline.STAGE_SCAFFOLD: self._stage_scaffold,
            c.Infra.Pipeline.STAGE_AUTO_FIX: self._stage_auto_fix,
            c.Infra.Pipeline.STAGE_LAZY_INIT: self._stage_lazy_init,
            c.Infra.Pipeline.STAGE_CENSUS_AFTER: self._stage_census_after,
        }
        stage_list: MutableSequence[m.Cli.PipelineStageSpec] = []
        prev: str | None = None
        for stage_id in c.Infra.Pipeline.STAGE_ORDER:
            handler = handlers[stage_id]
            deps: frozenset[str] = (
                frozenset((prev,)) if prev is not None else frozenset()
            )
            retry = 1 if stage_id == c.Infra.Pipeline.STAGE_AUTO_FIX else 0
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
    # Stage handlers
    # ------------------------------------------------------------------

    def _stage_discover(
        self,
        ctx: m.Cli.PipelineStageContext,
    ) -> r[m.Cli.PipelineStageResult]:
        """Discover workspace projects once for reuse across all stages."""
        try:
            projects_result = u.Infra.discover_projects(ctx.workspace_root)
            if not projects_result.is_success:
                return r[m.Cli.PipelineStageResult].fail(
                    f"project discovery failed: {projects_result.error}",
                )
            discovered = projects_result.unwrap()
        except Exception as exc:
            return r[m.Cli.PipelineStageResult].fail(f"discover failed: {exc}")
        self._state.discovered_projects = discovered
        return r[m.Cli.PipelineStageResult].ok(
            m.Cli.PipelineStageResult(
                stage_id=c.Infra.Pipeline.STAGE_DISCOVER,
                status=c.Cli.Pipeline.STATUS_OK,
                output={"projects_discovered": len(discovered)},
            ),
        )

    def _stage_py_typed(
        self,
        ctx: m.Cli.PipelineStageContext,
    ) -> r[m.Cli.PipelineStageResult]:
        """Run PEP 561 py.typed marker generation."""
        try:
            count = FlextInfraCodegenPyTyped.model_validate({
                "workspace_root": ctx.workspace_root,
            }).run()
        except Exception as exc:
            return r[m.Cli.PipelineStageResult].fail(f"py_typed failed: {exc}")
        return r[m.Cli.PipelineStageResult].ok(
            m.Cli.PipelineStageResult(
                stage_id=c.Infra.Pipeline.STAGE_PY_TYPED,
                status=c.Cli.Pipeline.STATUS_OK,
                output={"markers_updated": count},
            ),
        )

    def _stage_census_before(
        self,
        ctx: m.Cli.PipelineStageContext,
    ) -> r[m.Cli.PipelineStageResult]:
        """Run census (before fixes) and cache reports in typed state."""
        try:
            census = FlextInfraCodegenCensus.model_validate({
                "workspace_root": ctx.workspace_root,
            })
            projects = self._state.discovered_projects or None
            reports = census.run(projects=projects)
        except Exception as exc:
            return r[m.Cli.PipelineStageResult].fail(f"census_before failed: {exc}")
        self._state.census_service = census
        self._state.reports_before = reports
        total = sum(report.total for report in reports)
        fixable = sum(report.fixable for report in reports)
        return r[m.Cli.PipelineStageResult].ok(
            m.Cli.PipelineStageResult(
                stage_id=c.Infra.Pipeline.STAGE_CENSUS_BEFORE,
                status=c.Cli.Pipeline.STATUS_OK,
                output={"total_violations": total, "total_fixable": fixable},
            ),
        )

    def _stage_scaffold(
        self,
        ctx: m.Cli.PipelineStageContext,
    ) -> r[m.Cli.PipelineStageResult]:
        """Run scaffold stage and cache results."""
        try:
            dry_run = bool(ctx.config.get(c.Infra.Pipeline.KEY_DRY_RUN, False))
            projects = self._state.discovered_projects or None
            results = FlextInfraCodegenScaffolder.model_validate({
                "workspace_root": ctx.workspace_root,
            }).run(dry_run=dry_run, projects=projects)
        except Exception as exc:
            return r[m.Cli.PipelineStageResult].fail(f"scaffold failed: {exc}")
        self._state.scaffold_results = results
        created = sum(len(result.files_created) for result in results)
        skipped = sum(len(result.files_skipped) for result in results)
        return r[m.Cli.PipelineStageResult].ok(
            m.Cli.PipelineStageResult(
                stage_id=c.Infra.Pipeline.STAGE_SCAFFOLD,
                status=c.Cli.Pipeline.STATUS_OK,
                output={"total_created": created, "total_skipped": skipped},
            ),
        )

    def _stage_auto_fix(
        self,
        ctx: m.Cli.PipelineStageContext,
    ) -> r[m.Cli.PipelineStageResult]:
        """Run auto-fix stage and cache results."""
        try:
            dry_run = bool(ctx.config.get(c.Infra.Pipeline.KEY_DRY_RUN, False))
            projects = self._state.discovered_projects or None
            results = FlextInfraCodegenFixer.model_validate({
                "workspace_root": ctx.workspace_root,
                "dry_run": dry_run,
            }).fix_workspace(projects=projects)
        except Exception as exc:
            return r[m.Cli.PipelineStageResult].fail(f"auto_fix failed: {exc}")
        self._state.fix_results = results
        fixed = sum(len(result.violations_fixed) for result in results)
        skipped = sum(len(result.violations_skipped) for result in results)
        return r[m.Cli.PipelineStageResult].ok(
            m.Cli.PipelineStageResult(
                stage_id=c.Infra.Pipeline.STAGE_AUTO_FIX,
                status=c.Cli.Pipeline.STATUS_OK,
                output={"total_fixed": fixed, "total_skipped": skipped},
            ),
        )

    def _stage_lazy_init(
        self,
        ctx: m.Cli.PipelineStageContext,
    ) -> r[m.Cli.PipelineStageResult]:
        """Run lazy-init __init__.py generation."""
        try:
            dry_run = bool(ctx.config.get(c.Infra.Pipeline.KEY_DRY_RUN, False))
            count = FlextInfraCodegenLazyInit.model_validate({
                "workspace_root": ctx.workspace_root,
            }).generate_inits(check_only=dry_run)
        except Exception as exc:
            return r[m.Cli.PipelineStageResult].fail(f"lazy_init failed: {exc}")
        return r[m.Cli.PipelineStageResult].ok(
            m.Cli.PipelineStageResult(
                stage_id=c.Infra.Pipeline.STAGE_LAZY_INIT,
                status=c.Cli.Pipeline.STATUS_OK,
                output={"unmapped_count": count},
            ),
        )

    def _stage_census_after(
        self,
        ctx: m.Cli.PipelineStageContext,
    ) -> r[m.Cli.PipelineStageResult]:
        """Run census (after fixes) and cache reports."""
        try:
            census = self._state.census_service
            if census is None:
                census = FlextInfraCodegenCensus.model_validate({
                    "workspace_root": ctx.workspace_root,
                })
            projects = self._state.discovered_projects or None
            reports = census.run(projects=projects)
        except Exception as exc:
            return r[m.Cli.PipelineStageResult].fail(f"census_after failed: {exc}")
        self._state.reports_after = reports
        total = sum(report.total for report in reports)
        fixable = sum(report.fixable for report in reports)
        return r[m.Cli.PipelineStageResult].ok(
            m.Cli.PipelineStageResult(
                stage_id=c.Infra.Pipeline.STAGE_CENSUS_AFTER,
                status=c.Cli.Pipeline.STATUS_OK,
                output={"total_violations": total, "total_fixable": fixable},
            ),
        )

    # ------------------------------------------------------------------
    # Output collection
    # ------------------------------------------------------------------

    def _collect_pipeline_output(self) -> r[str]:
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

        if self.output_format == "json":
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


__all__ = ["FlextInfraCodegenPipeline"]
