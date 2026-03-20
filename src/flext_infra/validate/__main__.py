"""CLI entry point for core infrastructure services.

Usage:
    python -m flext_infra validate basemk-validate [--workspace PATH]
    python -m flext_infra validate inventory [--workspace PATH] [--output-dir PATH]
    python -m flext_infra validate pytest-diag --junit PATH --log PATH
    python -m flext_infra validate scan --workspace PATH --pattern REGEX
        --include GLOB [--exclude GLOB] [--match present|absent]
    python -m flext_infra validate skill-validate --skill NAME [--workspace PATH]
        [--mode baseline|strict]
    python -m flext_infra validate stub-validate [--workspace PATH]

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import sys
from collections.abc import Mapping
from pathlib import Path
from typing import TYPE_CHECKING

from flext_infra import c, t
from flext_infra.utilities import u

if TYPE_CHECKING:
    from flext_infra import m


class FlextInfraValidateCommand:
    @staticmethod
    def list_str(
        payload: m.Infra.InventoryReport | m.Infra.PytestDiagnostics,
        key: str,
    ) -> list[str]:
        """Extract string list from payload attribute."""
        return [item for item in getattr(payload, key, []) if isinstance(item, str)]

    @staticmethod
    def run_basemk_validate(cli: u.Infra.CliArgs) -> int:
        """Validate base.mk sync."""
        validator = FlextInfraBaseMkValidator()
        result = validator.validate(cli.workspace)
        if result.is_success:
            report: m.Infra.ValidationReport = result.value
            output.info(report.summary)
            for violation in report.violations:
                output.warning(violation)
            return 0 if report.passed else 1
        output.error(result.error or "unknown error")
        return 1

    @staticmethod
    def run_inventory(cli: u.Infra.CliArgs, output_dir: str | None) -> int:
        """Generate scripts inventory."""
        service = FlextInfraInventoryService()
        output_dir_path = Path(output_dir).resolve() if output_dir else None
        result = service.generate(cli.workspace, output_dir=output_dir_path)
        if result.is_success:
            report: m.Infra.InventoryReport = result.value
            for output_path in FlextInfraValidateCommand.list_str(
                report,
                "reports_written",
            ):
                output.info(f"Wrote: {output_path}")
            return 0
        output.error(result.error or "unknown error")
        return 1

    @staticmethod
    def run_pytest_diag(
        junit: str,
        log: str,
        failed: str | None,
        errors: str | None,
        warnings: str | None,
        slowest: str | None,
        skips: str | None,
    ) -> int:
        """Extract pytest diagnostics from JUnit and log files."""
        extractor = FlextInfraPytestDiagExtractor()
        result = extractor.extract(Path(junit), Path(log))
        if result.is_failure:
            output.error(result.error or "unknown error")
            return 1
        data: m.Infra.PytestDiagnostics = result.value
        if failed:
            u.write_file(
                Path(failed),
                "\n\n".join(FlextInfraValidateCommand.list_str(data, "failed_cases"))
                + "\n",
                encoding=c.Infra.Encoding.DEFAULT,
            )
        if errors:
            u.write_file(
                Path(errors),
                "\n\n".join(FlextInfraValidateCommand.list_str(data, "error_traces"))
                + "\n",
                encoding=c.Infra.Encoding.DEFAULT,
            )
        if warnings:
            u.write_file(
                Path(warnings),
                "\n".join(FlextInfraValidateCommand.list_str(data, "warning_lines"))
                + "\n",
                encoding=c.Infra.Encoding.DEFAULT,
            )
        if slowest:
            u.write_file(
                Path(slowest),
                "\n".join(FlextInfraValidateCommand.list_str(data, "slow_entries"))
                + "\n",
                encoding=c.Infra.Encoding.DEFAULT,
            )
        if skips:
            u.write_file(
                Path(skips),
                "\n".join(FlextInfraValidateCommand.list_str(data, "skip_cases"))
                + "\n",
                encoding=c.Infra.Encoding.DEFAULT,
            )
        return 0

    @staticmethod
    def run_scan(
        cli: u.Infra.CliArgs,
        pattern: str,
        include: list[str],
        exclude: list[str],
        match: str,
    ) -> int:
        """Scan text files for patterns."""
        scanner = FlextInfraTextPatternScanner()
        result = scanner.scan(
            cli.workspace,
            pattern,
            includes=include or [],
            excludes=exclude or [],
            match_mode=match,
        )
        if result.is_success:
            data: Mapping[str, t.Scalar] = result.value
            violation_count = data.get("violation_count", 0)
            return 1 if isinstance(violation_count, int) and violation_count > 0 else 0
        output.error(result.error or "unknown error")
        return 1

    @staticmethod
    def run_skill_validate(cli: u.Infra.CliArgs, skill: str, mode: str) -> int:
        """Validate a skill."""
        validator = FlextInfraSkillValidator()
        result = validator.validate(cli.workspace, skill, mode=mode)
        if result.is_success:
            report: m.Infra.ValidationReport = result.value
            output.info(report.summary)
            for violation in report.violations:
                output.warning(violation)
            return 0 if report.passed else 1
        output.error(result.error or "unknown error")
        return 1

    @staticmethod
    def run_stub_validate(cli: u.Infra.CliArgs, project: list[str] | None) -> int:
        """Validate stub supply chain."""
        chain = FlextInfraStubSupplyChain()
        project_dirs: list[Path] | None = (
            [cli.workspace / project_name for project_name in project]
            if project
            else None
        )
        result = chain.validate(cli.workspace, project_dirs=project_dirs)
        if result.is_success:
            report: m.Infra.ValidationReport = result.value
            output.info(report.summary)
            for violation in report.violations:
                output.warning(violation)
            return 0 if report.passed else 1
        output.error(result.error or "unknown error")
        return 1

    @staticmethod
    def run(argv: list[str] | None = None) -> int:
        """Run validation command dispatcher."""
        parser, subs = u.Infra.create_subcommand_parser(
            prog="flext_infra validate",
            description="Core infrastructure services",
            subcommands={
                "basemk-validate": "Validate base.mk sync",
                "inventory": "Generate scripts inventory",
                "pytest-diag": "Extract pytest diagnostics",
                "scan": "Scan text files for patterns",
                "skill-validate": "Validate a skill",
                "stub-validate": "Validate stub supply chain",
            },
            include_apply=False,
        )

        subs["inventory"].add_argument(
            "--output-dir",
            default=None,
            help="Output directory",
        )

        subs["pytest-diag"].add_argument(
            "--junit",
            required=True,
            help="JUnit XML path",
        )
        subs["pytest-diag"].add_argument("--log", required=True, help="Pytest log path")
        subs["pytest-diag"].add_argument("--failed", help="Path to write failed cases")
        subs["pytest-diag"].add_argument("--errors", help="Path to write error traces")
        subs["pytest-diag"].add_argument("--warnings", help="Path to write warnings")
        subs["pytest-diag"].add_argument(
            "--slowest",
            help="Path to write slowest entries",
        )
        subs["pytest-diag"].add_argument("--skips", help="Path to write skipped cases")

        subs["scan"].add_argument("--pattern", required=True, help="Regex pattern")
        subs["scan"].add_argument(
            "--include",
            action="append",
            required=True,
            help="Include glob",
        )
        subs["scan"].add_argument(
            "--exclude",
            action="append",
            default=[],
            help="Exclude glob",
        )
        subs["scan"].add_argument(
            "--match",
            choices=("present", "absent"),
            default=c.Infra.MatchModes.PRESENT,
            help="Violation mode",
        )

        subs["skill-validate"].add_argument(
            "--skill",
            required=True,
            help="Skill folder name",
        )
        subs["skill-validate"].add_argument(
            "--mode",
            choices=("baseline", "strict"),
            default=c.Infra.Modes.BASELINE,
        )

        subs["stub-validate"].add_argument(
            "--project",
            action="append",
            help="Project to validate",
        )
        _ = subs["stub-validate"].add_argument(
            "--all",
            action="store_true",
            help="Validate all projects",
        )

        args = parser.parse_args(argv)
        cli = u.Infra.resolve(args)

        commands = {
            "basemk-validate": lambda: _run_basemk_validate(cli),
            "inventory": lambda: _run_inventory(
                cli,
                getattr(args, "output_dir", None),
            ),
            "pytest-diag": lambda: _run_pytest_diag(
                getattr(args, "junit", ""),
                getattr(args, "log", ""),
                getattr(args, "failed", None),
                getattr(args, "errors", None),
                getattr(args, "warnings", None),
                getattr(args, "slowest", None),
                getattr(args, "skips", None),
            ),
            "scan": lambda: _run_scan(
                cli,
                getattr(args, "pattern", ""),
                getattr(args, "include", None) or [],
                getattr(args, "exclude", None) or [],
                getattr(args, "match", "present"),
            ),
            "skill-validate": lambda: _run_skill_validate(
                cli,
                getattr(args, "skill", ""),
                getattr(args, "mode", "baseline"),
            ),
            "stub-validate": lambda: _run_stub_validate(
                cli,
                getattr(args, "project", None),
            ),
        }
        handler = commands.get(args.command)
        if handler is None:
            parser.print_help()
            return 1
        return handler()


def _run_basemk_validate(cli: u.Infra.CliArgs) -> int:
    return FlextInfraValidateCommand.run_basemk_validate(cli)


def _run_inventory(cli: u.Infra.CliArgs, output_dir: str | None) -> int:
    return FlextInfraValidateCommand.run_inventory(cli, output_dir)


def _run_pytest_diag(
    junit: str,
    log: str,
    failed: str | None,
    errors: str | None,
    warnings: str | None,
    slowest: str | None,
    skips: str | None,
) -> int:
    return FlextInfraValidateCommand.run_pytest_diag(
        junit,
        log,
        failed,
        errors,
        warnings,
        slowest,
        skips,
    )


def _run_scan(
    cli: u.Infra.CliArgs,
    pattern: str,
    include: list[str],
    exclude: list[str],
    match: str,
) -> int:
    return FlextInfraValidateCommand.run_scan(
        cli,
        pattern,
        include,
        exclude,
        match,
    )


def _run_skill_validate(cli: u.Infra.CliArgs, skill: str, mode: str) -> int:
    return FlextInfraValidateCommand.run_skill_validate(cli, skill, mode)


def _run_stub_validate(cli: u.Infra.CliArgs, project: list[str] | None) -> int:
    return FlextInfraValidateCommand.run_stub_validate(cli, project)


def _main_inner(argv: list[str] | None = None) -> int:
    return FlextInfraValidateCommand.run(argv)


def main() -> int:
    """Run core infrastructure services."""
    return u.Infra.run_cli(_main_inner)


if __name__ == "__main__":
    sys.exit(main())
