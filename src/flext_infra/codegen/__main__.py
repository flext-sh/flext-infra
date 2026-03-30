"""CLI entry point for code generation services.

Usage:
    python -m flext_infra codegen lazy-init [--check] [--workspace PATH]
    python -m flext_infra codegen census [--workspace PATH] [--format json|text]
    python -m flext_infra codegen scaffold [--workspace PATH] [--dry-run|--apply]
    python -m flext_infra codegen auto-fix [--workspace PATH] [--dry-run|--apply]
    python -m flext_infra codegen pipeline [--workspace PATH] [--dry-run|--apply] [--format json|text]
    python -m flext_infra codegen constants-quality-gate [--workspace PATH] [--before-report PATH | --baseline-file PATH] [--format json|text]

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import sys
from collections.abc import Mapping, Sequence
from pathlib import Path

from pydantic import TypeAdapter

from flext_infra import (
    FlextInfraCodegenCensus,
    FlextInfraCodegenConstantsQualityGate,
    FlextInfraCodegenFixer,
    FlextInfraCodegenLazyInit,
    FlextInfraCodegenPyTyped,
    FlextInfraCodegenScaffolder,
    c,
    output,
    t,
    u,
)

_JSON_OUTPUT_ADAPTER: TypeAdapter[t.ContainerMapping] = TypeAdapter(
    t.ContainerMapping,
)


class FlextInfraCodegenCommand:
    """CLI entry point for code generation operations."""

    @staticmethod
    def run(argv: t.StrSequence | None) -> int:
        """Run codegen command dispatcher."""
        parser, subs = u.Infra.create_subcommand_parser(
            "flext-infra codegen",
            "Code generation tools for workspace standardization",
            subcommands={
                "lazy-init": "Generate/refresh PEP 562 lazy-import __init__.py files",
                "census": "Count namespace violations across workspace projects",
                "deduplicate": "Auto-fix duplicated constants (keep most-used)",
                "scaffold": "Generate missing base modules in src/ and tests/",
                "auto-fix": "Auto-fix namespace violations (move Finals/TypeVars)",
                "py-typed": "Create/remove PEP 561 py.typed markers",
                "pipeline": "Run full codegen pipeline",
                "constants-quality-gate": "Run constants migration quality gate",
            },
            include_apply=False,
            include_diff=False,
            include_format=False,
            include_check=False,
            subcommand_flags={
                "lazy-init": {"include_check": True},
                "census": {"include_format": True},
                "deduplicate": {"include_apply": True, "include_diff": False},
                "scaffold": {"include_apply": True, "include_diff": False},
                "auto-fix": {"include_apply": True, "include_diff": False},
                "py-typed": {"include_check": True},
                "pipeline": {
                    "include_apply": True,
                    "include_diff": False,
                    "include_format": True,
                },
            },
        )
        baseline_group = subs["constants-quality-gate"].add_mutually_exclusive_group(
            required=False,
        )
        _ = baseline_group.add_argument(
            "--before-report",
            type=Path,
            default=None,
            help="Path to pre-refactor report JSON for comparison",
        )
        _ = baseline_group.add_argument(
            "--baseline-file",
            type=Path,
            default=None,
            help="Path to baseline JSON payload for comparison",
        )
        _ = subs["census"].add_argument(
            "--class-to-analyze",
            type=str,
            default=None,
            help="Full class path to analyze attributes (e.g., flext_core.FlextConstants)",
        )
        _ = subs["deduplicate"].add_argument(
            "--class-to-analyze",
            type=str,
            required=True,
            help="Full class path to deduplicate (e.g., flext_core.FlextConstants)",
        )

        args = u.Infra.parse_subcommand_args(parser, argv)
        cli = u.Infra.resolve(args)
        if args.command == "lazy-init":
            return FlextInfraCodegenCommand.handle_lazy_init(cli)
        if args.command == "py-typed":
            return FlextInfraCodegenCommand.handle_py_typed(cli)
        if args.command == "census":
            return FlextInfraCodegenCommand.handle_census(cli)
        if args.command == "deduplicate":
            return FlextInfraCodegenCommand.handle_deduplicate(cli)
        if args.command == "scaffold":
            return FlextInfraCodegenCommand.handle_scaffold(cli)
        if args.command == "auto-fix":
            return FlextInfraCodegenCommand.handle_auto_fix(cli)
        if args.command == "pipeline":
            return FlextInfraCodegenCommand.handle_pipeline(cli)
        if args.command == "constants-quality-gate":
            return FlextInfraCodegenCommand.handle_constants_quality_gate(
                cli,
                before_report=getattr(args, "before_report", None),
                baseline_file=getattr(args, "baseline_file", None),
            )
        output.error(f"unknown command: {args.command}")
        return 1

    @staticmethod
    def handle_lazy_init(cli: u.Infra.CliArgs) -> int:
        """Handle lazy-init code generation."""
        generator = FlextInfraCodegenLazyInit(workspace_root=cli.workspace)
        errors = generator.run(check_only=cli.check)
        if errors > 0:
            output.error(f"lazy-init failed in {errors} package directories")
            return 1
        return 0

    @staticmethod
    def handle_py_typed(cli: u.Infra.CliArgs) -> int:
        """Handle py.typed marker generation."""
        service = FlextInfraCodegenPyTyped(workspace_root=cli.workspace)
        service.run(check_only=cli.check)
        return 0

    @staticmethod
    def handle_deduplicate(cli: u.Infra.CliArgs) -> int:
        """Handle constant deduplication with user selection."""
        class_to_analyze = getattr(cli, "class_to_analyze", None)
        if not class_to_analyze:
            output.error("--class-to-analyze is required")
            return 1

        # Get deduplicate proposals
        fixes = u.Infra.propose_deduplication_fixes(
            class_to_analyze,
            cli.workspace,
        )

        if not fixes:
            output.info("No duplicates found")
            return 0

        output.info(f"Found {len(fixes)} groups of duplicate constants\n")

        # Display fixes
        for i, fix in enumerate(fixes, 1):
            value_str = str(fix.get("value", ""))[:50]
            canonical = str(fix.get("canonical_name", ""))
            usages_val = fix.get("canonical_usages", 0)
            usages = int(usages_val) if isinstance(usages_val, int) else 0
            duplicates_val = fix.get("duplicates", [])
            duplicates: Sequence[Mapping[str, str | int]] = (
                duplicates_val if isinstance(duplicates_val, list) else []
            )
            output.info(
                f"{i}. Value: {value_str}"
                f" | Keep: {canonical} ({usages} uses)"
                f" | Replace {len(duplicates)} others",
            )
            for dup in duplicates:
                if isinstance(dup, dict):
                    dup_name = str(dup.get("name", ""))
                    dup_usages_val = dup.get("usages", 0)
                    dup_usages = (
                        int(dup_usages_val) if isinstance(dup_usages_val, int) else 0
                    )
                    output.info(f"   - {dup_name} ({dup_usages} uses)")

        # Apply fixes
        output.info(f"\nApplying {len(fixes)} deduplication fixes...")
        total_files_modified = 0
        for fix in fixes:
            result = u.Infra.apply_deduplication_fix(
                fix,
                cli.workspace,
                class_to_analyze,
                dry_run=cli.dry_run,
            )
            if result.get("status") == "success":
                files_mod_val = result.get("files_modified", 0)
                files_mod = int(files_mod_val) if isinstance(files_mod_val, int) else 0
                total_files_modified += files_mod
                canonical = str(result.get("canonical", ""))
                replaced_val = result.get("replaced", [])
                replaced: t.StrSequence = []
                if isinstance(replaced_val, list):
                    replaced = [item for item in replaced_val if isinstance(item, str)]
                output.info(
                    f"✓ {canonical}: replaced {len(replaced)} in {files_mod} files",
                )

        if not cli.dry_run:
            output.info(f"\n✓ Modified {total_files_modified} files")
        else:
            output.info(f"\n[DRY-RUN] Would modify {total_files_modified} files")

        return 0

    @staticmethod
    def handle_census(cli: u.Infra.CliArgs) -> int:
        """Handle namespace violation census."""
        class_to_analyze = getattr(cli, "class_to_analyze", None)
        census = FlextInfraCodegenCensus(
            workspace_root=cli.workspace,
            class_to_analyze=class_to_analyze,
        )
        reports = census.run()
        if cli.output_format == "json":
            output.info(
                _JSON_OUTPUT_ADAPTER.dump_json({
                    c.Infra.ReportKeys.PROJECTS: [rpt.model_dump() for rpt in reports],
                    "total_violations": sum(rpt.total for rpt in reports),
                    "total_fixable": sum(rpt.fixable for rpt in reports),
                }).decode(),
            )
        else:
            total_v = sum(rpt.total for rpt in reports)
            total_f = sum(rpt.fixable for rpt in reports)
            for rpt in reports:
                if rpt.total > 0:
                    output.info(
                        f"  {rpt.project}: {rpt.total} violations ({rpt.fixable} fixable)",
                    )
            output.info(
                f"Total: {total_v} violations ({total_f} fixable) across {len(reports)} projects",
            )
        return 0

    @staticmethod
    def handle_scaffold(cli: u.Infra.CliArgs) -> int:
        """Handle module scaffolding."""
        scaffolder = FlextInfraCodegenScaffolder(workspace_root=cli.workspace)
        if cli.dry_run:
            output.info("Dry-run mode: no files will be created")
        results = scaffolder.run()
        total_created = sum(len(res.files_created) for res in results)
        total_skipped = sum(len(res.files_skipped) for res in results)
        for res in results:
            if res.files_created:
                output.info(f"  {res.project}: created {len(res.files_created)} files")
        output.info(
            f"Scaffold: {total_created} created, {total_skipped} skipped across {len(results)} projects",
        )
        return 0

    @staticmethod
    def handle_auto_fix(cli: u.Infra.CliArgs) -> int:
        """Handle namespace violation auto-fix."""
        fixer = FlextInfraCodegenFixer(
            workspace_root=cli.workspace,
            dry_run=cli.dry_run,
        )
        if cli.dry_run:
            output.info("Dry-run mode: no files will be modified")
        results = fixer.run()
        total_fixed = sum(len(res.violations_fixed) for res in results)
        total_skipped = sum(len(res.violations_skipped) for res in results)
        for res in results:
            if res.violations_fixed:
                output.info(
                    f"  {res.project}: fixed {len(res.violations_fixed)} violations",
                )
        output.info(
            f"Auto-fix: {total_fixed} fixed, {total_skipped} skipped across {len(results)} projects",
        )
        return 0

    @staticmethod
    def handle_pipeline(cli: u.Infra.CliArgs) -> int:
        """Handle full codegen pipeline."""
        py_typed = FlextInfraCodegenPyTyped(workspace_root=cli.workspace)
        py_typed.run()
        census = FlextInfraCodegenCensus(workspace_root=cli.workspace)
        reports_before = census.run()
        scaffolder = FlextInfraCodegenScaffolder(workspace_root=cli.workspace)
        scaffold_results = scaffolder.run()
        fixer = FlextInfraCodegenFixer(
            workspace_root=cli.workspace,
            dry_run=cli.dry_run,
        )
        fix_results = fixer.run()
        generator = FlextInfraCodegenLazyInit(workspace_root=cli.workspace)
        generator.run(check_only=cli.dry_run)
        reports_after = census.run()
        if cli.output_format == "json":
            output.info(
                _JSON_OUTPUT_ADAPTER.dump_json({
                    "census_before": {
                        "total_violations": sum(r.total for r in reports_before),
                        "total_fixable": sum(r.fixable for r in reports_before),
                    },
                    "scaffold": {
                        "total_created": sum(
                            len(r.files_created) for r in scaffold_results
                        ),
                        "total_skipped": sum(
                            len(r.files_skipped) for r in scaffold_results
                        ),
                    },
                    "auto_fix": {
                        "total_fixed": sum(
                            len(r.violations_fixed) for r in fix_results
                        ),
                        "total_skipped": sum(
                            len(r.violations_skipped) for r in fix_results
                        ),
                    },
                    "census_after": {
                        "total_violations": sum(r.total for r in reports_after),
                        "total_fixable": sum(r.fixable for r in reports_after),
                    },
                }).decode(),
            )
        else:
            before_v = sum(r.total for r in reports_before)
            after_v = sum(r.total for r in reports_after)
            output.info(f"Census before: {before_v} violations")
            output.info(
                f"Scaffold: {sum(len(r.files_created) for r in scaffold_results)} files created",
            )
            output.info(
                f"Auto-fix: {sum(len(r.violations_fixed) for r in fix_results)} violations fixed",
            )
            output.info(f"Census after: {after_v} violations")
            output.info(f"Improvement: {before_v - after_v} violations resolved")
        return 0

    @staticmethod
    def handle_constants_quality_gate(
        cli: u.Infra.CliArgs,
        *,
        before_report: Path | None,
        baseline_file: Path | None,
    ) -> int:
        """Handle constants migration quality gate."""
        gate = FlextInfraCodegenConstantsQualityGate(
            workspace_root=cli.workspace,
            before_report=before_report,
            baseline_file=baseline_file,
        )
        report = gate.run()
        verdict = str(report.get("verdict", "FAIL"))
        return (
            0
            if FlextInfraCodegenConstantsQualityGate.is_success_verdict(verdict)
            else 1
        )


def main(argv: t.StrSequence | None = None) -> int:
    """Run codegen service CLI with centralized bootstrap."""
    return u.Infra.run_cli(FlextInfraCodegenCommand.run, argv)


if __name__ == "__main__":
    sys.exit(main())


__all__ = ["FlextInfraCodegenCommand", "main"]
