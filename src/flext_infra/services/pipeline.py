"""Direct codegen pipeline command service."""

from __future__ import annotations

from typing import override

from flext_core import r
from flext_infra import (
    FlextInfraCodegenCensus,
    FlextInfraCodegenFixer,
    FlextInfraCodegenLazyInit,
    FlextInfraCodegenPyTyped,
    FlextInfraCodegenScaffolder,
    s,
    t,
)


class FlextInfraCodegenPipeline(s[str]):
    """Run the full codegen pipeline directly from the validated CLI model."""

    @override
    def execute(self) -> r[str]:
        """Execute the end-to-end codegen pipeline."""
        FlextInfraCodegenPyTyped.model_validate({
            "workspace_root": self.workspace_root,
        }).run()
        census = FlextInfraCodegenCensus.model_validate({
            "workspace_root": self.workspace_root,
        })
        reports_before = census.run()
        scaffold_results = FlextInfraCodegenScaffolder.model_validate({
            "workspace_root": self.workspace_root,
        }).run(dry_run=self.dry_run or not self.apply_changes)
        fix_results = FlextInfraCodegenFixer.model_validate({
            "workspace_root": self.workspace_root,
            "dry_run": self.dry_run or not self.apply_changes,
        }).fix_workspace()
        FlextInfraCodegenLazyInit.model_validate({
            "workspace_root": self.workspace_root,
        }).generate_inits(check_only=self.dry_run or not self.apply_changes)
        reports_after = census.run()
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
