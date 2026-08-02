"""Canonical Git worktree, checkpoint, and patch operations for ``u.Infra``."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from flext_cli import u
from flext_core import r
from flext_infra.constants import c
from flext_infra.models import m
from flext_infra.typings import t

if TYPE_CHECKING:
    from flext_infra.protocols import p


class FlextInfraUtilitiesGitWorktreeMixin:
    """Extend the existing Git utility owner with isolated mutation primitives."""

    @staticmethod
    def git_run(
        repo_root: Path,
        arguments: t.StrSequence,
        *,
        input_data: bytes | None = None,
        timeout: int | None = None,
    ) -> p.Result[p.Cli.CommandOutput]:
        """Run one Git command through the canonical process facade."""
        result = u.Cli.run_raw(
            (c.Infra.GIT, *arguments),
            cwd=repo_root,
            input_data=input_data,
            remove_env_keys=c.Infra.GIT_LOCAL_ENV_KEYS,
            timeout=timeout,
        )
        if result.failure:
            return r.fail(result.error or "git command execution failed")
        output: p.Cli.CommandOutput = result.value
        return r.ok(output)

    @classmethod
    def git_capture(cls, repo_root: Path, arguments: t.StrSequence) -> p.Result[str]:
        """Capture stdout from one successful Git command."""
        result = cls.git_run(repo_root, arguments)
        if result.failure:
            return r[str].fail(result.error or "git command execution failed")
        output = result.value
        if output.exit_code != 0:
            detail = (output.stderr or output.stdout).strip()
            return r[str].fail(detail or f"git command exited {output.exit_code}")
        return r[str].ok(output.stdout)

    @classmethod
    def git_capture_bytes(
        cls, repo_root: Path, arguments: t.StrSequence
    ) -> p.Result[bytes]:
        """Capture byte-exact stdout from one successful Git command."""
        # mro-45r9: patch transport stays binary until the human error boundary.
        result = u.Cli.run_bytes(
            (c.Infra.GIT, *arguments),
            cwd=repo_root,
            remove_env_keys=c.Infra.GIT_LOCAL_ENV_KEYS,
        )
        if result.failure:
            return r[bytes].fail(result.error or "git command execution failed")
        output: p.Cli.CommandBytesOutput = result.value
        if output.exit_code != 0:
            detail = (output.stderr or output.stdout).decode(
                c.Cli.ENCODING_DEFAULT, errors="replace"
            )
            return r[bytes].fail(
                detail.strip() or f"git command exited {output.exit_code}"
            )
        return r[bytes].ok(output.stdout)

    @classmethod
    def git_repository_head(cls, repo_root: Path) -> p.Result[str]:
        """Capture the current repository HEAD SHA."""
        return cls.git_capture(repo_root, ("rev-parse", "HEAD")).map(str.strip)

    @classmethod
    def git_workspace_root(cls, repository_path: Path) -> p.Result[Path]:
        """Resolve the superproject root or the repository's own top level."""
        superproject = cls.git_capture(
            repository_path, ("rev-parse", "--show-superproject-working-tree")
        )
        if superproject.failure:
            # Not inside any Git work tree -> standalone project owning its own
            # root; a genuine in-repo failure still fails closed.
            inside = cls.git_capture(
                repository_path, ("rev-parse", "--is-inside-work-tree")
            )
            if inside.failure or inside.value.strip() != "true":
                return r[Path].ok(repository_path.expanduser().resolve())
            return r[Path].fail(
                superproject.error or "failed to resolve Git superproject"
            )
        superproject_path = superproject.value.strip()
        if superproject_path:
            return r[Path].ok(Path(superproject_path).resolve())
        top_level = cls.git_capture(repository_path, ("rev-parse", "--show-toplevel"))
        if top_level.failure:
            return r[Path].fail(top_level.error or "failed to resolve Git top level")
        return r[Path].ok(Path(top_level.value.strip()).resolve())

    @classmethod
    def git_primary_worktree_root(cls, repository_path: Path) -> p.Result[Path]:
        """Resolve the primary worktree from Git's canonical storage topology."""
        common_dir_result = cls.git_capture(
            repository_path, ("rev-parse", "--path-format=absolute", "--git-common-dir")
        )
        if common_dir_result.failure:
            return r[Path].fail(
                common_dir_result.error or "failed to resolve Git common directory"
            )
        common_dir = Path(common_dir_result.value.strip()).resolve()
        configured_result = cls.git_run(
            repository_path, ("config", "--path", "--get", "core.worktree")
        )
        if configured_result.failure:
            return r[Path].fail(
                configured_result.error or "failed to inspect Git worktree config"
            )
        configured_output = configured_result.value
        if configured_output.exit_code == 0:
            configured = Path(configured_output.stdout.strip())
            primary_root = (
                configured if configured.is_absolute() else common_dir / configured
            ).resolve()
        elif configured_output.exit_code != 1:
            detail = (configured_output.stderr or configured_output.stdout).strip()
            return r[Path].fail(
                detail or f"cannot inspect primary worktree from {common_dir}"
            )
        elif common_dir.name == c.Infra.GIT_DIR:
            primary_root = common_dir.parent
        else:
            git_dir_result = cls.git_capture(
                repository_path, ("rev-parse", "--path-format=absolute", "--git-dir")
            )
            if git_dir_result.failure:
                return r[Path].fail(
                    git_dir_result.error or "failed to resolve Git directory"
                )
            git_dir = Path(git_dir_result.value.strip()).resolve()
            if git_dir != common_dir:
                listed_result = cls.git_capture(
                    repository_path, ("worktree", "list", "--porcelain")
                )
                if listed_result.failure:
                    return r[Path].fail(
                        listed_result.error
                        or "failed to inspect Git's canonical worktree registry"
                    )
                registered = tuple(
                    Path(line.removeprefix("worktree ").strip()).resolve()
                    for line in listed_result.value.splitlines()
                    if line.startswith("worktree ")
                )
                if not registered:
                    return r[Path].fail(
                        f"Git worktree registry is empty for {repository_path}"
                    )
                primary_root = registered[0]
                registered_top_level = cls.git_capture(
                    primary_root, ("rev-parse", "--show-toplevel")
                )
                if registered_top_level.failure:
                    caller_top_level = cls.git_capture(
                        repository_path, ("rev-parse", "--show-toplevel")
                    )
                    if caller_top_level.failure:
                        return r[Path].fail(
                            caller_top_level.error
                            or f"cannot derive a usable worktree from {common_dir}"
                        )
                    caller_root = Path(caller_top_level.value.strip()).resolve()
                    if caller_root not in registered:
                        return r[Path].fail(
                            "current worktree is absent from Git's canonical registry: "
                            f"{caller_root}"
                        )
                    primary_root = caller_root
            else:
                caller_top_level = cls.git_capture(
                    repository_path, ("rev-parse", "--show-toplevel")
                )
                if caller_top_level.failure:
                    return r[Path].fail(
                        caller_top_level.error
                        or f"cannot derive primary worktree from {common_dir}"
                    )
                primary_root = Path(caller_top_level.value.strip()).resolve()
        top_level = cls.git_capture(primary_root, ("rev-parse", "--show-toplevel"))
        if top_level.failure:
            return r[Path].fail(
                top_level.error or f"invalid primary worktree: {primary_root}"
            )
        resolved_top_level = Path(top_level.value.strip()).resolve()
        if resolved_top_level != primary_root:
            return r[Path].fail(
                f"Git primary worktree mismatch: {primary_root} != {resolved_top_level}"
            )
        return r[Path].ok(primary_root)

    @classmethod
    def git_declared_submodule_paths(
        cls, repository_root: Path
    ) -> p.Result[t.SequenceOf[Path]]:
        """Read every valid path declared by the repository's ``.gitmodules``.

        Unlike ``git submodule status``, this contract includes uninitialized
        submodules and treats an empty file as an empty topology. Malformed,
        duplicate, absolute, or escaping paths fail closed.
        """
        gitmodules = repository_root / c.Infra.GITMODULES
        if not gitmodules.exists():
            return r[t.SequenceOf[Path]].ok(())
        if not gitmodules.is_file():
            return r[t.SequenceOf[Path]].fail(
                f"Git submodule manifest is not a regular file: {gitmodules}"
            )
        result = cls.git_run(
            repository_root,
            (
                "config",
                "--file",
                c.Infra.GITMODULES,
                "--get-regexp",
                r"^submodule\..*\.path$",
            ),
        )
        if result.failure:
            return r[t.SequenceOf[Path]].fail(
                result.error or "failed to read Git submodule declarations"
            )
        output = result.value
        if output.exit_code == 1 and not output.stdout.strip():
            return r[t.SequenceOf[Path]].ok(())
        if output.exit_code != 0:
            detail = (output.stderr or output.stdout).strip()
            return r[t.SequenceOf[Path]].fail(
                detail or f"invalid Git submodule manifest: {gitmodules}"
            )
        paths: t.MutableSequenceOf[Path] = []
        for raw_line in output.stdout.splitlines():
            match raw_line.split(maxsplit=1):
                case [_, raw_path]:
                    relative = Path(raw_path)
                case _:
                    return r[t.SequenceOf[Path]].fail(
                        f"malformed Git submodule path entry: {raw_line}"
                    )
            if relative.is_absolute() or relative == Path() or ".." in relative.parts:
                return r[t.SequenceOf[Path]].fail(
                    f"invalid Git submodule path: {raw_path}"
                )
            if relative in paths:
                return r[t.SequenceOf[Path]].fail(
                    f"duplicate Git submodule path: {raw_path}"
                )
            paths.append(relative)
        return r[t.SequenceOf[Path]].ok(tuple(paths))

    @classmethod
    def git_submodule_paths(cls, workspace_root: Path) -> p.Result[t.SequenceOf[Path]]:
        """Resolve every initialized recursive submodule path."""
        result = cls.git_capture(workspace_root, ("submodule", "status", "--recursive"))
        if result.failure:
            return r[t.SequenceOf[Path]].fail(
                result.error or "failed to discover Git submodules"
            )
        paths: t.MutableSequenceOf[Path] = []
        for raw_line in result.value.splitlines():
            normalized = raw_line.strip()
            if not normalized:
                continue
            try:
                _status_and_sha, relative_path_text, *_description = normalized.split(
                    maxsplit=2
                )
            except ValueError:
                continue
            relative_path = Path(relative_path_text)
            if (workspace_root / relative_path / ".git").exists():
                paths.append(relative_path)
        return r[t.SequenceOf[Path]].ok(
            tuple(sorted(paths, key=lambda path: (len(path.parts), path.as_posix())))
        )

    @classmethod
    def git_add_detached_worktree(
        cls, source_root: Path, worktree_root: Path
    ) -> p.Result[str]:
        """Create a detached worktree at the source repository HEAD."""
        ensure_parent = u.Cli.ensure_dir(worktree_root.parent)
        if ensure_parent.failure:
            return r[str].fail(
                ensure_parent.error or "failed to create worktree parent"
            )
        if worktree_root.exists():
            try:
                worktree_root.rmdir()
            except OSError as exc:
                return r[str].fail(f"worktree target is not empty: {exc}")
        head_result = cls.git_repository_head(source_root)
        if head_result.failure:
            return head_result
        # An isolated transaction is a generator-validation boundary, not a user
        # checkout. Host post-checkout hooks may depend on a toolchain which the
        # generated project is about to declare, so they cannot be its prerequisite.
        # Transaction validators still exercise the generated artifact explicitly.
        add_result = cls.git_capture(
            source_root,
            (
                "-c",
                "core.hooksPath=/dev/null",
                "worktree",
                "add",
                "--detach",
                str(worktree_root),
                head_result.value,
            ),
        )
        if add_result.failure:
            return r[str].fail(add_result.error or "failed to add detached worktree")
        return head_result

    @staticmethod
    def _git_path_is_excluded(path: Path, excluded: t.SequenceOf[Path]) -> bool:
        """Return whether a relative path belongs to an excluded subtree."""
        return any(path == prefix or prefix in path.parents for prefix in excluded)

    @classmethod
    def _git_copy_untracked(
        cls, source_root: Path, worktree_root: Path, excluded: t.SequenceOf[Path]
    ) -> p.Result[bool]:
        """Copy non-ignored untracked files into an isolated worktree."""
        untracked = cls.git_capture(
            source_root, ("ls-files", "--others", "--exclude-standard", "-z")
        )
        if untracked.failure:
            return r[bool].fail(untracked.error or "failed to list untracked files")
        for raw_path in untracked.value.split("\0"):
            if not raw_path:
                continue
            relative_path = Path(raw_path)
            if cls._git_path_is_excluded(relative_path, excluded):
                continue
            source_path = source_root / relative_path
            if source_path.is_dir():
                continue
            destination_path = worktree_root / relative_path
            ensure_parent = u.Cli.ensure_dir(destination_path.parent)
            if ensure_parent.failure:
                return r[bool].fail(
                    ensure_parent.error or f"failed to create {destination_path.parent}"
                )
            if source_path.is_symlink():
                try:
                    destination_path.symlink_to(source_path.readlink())
                except OSError as exc:
                    return r[bool].fail(
                        f"failed to copy symlink {relative_path}: {exc}"
                    )
                continue
            copy_result = u.Cli.files_copy(source_path, destination_path)
            if copy_result.failure:
                return r[bool].fail(
                    copy_result.error or f"failed to copy untracked {relative_path}"
                )
        return r[bool].ok(True)

    @classmethod
    def git_copy_worktree_state(
        cls,
        source_root: Path,
        worktree_root: Path,
        *,
        excluded: t.SequenceOf[Path] = (),
    ) -> p.Result[bool]:
        """Reproduce tracked, staged, unstaged, and untracked source state."""
        pathspecs = tuple(f":(exclude){path.as_posix()}" for path in excluded)
        diff_result = cls.git_capture_bytes(
            source_root, ("diff", "--binary", "HEAD", "--", ".", *pathspecs)
        )
        if diff_result.failure:
            return r[bool].fail(diff_result.error or "failed to capture dirty patch")
        patch_bytes = diff_result.value
        if patch_bytes:
            # git apply rejects a patch whose final line lacks the terminating
            # newline ("corrupt patch"); `git diff --binary` can emit exactly
            # that, so restore the single trailing newline the format requires.
            if not patch_bytes.endswith(b"\n"):
                patch_bytes += b"\n"
            apply_result = cls.git_run(
                worktree_root, ("apply", "--binary", "-"), input_data=patch_bytes
            )
            if apply_result.failure:
                return r[bool].fail(
                    apply_result.error or "dirty patch execution failed"
                )
            output = apply_result.value
            if output.exit_code != 0:
                return r[bool].fail(
                    (output.stderr or output.stdout).strip()
                    or "dirty patch did not apply"
                )
        return cls._git_copy_untracked(source_root, worktree_root, tuple(excluded))

    @classmethod
    def git_checkpoint_worktree(
        cls, worktree_root: Path, *, message: str, excluded: t.SequenceOf[Path] = ()
    ) -> p.Result[str]:
        """Commit the complete isolated state as a synthetic checkpoint."""
        # `make setup` fast-forwards every declared submodule to its branch tip by
        # contract, so staging gitlinks made the checkpoint differ from HEAD before
        # the verb even ran: every later verb then reported pending changes for
        # pointers it never touched, and `gen` aborted before applying anything.
        submodules_result = cls.git_declared_submodule_paths(worktree_root)
        if submodules_result.failure:
            return r[str].fail(
                submodules_result.error or "failed to resolve declared submodules"
            )
        gitlink_exclusions = tuple(
            f":(exclude){path.as_posix()}" for path in submodules_result.value
        )
        if excluded:
            tracked_result = cls.git_capture(
                worktree_root,
                (
                    "ls-files",
                    "-z",
                    "--cached",
                    "--others",
                    "--exclude-standard",
                    "--",
                    ".",
                    *(f":(exclude){path.as_posix()}" for path in excluded),
                ),
            )
            if tracked_result.failure:
                return r[str].fail(
                    tracked_result.error or "failed to resolve checkpoint paths"
                )
            tracked_paths = tuple(
                path for path in tracked_result.value.split("\0") if path
            )
            stage_result = (
                # Why: force-add matches git_repository_delta staging (line ~454);
                # checkpoint captures complete state incl. ignored-but-tracked paths.
                cls.git_capture(
                    worktree_root,
                    ("add", "-A", "-f", "--", *tracked_paths, *gitlink_exclusions),
                )
                if tracked_paths
                else r[str].ok("")
            )
        else:
            stage_result = cls.git_capture(
                worktree_root, ("add", "-A", "--", ".", *gitlink_exclusions)
            )
        if stage_result.failure:
            return r[str].fail(stage_result.error or "failed to stage checkpoint")
        tree_result = cls.git_capture(worktree_root, ("write-tree",))
        parent_result = cls.git_repository_head(worktree_root)
        if tree_result.failure or parent_result.failure:
            return r[str].fail(
                tree_result.error
                if tree_result.failure
                else parent_result.error or "failed to resolve checkpoint parent"
            )
        identity_result = cls.git_capture(
            worktree_root, ("show", "-s", "--format=%an%x00%ae", parent_result.value)
        )
        if identity_result.failure:
            return r[str].fail(
                identity_result.error or "failed to resolve checkpoint identity"
            )
        identity = identity_result.value.rstrip("\n").split("\0")
        match identity:
            case [author_name, author_email] if (
                author_name.strip() and author_email.strip()
            ):
                pass
            case _:
                return r[str].fail("checkpoint parent has invalid author identity")
        commit_result = cls.git_capture(
            worktree_root,
            (
                "-c",
                f"user.name={author_name}",
                "-c",
                f"user.email={author_email}",
                "commit-tree",
                tree_result.value.strip(),
                "-p",
                parent_result.value,
                "-m",
                message,
            ),
        )
        if commit_result.failure:
            return r[str].fail(
                commit_result.error or "failed to create checkpoint commit"
            )
        checkpoint_sha = commit_result.value.strip()
        update_result = cls.git_capture(
            worktree_root, ("update-ref", "HEAD", checkpoint_sha)
        )
        if update_result.failure:
            return r[str].fail(update_result.error or "failed to activate checkpoint")
        return r[str].ok(checkpoint_sha)

    @staticmethod
    def _transaction_exclusion_pathspecs() -> tuple[str, ...]:
        """Pathspecs that exclude tool-cache directories from operation deltas."""
        return tuple(
            f":(exclude){name}"
            for name in sorted(c.Infra.WORKTREE_TRANSACTION_EXCLUDED_DIRS)
        )

    @classmethod
    def git_repository_delta(
        cls,
        repository: m.Infra.RepositoryWorktree,
        *,
        source_gitlinks: t.MappingKV[str, str] | None = None,
    ) -> p.Result[m.Infra.RepositoryDelta]:
        """Stage and capture the operation-only patch after a checkpoint."""
        head_result = cls.git_repository_head(repository.worktree_root)
        if head_result.failure or head_result.value != repository.checkpoint_sha:
            return r[m.Infra.RepositoryDelta].fail(
                head_result.error
                if head_result.failure
                else "isolated command moved repository HEAD"
            )
        exclusions = cls._transaction_exclusion_pathspecs()
        stage_result = cls.git_capture(
            repository.worktree_root, ("add", "-A", "-f", *exclusions)
        )
        if stage_result.failure:
            return r[m.Infra.RepositoryDelta].fail(
                stage_result.error or "failed to stage operation delta"
            )
        for path, source_head in (source_gitlinks or {}).items():
            update_result = cls.git_capture(
                repository.worktree_root,
                ("update-index", "--add", "--cacheinfo", "160000", source_head, path),
            )
            if update_result.failure:
                return r[m.Infra.RepositoryDelta].fail(
                    update_result.error or f"failed to stage source gitlink: {path}"
                )
        # Gitlinks are owned by `make setup`, which fast-forwards each declared
        # submodule to its branch tip. Including them here made every verb that
        # runs after setup report "pending changes" for pointers it never
        # touched, so `gen` aborted before applying anything.
        names_result = cls.git_capture(
            repository.worktree_root,
            (
                "diff",
                "--cached",
                "--name-only",
                "-z",
                "--ignore-submodules=all",
                repository.checkpoint_sha,
                "--",
                *exclusions,
            ),
        )
        patch_result = cls.git_capture_bytes(
            repository.worktree_root,
            (
                "diff",
                "--cached",
                "--binary",
                "--ignore-submodules=all",
                repository.checkpoint_sha,
                "--",
                *exclusions,
            ),
        )
        if names_result.failure or patch_result.failure:
            return r[m.Infra.RepositoryDelta].fail(
                names_result.error
                if names_result.failure
                else patch_result.error or "failed to capture operation patch"
            )
        # git apply rejects a patch whose final line has no terminating newline
        # ("corrupt patch"). `git diff --binary` can emit exactly that when the
        # last hunk ends on a context line, so restore the single trailing
        # newline the patch format requires before the delta is applied.
        patch_bytes = patch_result.value
        if patch_bytes and not patch_bytes.endswith(b"\n"):
            patch_bytes += b"\n"
        return r[m.Infra.RepositoryDelta].ok(
            m.Infra.RepositoryDelta(
                relative_path=repository.relative_path,
                source_root=repository.source_root,
                worktree_root=repository.worktree_root,
                checkpoint_sha=repository.checkpoint_sha,
                changed_files=tuple(
                    name for name in names_result.value.split("\0") if name
                ),
                patch=patch_bytes,
            )
        )

    @classmethod
    def _git_check_patch_at(
        cls, repository_root: Path, patch: bytes, *, reverse: bool
    ) -> p.Result[bool]:
        """Check one patch direction against an explicit repository root."""
        if not patch:
            return r[bool].ok(True)
        direction = ("--reverse",) if reverse else ()
        result = cls.git_run(
            repository_root,
            ("apply", "--check", "--binary", *direction, "-"),
            input_data=patch,
        )
        if result.failure:
            return r[bool].fail(result.error or "git apply --check failed")
        output = result.value
        if output.exit_code != 0:
            return r[bool].fail(
                (output.stderr or output.stdout).strip() or "git apply --check failed"
            )
        return r[bool].ok(True)

    @classmethod
    def git_check_patch(cls, delta: m.Infra.RepositoryDelta) -> p.Result[bool]:
        """Forward-check one operation patch against the live source worktree."""
        return cls._git_check_patch_at(delta.source_root, delta.patch, reverse=False)

    @classmethod
    def git_check_forward_patch(cls, delta: m.Infra.RepositoryDelta) -> p.Result[bool]:
        """Preflight a forward-applicable or already-converged source patch."""
        forward = cls.git_check_patch(delta)
        if forward.success:
            return forward
        converged = cls._git_source_has_patch(delta)
        if converged.success:
            return r[bool].ok(True)
        return r[bool].fail(forward.error or "source patch forward-check failed")

    @classmethod
    def git_check_isolated_patch(cls, delta: m.Infra.RepositoryDelta) -> p.Result[bool]:
        """Reverse-check that the isolated worktree contains the patch target."""
        return cls._git_check_patch_at(delta.worktree_root, delta.patch, reverse=True)

    @classmethod
    def _git_source_has_patch(cls, delta: m.Infra.RepositoryDelta) -> p.Result[bool]:
        """Return success when the live source already contains the patch target."""
        return cls._git_check_patch_at(delta.source_root, delta.patch, reverse=True)

    @staticmethod
    def _git_patch_added_paths(patch: bytes) -> tuple[Path, ...]:
        """Return paths declared as new files by one binary Git patch."""
        added: list[Path] = []
        current: Path | None = None
        for raw_line in patch.splitlines():
            if raw_line.startswith(b"diff --git a/"):
                _, _, _source, target = raw_line.split(maxsplit=3)
                current = Path(target.removeprefix(b"b/").decode())
                continue
            if raw_line.startswith(b"new file mode ") and current is not None:
                added.append(current)
        return tuple(added)

    @classmethod
    def _git_apply_gitlinks(cls, repository_root: Path, patch: bytes) -> p.Result[bool]:
        """Apply submodule entries that have no working-tree file representation."""
        current: Path | None = None
        gitlink = False
        for raw_line in patch.splitlines():
            if raw_line.startswith(b"diff --git a/"):
                _, _, _source, target = raw_line.split(maxsplit=3)
                current = Path(target.removeprefix(b"b/").decode())
                gitlink = False
                continue
            if raw_line == b"new file mode 160000" or (
                raw_line.startswith(b"index ") and raw_line.endswith(b" 160000")
            ):
                gitlink = True
                continue
            if (
                gitlink
                and current is not None
                and raw_line.startswith(b"+Subproject commit ")
            ):
                commit = raw_line.removeprefix(b"+Subproject commit ").decode()
                updated = cls.git_capture(
                    repository_root,
                    (
                        "update-index",
                        "--add",
                        "--cacheinfo",
                        "160000",
                        commit,
                        current.as_posix(),
                    ),
                )
                if updated.failure:
                    return r[bool].fail(
                        updated.error or f"failed to apply gitlink: {current}"
                    )
        return r[bool].ok(True)

    @classmethod
    def _git_apply_with_ignored_additions(
        cls, delta: m.Infra.RepositoryDelta
    ) -> p.Result[bool]:
        """Apply additions over existing ignored projections with rollback."""
        collisions = tuple(
            path
            for path in cls._git_patch_added_paths(delta.patch)
            if (delta.source_root / path).is_file()
        )
        if not collisions:
            return r[bool].fail("patch has no existing ignored additions")
        original = {
            path: (delta.source_root / path).read_bytes() for path in collisions
        }
        for path in collisions:
            (delta.source_root / path).unlink()
        result = cls.git_run(
            delta.source_root, ("apply", "--binary", "-"), input_data=delta.patch
        )
        if result.success and result.value.exit_code == 0:
            return r[bool].ok(True)
        for path, content in original.items():
            target = delta.source_root / path
            if target.exists():
                target.unlink()
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(content)
        if result.failure:
            return r[bool].fail(result.error or "git apply failed")
        output = result.value
        return r[bool].fail(
            (output.stderr or output.stdout).strip() or "git apply failed"
        )

    @classmethod
    def git_apply_patch(cls, delta: m.Infra.RepositoryDelta) -> p.Result[bool]:
        """Forward-check and idempotently converge one source operation patch."""
        if not delta.patch:
            return r[bool].ok(True)
        check_result = cls.git_check_patch(delta)
        if check_result.failure:
            converged_result = cls._git_source_has_patch(delta)
            if converged_result.success:
                return cls._git_apply_gitlinks(delta.source_root, delta.patch)
            collision_result = cls._git_apply_with_ignored_additions(delta)
            if collision_result.success:
                return cls._git_apply_gitlinks(delta.source_root, delta.patch)
            return r[bool].fail(check_result.error or collision_result.error)
        result = cls.git_run(
            delta.source_root, ("apply", "--binary", "-"), input_data=delta.patch
        )
        if result.failure:
            return r[bool].fail(result.error or "git apply failed")
        output = result.value
        if output.exit_code != 0:
            converged_result = cls._git_source_has_patch(delta)
            if converged_result.success:
                return cls._git_apply_gitlinks(delta.source_root, delta.patch)
            return r[bool].fail(
                (output.stderr or output.stdout).strip() or "git apply failed"
            )
        return cls._git_apply_gitlinks(delta.source_root, delta.patch)

    @classmethod
    def git_remove_worktree(
        cls, source_root: Path, worktree_root: Path
    ) -> p.Result[bool]:
        """Remove one explicitly selected temporary worktree and prune metadata."""
        remove_result = cls.git_capture(
            source_root, ("worktree", "remove", "--force", str(worktree_root))
        )
        if remove_result.failure:
            return r[bool].fail(remove_result.error or "failed to remove worktree")
        prune_result = cls.git_capture(source_root, ("worktree", "prune"))
        if prune_result.failure:
            return r[bool].fail(
                prune_result.error or "failed to prune worktree metadata"
            )
        return r[bool].ok(True)

    @classmethod
    def git_remove_clean_worktree(
        cls, source_root: Path, worktree_root: Path
    ) -> p.Result[bool]:
        """Remove an explicitly selected clean worktree and prune metadata."""
        remove_result = cls.git_capture(
            source_root, ("worktree", "remove", str(worktree_root))
        )
        if remove_result.failure:
            return r[bool].fail(
                remove_result.error or "failed to remove clean worktree"
            )
        prune_result = cls.git_capture(source_root, ("worktree", "prune"))
        if prune_result.failure:
            return r[bool].fail(
                prune_result.error or "failed to prune worktree metadata"
            )
        return r[bool].ok(True)


__all__: list[str] = ["FlextInfraUtilitiesGitWorktreeMixin"]
