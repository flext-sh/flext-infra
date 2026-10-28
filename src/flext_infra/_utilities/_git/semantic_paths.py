"""Canonical Git responsibility mixin for ``u.Infra``.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import os
from pathlib import Path

from flext_cli import u
from git import GitCommandError, HookExecutionError, InvalidGitRepositoryError, Repo
from gitdb.util import LockedFD

from flext_infra import m, p, r
from flext_infra._utilities import (
    FlextInfraUtilitiesGitSemanticPublishMixin,
    FlextInfraUtilitiesGitStateFilesMixin,
)
from flext_infra._utilities._git.state_trees import (
    FlextInfraUtilitiesGitStateTreesMixin,
)


class FlextInfraUtilitiesGitSemanticPathsMixin(
    FlextInfraUtilitiesGitSemanticPublishMixin,
    FlextInfraUtilitiesGitStateFilesMixin,
):
    """Own semantic paths operations."""

    @classmethod
    def git_capture_index_file(
        cls,
        request: m.Infra.GitRelativePathRequest,
    ) -> p.Result[m.Infra.GitIndexFileState]:
        """Read one stage-zero entry and its immutable blob without staging.

        Returns:
            The exact preimage, or typed absence for an untracked file.

        """
        result_type = r[m.Infra.GitIndexFileState]
        try:
            captured = cls._capture_index_state(request)
        except (GitCommandError, OSError, ValueError, AssertionError) as exc:
            return result_type.fail_op("capture managed artifact index entry", exc)
        return result_type.ok(captured)

    @classmethod
    def _capture_index_state(
        cls,
        request: m.Infra.GitRelativePathRequest,
    ) -> m.Infra.GitIndexFileState:
        """Read the stage-zero entry and blob, or absence for an untracked path.

        Returns:
            The captured index entry with its immutable blob content.

        Raises:
            ValueError: If the index artifact has unresolved stages.

        """
        entries = FlextInfraUtilitiesGitStateTreesMixin.state_snapshot_index(
            request.repo_root,
            (Path(request.relative_path),),
        )
        if not entries:
            return m.Infra.GitIndexFileState(entry=None, content=None)
        if len(entries) != 1:
            msg = f"index artifact has unresolved stages: {request.relative_path}"
            raise ValueError(msg)
        entry = entries[0]
        return m.Infra.GitIndexFileState(
            entry=entry,
            content=cls._state_blob_payload(request.repo_root, entry.oid),
        )

    @classmethod
    def git_retire_index_file(
        cls,
        request: m.Infra.GitIndexRetirementRequest,
    ) -> p.Result[m.Infra.GitBoolReport]:
        """Retire an exact entry after reading it under Git's native write lock.

        Only the index lock's unpublished replacement is discarded on failure.
        No working file or previously published index generation is restored.

        Returns:
            A receipt after the captured path alone leaves the index.

        """
        try:
            return cls._retire_index_locked(request)
        except (GitCommandError, OSError, ValueError, AssertionError) as exc:
            return r[m.Infra.GitBoolReport].fail_op(
                "retire managed artifact index entry",
                exc,
            )

    @classmethod
    def _retire_index_locked(
        cls,
        request: m.Infra.GitIndexRetirementRequest,
    ) -> p.Result[m.Infra.GitBoolReport]:
        """Replace the locked index projection with the exact retired entry set.

        Returns:
            A receipt once the captured path alone leaves the index.

        Raises:
            TypeError: If the native index lock has an invalid capability or descriptor.
            ValueError: If the path is absolute/traversing, the entry changed
                after planning, or the locked index has no captured bytes.

        """
        result_type = r[m.Infra.GitBoolReport]
        relative = cls._retirable_relative_path(request)
        index_path = cls._git_index_path(request.repo_root)
        entries = FlextInfraUtilitiesGitStateTreesMixin.state_snapshot_index(
            request.repo_root,
            (relative,),
        )
        if len(entries) != 1 or entries[0] != request.entry:
            msg = f"index artifact changed after planning: {relative}"
            raise ValueError(msg)
        captured = u.Cli.atomic_read_binary_file_state(index_path, required=True)
        if captured.failure:
            return result_type.from_failure(captured)
        if captured.value.content is None:
            msg = "the locked index has no captured bytes"
            raise ValueError(msg)
        lock = LockedFD(index_path)
        if type(lock) is not LockedFD:
            msg = "native gitdb LockedFD does not provide the index lock contract"
            raise TypeError(msg)
        committed = False
        try:
            descriptor = lock.open(write=True, stream=False)
            if type(descriptor) is not int:
                msg = "the index lock did not return a raw file descriptor"
                raise TypeError(msg)
            FlextInfraUtilitiesGitSemanticPathsMixin._write_index_replacement(
                request,
                index_path,
                descriptor,
                captured.value.content,
            )
            lock.commit()
            committed = True
        finally:
            if not committed:
                lock.rollback()
        return result_type.ok(m.Infra.GitBoolReport(value=True))

    @staticmethod
    def _retirable_relative_path(
        request: m.Infra.GitIndexRetirementRequest,
    ) -> Path:
        """Return the index-relative path, rejecting absolute or traversing input.

        Returns:
            The validated repository-relative index path.

        Raises:
            ValueError: If the path is absolute or escapes the repository.

        """
        relative = request.entry.path
        if relative.is_absolute() or ".." in relative.parts:
            msg = f"index artifact path must be relative: {relative}"
            raise ValueError(msg)
        return relative

    @staticmethod
    def _write_index_replacement(
        request: m.Infra.GitIndexRetirementRequest,
        index_path: Path,
        descriptor: int,
        content: bytes,
    ) -> None:
        """Persist the verified preimage and re-stage the retirement in the lock.

        Args:
            request: The validated retirement request.
            index_path: The index file whose lock projection is rewritten.
            descriptor: The open write descriptor of the index lock.
            content: The verified preimage bytes to persist.

        """
        with os.fdopen(descriptor, "wb", closefd=False) as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        lock_path = index_path.with_name(f"{index_path.name}.lock")
        FlextInfraUtilitiesGitStateTreesMixin.state_index_update(
            request.repo_root,
            (request.entry.path,),
            (),
            index_file=lock_path,
        )
        with lock_path.open("rb") as produced:
            os.fsync(produced.fileno())

    @classmethod
    def git_init(
        cls,
        request: m.Infra.GitRepoRequest,
    ) -> p.Result[m.Infra.GitBoolReport]:
        """Initialize a new Git repository at ``repo_root``.

        Returns:
            The resulting ``p.Result[m.Infra.GitBoolReport]``.

        """
        try:
            Repo.init(request.repo_root).close()
        except (OSError, ValueError, InvalidGitRepositoryError) as exc:
            return r[m.Infra.GitBoolReport].fail(
                f"git init failed: {exc}",
                exception=exc,
            )
        return r[m.Infra.GitBoolReport].ok(m.Infra.GitBoolReport(value=True))

    @classmethod
    def git_checkout_restore(
        cls,
        request: m.Infra.GitRepoRequest,
    ) -> p.Result[m.Infra.GitBoolReport]:
        """Restore tracked paths via ``git checkout -- .``.

        Returns:
            The resulting ``p.Result[m.Infra.GitBoolReport]``.

        """
        try:
            repo = cls._repo(request.repo_root)
            repo.git.checkout("--", ".")
        except GitCommandError as exc:
            return r[m.Infra.GitBoolReport].fail(str(exc), exception=exc)
        except (OSError, ValueError) as exc:
            return r[m.Infra.GitBoolReport].fail(
                f"git checkout restore failed: {exc}",
                exception=exc,
            )
        return r[m.Infra.GitBoolReport].ok(m.Infra.GitBoolReport(value=True))

    @classmethod
    def git_mv_path(
        cls,
        request: m.Infra.GitPathPairRequest,
    ) -> p.Result[m.Infra.GitBoolReport]:
        """Move a tracked path with ``git mv``.

        Returns:
            The resulting ``p.Result[m.Infra.GitBoolReport]``.

        """
        try:
            repo = cls._repo(request.repo_root)
            repo.index.move([request.source, request.target])
        except GitCommandError as exc:
            return r[m.Infra.GitBoolReport].fail(str(exc), exception=exc)
        except (OSError, ValueError) as exc:
            return r[m.Infra.GitBoolReport].fail(f"git mv failed: {exc}", exception=exc)
        return r[m.Infra.GitBoolReport].ok(m.Infra.GitBoolReport(value=True))

    @classmethod
    def git_rm_cached(
        cls,
        request: m.Infra.GitRelativePathRequest,
    ) -> p.Result[m.Infra.GitBoolReport]:
        """Untrack a path with ``git rm --cached``.

        Returns:
            The resulting ``p.Result[m.Infra.GitBoolReport]``.

        """
        try:
            repo = cls._repo(request.repo_root)
            repo.index.remove([request.relative_path], cached=True, r=True, f=True)
        except GitCommandError as exc:
            return r[m.Infra.GitBoolReport].fail(str(exc), exception=exc)
        except (OSError, ValueError) as exc:
            return r[m.Infra.GitBoolReport].fail(
                f"git rm --cached failed: {exc}",
                exception=exc,
            )
        return r[m.Infra.GitBoolReport].ok(m.Infra.GitBoolReport(value=True))

    @classmethod
    def git_rm_path(
        cls,
        request: m.Infra.GitRelativePathRequest,
    ) -> p.Result[m.Infra.GitBoolReport]:
        """Remove a tracked path with ``git rm``.

        Returns:
            The resulting ``p.Result[m.Infra.GitBoolReport]``.

        """
        try:
            repo = cls._repo(request.repo_root)
            repo.index.remove([request.relative_path], cached=False, r=True, f=True)
        except GitCommandError as exc:
            return r[m.Infra.GitBoolReport].fail(str(exc), exception=exc)
        except (OSError, ValueError) as exc:
            return r[m.Infra.GitBoolReport].fail(f"git rm failed: {exc}", exception=exc)
        return r[m.Infra.GitBoolReport].ok(m.Infra.GitBoolReport(value=True))

    @classmethod
    def git_is_tracked(
        cls,
        request: m.Infra.GitRelativePathRequest,
    ) -> p.Result[m.Infra.GitBoolReport]:
        """Return whether a relative path is git-tracked.

        Returns:
            Whether a relative path is git-tracked.

        """
        try:
            repo = cls._repo(request.repo_root)
            listed = repo.git.ls_files("-z", "--", request.relative_path)
        except (GitCommandError, OSError, ValueError) as exc:
            return r[m.Infra.GitBoolReport].fail(
                f"failed to check tracked status: {exc}",
                exception=exc,
            )
        return r[m.Infra.GitBoolReport].ok(
            m.Infra.GitBoolReport(value=bool(listed.strip())),
        )

    @classmethod
    def git_path_has_history(
        cls,
        request: m.Infra.GitRelativePathRequest,
    ) -> p.Result[m.Infra.GitBoolReport]:
        """Report whether any native repository ref contains the declared path.

        Returns:
            The native history observation, or its original Git failure.

        """
        try:
            with cls._repo(request.repo_root) as repo:
                history = repo.iter_commits(
                    "--all",
                    paths=request.relative_path,
                    max_count=1,
                )
                present = next(history, None) is not None
        except (GitCommandError, OSError, ValueError) as exc:
            return r[m.Infra.GitBoolReport].fail(
                f"failed to inspect path history: {exc}",
                exception=exc,
            )
        return r[m.Infra.GitBoolReport].ok(
            m.Infra.GitBoolReport(value=present),
        )

    @classmethod
    def git_add_paths(
        cls,
        request: m.Infra.GitPathsRequest,
    ) -> p.Result[m.Infra.GitBoolReport]:
        """Stage multiple paths via ``git add --force``.

        The sole caller is the release stamp stage: it stages exactly the
        paths the preceding ``git status --porcelain`` listed (the preflight
        proved the checkout clean, so every listed path was produced by the
        stamp). ``--force`` is required because generated release artifacts
        may also match ``.gitignore`` projections; ignore rules must never
        silently drop a proven produced path from the release commit.

        Returns:
            The resulting ``p.Result[m.Infra.GitBoolReport]``.

        """
        try:
            repo = cls._repo(request.repo_root)
            repo.git.add("--force", "--", *request.paths)
        except GitCommandError as exc:
            return r[m.Infra.GitBoolReport].fail(str(exc), exception=exc)
        except (OSError, ValueError) as exc:
            return r[m.Infra.GitBoolReport].fail(
                f"git add failed: {exc}",
                exception=exc,
            )
        return r[m.Infra.GitBoolReport].ok(m.Infra.GitBoolReport(value=True))

    @classmethod
    def git_restore_paths(
        cls,
        request: m.Infra.GitCheckoutPathsRequest,
    ) -> p.Result[m.Infra.GitBoolReport]:
        """Restore tracked paths via ``git checkout --``.

        Returns:
            The resulting ``p.Result[m.Infra.GitBoolReport]``.

        """
        try:
            repo = cls._repo(request.repo_root)
            if request.paths:
                repo.index.checkout(paths=list(request.paths), force=True)
            else:
                repo.git.checkout("--", ".")
        except GitCommandError as exc:
            return r[m.Infra.GitBoolReport].fail(str(exc), exception=exc)
        except (OSError, ValueError) as exc:
            return r[m.Infra.GitBoolReport].fail(
                f"git restore failed: {exc}",
                exception=exc,
            )
        return r[m.Infra.GitBoolReport].ok(m.Infra.GitBoolReport(value=True))

    @classmethod
    def git_commit(
        cls,
        request: m.Infra.GitCommitRequest,
    ) -> p.Result[m.Infra.GitOidReport]:
        """Create a commit with the staged tree, gated by the repository hooks.

        Returns:
            The resulting ``p.Result[m.Infra.GitOidReport]``.

        """
        try:
            repo = cls._repo(request.repo_root)
            commit = repo.index.commit(request.message)
        except (GitCommandError, HookExecutionError) as exc:
            return r[m.Infra.GitOidReport].fail(str(exc), exception=exc)
        except (OSError, ValueError) as exc:
            return r[m.Infra.GitOidReport].fail(
                f"git commit failed: {exc}",
                exception=exc,
            )
        return r[m.Infra.GitOidReport].ok(m.Infra.GitOidReport(oid=commit.hexsha))


__all__: list[str] = ["FlextInfraUtilitiesGitSemanticPathsMixin"]
