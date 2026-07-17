"""Worktree transaction governance for mutating CLI routes."""

from __future__ import annotations

from pathlib import Path
from typing import ClassVar

from flext_cli import cli as cli_facade
from flext_infra import c, m, t, u
from flext_infra.services.cli_routes import CliRouteService


class CliTransactionService(CliRouteService, type(cli_facade)):
    """Execute governed route mutations through one worktree transaction."""

    app_name: ClassVar[str] = "flext-infra"
    help_flags: ClassVar[frozenset[str]] = frozenset({"-h", "--help"})
    shared_bool_flags: ClassVar[frozenset[str]] = c.Infra.SHARED_BOOL_FLAGS
    shared_value_flags: ClassVar[frozenset[str]] = c.Infra.SHARED_VALUE_FLAGS

    @classmethod
    def transaction_route_key(cls, group: str, args: t.StrSequence) -> str | None:
        """Resolve one governed write route from unnormalized CLI arguments."""
        route_names = {route.name for route in cls.group_commands[group]}
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
    def transaction_apply_requested(route_key: str, args: t.StrSequence) -> bool:
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
    def transaction_check_requested(route_key: str, args: t.StrSequence) -> bool:
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
    def transaction_inner_args(route_key: str, args: t.StrSequence) -> t.StrSequence:
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
    def transaction_workspace_argument(args: t.StrSequence) -> Path:
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

    def run_worktree_transaction(self, group: str, args: t.StrSequence) -> int | None:
        """Execute a governed mutation through the central worktree transaction."""
        if any(argument in self.help_flags for argument in args):
            return None
        process_environment = u.Cli.process_env()
        if process_environment.get(c.Infra.WORKTREE_TRANSACTION_ENV) == "1":
            return None
        route_key = self.transaction_route_key(group, args)
        if route_key is None:
            return None
        candidate_root = self.transaction_workspace_argument(args)
        workspace_result = u.Infra.git_workspace_root(candidate_root)
        if workspace_result.failure:
            self.display_message(
                workspace_result.error or "failed to resolve transaction workspace",
                c.Cli.MessageTypes.ERROR,
            )
            return 1
        apply_requested = self.transaction_apply_requested(route_key, args)
        request = m.Infra.WorktreeTransactionRequest(
            workspace_root=workspace_result.value,
            command=(group, *self.transaction_inner_args(route_key, args)),
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
        check_failed = self.transaction_check_requested(route_key, args) and any(
            repository.patch for repository in report.repositories
        )
        if check_failed:
            rendered = f"{rendered}\npending changes detected"
        message_type = (
            c.Cli.MessageTypes.ERROR
            if report.breakage_detected or check_failed
            else c.Cli.MessageTypes.INFO
        )
        if len(rendered) > c.Cli.OUTPUT_PLAIN_MESSAGE_THRESHOLD:
            self.display_message_plain(rendered, message_type)
        else:
            self.display_message(rendered, message_type)
        if (
            report.breakage_detected
            or check_failed
            or (apply_requested and not report.applied)
        ):
            return 1
        return 0


__all__: list[str] = ["CliTransactionService"]
