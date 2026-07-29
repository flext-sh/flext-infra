"""Public command dispatch for the composed flext-infra CLI."""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_infra.services.cli_transaction import CliTransactionService

if TYPE_CHECKING:
    from flext_infra import p, t


class CliDispatchService(CliTransactionService):
    """Dispatch public command groups through their typed route models."""

    def execute_selection(
        self, group: str, command: str, args: t.StrSequence
    ) -> int:
        """Execute the exact command selected by the lightweight entrypoint."""
        transaction_result = self.run_worktree_transaction(group, command, args)
        if transaction_result is not None:
            return transaction_result
        return self.run_group(group, command, args)

    def normalize_group_args(self, args: t.StrSequence) -> list[str]:
        """Normalize group arguments."""
        from flext_cli import u
        from flext_infra import t

        normalized = t.Cli.STR_SEQUENCE_ADAPTER.validate_python(
            u.Cli.reorder_prefixed_options(
                args,
                bool_options=tuple(self.shared_bool_flags),
                value_options=tuple(self.shared_value_flags),
            )
        )
        return list(normalized)

    def register_group_commands(
        self, group: str, command: str | None, app: p.Cli.Application
    ) -> None:
        """Register only the selected group's selected command route."""
        self.register_result_routes(app, self.routes_for(group, command))

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
        from flext_core import r

        what, remaining = self.split_what(args)
        if what is None:
            return r[list[str]].ok(list(args))

        from flext_infra import c

        if group == c.Infra.CLI_GROUP_CHECK:
            from flext_infra.check.workspace_check import FlextInfraWorkspaceChecker

            gate_check = FlextInfraWorkspaceChecker.resolve_gates([what])
            if gate_check.failure:
                return r[list[str]].fail(gate_check.error or f"unknown gate '{what}'")
            check_routes = self.route_names(group)
            has_subcommand = bool(remaining) and remaining[0] in check_routes
            prefix = (
                list(remaining) if has_subcommand else [c.Infra.VERB_RUN, *remaining]
            )
            return r[list[str]].ok([*prefix, "--gates", what])
        if group == c.Infra.CLI_GROUP_VALIDATE:
            valid_names = self.route_names(group)
            if what not in valid_names:
                return r[list[str]].fail(f"unknown validator '{what}'")
            return r[list[str]].ok([what, *remaining])
        if group == c.Infra.CLI_GROUP_CODEGEN and remaining[:1] == ["conform"]:
            return r[list[str]].ok([*remaining, "--what", what])
        return r[list[str]].fail(f"--what is not supported for group '{group}'")

    def run_group(self, group: str, command: str, args: t.StrSequence) -> int:
        """Execute one registered flext-cli command group."""
        from flext_cli import u
        from flext_infra import c, m

        what_result = self.translate_what(group, args)
        if what_result.failure:
            self.display_message(
                what_result.error or "invalid --what phase", c.Cli.MessageTypes.ERROR
            )
            return int(c.Infra.ScriptExitCode.USAGE)
        normalized_args = self.normalize_group_args(what_result.value)
        app = self.create_app_with_common_params(
            name=f"{self.app_name} {group}",
            help_text=c.Infra.CLI_GROUP_DESCRIPTIONS[group],
        )
        self.register_group_commands(group, command, app)
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
