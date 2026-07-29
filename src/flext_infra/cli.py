"""Lightweight entrypoint for the canonical flext-infra command surface."""

from __future__ import annotations

import sys
from collections.abc import Sequence

from flext_infra.cli_catalog import CliCatalog


def _write_line(message: str) -> None:
    sys.stdout.write(f"{message}\n")


class FlextInfraCli:
    """Select one exact command before importing its runtime dependencies."""

    @staticmethod
    def print_help() -> None:
        """Display canonical groups without importing runtime facades."""
        _write_line("Usage: flext-infra <group> <command> [args...]")
        _write_line("Groups")
        for group, description in CliCatalog.group_descriptions.items():
            _write_line(f"  {group:<16}{description}")

    @staticmethod
    def print_group_help(group: str) -> None:
        """Display canonical command descriptors without importing handlers."""
        _write_line(f"Usage: flext-infra {group} <command> [args...]")
        _write_line("Commands")
        for command, description in CliCatalog.command_descriptions[group].items():
            _write_line(f"  {command:<28}{description}")

    def main(self, args: Sequence[str] | None = None) -> int:
        """Select and execute exactly one public command."""
        cli_args = list(args) if args is not None else sys.argv[1:]
        if not cli_args:
            self.print_help()
            return 1
        if cli_args[0] in CliCatalog.help_flags:
            self.print_help()
            return 0
        group = cli_args[0]
        group_args = cli_args[1:]
        if group not in CliCatalog.group_descriptions:
            _write_line(f"unknown group '{group}'")
            self.print_help()
            return 1
        command = CliCatalog.selected_command(group, group_args)
        if command is None:
            self.print_group_help(group)
            return 0 if any(flag in group_args for flag in CliCatalog.help_flags) else 1
        if command not in CliCatalog.command_descriptions[group]:
            _write_line(f"unknown command '{command}' for group '{group}'")
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
