"""Public command dispatch for the composed flext-infra CLI."""

from __future__ import annotations

import sys
from typing import TYPE_CHECKING

from flext_infra.constants import c
from flext_infra.models import m
from flext_infra.protocols import p
from flext_infra.services.cli_transaction import CliTransactionService
from flext_infra.typings import t
from flext_infra.utilities import u

if TYPE_CHECKING:
    from flext_infra import p


class CliDispatchService(CliTransactionService):
    """Dispatch public command groups through their typed route models."""

    def main(self, args: t.StrSequence | None = None) -> int:
        """Run the centralized dispatcher."""
        u.ensure_structlog_configured()
        cli_args = list(args) if args is not None else sys.argv[1:]
        if not cli_args:
            self.print_help()
            return 1
        if cli_args[0] in self.help_flags:
            self.print_help()
            return 0
        group, group_args = cli_args[0], cli_args[1:]
        if group not in c.Infra.CLI_GROUP_DESCRIPTIONS:
            self.display_message(f"unknown group '{group}'", c.Cli.MessageTypes.ERROR)
            self.print_help()
            return 1
        transaction_result = self.run_worktree_transaction(group, group_args)
        if transaction_result is not None:
            return transaction_result
        return self.run_group(group, group_args)

    def print_help(self) -> None:
        """Display the canonical command groups."""
        self.display_message(
            "Usage: flext-infra <group> [subcommand] [args...]", c.Cli.MessageTypes.INFO
        )
        self.display_message("Groups", c.Cli.MessageTypes.INFO)
        for group in sorted(c.Infra.CLI_GROUP_DESCRIPTIONS):
            self.display_message(
                f"  {group:<16}{c.Infra.CLI_GROUP_DESCRIPTIONS[group]}",
                c.Cli.MessageTypes.INFO,
            )

    def normalize_group_args(self, args: t.StrSequence) -> list[str]:
        """Normalize group arguments."""
        normalized = t.Cli.STR_SEQUENCE_ADAPTER.validate_python(
            u.Cli.reorder_prefixed_options(
                args,
                bool_options=tuple(self.shared_bool_flags),
                value_options=tuple(self.shared_value_flags),
            )
        )
        return list(normalized)

    def register_group_commands(self, group: str, app: p.Cli.Application) -> None:
        """Register one group's command routes."""
        self.register_result_routes(app, self.group_commands[group])

    def run_group(self, group: str, args: t.StrSequence) -> int:
        """Execute one registered flext-cli command group."""
        app = self.create_app_with_common_params(
            name=f"{self.app_name} {group}",
            help_text=c.Infra.CLI_GROUP_DESCRIPTIONS[group],
        )
        self.register_group_commands(group, app)
        normalized_args = self.normalize_group_args(args)
        if not normalized_args:
            _ = self.execute_app(
                app, prog_name=f"{self.app_name} {group}", args=["--help"]
            )
            return 1
        result = self.execute_app(
            app, prog_name=f"{self.app_name} {group}", args=normalized_args
        )
        if result.success:
            return 0
        if result.error_code == c.Infra.PROCESS_EXIT_ERROR_CODE:
            process_exit = m.Infra.ProcessExit.model_validate(result.error_data)
            exit_code: int = process_exit.exit_code
            return exit_code
        error_message = result.error
        if error_message:
            self.display_message(error_message, c.Cli.MessageTypes.ERROR)
        return 2 if error_message and u.Cli.cli_usage_error(error_message) else 1


__all__: list[str] = ["CliDispatchService"]
