"""Direct codegen pipeline command service."""

from __future__ import annotations

from collections.abc import Callable, Mapping, MutableSequence, Sequence
from dataclasses import dataclass
from typing import override

from flext_core import FlextLogger, r
from flext_infra import (
    FlextInfraCodegenCensus,
    FlextInfraCodegenFixer,
    FlextInfraCodegenLazyInit,
    FlextInfraCodegenPyTyped,
    FlextInfraCodegenScaffolder,
    m,
    s,
    t,
    u,
)


@dataclass
class _CodegenState:
    """Typed inter-stage state for the codegen pipeline."""

    census_service: FlextInfraCodegenCensus | None = None
    reports_before: Sequence[m.Infra.CensusReport] = ()
    reports_after: Sequence[m.Infra.CensusReport] = ()
    scaffold_results: Sequence[m.Infra.ScaffoldResult] = ()
    fix_results: Sequence[m.Infra.AutoFixResult] = ()


_log = FlextLogger.create_module_logger(__name__)

# Stage IDs as constants to avoid string duplication.
_STAGE_PY_TYPED = "py_typed"
_STAGE_CENSUS_BEFORE = "census_before"
_STAGE_SCAFFOLD = "scaffold"
_STAGE_AUTO_FIX = "auto_fix"
_STAGE_LAZY_INIT = "lazy_init"
_STAGE_CENSUS_AFTER = "census_after"

# Canonical execution order.
_STAGE_ORDER: Sequence[str] = [
    _STAGE_PY_TYPED,
    _STAGE_CENSUS_BEFORE,
    _STAGE_SCAFFOLD,
    _STAGE_AUTO_FIX,
    _STAGE_LAZY_INIT,
    _STAGE_CENSUS_AFTER,
]


class FlextInfraCodegenPipeline(s[str]):
    """Run the full codegen pipeline directly from the validated CLI model."""

    _state: _CodegenState

    @override
    def execute(self) -> r[str]:
        """Execute the end-to-end codegen pipeline via DAG engine."""
        self._state = _CodegenState()
        ctx = m.Cli.PipelineStageContext(
            workspace_root=self.workspace_root,
            shared={},
            config={
                "dry_run": self.dry_run or not self.apply_changes,
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
            _STAGE_PY_TYPED: self._stage_py_typed,
            _STAGE_CENSUS_BEFORE: self._stage_census_before,
            _STAGE_SCAFFOLD: self._stage_scaffold,
            _STAGE_AUTO_FIX: self._stage_auto_fix,
            _STAGE_LAZY_INIT: self._stage_lazy_init,
            _STAGE_CENSUS_AFTER: self._stage_census_after,
        }
        stage_list: MutableSequence[m.Cli.PipelineStageSpec] = []
        prev: str | None = None
        for stage_id in _STAGE_ORDER:
            handler = handlers[stage_id]
            deps = frozenset({prev}) if prev is not None else frozenset()
            stage_list.append(
                m.Cli.PipelineStageSpec(
                    stage_id=stage_id,
                    depends_on=deps,
                    handler=handler,
                ),
            )
            prev = stage_id
        return stage_list

    # ------------------------------------------------------------------
    # Stage handlers
    # ------------------------------------------------------------------

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
                stage_id=_STAGE_PY_TYPED,
                status="ok",
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
            reports = census.run()
        except Exception as exc:
            return r[m.Cli.PipelineStageResult].fail(f"census_before failed: {exc}")
        self._state.census_service = census
        self._state.reports_before = reports
        total = sum(report.total for report in reports)
        fixable = sum(report.fixable for report in reports)
        return r[m.Cli.PipelineStageResult].ok(
            m.Cli.PipelineStageResult(
                stage_id=_STAGE_CENSUS_BEFORE,
                status="ok",
                output={"total_violations": total, "total_fixable": fixable},
            ),
        )

    def _stage_scaffold(
        self,
        ctx: m.Cli.PipelineStageContext,
    ) -> r[m.Cli.PipelineStageResult]:
        """Run scaffold stage and cache results."""
        try:
            dry_run = bool(ctx.config.get("dry_run", False))
            results = FlextInfraCodegenScaffolder.model_validate({
                "workspace_root": ctx.workspace_root,
            }).run(dry_run=dry_run)
        except Exception as exc:
            return r[m.Cli.PipelineStageResult].fail(f"scaffold failed: {exc}")
        self._state.scaffold_results = results
        created = sum(len(result.files_created) for result in results)
        skipped = sum(len(result.files_skipped) for result in results)
        return r[m.Cli.PipelineStageResult].ok(
            m.Cli.PipelineStageResult(
                stage_id=_STAGE_SCAFFOLD,
                status="ok",
                output={"total_created": created, "total_skipped": skipped},
            ),
        )

    def _stage_auto_fix(
        self,
        ctx: m.Cli.PipelineStageContext,
    ) -> r[m.Cli.PipelineStageResult]:
        """Run auto-fix stage and cache results."""
        try:
            dry_run = bool(ctx.config.get("dry_run", False))
            results = FlextInfraCodegenFixer.model_validate({
                "workspace_root": ctx.workspace_root,
                "dry_run": dry_run,
            }).fix_workspace()
        except Exception as exc:
            return r[m.Cli.PipelineStageResult].fail(f"auto_fix failed: {exc}")
        self._state.fix_results = results
        fixed = sum(len(result.violations_fixed) for result in results)
        skipped = sum(len(result.violations_skipped) for result in results)
        return r[m.Cli.PipelineStageResult].ok(
            m.Cli.PipelineStageResult(
                stage_id=_STAGE_AUTO_FIX,
                status="ok",
                output={"total_fixed": fixed, "total_skipped": skipped},
            ),
        )

    def _stage_lazy_init(
        self,
        ctx: m.Cli.PipelineStageContext,
    ) -> r[m.Cli.PipelineStageResult]:
        """Run lazy-init __init__.py generation."""
        try:
            dry_run = bool(ctx.config.get("dry_run", False))
            count = FlextInfraCodegenLazyInit.model_validate({
                "workspace_root": ctx.workspace_root,
            }).generate_inits(check_only=dry_run)
        except Exception as exc:
            return r[m.Cli.PipelineStageResult].fail(f"lazy_init failed: {exc}")
        return r[m.Cli.PipelineStageResult].ok(
            m.Cli.PipelineStageResult(
                stage_id=_STAGE_LAZY_INIT,
                status="ok",
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
            reports = census.run()
        except Exception as exc:
            return r[m.Cli.PipelineStageResult].fail(f"census_after failed: {exc}")
        self._state.reports_after = reports
        total = sum(report.total for report in reports)
        fixable = sum(report.fixable for report in reports)
        return r[m.Cli.PipelineStageResult].ok(
            m.Cli.PipelineStageResult(
                stage_id=_STAGE_CENSUS_AFTER,
                status="ok",
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
