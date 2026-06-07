"""Codegen pipeline stage handlers — extracted concern of FlextInfraCodegenPipeline."""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING

from flext_infra import (
    FlextInfraCodegenCensus,
    FlextInfraCodegenFixer,
    FlextInfraCodegenLazyInit,
    FlextInfraCodegenPyTyped,
    FlextInfraCodegenScaffolder,
    c,
    m,
    p,
    t,
    u,
)


class FlextInfraCodegenPipelineStagesMixin:
    """Seven linear codegen stage handlers, each a single fail-fast boundary.

    Composed into FlextInfraCodegenPipeline via MRO; every handler runs through
    the facade's ``_run_stage`` harness and caches its output in ``self._state``.
    """

    if TYPE_CHECKING:
        # Provided by the composed facade (FlextInfraCodegenPipeline); declared
        # here so the handlers type-resolve against the facade state + harness.
        _state: m.Infra.CodegenPipelineState

        def _run_stage[V](
            self,
            stage_id: str,
            action: Callable[[], V],
            emit: Callable[[V], t.JsonMapping],
        ) -> p.Result[m.Cli.PipelineStageResult]: ...

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


__all__: list[str] = ["FlextInfraCodegenPipelineStagesMixin"]
