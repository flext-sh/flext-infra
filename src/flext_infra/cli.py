"""CLI entrypoint for the canonical flext-infra command surface."""

from __future__ import annotations

import sys
from typing import ClassVar

from flext_cli import cli as cli_facade, p as cli_p
from flext_core import r
from flext_infra._constants.cli_routes import (
    CODEGEN_ROUTES as _ROUTES_CODEGEN,
    VALIDATE_ROUTES as _ROUTES_VALIDATE,
    WORKSPACE_ROUTES as _ROUTES_WORKSPACE,
)
from flext_infra.check.workspace_check import FlextInfraWorkspaceChecker
from flext_infra.constants import c
from flext_infra.models import m
from flext_infra.protocols import p
from flext_infra.typings import t
from flext_infra.utilities import u


class FlextInfraCli(type(cli_facade)):
    """Single CLI entry surface for every flext-infra command group."""

    app_name: ClassVar[str] = "flext-infra"
    _HELP_FLAGS: ClassVar[frozenset[str]] = frozenset({"-h", "--help"})
    _SHARED_BOOL_FLAGS: ClassVar[frozenset[str]] = c.Infra.SHARED_BOOL_FLAGS
    _SHARED_VALUE_FLAGS: ClassVar[frozenset[str]] = c.Infra.SHARED_VALUE_FLAGS
    _GROUP_COMMANDS: ClassVar[dict[str, tuple[m.Cli.ResultCommandRoute, ...]]] = {
        **_ROUTES_CODEGEN,
        **_ROUTES_VALIDATE,
        **_ROUTES_WORKSPACE,
    }

    @staticmethod
    def _cli_settings() -> cli_p.Cli.Settings:
        """Cli settings via the canonical cli facade."""
        return cli_facade.settings

    def main(self, args: t.StrSequence | None = None) -> int:
        """Run the centralized dispatcher."""
        u.ensure_structlog_configured()
        cli_args = list(args) if args is not None else sys.argv[1:]
        if not cli_args:
            self.print_help()
            return 1
        if cli_args[0] in self._HELP_FLAGS:
            self.print_help()
            return 0
        group, group_args = cli_args[0], cli_args[1:]
        if group not in c.Infra.CLI_GROUP_DESCRIPTIONS:
            self.display_message(
                f"unknown group '{group}'",
                c.Cli.MessageTypes.ERROR,
            )
            self.print_help()
            return 1
        return self._run_group(group, group_args)

    def print_help(self) -> None:
        """Display the canonical command groups."""
        self.display_message(
            "Usage: flext-infra <group> [subcommand] [args...]",
            c.Cli.MessageTypes.INFO,
        )
        self.display_message("Groups", c.Cli.MessageTypes.INFO)
        for group in sorted(c.Infra.CLI_GROUP_DESCRIPTIONS):
            self.display_message(
                f"  {group:<16}{c.Infra.CLI_GROUP_DESCRIPTIONS[group]}",
                c.Cli.MessageTypes.INFO,
            )

    def _normalize_group_args(self, args: t.StrSequence) -> list[str]:
        """Normalize group args."""
        reordered: list[str] = u.Cli.reorder_prefixed_options(
            args,
            bool_options=tuple(self._SHARED_BOOL_FLAGS),
            value_options=tuple(self._SHARED_VALUE_FLAGS),
        )
        return reordered

    def _register_group_commands(self, group: str, app: t.Cli.CliApp) -> None:
        """Register group commands."""
        self.register_result_routes(app, self._GROUP_COMMANDS[group])

    @staticmethod
    def _split_what(args: t.StrSequence) -> tuple[str | None, list[str]]:
        """Extract the ``--what`` value and return remaining args without it."""
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

    def _translate_what(self, group: str, args: t.StrSequence) -> p.Result[list[str]]:
        """Map ``--what <phase>`` onto the existing gate/validator selectors.

        ``check --what <gate>`` reuses ``resolve_gates`` and feeds the gate
        through the canonical ``run --gates`` path. ``validate --what <name>``
        selects the matching validator subcommand. Unknown phases yield a
        usage failure so the caller returns ``ScriptExitCode.USAGE``.
        """
        what, remaining = self._split_what(args)
        if what is None:
            return r[list[str]].ok(list(args))
        if group == c.Infra.CLI_GROUP_CHECK:
            gate_check = FlextInfraWorkspaceChecker.resolve_gates([what])
            if gate_check.failure:
                return r[list[str]].fail(gate_check.error or f"unknown gate '{what}'")
            check_routes = {route.name for route in self._GROUP_COMMANDS[group]}
            has_subcommand = bool(remaining) and remaining[0] in check_routes
            prefix = (
                list(remaining) if has_subcommand else [c.Infra.VERB_RUN, *remaining]
            )
            return r[list[str]].ok([*prefix, "--gates", what])
        if group == c.Infra.CLI_GROUP_VALIDATE:
            valid_names = {route.name for route in self._GROUP_COMMANDS[group]}
            if what not in valid_names:
                return r[list[str]].fail(f"unknown validator '{what}'")
            return r[list[str]].ok([what, *remaining])
        return r[list[str]].fail(f"--what is not supported for group '{group}'")

    def _run_group(self, group: str, args: t.StrSequence) -> int:
        """Execute a registered flext-cli group."""
        app = self.create_app_with_common_params(
            name=f"{self.app_name} {group}",
            help_text=c.Infra.CLI_GROUP_DESCRIPTIONS[group],
            settings=self._cli_settings(),
        )
        self._register_group_commands(group, app)
        what_result = self._translate_what(group, args)
        if what_result.failure:
            self.display_message(
                what_result.error or "invalid --what phase",
                c.Cli.MessageTypes.ERROR,
            )
            return int(c.Infra.ScriptExitCode.USAGE)
        normalized_args = self._normalize_group_args(what_result.value)
        if not normalized_args:
            _ = self.execute_app(
                app,
                prog_name=f"{self.app_name} {group}",
                args=["--help"],
            )
            return 1
        result = self.execute_app(
            app,
            prog_name=f"{self.app_name} {group}",
            args=normalized_args,
        )
        if result.success:
            return 0
        error_message = result.error
        if error_message:
            self.display_message(
                error_message,
                c.Cli.MessageTypes.ERROR,
            )
        return 2 if error_message and u.Cli.cli_usage_error(error_message) else 1


def main(args: t.StrSequence | None = None) -> int:
    """Run the canonical flext-infra CLI."""
    cli_args = list(args) if args is not None else sys.argv[1:]
    return FlextInfraCli().main(cli_args)


__all__: list[str] = ["FlextInfraCli", "main"]
