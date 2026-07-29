"""Lightweight entrypoint for the canonical flext-infra command surface."""

from __future__ import annotations

import sys
from typing import TYPE_CHECKING

from flext_infra.cli_registry import (
    CLI_COMMAND_DESCRIPTIONS,
    CLI_GROUP_DESCRIPTIONS,
    CLI_GROUP_WHAT_STRATEGIES,
    CLI_OPTION_ARITIES,
)

if TYPE_CHECKING:
    from flext_infra import t


class FlextInfraCli:
    """Select one exact command before importing its runtime dependencies."""

    help_flags = frozenset(
        name for name, arity in CLI_OPTION_ARITIES.items() if arity == 0
    ).intersection({"-h", "--help"})

    @staticmethod
    def _write_line(message: str) -> None:
        """Write one stable CLI help line."""
        sys.stdout.write(f"{message}\n")

    @classmethod
    def print_help(cls) -> None:
        """Display canonical groups without importing runtime facades."""
        cls._write_line("Usage: flext-infra <group> <command> [args...]")
        cls._write_line("Groups")
        for group, description in CLI_GROUP_DESCRIPTIONS.items():
            cls._write_line(f"  {group:<16}{description}")

    @classmethod
    def print_group_help(cls, group: str) -> None:
        """Display canonical command descriptors without importing handlers."""
        cls._write_line(f"Usage: flext-infra {group} <command> [args...]")
        cls._write_line("Commands")
        for command, description in CLI_COMMAND_DESCRIPTIONS[group].items():
            cls._write_line(f"  {command:<28}{description}")

    @classmethod
    def print_command_help(cls, group: str, command: str) -> None:
        """Display one command's generated help without loading its route."""
        cls._write_line(f"Usage: flext-infra {group} {command} [args...]")
        cls._write_line(CLI_COMMAND_DESCRIPTIONS[group][command])

    @classmethod
    def _option_value(cls, args: t.StrSequence, name: str) -> str | None:
        """Resolve one structured option value without importing handlers."""
        for index, argument in enumerate(args):
            if argument == name and index + 1 < len(args):
                return args[index + 1]
            prefix = f"{name}="
            if argument.startswith(prefix):
                return argument.removeprefix(prefix)
        return None

    @classmethod
    def _positional_command(cls, args: t.StrSequence) -> str | None:
        """Return the first positional token after structurally skipping options."""
        values_to_skip = 0
        for argument in args:
            if values_to_skip:
                values_to_skip -= 1
                continue
            option_name = argument.partition("=")[0]
            arity = CLI_OPTION_ARITIES.get(option_name)
            if arity is not None:
                values_to_skip = arity if "=" not in argument else 0
                continue
            if not argument.startswith("-"):
                return argument
        return None

    @classmethod
    def selected_command(cls, group: str, args: t.StrSequence) -> str | None:
        """Resolve the exact command before importing its implementation."""
        what = cls._option_value(args, "--what")
        strategy = CLI_GROUP_WHAT_STRATEGIES[group]
        if what is not None and strategy == "check-run":
            return "run"
        if what is not None and strategy == "validate-command":
            return what
        return cls._positional_command(args)

    def main(self, args: t.StrSequence | None = None) -> int:
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
        if group not in CLI_GROUP_DESCRIPTIONS:
            self._write_line(f"unknown group '{group}'")
            self.print_help()
            return 1
        command = self.selected_command(group, group_args)
        if command is None:
            self.print_group_help(group)
            return 0 if any(flag in group_args for flag in self.help_flags) else 1

        if command not in CLI_COMMAND_DESCRIPTIONS[group]:
            self._write_line(f"unknown command '{command}' for group '{group}'")
            self.print_group_help(group)
            return 2
        if any(flag in group_args for flag in self.help_flags):
            self.print_command_help(group, command)
            return 0

        from flext_infra.services.cli_dispatch import CliDispatchService

        return CliDispatchService().execute_selection(group, command, group_args)


def main(args: t.StrSequence | None = None) -> int:
    """Run the canonical flext-infra CLI."""
    return FlextInfraCli().main(args)


def docs_main(args: t.StrSequence | None = None) -> int:
    """Run the docs group directly (``flext-docs`` == ``flext-infra docs``)."""
    cli_args = list(args) if args is not None else sys.argv[1:]
    return FlextInfraCli().main(["docs", *cli_args])


__all__: list[str] = ["FlextInfraCli", "docs_main", "main"]
