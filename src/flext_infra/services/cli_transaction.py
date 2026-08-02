"""Worktree transaction governance for mutating CLI routes."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, ClassVar

from flext_cli import cli as cli_facade
from flext_core import r
from flext_infra import c, config, m, t, u
from flext_infra.deps.extra_paths import FlextInfraExtraPathsManager
from flext_infra.services.cli_routes import CliRouteService
from flext_infra.workspace.detector import FlextInfraWorkspaceDetector

if TYPE_CHECKING:
    from flext_infra import p


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
        return any(
            argument == option or argument.startswith(f"{option}=") for argument in args
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
        stripped = frozenset((*policy.strip_options, policy.apply_option))
        normalized = tuple(
            argument
            for argument in args
            if argument not in stripped
            and not argument.startswith(f"{policy.apply_option}=")
        )
        return (*normalized, policy.apply_option)

    @staticmethod
    def _transaction_path_values(
        policy: m.Infra.CliTransactionPolicySpec, args: t.StrSequence
    ) -> tuple[tuple[m.Infra.CliTransactionPathOptionSpec, str], ...]:
        """Parse configured path options from both supported CLI spellings."""
        options = {option.name: option for option in policy.path_options}
        values: list[tuple[m.Infra.CliTransactionPathOptionSpec, str]] = []
        for index, argument in enumerate(args):
            option_name, separator, inline_value = argument.partition("=")
            option = options.get(option_name)
            if option is None:
                continue
            following = args[index + 1] if index + 1 < len(args) else ""
            value = inline_value if separator else following
            if value:
                values.append((option, value))
        return tuple(values)

    @classmethod
    def transaction_workspace_argument(
        cls, policy: m.Infra.CliTransactionPolicySpec, args: t.StrSequence
    ) -> Path:
        """Resolve an explicit workspace/root argument or the current directory."""
        return next(
            (
                Path(value).resolve()
                for option, value in cls._transaction_path_values(policy, args)
                if option.workspace_root
            ),
            Path.cwd().resolve(),
        )

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
        return (
            ()
            if spec.failure
            else tuple(member.path for member in spec.value.members if member.path.parts)
        )

    @staticmethod
    def _resolve_transaction_path(
        option: m.Infra.CliTransactionPathOptionSpec,
        raw_path: str,
        workspace_root: Path,
    ) -> Path:
        """Resolve one configured path according to its declared base."""
        candidate = Path(raw_path).expanduser()
        return (
            (workspace_root / candidate).resolve()
            if option.relative_to == "workspace" and not candidate.is_absolute()
            else candidate.resolve()
        )

    @classmethod
    def transaction_scoped_paths(
        cls,
        policy: m.Infra.CliTransactionPolicySpec,
        args: t.StrSequence,
        workspace_root: Path,
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
        path_values = cls._transaction_path_values(policy, args)
        raw_scope = (
            (option, token.strip())
            for option, value in path_values
            if option.scope
            for token in value.split(",")
            if token.strip()
        )
        resolved = tuple(
            cls._resolve_transaction_path(option, token, workspace_root)
            for option, token in raw_scope
        )
        if not all(candidate.is_relative_to(workspace_root) for candidate in resolved):
            return ()
        scoped = tuple(candidate.relative_to(workspace_root) for candidate in resolved)
        return (
            cls._dependency_closure_scope(scoped, workspace_root)
            if scoped
            else cls._manifest_member_scope(workspace_root)
        )

    @staticmethod
    def _dependency_closure_scope(
        scoped: t.SequenceOf[Path], workspace_root: Path
    ) -> tuple[Path, ...]:
        """Expand explicit targets through the canonical path-dependency graph."""
        manager = FlextInfraExtraPathsManager(workspace_root=workspace_root)
        workspace_names = tuple(manager.workspace_project_names)
        if not workspace_names:
            return tuple(scoped)
        pyprojects = (
            workspace_root / target / c.Infra.PYPROJECT_FILENAME for target in scoped
        )
        declared = tuple(
            name
            for pyproject in pyprojects
            if pyproject.is_file()
            for name in u.Infra.local_dependency_names_from_payload(
                u.Infra.pyproject_payload(pyproject),
                workspace_project_names=workspace_names,
            )
        )
        dependencies = (
            Path(name)
            for name in manager.resolve_transitive_dependency_names(declared)
            if (workspace_root / name).is_dir()
        )
        return tuple(dict.fromkeys((*scoped, *dependencies)))

    @classmethod
    def _active_transaction_route(
        cls, group: str, args: t.StrSequence
    ) -> str | None:
        """Resolve a route only when this is the outer mutating invocation."""
        transaction_active = (
            u.Cli.process_env().get(c.Infra.WORKTREE_TRANSACTION_ENV) == "1"
        )
        bypassed = (
            any(argument in cls.help_flags for argument in args) or transaction_active
        )
        return None if bypassed else cls.transaction_route_key(group, args)

    @classmethod
    def _transaction_request(
        cls, route_key: str, group: str, args: t.StrSequence
    ) -> p.Result[m.Infra.WorktreeTransactionRequest]:
        """Build the validated transaction request from config-owned route policy."""
        policy = cls._transaction_policy(route_key)
        candidate_root = cls.transaction_workspace_argument(policy, args)
        workspace_result = u.Infra.git_workspace_root(candidate_root)
        if workspace_result.failure:
            return r[m.Infra.WorktreeTransactionRequest].fail(
                workspace_result.error or "failed to resolve transaction workspace"
            )
        workspace_root = workspace_result.value
        return r[m.Infra.WorktreeTransactionRequest].ok(
            m.Infra.WorktreeTransactionRequest(
                workspace_root=workspace_root,
                command=(group, *cls.transaction_inner_args(route_key, args)),
                apply_patch=cls.transaction_apply_requested(route_key, args),
                timeout_seconds=c.Infra.WORKTREE_TRANSACTION_TIMEOUT_SECONDS,
                scoped_paths=cls.transaction_scoped_paths(policy, args, workspace_root),
            )
        )

    def _report_transaction(
        self,
        route_key: str,
        args: t.StrSequence,
        request: m.Infra.WorktreeTransactionRequest,
        report: m.Infra.WorktreeTransactionReport,
    ) -> int:
        """Render the transaction evidence and return its process exit code."""
        pending = any(repository.patch for repository in report.repositories)
        check_failed = self.transaction_check_requested(route_key, args) and pending
        rendered = u.Infra.render_worktree_transaction_report(report)
        if check_failed:
            rendered = f"{rendered}\npending changes detected"
        failed = (
            report.breakage_detected
            or check_failed
            or (request.apply_patch and not report.applied and pending)
        )
        message_type = (
            c.Cli.MessageTypes.ERROR if failed else c.Cli.MessageTypes.INFO
        )
        self.display_message_plain(rendered, message_type)
        return int(failed)

    def run_worktree_transaction(self, group: str, args: t.StrSequence) -> int | None:
        """Execute a governed mutation through the central worktree transaction."""
        route_key = self._active_transaction_route(group, args)
        if route_key is None:
            return None
        request_result = self._transaction_request(route_key, group, args)
        if request_result.failure:
            self.display_message(
                request_result.error or "failed to build worktree transaction request",
                c.Cli.MessageTypes.ERROR,
            )
            return 1
        request = request_result.value
        result = u.Infra.execute_worktree_transaction(request)
        if result.failure:
            self.display_message(
                result.error or "worktree transaction failed", c.Cli.MessageTypes.ERROR
            )
            return 1
        return self._report_transaction(route_key, args, request, result.value)


__all__: list[str] = ["CliTransactionService"]
