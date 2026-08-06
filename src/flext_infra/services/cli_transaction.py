"""Worktree transaction governance for mutating CLI routes."""

from __future__ import annotations

from pathlib import Path
from typing import ClassVar

from flext_cli import cli as cli_facade
from flext_infra import c, m, t, u
from flext_infra.deps.extra_paths import FlextInfraExtraPathsManager
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
        # Why: adopts the lane's per-group lazy route resolution (cli_routes.
        # route_table_for); `group_commands` no longer exists after that cutover.
        route_names = {route.name for route in cls.route_table_for(group)}
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
                # A bare selector token is a workspace member NAME, not a
                # cwd-relative path: --projects flext-infra resolved against
                # the current directory yields <member>/<member> whenever a
                # verb runs from inside a member, so the transaction scoped
                # itself to a directory that does not exist.
                candidate = Path(token).expanduser()
                resolved = (
                    candidate.resolve()
                    if candidate.is_absolute()
                    else (workspace_root / candidate).resolve()
                )
                try:
                    scoped.append(resolved.relative_to(workspace_root))
                except ValueError:
                    return ()
        if scoped:
            return cls._dependency_closure_scope(scoped, workspace_root)
        return cls._manifest_member_scope(workspace_root)

    @staticmethod
    def _dependency_closure_scope(
        scoped: t.SequenceOf[Path], workspace_root: Path
    ) -> tuple[Path, ...]:
        """Expand explicit targets to the declared workspace dependency closure.

        A scoped target is not self-contained: it imports its declared
        workspace path dependencies, and routes that derive from on-disk
        topology (extra-paths) read those sibling source roots directly.
        Isolating the target alone made the transaction contradict itself --
        the fresh-import probe still imported the target, whose package
        imports its dependencies, so the probe failed closed; and the search
        path derivation observed no siblings on disk and collapsed to
        ['src', '.'], which would then be applied back over the correct value.

        Reuses FlextInfraExtraPathsManager's transitive resolver so the scope
        is exactly the auto-adjusted dependency set the project declares --
        never a second, divergent notion of what a project depends on.
        """
        manager = FlextInfraExtraPathsManager(workspace_root=workspace_root)
        workspace_names = tuple(manager.workspace_project_names)
        if not workspace_names:
            return tuple(scoped)
        closure: dict[Path, None] = dict.fromkeys(scoped)
        for target in scoped:
            pyproject = workspace_root / target / c.Infra.PYPROJECT_FILENAME
            if not pyproject.is_file():
                continue
            declared = u.Infra.local_dependency_names_from_payload(
                u.Infra.pyproject_payload(pyproject),
                workspace_project_names=workspace_names,
            )
            for name in manager.resolve_transitive_dependency_names(declared):
                if (workspace_root / name).is_dir():
                    closure.setdefault(Path(name), None)
        return tuple(closure)

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
        workspace_result = u.Infra.git_workspace_root(
            m.Infra.GitRepoRequest(repo_root=candidate_root)
        )
        if workspace_result.failure:
            self.display_message(
                workspace_result.error or "failed to resolve transaction workspace",
                c.Cli.MessageTypes.ERROR,
            )
            return 1
        workspace_root = workspace_result.value.workspace_root
        apply_requested = self.transaction_apply_requested(route_key, args)
        request = m.Infra.WorktreeTransactionRequest(
            workspace_root=workspace_root,
            command=(group, *self.transaction_inner_args(route_key, args)),
            apply_patch=apply_requested,
            timeout_seconds=c.Infra.WORKTREE_TRANSACTION_TIMEOUT_SECONDS,
            scoped_paths=self.transaction_scoped_paths(args, workspace_root),
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
