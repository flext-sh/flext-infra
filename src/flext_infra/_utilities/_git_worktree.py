"""Canonical Git worktree, checkpoint, and patch operations for ``u.Infra``."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from flext_cli import u
from flext_core import r
from flext_infra import c, m, t

if TYPE_CHECKING:
    from flext_infra import p


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
        result = u.Cli.run_bytes((c.Infra.GIT, *arguments), cwd=repo_root)
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
        add_result = cls.git_capture(
            source_root,
            ("worktree", "add", "--detach", str(worktree_root), head_result.value),
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
        cls, worktree_root: Path, *, message: str
    ) -> p.Result[str]:
        """Commit the complete isolated state as a synthetic checkpoint."""
        stage_result = cls.git_capture(worktree_root, ("add", "-A"))
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
        commit_result = cls.git_capture(
            worktree_root,
            (
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

    @classmethod
    def git_repository_delta(
        cls, repository: m.Infra.RepositoryWorktree
    ) -> p.Result[m.Infra.RepositoryDelta]:
        """Stage and capture the operation-only patch after a checkpoint."""
        head_result = cls.git_repository_head(repository.worktree_root)
        if head_result.failure or head_result.value != repository.checkpoint_sha:
            return r[m.Infra.RepositoryDelta].fail(
                head_result.error
                if head_result.failure
                else "isolated command moved repository HEAD"
            )
        stage_result = cls.git_capture(repository.worktree_root, ("add", "-A"))
        if stage_result.failure:
            return r[m.Infra.RepositoryDelta].fail(
                stage_result.error or "failed to stage operation delta"
            )
        names_result = cls.git_capture(
            repository.worktree_root,
            ("diff", "--cached", "--name-only", "-z", repository.checkpoint_sha),
        )
        patch_result = cls.git_capture_bytes(
            repository.worktree_root,
            ("diff", "--cached", "--binary", repository.checkpoint_sha, "--"),
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
                return r[bool].ok(True)
            collision_result = cls._git_apply_with_ignored_additions(delta)
            if collision_result.success:
                return collision_result
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
                return r[bool].ok(True)
            return r[bool].fail(
                (output.stderr or output.stdout).strip() or "git apply failed"
            )
        return r[bool].ok(True)

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


__all__: list[str] = ["FlextInfraUtilitiesGitWorktreeMixin"]
