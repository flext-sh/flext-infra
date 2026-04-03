"""Codegen CLI handlers mixin — simple command handlers."""

from __future__ import annotations

from pathlib import Path

from flext_core import r
from flext_infra import (
    FlextInfraCodegenCensus,
    FlextInfraCodegenConstantsQualityGate,
    FlextInfraCodegenFixer,
    FlextInfraCodegenLazyInit,
    FlextInfraCodegenPyTyped,
    FlextInfraCodegenScaffolder,
    c,
    m,
    u,
)

_resolve = u.Infra.resolve_workspace
_format = u.Infra.format_result

__all__ = ["FlextInfraCliCodegenHandlers"]


class FlextInfraCliCodegenHandlers:
    """Mixin providing simple codegen command handlers."""

    @staticmethod
    def _handle_lazy_init(params: m.Infra.CodegenLazyInitInput) -> r[bool]:
        """Handle lazy-init code generation."""
        generator = FlextInfraCodegenLazyInit(workspace_root=_resolve(params))
        errors = generator.run(check_only=params.check)
        if errors > 0:
            return r[bool].fail(
                f"lazy-init failed in {errors} package directories",
            )
        return r[bool].ok(True)

    @staticmethod
    def _handle_codegen_census(params: m.Infra.CodegenCensusInput) -> r[str]:
        """Handle namespace violation census."""
        census = FlextInfraCodegenCensus(
            workspace_root=_resolve(params),
            class_to_analyze=params.class_to_analyze,
        )
        reports = census.run()
        total_v = sum(rpt.total for rpt in reports)
        total_f = sum(rpt.fixable for rpt in reports)

        def _text() -> str:
            lines: list[str] = [
                f"  {rpt.project}: {rpt.total} violations ({rpt.fixable} fixable)"
                for rpt in reports
                if rpt.total > 0
            ]
            lines.append(
                f"Total: {total_v} violations ({total_f} fixable)"
                f" across {len(reports)} projects",
            )
            return "\n".join(lines)

        return _format(
            {
                c.Infra.ReportKeys.PROJECTS: [rpt.model_dump() for rpt in reports],
                "total_violations": total_v,
                "total_fixable": total_f,
            },
            output_format=params.output_format,
            text_fn=_text,
        )

    @staticmethod
    def _handle_deduplicate(params: m.Infra.CodegenDeduplicateInput) -> r[str]:
        """Handle constant deduplication with user selection."""
        return u.Infra.deduplicate_constants(
            class_path=params.class_to_analyze,
            root_path=_resolve(params),
            dry_run=not params.apply,
        ).map(lambda report: report.render_text())

    @staticmethod
    def _handle_scaffold(params: m.Infra.CodegenScaffoldInput) -> r[str]:
        """Handle module scaffolding."""
        scaffolder = FlextInfraCodegenScaffolder(workspace_root=_resolve(params))
        results = scaffolder.run()
        lines: list[str] = []
        total_created = sum(len(res.files_created) for res in results)
        total_skipped = sum(len(res.files_skipped) for res in results)
        if not params.apply:
            lines.append("Dry-run mode: no files will be created")
        lines.extend(
            f"  {res.project}: created {len(res.files_created)} files"
            for res in results
            if res.files_created
        )
        lines.append(
            f"Scaffold: {total_created} created, {total_skipped} skipped"
            f" across {len(results)} projects",
        )
        return r[str].ok("\n".join(lines))

    @staticmethod
    def _handle_auto_fix(params: m.Infra.CodegenAutoFixInput) -> r[str]:
        """Handle namespace violation auto-fix."""
        dry_run = not params.apply
        fixer = FlextInfraCodegenFixer(
            workspace_root=_resolve(params),
            dry_run=dry_run,
        )
        lines: list[str] = []
        if dry_run:
            lines.append("Dry-run mode: no files will be modified")
        results = fixer.run()
        total_fixed = sum(len(res.violations_fixed) for res in results)
        total_skipped = sum(len(res.violations_skipped) for res in results)
        lines.extend(
            f"  {res.project}: fixed {len(res.violations_fixed)} violations"
            for res in results
            if res.violations_fixed
        )
        lines.append(
            f"Auto-fix: {total_fixed} fixed, {total_skipped} skipped"
            f" across {len(results)} projects",
        )
        return r[str].ok("\n".join(lines))

    @staticmethod
    def _handle_py_typed(params: m.Infra.CodegenPyTypedInput) -> r[bool]:
        """Handle py.typed marker generation."""
        service = FlextInfraCodegenPyTyped(workspace_root=_resolve(params))
        service.run(check_only=params.check)
        return r[bool].ok(True)

    @staticmethod
    def _handle_pipeline(params: m.Infra.CodegenPipelineInput) -> r[str]:
        """Handle full codegen pipeline."""
        workspace = _resolve(params)
        dry_run = not params.apply

        FlextInfraCodegenPyTyped(workspace_root=workspace).run()

        census = FlextInfraCodegenCensus(workspace_root=workspace)
        reports_before = census.run()

        scaffold_results = FlextInfraCodegenScaffolder(
            workspace_root=workspace,
        ).run()

        fix_results = FlextInfraCodegenFixer(
            workspace_root=workspace,
            dry_run=dry_run,
        ).run()

        FlextInfraCodegenLazyInit(workspace_root=workspace).run(check_only=dry_run)

        reports_after = census.run()

        before_v = sum(rpt.total for rpt in reports_before)
        before_f = sum(rpt.fixable for rpt in reports_before)
        after_v = sum(rpt.total for rpt in reports_after)
        after_f = sum(rpt.fixable for rpt in reports_after)
        scaffold_created = sum(len(res.files_created) for res in scaffold_results)
        scaffold_skipped = sum(len(res.files_skipped) for res in scaffold_results)
        fix_fixed = sum(len(res.violations_fixed) for res in fix_results)
        fix_skipped = sum(len(res.violations_skipped) for res in fix_results)

        def _text() -> str:
            return "\n".join([
                f"Census before: {before_v} violations",
                f"Scaffold: {scaffold_created} files created",
                f"Auto-fix: {fix_fixed} violations fixed",
                f"Census after: {after_v} violations",
                f"Improvement: {before_v - after_v} violations resolved",
            ])

        return _format(
            {
                "census_before": {
                    "total_violations": before_v,
                    "total_fixable": before_f,
                },
                "scaffold": {
                    "total_created": scaffold_created,
                    "total_skipped": scaffold_skipped,
                },
                "auto_fix": {
                    "total_fixed": fix_fixed,
                    "total_skipped": fix_skipped,
                },
                "census_after": {
                    "total_violations": after_v,
                    "total_fixable": after_f,
                },
            },
            output_format=params.output_format,
            text_fn=_text,
        )

    @staticmethod
    def _handle_constants_quality_gate(
        params: m.Infra.CodegenConstantsQualityGateInput,
    ) -> r[bool]:
        """Handle constants migration quality gate."""
        if params.before_report and params.baseline_file:
            return r[bool].fail(
                "--before-report and --baseline-file are mutually exclusive",
            )
        before_report = Path(params.before_report) if params.before_report else None
        baseline_file = Path(params.baseline_file) if params.baseline_file else None
        gate = FlextInfraCodegenConstantsQualityGate(
            workspace_root=_resolve(params),
            before_report=before_report,
            baseline_file=baseline_file,
        )
        report = gate.run()
        verdict = u.Infra.pick(report, "verdict", "FAIL")
        if FlextInfraCodegenConstantsQualityGate.is_success_verdict(verdict):
            return r[bool].ok(value=True)
        return r[bool].fail(f"quality gate verdict: {verdict}")
