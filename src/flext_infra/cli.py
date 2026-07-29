"""Lightweight entrypoint for the canonical flext-infra command surface."""

from __future__ import annotations

import sys
from collections.abc import Sequence

from flext_infra._constants.cli import FlextInfraConstantsCli


class FlextInfraCli:
    """Select one exact command before importing its runtime dependencies."""

    help_flags = FlextInfraConstantsCli.HELP_FLAGS

    @staticmethod
    def _write_line(message: str) -> None:
        """Write one stable CLI help line."""
        sys.stdout.write(f"{message}\n")

    @classmethod
    def print_help(cls) -> None:
        """Display canonical groups without importing runtime facades."""
        cls._write_line("Usage: flext-infra <group> <command> [args...]")
        cls._write_line("Groups")
        for group, description in FlextInfraConstantsCli.CLI_GROUP_DESCRIPTIONS.items():
            cls._write_line(f"  {group:<16}{description}")

    @classmethod
    def print_group_help(cls, group: str) -> None:
        """Display canonical command descriptors without importing handlers."""
        from flext_infra.services.cli_routes import CliRouteService

        cls._write_line(f"Usage: flext-infra {group} <command> [args...]")
        cls._write_line("Commands")
        for command, description in CliRouteService.command_descriptions(group).items():
            cls._write_line(f"  {command:<28}{description}")

    @classmethod
    def _option_value(cls, args: Sequence[str], name: str) -> str | None:
        """Resolve one structured option value without importing handlers."""
        for index, argument in enumerate(args):
            if argument == name and index + 1 < len(args):
                return args[index + 1]
            prefix = f"{name}="
            if argument.startswith(prefix):
                return argument.removeprefix(prefix)
        return None

    @classmethod
    def _positional_command(cls, args: Sequence[str]) -> str | None:
        """Return the first positional token after structurally skipping options."""
        skip_value = False
        for argument in args:
            if skip_value:
                skip_value = False
                continue
            if argument in FlextInfraConstantsCli.SHARED_VALUE_FLAGS:
                skip_value = True
                continue
            if (
                argument in FlextInfraConstantsCli.SHARED_BOOL_FLAGS
                or argument in cls.help_flags
            ):
                continue
            if any(
                argument.startswith(f"{option}=")
                for option in FlextInfraConstantsCli.SHARED_VALUE_FLAGS
            ):
                continue
            if not argument.startswith("-"):
                return argument
        return None

    @classmethod
    def selected_command(cls, group: str, args: Sequence[str]) -> str | None:
        """Resolve the exact command before importing its implementation."""
        what = cls._option_value(args, "--what")
        if what is not None and group == "check":
            return "run"
        if what is not None and group == "validate":
            return what
        return cls._positional_command(args)

    def main(self, args: Sequence[str] | None = None) -> int:
        """Select and execute exactly one public command."""
        cli_args = list(args) if args is not None else sys.argv[1:]
        if not cli_args:
            self.print_help()
            return 1
        if cli_args[0] in self.help_flags:
            self.print_help()
            return 0
        group = cli_args[0]
        group_args = cli_args[1:]
        if group not in FlextInfraConstantsCli.CLI_GROUP_DESCRIPTIONS:
            self._write_line(f"unknown group '{group}'")
            self.print_help()
            return 1
        command = self.selected_command(group, group_args)
        if command is None:
            self.print_group_help(group)
            return 0 if any(flag in group_args for flag in self.help_flags) else 1

        from flext_infra.services.cli_routes import CliRouteService

        if command not in CliRouteService.route_names(group):
            self._write_line(f"unknown command '{command}' for group '{group}'")
            self.print_group_help(group)
            return 2

        from flext_infra.services.cli_dispatch import CliDispatchService

        return CliDispatchService().execute_selection(group, command, group_args)


def main(args: Sequence[str] | None = None) -> int:
    """Run the canonical flext-infra CLI."""
    return FlextInfraCli().main(args)


def docs_main(args: Sequence[str] | None = None) -> int:
    """Run the docs group directly (``flext-docs`` == ``flext-infra docs``)."""
    cli_args = list(args) if args is not None else sys.argv[1:]
    return FlextInfraCli().main(["docs", *cli_args])


__all__: list[str] = ["FlextInfraCli", "docs_main", "main"]
