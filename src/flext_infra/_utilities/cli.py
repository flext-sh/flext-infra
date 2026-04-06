"""CLI argument parsing utilities for flext-infra commands.

Centralizes argument parser creation and argument resolution for all
flext_infra CLI commands, providing a consistent interface for workspace,
apply/dry-run, format, check, and project selection flags.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from argparse import ArgumentParser
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Annotated

from pydantic import Field

from flext_cli import FlextCliUtilities
from flext_infra import (
    FlextInfraUtilitiesCliShared,
    FlextInfraUtilitiesCliSubcommand,
    c,
    m,
    t,
)


class FlextInfraUtilitiesCli(FlextInfraUtilitiesCliShared):
    """Static facade for CLI argument parsing and resolution.

    Provides standardized argument parser creation and resolution for
    flext_infra commands, supporting optional flags for apply/dry-run,
    output format, check mode, and project selection.
    """

    @staticmethod
    def apply_option_json_schema_extra(schema: t.Infra.JsonDict) -> None:
        """Inject Typer dual-flag metadata using a Pydantic-supported hook."""
        schema["typer_param_decls"] = list(c.Infra.Cli.APPLY_OPTION_DECLS)

    class CliArgs(m.ContractModel):
        """Parsed CLI arguments with strict validation.

        Immutable model representing resolved command-line arguments,
        with optional fields for apply, format, check, and project selection.
        """

        workspace: Annotated[
            Path,
            Field(
                default_factory=Path.cwd, description="Workspace root directory path"
            ),
        ]
        apply: Annotated[bool, Field(description="Apply changes flag")] = False
        output_format: Annotated[str, Field(description="Output format")] = "text"
        check: Annotated[bool, Field(description="Check mode flag")] = False
        diff: Annotated[bool, Field(description="Show unified diff of changes")] = False
        projects: Annotated[
            list[str] | None,
            Field(description="Selected project names"),
        ] = None
        class_to_analyze: Annotated[
            str | None, Field(description="Class to analyze")
        ] = None

        @property
        def dry_run(self) -> bool:
            """Return True if not in apply mode (i.e., dry-run mode)."""
            return not self.apply

        def project_names(self) -> t.StrSequence | None:
            """Extract project names from repeated or comma-separated `--projects` flags.

            Returns:
                List of project names if any specified, else None.

            """
            return FlextCliUtilities.Cli.project_names_from_values(self.projects)

        def project_dirs(self) -> Sequence[Path] | None:
            """Convert project names to absolute directory paths under workspace.

            Uses project_names() to resolve projects, then prepends workspace root
            to each name to create full paths.

            Returns:
                List of Path objects (workspace / project_name) if projects specified.
                None if no projects were specified via --projects.

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
    ) -> t.Infra.Pair[
        t.Infra.CliArgumentParser, Mapping[str, t.Infra.CliArgumentParser]
    ]:
        """Create main parser with subcommands and shared flags."""
        return FlextInfraUtilitiesCliSubcommand.create_subcommand_parser(
            prog,
            description,
            subcommands=subcommands,
            flags=flags.to_dict() if flags is not None else None,
            subcommand_flags=subcommand_flags,
        )

    @staticmethod
    def create_parser(
        prog: str,
        description: str,
        *,
        flags: FlextInfraUtilitiesCli.SharedFlags | None = None,
    ) -> t.Infra.CliArgumentParser:
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
        parser: t.Infra.CliArgumentParser,
        argv: t.StrSequence | None = None,
        *,
        passthrough_subcommands: t.StrSequence | None = None,
    ) -> t.Infra.CliNamespace:
        """Parse and validate subcommand args against per-command shared flags."""
        return FlextInfraUtilitiesCliSubcommand.parse_subcommand_args(
            parser,
            argv,
            passthrough_subcommands=passthrough_subcommands,
        )

    @staticmethod
    def resolve(args: t.Infra.CliNamespace) -> FlextInfraUtilitiesCli.CliArgs:
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

        raw_projects = getattr(args, "projects", None)
        projects = FlextCliUtilities.Cli.project_names_from_values(raw_projects)

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
            projects=projects,
            class_to_analyze=class_to_analyze,
        )


__all__ = ["FlextInfraUtilitiesCli"]
