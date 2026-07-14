"""CLI entrypoint for the canonical flext-infra command surface.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import ClassVar

from flext_cli import cli as cli_facade
from flext_core import r
from flext_infra import c, m, p, t, u
from flext_infra._constants.cli_routes import (
    CODEGEN_ROUTES as _ROUTES_CODEGEN,
    VALIDATE_ROUTES as _ROUTES_VALIDATE,
    WORKSPACE_ROUTES as _ROUTES_WORKSPACE,
)
from flext_infra.check.workspace_check import FlextInfraWorkspaceChecker
from flext_infra.codegen.conform import FlextInfraCodegenConform


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
        # NOTE (multi-agent, mro-wkii.17 / agent: codex): operational route
        # composition belongs to cli; constants remain declaration-only.
        c.Infra.CLI_GROUP_CODEGEN: (
            m.Cli.ResultCommandRoute(
                name="conform",
                help_text="Conform generated project and workspace files",
                model_cls=m.Infra.CodegenConformRequest,
                handler=FlextInfraCodegenConform.execute_request,
                success_message="project conformance complete",
            ),
            *_ROUTES_CODEGEN[c.Infra.CLI_GROUP_CODEGEN],
        ),
    }

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
            self.display_message(f"unknown group '{group}'", c.Cli.MessageTypes.ERROR)
            self.print_help()
            return 1
        # mro-wkii.17.26 (codex): every mutating fix/codegen route executes
        # against a complete dirty-state checkpoint before touching source.
        transaction_result = self._run_worktree_transaction(group, group_args)
        if transaction_result is not None:
            return transaction_result
        return self._run_group(group, group_args)

    @classmethod
    def _transaction_route_key(cls, group: str, args: t.StrSequence) -> str | None:
        """Resolve one governed write route from unnormalized CLI arguments."""
        route_names = {route.name for route in cls._GROUP_COMMANDS[group]}
        command_name = next(
            (argument for argument in args if argument in route_names), None
        )
        if command_name is None:
            return None
        route_key = f"{group}:{command_name}"
        governed_routes = (
            c.Infra.WORKTREE_TRANSACTION_APPLY_ROUTES
            | c.Infra.WORKTREE_TRANSACTION_MODE_ROUTES
        )
        return route_key if route_key in governed_routes else None

    @staticmethod
    def _transaction_apply_requested(route_key: str, args: t.StrSequence) -> bool:
        """Return whether the outer invocation requested source application."""
        if route_key in c.Infra.WORKTREE_TRANSACTION_APPLY_ROUTES:
            return "--apply" in args
        return any(
            argument == "--mode=apply"
            or (
                argument == "--mode"
                and index + 1 < len(args)
                and args[index + 1] == "apply"
            )
            for index, argument in enumerate(args)
        )

    @staticmethod
    def _transaction_check_requested(route_key: str, args: t.StrSequence) -> bool:
        """Return whether the outer invocation requires a zero-delta check."""
        if route_key in c.Infra.WORKTREE_TRANSACTION_APPLY_ROUTES:
            return any(argument in {"--check", "--check-only"} for argument in args)
        return any(
            argument == "--mode=check"
            or (
                argument == "--mode"
                and index + 1 < len(args)
                and args[index + 1] == "check"
            )
            for index, argument in enumerate(args)
        )

    @staticmethod
    def _transaction_inner_args(route_key: str, args: t.StrSequence) -> t.StrSequence:
        """Force the isolated invocation to materialize its complete patch."""
        normalized: t.MutableSequenceOf[str] = []
        skip_next = False
        for argument in args:
            if skip_next:
                skip_next = False
                continue
            if route_key in c.Infra.WORKTREE_TRANSACTION_MODE_ROUTES:
                if argument == "--mode":
                    skip_next = True
                    continue
                if argument.startswith("--mode="):
                    continue
            elif argument in {"--apply", "--check", "--check-only", "--dry-run"}:
                continue
            normalized.append(argument)
        if route_key in c.Infra.WORKTREE_TRANSACTION_MODE_ROUTES:
            normalized.extend(("--mode", "apply"))
        else:
            normalized.append("--apply")
        return tuple(normalized)

    @staticmethod
    def _transaction_workspace_argument(args: t.StrSequence) -> Path:
        """Resolve an explicit workspace/root argument or the current directory."""
        path_flags = frozenset({"--root", "--workspace"})
        for index, argument in enumerate(args):
            if argument in path_flags and index + 1 < len(args):
                return Path(args[index + 1]).resolve()
            for flag in path_flags:
                prefix = f"{flag}="
                if argument.startswith(prefix):
                    return Path(argument.removeprefix(prefix)).resolve()
        return Path.cwd().resolve()

    def _run_worktree_transaction(self, group: str, args: t.StrSequence) -> int | None:
        """Execute a governed mutation through the central worktree transaction."""
        if any(argument in self._HELP_FLAGS for argument in args):
            return None
        process_environment = u.Cli.process_env()
        if process_environment.get(c.Infra.WORKTREE_TRANSACTION_ENV) == "1":
            return None
        route_key = self._transaction_route_key(group, args)
        if route_key is None:
            return None
        candidate_root = self._transaction_workspace_argument(args)
        workspace_result = u.Infra.git_workspace_root(candidate_root)
        if workspace_result.failure:
            self.display_message(
                workspace_result.error or "failed to resolve transaction workspace",
                c.Cli.MessageTypes.ERROR,
            )
            return 1
        apply_requested = self._transaction_apply_requested(route_key, args)
        request = m.Infra.WorktreeTransactionRequest(
            workspace_root=workspace_result.value,
            command=(group, *self._transaction_inner_args(route_key, args)),
            apply_patch=apply_requested,
            timeout_seconds=c.Infra.WORKTREE_TRANSACTION_TIMEOUT_SECONDS,
        )
        result = u.Infra.execute_worktree_transaction(request)
        if result.failure:
            self.display_message(
                result.error or "worktree transaction failed", c.Cli.MessageTypes.ERROR
            )
            return 1
        report = result.value
        rendered = u.Infra.render_worktree_transaction_report(report)
        check_failed = self._transaction_check_requested(route_key, args) and any(
            repository.patch for repository in report.repositories
        )
        if check_failed:
            rendered = f"{rendered}\npending changes detected"
        message_type = (
            c.Cli.MessageTypes.ERROR
            if report.breakage_detected or check_failed
            else c.Cli.MessageTypes.INFO
        )
        self.display_message(rendered, message_type)
        if (
            report.breakage_detected
            or check_failed
            or (apply_requested and not report.applied)
        ):
            return 1
        return 0

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

    def _normalize_group_args(self, args: t.StrSequence) -> list[str]:
        """Normalize group args."""
        reordered: list[str] = u.Cli.reorder_prefixed_options(
            args,
            bool_options=tuple(self._SHARED_BOOL_FLAGS),
            value_options=tuple(self._SHARED_VALUE_FLAGS),
        )
        return reordered

    def _register_group_commands(self, group: str, app: p.Cli.Application) -> None:
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


        Returns:
            A result containing translated command arguments or a selector error.
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
        )
        self._register_group_commands(group, app)
        what_result = self._translate_what(group, args)
        if what_result.failure:
            self.display_message(
                what_result.error or "invalid --what phase", c.Cli.MessageTypes.ERROR
            )
            return int(c.Infra.ScriptExitCode.USAGE)
        normalized_args = self._normalize_group_args(what_result.value)
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


def main(args: t.StrSequence | None = None) -> int:
    """Run the canonical flext-infra CLI."""
    cli_args = list(args) if args is not None else sys.argv[1:]
    return FlextInfraCli().main(cli_args)


def docs_main(args: t.StrSequence | None = None) -> int:
    """Run the docs group directly (``flext-docs`` == ``flext-infra docs``)."""
    cli_args = list(args) if args is not None else sys.argv[1:]
    return FlextInfraCli().main([c.Infra.CLI_GROUP_DOCS, *cli_args])


__all__: list[str] = ["FlextInfraCli", "docs_main", "main"]
