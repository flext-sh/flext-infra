"""CLI argument parsing utilities for flext-infra commands.

Centralizes argument parser creation and argument resolution for all
flext_infra CLI commands, providing a consistent interface for workspace,
apply/dry-run, format, check, and project selection flags.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import sys
from argparse import SUPPRESS, ArgumentParser, Namespace
from collections.abc import Callable, Mapping, MutableMapping, MutableSequence, Sequence
from pathlib import Path

import orjson
from flext_core import FlextRuntime, r
from pydantic import BaseModel

from flext_infra import FlextInfraUtilitiesDiscovery, m, output, t


class FlextInfraUtilitiesCli:
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

        @property
        def mode_label(self) -> str:
            """Return human-readable mode label."""
            return "apply" if self.apply else "dry-run"

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
    def _shared_flag_options(
        *,
        include_apply: bool = True,
        include_diff: bool | None = None,
        include_format: bool = False,
        include_check: bool = False,
        include_project: bool = False,
    ) -> MutableMapping[str, bool]:
        """Resolve shared parser options with backward-compatible diff behavior."""
        resolved_include_diff = include_apply if include_diff is None else include_diff
        return {
            "include_apply": include_apply,
            "include_diff": resolved_include_diff,
            "include_format": include_format,
            "include_check": include_check,
            "include_project": include_project,
        }

    @staticmethod
    def _merge_shared_flag_options(
        base_options: Mapping[str, bool],
        overrides: Mapping[str, bool] | None,
    ) -> MutableMapping[str, bool]:
        """Merge per-subcommand shared-flag overrides onto base options."""
        merged: MutableMapping[str, bool] = dict(base_options)
        if overrides is None:
            return merged
        unknown_keys = set(overrides) - set(base_options)
        if unknown_keys:
            msg = ", ".join(sorted(unknown_keys))
            error_msg = f"Unknown shared flag override(s): {msg}"
            raise ValueError(error_msg)
        for key, value in overrides.items():
            merged[key] = value
        return merged

    @staticmethod
    def _union_shared_flag_options(
        options: Sequence[Mapping[str, bool]],
    ) -> MutableMapping[str, bool]:
        """Compute the union of enabled shared flags across subcommands."""
        union = FlextInfraUtilitiesCli._shared_flag_options(
            include_apply=False,
            include_diff=False,
            include_format=False,
            include_check=False,
            include_project=False,
        )
        for option_set in options:
            for key, value in option_set.items():
                union[key] = union[key] or value
        return union

    @staticmethod
    def _shared_option_tokens(options: Mapping[str, bool]) -> Sequence[str]:
        """Return CLI option tokens enabled by the given shared-flag config."""
        tokens: MutableSequence[str] = []
        if options.get("include_apply", False):
            tokens.extend(["--dry-run", "--apply"])
        if options.get("include_diff", False):
            tokens.append("--diff")
        if options.get("include_format", False):
            tokens.append("--format")
        if options.get("include_check", False):
            tokens.append("--check")
        if options.get("include_project", False):
            tokens.extend(["--project", "--projects"])
        return tokens

    @staticmethod
    def _add_shared_flags(
        parser: ArgumentParser,
        *,
        include_apply: bool = True,
        include_diff: bool | None = None,
        include_format: bool = False,
        include_check: bool = False,
        include_project: bool = False,
        suppress_defaults: bool = False,
    ) -> None:
        """Attach standard shared CLI flags to an existing parser."""
        options = FlextInfraUtilitiesCli._shared_flag_options(
            include_apply=include_apply,
            include_diff=include_diff,
            include_format=include_format,
            include_check=include_check,
            include_project=include_project,
        )
        resolved_include_apply = options["include_apply"]
        resolved_include_diff = options["include_diff"]
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
        if options["include_format"]:
            _ = parser.add_argument(
                "--format",
                dest="output_format",
                choices=["json", "text"],
                default=default_text,
                help="Output format (default: text)",
            )
        if options["include_check"]:
            _ = parser.add_argument(
                "--check",
                action="store_true",
                default=default_bool,
                help="Run in check mode",
            )
        if options["include_project"]:
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
        *,
        include_apply: bool = True,
        include_diff: bool | None = None,
        include_format: bool = False,
        include_check: bool = False,
        include_project: bool = False,
        suppress_defaults: bool = False,
    ) -> ArgumentParser:
        """Create base argument parser with optional standard flags.

        Builds a reusable ArgumentParser with common CLI flags that can be
        selectively enabled via booleans. Always includes --workspace flag.

        This is used as parent parser for primary commands and subcommands,
        allowing consistent flag handling across all flext_infra CLI tools.

        Args:
            include_apply: Add --dry-run/--apply mutually exclusive group (default True).
            include_format: Add --format choice (json|text) (default False).
            include_check: Add --check boolean flag (default False).
            include_project: Add --project and --projects string arguments (default False).

        Returns:
            ArgumentParser configured with selected flags, add_help=False so parent
            parser can build top-level help without duplication.

        """
        base = ArgumentParser(add_help=False)
        FlextInfraUtilitiesCli._add_shared_flags(
            base,
            include_apply=include_apply,
            include_diff=include_diff,
            include_format=include_format,
            include_check=include_check,
            include_project=include_project,
            suppress_defaults=suppress_defaults,
        )
        return base

    @staticmethod
    def create_subcommand_parser(
        prog: str,
        description: str,
        *,
        subcommands: t.StrMapping,
        include_apply: bool = True,
        include_diff: bool | None = None,
        include_format: bool = False,
        include_check: bool = False,
        include_project: bool = False,
        subcommand_flags: Mapping[str, Mapping[str, bool]] | None = None,
    ) -> t.Infra.Pair[ArgumentParser, Mapping[str, ArgumentParser]]:
        """Create main parser with subcommands and shared flags.

        Builds an ArgumentParser supporting multiple subcommands (e.g., "check",
        "fix", "report"). Each subcommand inherits shared flags from parent.

        Structure:
            flext-cmd [shared-flags] subcommand [subcommand-flags]

        Example:
            flext-infra --workspace /path check --dry-run

        Args:
            prog: Program name for parser (e.g., "flext-infra").
            description: Help text for main parser.
            subcommands: Dict mapping subcommand names to help strings.
                Used to build subparsers dynamically.
            include_apply: Pass to shared flags (add --dry-run/--apply group).
            include_format: Pass to shared flags (add --format choice).
            include_check: Pass to shared flags (add --check boolean).
            include_project: Pass to shared flags (add --project/--projects).

        Returns:
            Tuple of (main_parser, subcommand_parsers_dict) where:
            - main_parser: Top-level ArgumentParser accepting shared flags + subcommand
            - subcommand_parsers_dict: Dict[command_name, ArgumentParser] for each subcommand
              Each subcommand parser inherits shared flags from parent via MRO.

        """
        base_options = FlextInfraUtilitiesCli._shared_flag_options(
            include_apply=include_apply,
            include_diff=include_diff,
            include_format=include_format,
            include_check=include_check,
            include_project=include_project,
        )
        command_options: MutableMapping[str, MutableMapping[str, bool]] = {}
        for command in subcommands:
            overrides = subcommand_flags.get(command) if subcommand_flags else None
            command_options[command] = (
                FlextInfraUtilitiesCli._merge_shared_flag_options(
                    base_options,
                    overrides,
                )
            )
        root_options = FlextInfraUtilitiesCli._union_shared_flag_options(
            [base_options, *command_options.values()],
        )
        root_shared_tokens = tuple(
            FlextInfraUtilitiesCli._shared_option_tokens(root_options),
        )
        shared = FlextInfraUtilitiesCli._shared_flags_parser(**root_options)
        parser = ArgumentParser(prog=prog, description=description, parents=[shared])
        subparsers = parser.add_subparsers(dest="command")
        command_parsers: MutableMapping[str, ArgumentParser] = {}
        for command, command_help in subcommands.items():
            command_shared = FlextInfraUtilitiesCli._shared_flags_parser(
                **command_options[command],
                suppress_defaults=True,
            )
            command_parsers[command] = subparsers.add_parser(
                command,
                help=command_help,
                parents=[command_shared],
            )
            command_parsers[command].set_defaults(
                _allowed_shared_option_tokens=tuple(
                    FlextInfraUtilitiesCli._shared_option_tokens(
                        command_options[command],
                    ),
                ),
                _root_shared_option_tokens=root_shared_tokens,
            )
        return parser, command_parsers

    @staticmethod
    def create_parser(
        prog: str,
        description: str,
        *,
        include_apply: bool = True,
        include_diff: bool | None = None,
        include_format: bool = False,
        include_check: bool = False,
        include_project: bool = False,
    ) -> ArgumentParser:
        """Create a standard ArgumentParser with common CLI flags.

        Args:
            prog: Program name for the parser.
            description: Description of the command.
            include_apply: If True, add --dry-run/--apply mutually exclusive group.
            include_format: If True, add --format flag for output format selection.
            include_check: If True, add --check flag for validation mode.
            include_project: If True, add --project and --projects flags.

        Returns:
            Configured ArgumentParser instance.

        """
        parser = ArgumentParser(prog=prog, description=description)
        FlextInfraUtilitiesCli._add_shared_flags(
            parser,
            include_apply=include_apply,
            include_diff=include_diff,
            include_format=include_format,
            include_check=include_check,
            include_project=include_project,
        )
        return parser

    @staticmethod
    def _extract_used_shared_options(
        argv: t.StrSequence,
        candidate_tokens: Sequence[str],
    ) -> Sequence[str]:
        """Extract shared-option tokens explicitly provided on the CLI."""
        used: MutableSequence[str] = []
        known_tokens = set(candidate_tokens)
        for token in argv:
            normalized = token.split("=", 1)[0]
            if normalized not in known_tokens or normalized in used:
                continue
            used.append(normalized)
        return used

    @staticmethod
    def _coerce_option_tokens(
        value: tuple[str, ...] | list[str] | None,
    ) -> t.StrSequence:
        """Normalize argparse metadata into a concrete list of option tokens."""
        if value is None:
            return []
        return list(value)

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
        passthrough_subcommands: Sequence[str] | None = None,
    ) -> Namespace:
        """Parse and validate subcommand args against per-command shared flags."""
        args, unknown_args = parser.parse_known_args(argv)
        raw_argv = list(argv) if argv is not None else sys.argv[1:]
        allowed_tokens = FlextInfraUtilitiesCli._coerce_option_tokens(
            getattr(args, "_allowed_shared_option_tokens", None),
        )
        root_tokens = FlextInfraUtilitiesCli._coerce_option_tokens(
            getattr(args, "_root_shared_option_tokens", None),
        )
        if not root_tokens:
            return args
        used_tokens = FlextInfraUtilitiesCli._extract_used_shared_options(
            raw_argv,
            root_tokens,
        )
        allowed_token_set = set(allowed_tokens)
        disallowed = [token for token in used_tokens if token not in allowed_token_set]
        if not disallowed:
            passthrough = set(passthrough_subcommands or ())
            command = getattr(args, "command", None)
            command_label = str(command) if isinstance(command, str) else ""
            if unknown_args:
                if command_label in passthrough:
                    setattr(args, "_unknown_args", tuple(unknown_args))
                    return args
                parser.error(f"unrecognized arguments: {' '.join(unknown_args)}")
            return args
        command = getattr(args, "command", None)
        command_label = (
            str(command) if isinstance(command, str) and command else "subcommand"
        )
        parser.error(
            f"unrecognized arguments for '{command_label}': {' '.join(disallowed)}",
        )
        return args

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
            FlextRuntime.ensure_structlog_configured()
            return main_fn(argv)
        except SystemExit as exc:
            exit_value = exc.code
            if isinstance(exit_value, int):
                return exit_value
            if exit_value is None:
                return 0
            output.error(str(exit_value))
            return 1
        except Exception as exc:
            output.error(str(exc))
            return 1

    @staticmethod
    def exit_code[T](
        result: r[T],
        *,
        failure_msg: str = "operation failed",
    ) -> int:
        if result.is_success:
            return 0
        output.error(result.error or failure_msg)
        return 1

    @staticmethod
    def iter_projects(
        cli: FlextInfraUtilitiesCli.CliArgs,
    ) -> r[Sequence[m.Infra.ProjectInfo]]:
        """Discover, filter, and sort workspace projects.

        Centralizes the discover_projects -> filter -> sort pattern
        that was previously duplicated across 13 call sites.

        Args:
            cli: Parsed CLI arguments with workspace and project filters.

        Returns:
            Sorted, filtered list of project info models.

        """
        result = FlextInfraUtilitiesDiscovery.discover_projects(cli.workspace)
        if result.is_failure:
            return r[Sequence[m.Infra.ProjectInfo]].fail(
                result.error or "discovery failed",
            )
        projects = list(result.value)
        filter_names = cli.project_names()
        if filter_names is not None:
            name_set = set(filter_names)
            projects = [p for p in projects if p.name in name_set]
        return r[Sequence[m.Infra.ProjectInfo]].ok(
            sorted(projects, key=lambda p: p.name),
        )

    @staticmethod
    def emit(
        data: BaseModel | Mapping[str, t.Scalar],
        *,
        text_fn: Callable[[BaseModel | Mapping[str, t.Scalar]], str] | None = None,
        cli: FlextInfraUtilitiesCli.CliArgs,
    ) -> None:
        """Emit structured data in the format requested by CLI flags.

        Centralizes the JSON-vs-text output branching that was previously
        duplicated across multiple CLI commands.

        Args:
            data: Pydantic model or scalar mapping to emit.
            text_fn: Optional formatter for text mode. Receives data, returns string.
            cli: Parsed CLI arguments with output_format.

        """
        if cli.output_format == "json":
            if isinstance(data, BaseModel):
                sys.stdout.write(data.model_dump_json())
            else:
                sys.stdout.write(orjson.dumps(dict(data)).decode())
            sys.stdout.write("\n")
        elif text_fn is not None:
            output.write(text_fn(data))
        else:
            output.write(str(data))


__all__ = ["FlextInfraUtilitiesCli"]
