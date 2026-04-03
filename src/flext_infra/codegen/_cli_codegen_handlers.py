"""Codegen CLI handlers mixin — simple command handlers."""

from __future__ import annotations

from collections.abc import Sequence
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
    t,
    u,
)

__all__ = ["FlextInfraCliCodegenHandlers"]


class FlextInfraCliCodegenHandlers:
    """Mixin providing simple codegen command handlers."""

    @staticmethod
    def _handle_lazy_init(params: m.Infra.CodegenLazyInitInput) -> r[bool]:
        """Handle lazy-init code generation."""
        workspace = Path(params.workspace).resolve()
        generator = FlextInfraCodegenLazyInit(workspace_root=workspace)
        errors = generator.run(check_only=params.check)
        if errors > 0:
            return r[bool].fail(
                f"lazy-init failed in {errors} package directories",
            )
        return r[bool].ok(True)

    @staticmethod
    def _handle_codegen_census(params: m.Infra.CodegenCensusInput) -> r[str]:
        """Handle namespace violation census."""
        workspace = Path(params.workspace).resolve()
        census = FlextInfraCodegenCensus(
            workspace_root=workspace,
            class_to_analyze=params.class_to_analyze,
        )
        reports = census.run()
        if params.output_format == "json":
            text = t.Infra.CONTAINER_MAPPING_ADAPTER.dump_json({
                c.Infra.ReportKeys.PROJECTS: [rpt.model_dump() for rpt in reports],
                "total_violations": sum(rpt.total for rpt in reports),
                "total_fixable": sum(rpt.fixable for rpt in reports),
            }).decode()
        else:
            total_v = sum(rpt.total for rpt in reports)
            total_f = sum(rpt.fixable for rpt in reports)
            lines: list[str] = [
                f"  {rpt.project}: {rpt.total} violations ({rpt.fixable} fixable)"
                for rpt in reports
                if rpt.total > 0
            ]
            lines.append(
                f"Total: {total_v} violations ({total_f} fixable)"
                f" across {len(reports)} projects",
            )
            text = "\n".join(lines)
        return r[str].ok(text)

    @staticmethod
    def _handle_deduplicate(params: m.Infra.CodegenDeduplicateInput) -> r[str]:
        """Handle constant deduplication with user selection."""
        workspace = Path(params.workspace).resolve()
        dry_run = not params.apply
        fixes = u.Infra.propose_deduplication_fixes(
            params.class_to_analyze,
            workspace,
        )
        if not fixes:
            return r[str].ok("No duplicates found")

        lines: list[str] = [f"Found {len(fixes)} groups of duplicate constants\n"]

        for i, fix in enumerate(fixes, 1):
            value_str = str(fix.get("value", ""))[:50]
            canonical = str(fix.get("canonical_name", ""))
            usages_val = fix.get("canonical_usages", 0)
            usages = int(usages_val) if isinstance(usages_val, int) else 0
            duplicates_val = fix.get("duplicates", [])
            duplicates: Sequence[t.Infra.CensusRecord] = (
                duplicates_val if isinstance(duplicates_val, list) else []
            )
            lines.append(
                f"{i}. Value: {value_str}"
                f" | Keep: {canonical} ({usages} uses)"
                f" | Replace {len(duplicates)} others",
            )
            for dup in duplicates:
                if u.is_mapping(dup):
                    dup_name = str(dup.get("name", ""))
                    dup_usages_val = dup.get("usages", 0)
                    dup_usages = (
                        int(dup_usages_val) if isinstance(dup_usages_val, int) else 0
                    )
                    lines.append(f"   - {dup_name} ({dup_usages} uses)")

        lines.append(f"\nApplying {len(fixes)} deduplication fixes...")
        total_files_modified = 0
        for fix in fixes:
            result = u.Infra.apply_deduplication_fix(
                fix,
                workspace,
                params.class_to_analyze,
                dry_run=dry_run,
            )
            if result.get("status") == "success":
                files_mod_val = result.get("files_modified", 0)
                files_mod = int(files_mod_val) if isinstance(files_mod_val, int) else 0
                total_files_modified += files_mod
                canonical_name = str(result.get("canonical", ""))
                replaced_val = result.get("replaced", [])
                replaced: t.StrSequence = []
                if isinstance(replaced_val, list):
                    replaced = [item for item in replaced_val if isinstance(item, str)]
                lines.append(
                    f"  {canonical_name}: replaced {len(replaced)}"
                    f" in {files_mod} files",
                )

        if dry_run:
            lines.append(f"\n[DRY-RUN] Would modify {total_files_modified} files")
        else:
            lines.append(f"\nModified {total_files_modified} files")

        return r[str].ok("\n".join(lines))

    @staticmethod
    def _handle_scaffold(params: m.Infra.CodegenScaffoldInput) -> r[str]:
        """Handle module scaffolding."""
        workspace = Path(params.workspace).resolve()
        scaffolder = FlextInfraCodegenScaffolder(workspace_root=workspace)
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
        workspace = Path(params.workspace).resolve()
        dry_run = not params.apply
        fixer = FlextInfraCodegenFixer(
            workspace_root=workspace,
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
        workspace = Path(params.workspace).resolve()
        service = FlextInfraCodegenPyTyped(workspace_root=workspace)
        service.run(check_only=params.check)
        return r[bool].ok(True)

    @staticmethod
    def _handle_pipeline(params: m.Infra.CodegenPipelineInput) -> r[str]:
        """Handle full codegen pipeline."""
        workspace = Path(params.workspace).resolve()
        dry_run = not params.apply

        py_typed = FlextInfraCodegenPyTyped(workspace_root=workspace)
        py_typed.run()

        census = FlextInfraCodegenCensus(workspace_root=workspace)
        reports_before = census.run()

        scaffolder = FlextInfraCodegenScaffolder(workspace_root=workspace)
        scaffold_results = scaffolder.run()

        fixer = FlextInfraCodegenFixer(
            workspace_root=workspace,
            dry_run=dry_run,
        )
        fix_results = fixer.run()

        generator = FlextInfraCodegenLazyInit(workspace_root=workspace)
        generator.run(check_only=dry_run)

        reports_after = census.run()

        if params.output_format == "json":
            text = t.Infra.CONTAINER_MAPPING_ADAPTER.dump_json({
                "census_before": {
                    "total_violations": sum(rpt.total for rpt in reports_before),
                    "total_fixable": sum(rpt.fixable for rpt in reports_before),
                },
                "scaffold": {
                    "total_created": sum(
                        len(res.files_created) for res in scaffold_results
                    ),
                    "total_skipped": sum(
                        len(res.files_skipped) for res in scaffold_results
                    ),
                },
                "auto_fix": {
                    "total_fixed": sum(
                        len(res.violations_fixed) for res in fix_results
                    ),
                    "total_skipped": sum(
                        len(res.violations_skipped) for res in fix_results
                    ),
                },
                "census_after": {
                    "total_violations": sum(rpt.total for rpt in reports_after),
                    "total_fixable": sum(rpt.fixable for rpt in reports_after),
                },
            }).decode()
        else:
            before_v = sum(rpt.total for rpt in reports_before)
            after_v = sum(rpt.total for rpt in reports_after)
            scaffold_count = sum(len(res.files_created) for res in scaffold_results)
            fix_count = sum(len(res.violations_fixed) for res in fix_results)
            lines = [
                f"Census before: {before_v} violations",
                f"Scaffold: {scaffold_count} files created",
                f"Auto-fix: {fix_count} violations fixed",
                f"Census after: {after_v} violations",
                f"Improvement: {before_v - after_v} violations resolved",
            ]
            text = "\n".join(lines)
        return r[str].ok(text)

    @staticmethod
    def _handle_constants_quality_gate(
        params: m.Infra.CodegenConstantsQualityGateInput,
    ) -> r[bool]:
        """Handle constants migration quality gate."""
        workspace = Path(params.workspace).resolve()
        if params.before_report and params.baseline_file:
            return r[bool].fail(
                "--before-report and --baseline-file are mutually exclusive",
            )
        before_report = Path(params.before_report) if params.before_report else None
        baseline_file = Path(params.baseline_file) if params.baseline_file else None
        gate = FlextInfraCodegenConstantsQualityGate(
            workspace_root=workspace,
            before_report=before_report,
            baseline_file=baseline_file,
        )
        report = gate.run()
        verdict = str(report.get("verdict", "FAIL"))
        if FlextInfraCodegenConstantsQualityGate.is_success_verdict(verdict):
            return r[bool].ok(value=True)
        return r[bool].fail(f"quality gate verdict: {verdict}")
