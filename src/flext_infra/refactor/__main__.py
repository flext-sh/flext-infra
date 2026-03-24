"""Run flext_infra.refactor CLI."""

from __future__ import annotations

import sys
from pathlib import Path

from flext_infra import output, t, u

from .census import FlextInfraRefactorCensus
from .migrate_to_class_mro import FlextInfraRefactorMigrateToClassMRO
from .namespace_enforcer import FlextInfraNamespaceEnforcer


class FlextInfraRefactorCommand:
    """CLI entry point for refactoring and modernization tool commands."""

    @staticmethod
    def run(argv: t.StrSequence | None = None) -> int:
        """Dispatch CLI command handlers and return process exit code."""
        parser, subs = u.Infra.create_subcommand_parser(
            "flext_infra refactor",
            "Refactor and modernization tools for flext workspace",
            subcommands={
                "centralize-pydantic": "Centralize BaseModel/TypedDict/dict-like aliases into _models.py",
                "migrate-mro": "Migrate loose declarations into MRO facade classes",
                "namespace-enforce": "Scan workspace for namespace governance violations",
                "imports": "Detect and fix all import violations across workspace (CST-based)",
                "ultrawork-models": "Run full centralization + MRO + namespace workflow",
                "census": "Run AST/CST census of MRO family method usage",
            },
            include_apply=True,
            include_project=True,
        )
        _ = subs["centralize-pydantic"].add_argument(
            "--normalize-remaining",
            action="store_true",
            help="Remove remaining BaseModel/TypedDict bases in non-allowed files",
        )
        _ = subs["migrate-mro"].add_argument(
            "--target",
            choices=["constants", "typings", "protocols", "models", "utilities", "all"],
            default="all",
            help="Migration target scope",
        )
        _ = subs["census"].add_argument(
            "--family",
            type=str,
            default="u",
            choices=sorted({"c", "t", "p", "m", "u"}),
            help="MRO family to census (default: u). Options: c, t, p, m, u",
        )
        _ = subs["census"].add_argument(
            "--json-output",
            type=Path,
            default=None,
            help="Path to write JSON report (optional)",
        )
        _ = subs["ultrawork-models"].add_argument(
            "--normalize-remaining",
            action="store_true",
            help="Remove remaining BaseModel/TypedDict bases in non-allowed files",
        )

        args = parser.parse_args(argv)
        cli = u.Infra.resolve(args)
        command = str(args.command)

        if command == "centralize-pydantic":
            return FlextInfraRefactorCommand.run_centralize_pydantic(
                cli,
                normalize_remaining=bool(getattr(args, "normalize_remaining", False)),
            )
        if command == "migrate-mro":
            return FlextInfraRefactorCommand.run_migrate_to_mro(
                cli,
                target=str(getattr(args, "target", "all")),
            )
        if command == "namespace-enforce":
            return FlextInfraRefactorCommand.run_namespace_enforce(cli)
        if command == "imports":
            return FlextInfraRefactorCommand.run_imports(cli)
        if command == "ultrawork-models":
            return FlextInfraRefactorCommand.run_ultrawork_models(
                cli,
                normalize_remaining=bool(getattr(args, "normalize_remaining", False)),
            )
        if command == "census":
            return FlextInfraRefactorCommand.run_census(
                cli,
                family=str(getattr(args, "family", "u")),
                json_output=getattr(args, "json_output", None),
            )

        parser.print_help()
        return 1

    @staticmethod
    def run_centralize_pydantic(
        cli: u.Infra.CliArgs,
        *,
        normalize_remaining: bool,
    ) -> int:
        """Run pydantic centralization workflow for the workspace."""
        summary = u.Infra.pydantic_centralize_workspace(
            cli.workspace,
            apply=cli.apply,
            normalize_remaining=normalize_remaining,
        )
        output.metrics(
            {
                "workspace": cli.workspace,
                "mode": cli.mode_label,
            },
            summary,
        )
        return 0

    @staticmethod
    def run_migrate_to_mro(cli: u.Infra.CliArgs, *, target: str) -> int:
        """Run MRO migration workflow for the selected target scope."""
        service = FlextInfraRefactorMigrateToClassMRO(workspace_root=cli.workspace)
        report = service.run(target=target, apply=cli.apply)
        output.write(FlextInfraRefactorMigrateToClassMRO.render_text(report))
        if report.errors:
            for error in report.errors:
                output.error(error)
            return 1
        return 0

    @staticmethod
    def run_namespace_enforce(cli: u.Infra.CliArgs) -> int:
        """Run namespace enforcement checks and optionally apply fixes."""
        enforcer = FlextInfraNamespaceEnforcer(workspace_root=cli.workspace)
        report = enforcer.enforce(
            apply=cli.apply,
            project_names=cli.project_names(),
        )
        sys.stdout.write(FlextInfraNamespaceEnforcer.render_text(report))
        sys.stdout.flush()
        if report.has_violations:
            return 1
        return 0

    @staticmethod
    def run_imports(cli: u.Infra.CliArgs) -> int:
        """Detect and optionally fix import violations across workspace (CST-based)."""
        enforcer = FlextInfraNamespaceEnforcer(workspace_root=cli.workspace)
        report = enforcer.enforce(
            apply=cli.apply,
            project_names=cli.project_names(),
        )
        sys.stdout.write(FlextInfraNamespaceEnforcer.render_text(report))
        sys.stdout.flush()
        if report.has_violations:
            return 1
        return 0

    @staticmethod
    def run_ultrawork_models(
        cli: u.Infra.CliArgs,
        *,
        normalize_remaining: bool,
    ) -> int:
        """Run centralization, MRO migration, and namespace enforcement together."""
        centralize_summary = u.Infra.pydantic_centralize_workspace(
            cli.workspace,
            apply=cli.apply,
            normalize_remaining=normalize_remaining,
        )
        mro_report = FlextInfraRefactorMigrateToClassMRO(
            workspace_root=cli.workspace,
        ).run(
            target="all",
            apply=cli.apply,
        )
        namespace_report = FlextInfraNamespaceEnforcer(
            workspace_root=cli.workspace,
        ).enforce(apply=cli.apply)
        output.metrics(
            {
                "workspace": cli.workspace,
                "mode": cli.mode_label,
            },
            centralize_summary,
            {
                "mro_remaining_violations": mro_report.remaining_violations,
                "mro_files_scanned": mro_report.files_scanned,
                "mro_files_with_candidates": mro_report.files_with_candidates,
                "mro_failures": mro_report.mro_failures,
            },
            {
                "namespace_loose_objects": namespace_report.total_loose_objects,
                "namespace_import_violations": namespace_report.total_import_violations,
                "namespace_cyclic_imports": namespace_report.total_cyclic_imports,
                "namespace_runtime_alias_violations": namespace_report.total_runtime_alias_violations,
                "namespace_manual_protocols": namespace_report.total_manual_protocol_violations,
                "namespace_manual_typing_aliases": namespace_report.total_manual_typing_violations,
                "namespace_compatibility_aliases": namespace_report.total_compatibility_alias_violations,
                "namespace_parse_failures": namespace_report.total_parse_failures,
                "namespace_files_scanned": namespace_report.total_files_scanned,
            },
        )
        if mro_report.errors:
            for error in mro_report.errors:
                output.error(error)
            return 1
        return 0

    @staticmethod
    def run_census(
        cli: u.Infra.CliArgs,
        *,
        family: str,
        json_output: Path | None,
    ) -> int:
        """Run method-usage census and optionally export JSON report."""
        census = FlextInfraRefactorCensus()

        target = u.Infra.build_mro_target(family)
        result = census.run(workspace_root=cli.workspace, target=target)
        if result.is_failure:
            return u.Infra.exit_code(result, failure_msg="Census failed")
        report = result.value
        output.write(FlextInfraRefactorCensus.render_text(report))
        output.write("\n")
        if json_output:
            json_path = Path(json_output).resolve()
            u.Infra.export_pydantic_json(report, json_path)
            output.info(f"JSON report exported to: {json_path}")

        output.metrics(
            {"family": family, "workspace": cli.workspace},
            report,
        )
        return 0


def main(argv: t.StrSequence | None = None) -> int:
    """Wrapped CLI entry point with centralized error handling."""
    return u.Infra.run_cli(FlextInfraRefactorCommand.run, argv)


if __name__ == "__main__":
    sys.exit(main())
