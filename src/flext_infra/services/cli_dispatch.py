"""Public command dispatch for the composed flext-infra CLI."""

from __future__ import annotations

import sys
from typing import TYPE_CHECKING

from flext_core import r
from flext_infra import c, t, u
from flext_infra.check.workspace_check import FlextInfraWorkspaceChecker
from flext_infra.services.cli_transaction import CliTransactionService

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
        return u.Cli.reorder_prefixed_options(
            args,
            bool_options=tuple(self.shared_bool_flags),
            value_options=tuple(self.shared_value_flags),
        )

    def register_group_commands(self, group: str, app: p.Cli.Application) -> None:
        """Register one group's command routes."""
        self.register_result_routes(app, self.group_commands[group])

    @staticmethod
    def split_what(args: t.StrSequence) -> tuple[str | None, list[str]]:
        """Extract the ``--what`` value and return the remaining arguments."""
        remaining: list[str] = []
        what: str | None = None
        index = 0
        items = list(args)
        while index < len(items):
            arg = items[index]
            if arg == "--what" and index + 1 < len(items):
                what = items[index + 1]
                index += 2
                continue
            if arg.startswith("--what="):
                what = arg.split("=", 1)[1]
                index += 1
                continue
            remaining.append(arg)
            index += 1
        return what, remaining

    def translate_what(self, group: str, args: t.StrSequence) -> p.Result[list[str]]:
        """Map ``--what <phase>`` onto the canonical command selector."""
        what, remaining = self.split_what(args)
        if what is None:
            return r[list[str]].ok(list(args))
        if group == c.Infra.CLI_GROUP_CHECK:
            gate_check = FlextInfraWorkspaceChecker.resolve_gates([what])
            if gate_check.failure:
                return r[list[str]].fail(gate_check.error or f"unknown gate '{what}'")
            check_routes = {route.name for route in self.group_commands[group]}
            has_subcommand = bool(remaining) and remaining[0] in check_routes
            prefix = (
                list(remaining) if has_subcommand else [c.Infra.VERB_RUN, *remaining]
            )
            return r[list[str]].ok([*prefix, "--gates", what])
        if group == c.Infra.CLI_GROUP_VALIDATE:
            valid_names = {route.name for route in self.group_commands[group]}
            if what not in valid_names:
                return r[list[str]].fail(f"unknown validator '{what}'")
            return r[list[str]].ok([what, *remaining])
        if group == c.Infra.CLI_GROUP_CODEGEN and remaining[:1] == ["conform"]:
            return r[list[str]].ok([*remaining, "--what", what])
        return r[list[str]].fail(f"--what is not supported for group '{group}'")

    def run_group(self, group: str, args: t.StrSequence) -> int:
        """Execute one registered flext-cli command group."""
        app = self.create_app_with_common_params(
            name=f"{self.app_name} {group}",
            help_text=c.Infra.CLI_GROUP_DESCRIPTIONS[group],
        )
        self.register_group_commands(group, app)
        what_result = self.translate_what(group, args)
        if what_result.failure:
            self.display_message(
                what_result.error or "invalid --what phase", c.Cli.MessageTypes.ERROR
            )
            return int(c.Infra.ScriptExitCode.USAGE)
        normalized_args = self.normalize_group_args(what_result.value)
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
        error_message = result.error
        if error_message:
            self.display_message(error_message, c.Cli.MessageTypes.ERROR)
        return 2 if error_message and u.Cli.cli_usage_error(error_message) else 1


__all__: list[str] = ["CliDispatchService"]
