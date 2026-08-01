"""Worktree transaction governance for mutating CLI routes."""

from __future__ import annotations

from pathlib import Path
from typing import ClassVar

from flext_cli import cli as cli_facade
from flext_infra import c, config, m, t, u
from flext_infra.services.cli_routes import CliRouteService
from flext_infra.workspace.detector import FlextInfraWorkspaceDetector


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
        policy = config.Infra.codegen.cli_transaction_policy(route_key)
        return route_key if policy is not None else None

    @staticmethod
    def _transaction_policy(route_key: str) -> m.Infra.CliTransactionPolicySpec:
        """Resolve one already-governed route from the config SSOT."""
        policy = config.Infra.codegen.cli_transaction_policy(route_key)
        if policy is None:
            msg = f"missing CLI transaction policy: {route_key}"
            raise ValueError(msg)
        return policy

    @staticmethod
    def transaction_apply_requested(route_key: str, args: t.StrSequence) -> bool:
        """Return whether the outer invocation requested source application."""
        policy = CliTransactionService._transaction_policy(route_key)
        option = policy.apply_option
        if policy.apply_value_source == "presence":
            return any(
                argument == option or argument.startswith(f"{option}=")
                for argument in args
            )
        expected = config.Infra.codegen.make.apply_value
        return any(
            (argument == option and index + 1 < len(args) and args[index + 1] == expected)
            or argument == f"{option}={expected}"
            for index, argument in enumerate(args)
        )

    @staticmethod
    def transaction_check_requested(route_key: str, args: t.StrSequence) -> bool:
        """Return whether the outer invocation requires a zero-delta check."""
        policy = CliTransactionService._transaction_policy(route_key)
        return any(argument in policy.check_options for argument in args)

    @staticmethod
    def transaction_inner_args(route_key: str, args: t.StrSequence) -> t.StrSequence:
        """Force the isolated invocation to materialize its complete patch."""
        policy = CliTransactionService._transaction_policy(route_key)
        supplied_apply_value: str | None = None
        normalized: t.MutableSequenceOf[str] = []
        index = 0
        while index < len(args):
            argument = args[index]
            if argument == policy.apply_option:
                if policy.apply_value_source == "make" and index + 1 < len(args):
                    supplied_apply_value = args[index + 1]
                index += 2 if policy.apply_value_source == "make" else 1
                continue
            if argument.startswith(f"{policy.apply_option}="):
                if policy.apply_value_source == "make":
                    supplied_apply_value = argument.partition("=")[2]
                index += 1
                continue
            if argument in policy.strip_options:
                index += 1
                continue
            normalized.append(argument)
            index += 1
        normalized.append(policy.apply_option)
        if policy.apply_value_source == "make":
            if supplied_apply_value is not None:
                normalized.append(supplied_apply_value)
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

    @staticmethod
    def _manifest_member_scope(workspace_root: Path) -> tuple[Path, ...]:
        """Return workspace-member submodule paths from the topology manifest.

        A workspace-scoped route (scaffold/conform) only touches the root plus
        its declared members, never unrelated sibling submodules. Reading the
        manifest lets the transaction isolate exactly those repositories. Any
        load/parse failure returns an empty tuple so the caller falls back to
        full-workspace isolation (safe default).
        """
        spec = FlextInfraWorkspaceDetector.load_workspace_spec(workspace_root)
        if spec.failure:
            return ()
        members: list[Path] = []
        for member in spec.value.members:
            member_path = Path(member.path)
            if member_path != Path():
                members.append(member_path)
        return tuple(members)

    @classmethod
    def transaction_scoped_paths(
        cls, args: t.StrSequence, workspace_root: Path
    ) -> tuple[Path, ...]:
        """Derive workspace-relative paths the command can touch.

        Any explicit target flag wins: ``--root``, ``--output-root``,
        ``--project``, and ``--projects`` all name the scope the caller asked
        for. A route that names its own target must never inherit the whole
        manifest, or the transaction adopts siblings the scoped project never
        declared. Otherwise, for a workspace-scoped route, fall back to the
        manifest's member paths so the transaction isolates the root plus
        declared members instead of every sibling submodule. Returns an empty
        tuple (full-workspace isolation, safe default) only when neither
        source yields a target.
        """
        scoped: list[Path] = []
        value_flags = frozenset({"--output-root", "--project", "--projects", "--root"})
        for index, argument in enumerate(args):
            raw: str | None = None
            if argument in value_flags and index + 1 < len(args):
                raw = args[index + 1]
            else:
                for flag in value_flags:
                    prefix = f"{flag}="
                    if argument.startswith(prefix):
                        raw = argument.removeprefix(prefix)
                        break
            if raw is None:
                continue
            for token in raw.split(","):
                token = token.strip()
                if not token:
                    continue
                resolved = Path(token).expanduser().resolve()
                try:
                    scoped.append(resolved.relative_to(workspace_root))
                except ValueError:
                    return ()
        if scoped:
            return tuple(scoped)
        return cls._manifest_member_scope(workspace_root)

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
            scoped_paths=self.transaction_scoped_paths(args, workspace_result.value),
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
        self.display_message_plain(rendered, message_type)
        if (
            report.breakage_detected
            or check_failed
            or (
                apply_requested
                and not report.applied
                and any(repository.patch for repository in report.repositories)
            )
        ):
            return 1
        return 0


__all__: list[str] = ["CliTransactionService"]
