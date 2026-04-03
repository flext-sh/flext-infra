"""CLI argument parsing utilities for flext-infra commands.

Centralizes argument parser creation and argument resolution for all
flext_infra CLI commands, providing a consistent interface for workspace,
apply/dry-run, format, check, and project selection flags.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from argparse import SUPPRESS, ArgumentParser, Namespace
from collections.abc import Callable, Mapping, MutableSequence, Sequence
from pathlib import Path

from pydantic import model_validator

from flext_core import u
from flext_infra import FlextInfraUtilitiesOutput, m, t


class _SharedFlags(m.FrozenStrictModel):
    """Bundled CLI flag configuration for shared parser options."""

    include_apply: bool = True
    include_diff: bool = True
    include_format: bool = False
    include_check: bool = False
    include_project: bool = False

    @model_validator(mode="before")
    @classmethod
    def _resolve_include_diff(
        cls,
        data: t.OptionalBoolMapping | _SharedFlags,
    ) -> t.OptionalBoolMapping | _SharedFlags:
        if u.is_mapping(data) and (
            "include_diff" not in data or data.get("include_diff") is None
        ):
            resolved: t.MutableOptionalBoolMapping = dict(data)
            resolved["include_diff"] = data.get("include_apply", True)
            return resolved
        return data

    def to_dict(self) -> t.MutableBoolMapping:
        return {
            "include_apply": self.include_apply,
            "include_diff": self.include_diff,
            "include_format": self.include_format,
            "include_check": self.include_check,
            "include_project": self.include_project,
        }

    @staticmethod
    def from_dict(data: t.BoolMapping) -> _SharedFlags:
        return _SharedFlags.model_validate(data)


class FlextInfraUtilitiesCli:
    """Static facade for CLI argument parsing and resolution.

    Provides standardized argument parser creation and resolution for
    flext_infra commands, supporting optional flags for apply/dry-run,
    output format, check mode, and project selection.
    """

    SharedFlags = _SharedFlags

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
    def _add_shared_flags(
        parser: ArgumentParser,
        flags: _SharedFlags,
        *,
        suppress_defaults: bool = False,
    ) -> None:
        resolved_include_apply = flags.include_apply
        resolved_include_diff = flags.include_diff
        default_path = SUPPRESS if suppress_defaults else Path.cwd()
        default_bool = SUPPRESS if suppress_defaults else False
        default_text = SUPPRESS if suppress_defaults else "text"
        default_project = SUPPRESS if suppress_defaults else None
        _ = parser.add_argument(
            "--workspace",
            type=Path,
            default=default_path,
            help="Workspace root directory (default: cwd)",
        )
        if resolved_include_apply or resolved_include_diff:
            mode = parser.add_mutually_exclusive_group(required=False)
            if resolved_include_apply:
                _ = mode.add_argument(
                    "--dry-run",
                    action="store_true",
                    default=default_bool,
                    help="Plan/Scan only",
                )
                _ = mode.add_argument(
                    "--apply",
                    action="store_true",
                    default=default_bool,
                    help="Apply changes",
                )
            if resolved_include_diff:
                _ = mode.add_argument(
                    "--diff",
                    action="store_true",
                    default=default_bool,
                    help="Show unified diff of changes without applying",
                )
        if flags.include_format:
            _ = parser.add_argument(
                "--format",
                dest="output_format",
                choices=["json", "text"],
                default=default_text,
                help="Output format (default: text)",
            )
        if flags.include_check:
            _ = parser.add_argument(
                "--check",
                action="store_true",
                default=default_bool,
                help="Run in check mode",
            )
        if flags.include_project:
            _ = parser.add_argument(
                "--project",
                type=str,
                default=default_project,
                help="Single project to process",
            )
            _ = parser.add_argument(
                "--projects",
                type=str,
                default=default_project,
                help="Multiple projects (comma-separated or glob pattern)",
            )

    @staticmethod
    def _shared_flags_parser(
        flags: _SharedFlags,
        *,
        suppress_defaults: bool = False,
    ) -> ArgumentParser:
        base = ArgumentParser(add_help=False)
        FlextInfraUtilitiesCli._add_shared_flags(
            base,
            flags,
            suppress_defaults=suppress_defaults,
        )
        return base

    @staticmethod
    def shared_flags_parser(
        flags: _SharedFlags,
        *,
        suppress_defaults: bool = False,
    ) -> ArgumentParser:
        """Build the shared-flags parser exposed to sibling CLI helpers."""
        return FlextInfraUtilitiesCli._shared_flags_parser(
            flags,
            suppress_defaults=suppress_defaults,
        )

    @staticmethod
    def create_subcommand_parser(
        prog: str,
        description: str,
        *,
        subcommands: t.StrMapping,
        flags: _SharedFlags | None = None,
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
    def create_parser(
        prog: str,
        description: str,
        *,
        flags: _SharedFlags | None = None,
    ) -> ArgumentParser:
        """Create a standard ArgumentParser with common CLI flags.

        Args:
            prog: Program name for the parser.
            description: Description of the command.
            flags: Bundled flag configuration. Defaults to _SharedFlags() if None.

        Returns:
            Configured ArgumentParser instance.

        """
        resolved_flags = flags or _SharedFlags()
        parser = ArgumentParser(prog=prog, description=description)
        FlextInfraUtilitiesCli._add_shared_flags(parser, resolved_flags)
        return parser

    @staticmethod
    def project_names_from_values(
        *values: str | t.StrSequence | None,
    ) -> t.StrSequence | None:
        """Normalize project selectors from repeated or comma-separated CLI values."""
        names: MutableSequence[str] = []
        for value in values:
            if value is None:
                continue
            raw_values = [value] if isinstance(value, str) else list(value)
            for raw_value in raw_values:
                names.extend(
                    item.strip() for item in raw_value.split(",") if item.strip()
                )
        return names or None

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
            u.ensure_structlog_configured()
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


from flext_infra._utilities.cli_subcommand import FlextInfraUtilitiesCliSubcommand

__all__ = ["FlextInfraUtilitiesCli"]
