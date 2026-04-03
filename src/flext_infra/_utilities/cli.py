"""CLI argument parsing utilities for flext-infra commands.

Centralizes argument parser creation and argument resolution for all
flext_infra CLI commands, providing a consistent interface for workspace,
apply/dry-run, format, check, and project selection flags.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from argparse import ArgumentParser, Namespace
from collections.abc import Callable, Mapping, Sequence
from pathlib import Path

from flext_cli import FlextCliUtilities
from flext_infra._utilities.base import FlextInfraUtilitiesBase
from flext_infra._utilities.cli_shared import FlextInfraUtilitiesCliShared
from flext_infra._utilities.cli_subcommand import FlextInfraUtilitiesCliSubcommand
from flext_infra._utilities.output import FlextInfraUtilitiesOutput
from flext_infra.models import FlextInfraModels as m
from flext_infra.typings import FlextInfraTypes as t


class FlextInfraUtilitiesCli(FlextInfraUtilitiesCliShared):
    """Static facade for CLI argument parsing and resolution.

    Provides standardized argument parser creation and resolution for
    flext_infra commands, supporting optional flags for apply/dry-run,
    output format, check mode, and project selection.
    """

    class CliArgs(m.FrozenStrictModel):
        """Parsed CLI arguments with strict validation.

        Immutable model representing resolved command-line arguments,
        with optional fields for apply, format, check, and project selection.
        """

        workspace: Path = Path.cwd()
        apply: bool = False
        output_format: str = "text"
        check: bool = False
        diff: bool = False
        project: str | None = None
        projects: str | None = None
        class_to_analyze: str | None = None

        @property
        def dry_run(self) -> bool:
            """Return True if not in apply mode (i.e., dry-run mode)."""
            return not self.apply

        def project_names(self) -> t.StrSequence | None:
            """Extract project names from single or comma-separated project string.

            Combines --project (single) and --projects (comma-separated) arguments.
            Strips whitespace and ignores empty entries.

            Returns:
                List of project names if any specified, None if both arguments empty.

            """
            return FlextInfraUtilitiesCli.project_names_from_values(
                self.project,
                self.projects,
            )

        def project_dirs(self) -> Sequence[Path] | None:
            """Convert project names to absolute directory paths under workspace.

            Uses project_names() to resolve projects, then prepends workspace root
            to each name to create full paths.

            Returns:
                List of Path objects (workspace / project_name) if projects specified.
                None if no projects were specified via --project or --projects.

            """
            names = self.project_names()
            if names is None:
                return None
            return [self.workspace / name for name in names]

    @staticmethod
    def create_subcommand_parser(
        prog: str,
        description: str,
        *,
        subcommands: t.StrMapping,
        flags: FlextInfraUtilitiesCli.SharedFlags | None = None,
        subcommand_flags: Mapping[str, t.BoolMapping] | None = None,
    ) -> t.Infra.Pair[ArgumentParser, Mapping[str, ArgumentParser]]:
        """Create main parser with subcommands and shared flags."""
        return FlextInfraUtilitiesCliSubcommand.create_subcommand_parser(
            prog,
            description,
            subcommands=subcommands,
            flags=flags.to_dict() if flags is not None else None,
            subcommand_flags=subcommand_flags,
        )

    @staticmethod
    def project_names_from_values(
        *values: str | t.StrSequence | None,
    ) -> t.StrSequence | None:
        """Normalize project selectors through the canonical CLI utility."""
        return FlextCliUtilities.Cli.project_names_from_values(*values)

    @staticmethod
    def create_parser(
        prog: str,
        description: str,
        *,
        flags: FlextInfraUtilitiesCli.SharedFlags | None = None,
    ) -> ArgumentParser:
        """Create a standard ArgumentParser with common CLI flags.

        Args:
            prog: Program name for the parser.
            description: Description of the command.
            flags: Bundled flag configuration. Defaults to FlextInfraUtilitiesCli.SharedFlags() if None.

        Returns:
            Configured ArgumentParser instance.

        """
        resolved_flags = flags or FlextInfraUtilitiesCli.SharedFlags()
        parser = ArgumentParser(prog=prog, description=description)
        FlextInfraUtilitiesCli._add_shared_flags(parser, resolved_flags)
        return parser

    @staticmethod
    def parse_subcommand_args(
        parser: ArgumentParser,
        argv: t.StrSequence | None = None,
        *,
        passthrough_subcommands: t.StrSequence | None = None,
    ) -> Namespace:
        """Parse and validate subcommand args against per-command shared flags."""
        return FlextInfraUtilitiesCliSubcommand.parse_subcommand_args(
            parser,
            argv,
            passthrough_subcommands=passthrough_subcommands,
        )

    @staticmethod
    def resolve(args: Namespace) -> FlextInfraUtilitiesCli.CliArgs:
        """Resolve parsed arguments into a typed CliArgs model.

        Args:
            args: Parsed arguments from ArgumentParser.

        Returns:
            CliArgs instance with resolved values.

        Raises:
            ValidationError: If argument values fail Pydantic validation.

        """
        # Determine apply/diff flags
        apply_flag = bool(getattr(args, "apply", False))
        diff_flag = bool(getattr(args, "diff", False))

        # Get output format, defaulting to "text"
        output_format = getattr(args, "output_format", "text")

        # Get check flag, defaulting to False
        check_flag = bool(getattr(args, "check", False))

        raw_project = getattr(args, "project", None)
        project = raw_project if isinstance(raw_project, str) else None

        raw_projects = getattr(args, "projects", None)
        projects = raw_projects if isinstance(raw_projects, str) else None

        raw_class_to_analyze = getattr(args, "class_to_analyze", None)
        class_to_analyze = (
            raw_class_to_analyze if isinstance(raw_class_to_analyze, str) else None
        )

        # Resolve workspace path
        raw_workspace = getattr(args, "workspace", Path.cwd())
        workspace_path: Path = (
            raw_workspace.resolve()
            if isinstance(raw_workspace, Path)
            else Path(raw_workspace).resolve()
        )

        return FlextInfraUtilitiesCli.CliArgs(
            workspace=workspace_path,
            apply=apply_flag,
            diff=diff_flag,
            output_format=output_format,
            check=check_flag,
            project=project,
            projects=projects,
            class_to_analyze=class_to_analyze,
        )

    @staticmethod
    def run_cli(
        main_fn: Callable[[t.StrSequence | None], int],
        argv: t.StrSequence | None = None,
    ) -> int:
        try:
            FlextInfraUtilitiesBase.ensure_structlog_configured()
            return main_fn(argv)
        except SystemExit as exc:
            exit_value = exc.code
            if isinstance(exit_value, int):
                return exit_value
            if exit_value is None:
                return 0
            FlextInfraUtilitiesOutput.error(str(exit_value))
            return 1
        except Exception as exc:
            FlextInfraUtilitiesOutput.error(str(exc))
            return 1


__all__ = ["FlextInfraUtilitiesCli"]
