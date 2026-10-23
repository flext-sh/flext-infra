"""Canonical Git responsibility mixin for ``u.Infra``.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import os
import stat
from pathlib import Path

from flext_cli import u as cli_u
from git import (
    GitCommandError,
    HookExecutionError,
    IndexFile,
    InvalidGitRepositoryError,
    Repo,
)
from gitdb.util import LockedFD

from flext_infra import m, p, r, t
from flext_infra._utilities import FlextInfraUtilitiesGitWorktreeIO
from flext_infra._utilities._git import (
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
        index_path = Path(cls._repo(request.repo_root).index.path)
        entries = FlextInfraUtilitiesGitStateTreesMixin.state_snapshot_index(
            request.repo_root,
            (relative,),
        )
        if len(entries) != 1 or entries[0] != request.entry:
            msg = f"index artifact changed after planning: {relative}"
            raise ValueError(msg)
        captured = cli_u.Cli.atomic_read_binary_file_state(index_path, required=True)
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

    @staticmethod
    def _git_publication_digest(state: m.Infra.GitPublicationState) -> str:
        index = state.index_before.content
        return cli_u.Cli.sha256_content(
            state.model_dump_json()
            + (cli_u.Cli.sha256_bytes(index) if index is not None else "absent")
        )

    @classmethod
    def _git_publication_current(
        cls, state: m.Infra.GitPublicationState
    ) -> p.Result[bool]:
        storage = state.__pydantic_private__
        if storage is None or storage.get("_publication_birth") != (
            id(state),
            cls._git_publication_digest(state),
        ):
            return r[bool].fail(
                "Git publication admission was not emitted by this owner"
            )
        repo = cls._repo(state.repo_root)
        if (
            repo.head.commit.hexsha != state.caller_oid
            or repo.active_branch.name != state.caller_branch
        ):
            return r[bool].fail("caller branch or HEAD changed after Git admission")
        return cli_u.Cli.atomic_verify_binary_file_states((state.index_before,))

    @classmethod
    def _git_publication_preimages(
        cls,
        root: Path,
        publications: t.VariadicTuple[m.Infra.CodegenPhaseOutcome],
    ) -> t.VariadicTuple[m.Cli.AtomicFileState]:
        if not publications:
            msg = "Git publication requires actual native output receipts"
            raise ValueError(msg)
        inputs: dict[Path, m.Cli.AtomicFileState] = {}
        pending = list(reversed(publications))
        while pending:
            publication = pending.pop()
            if (
                publication.root != root
                or not publication.completed
                or publication.error
                or publication.issues
                or publication.pending_files
            ):
                msg = (
                    "Git publication requires complete repository-bound native effects"
                )
                raise ValueError(msg)
            pending.extend(reversed(publication.batches))
            for published in publication.published_files:
                if published.tracking == "runtime-local":
                    continue
                before = published.before
                if (
                    published.project != root
                    or not before.path.is_relative_to(root)
                    or before.path not in publication.effect_targets
                ):
                    msg = f"native Git output is outside the repository: {before.path}"
                    raise ValueError(msg)
                relative = before.path.relative_to(root)
                cls._state_pathspecs((relative,))
                inputs.setdefault(before.path, before)
        return tuple(inputs.values())

    @classmethod
    def _git_publication_entry(
        cls, root: Path, state: m.Cli.AtomicFileState, *, write: bool
    ) -> m.Infra.GitWorktreeIndexEntry | None:
        if state.content is None:
            return None
        if state.mode is None:
            msg = f"native publication has no file mode: {state.path}"
            raise ValueError(msg)
        with FlextInfraUtilitiesGitWorktreeIO.git_stdin(state.content) as stream:
            oid = cls._repo(root).git.hash_object(
                *(("-w", "--stdin") if write else ("--stdin",)), istream=stream
            )
        return m.Infra.GitWorktreeIndexEntry(
            path=state.path.relative_to(root),
            mode="100755" if state.mode & stat.S_IXUSR else "100644",
            oid=oid,
        )

    @classmethod
    def git_commit_publications(
        cls,
        state: m.Infra.GitPublicationState,
        publications: t.VariadicTuple[m.Infra.CodegenPhaseOutcome],
        *,
        publication_verifier: p.Infra.GitPublicationVerifier,
    ) -> p.Result[m.Infra.GitOidReport]:
        """Commit authenticated outputs without staging into the caller's index.

        Returns:
            The owned commit, or the first origin, affected-path, hook, or CAS failure.

        """
        try:
            current = cls._git_publication_current(state)
            if current.failure:
                return r[m.Infra.GitOidReport].from_failure(current)
            with cls._state_leases((state.repo_root,)):
                return cls._git_commit_publications_locked(
                    state, publications, publication_verifier
                )
        except (GitCommandError, HookExecutionError, OSError, ValueError) as exc:
            return r[m.Infra.GitOidReport].fail_op("publish native Git outputs", exc)

    @classmethod
    def _git_publication_entries(
        cls,
        state: m.Infra.GitPublicationState,
        inputs: t.VariadicTuple[m.Cli.AtomicFileState],
        outputs: t.VariadicTuple[m.Cli.AtomicFileState],
    ) -> p.Result[t.VariadicTuple[m.Infra.GitWorktreeIndexEntry]]:
        result = r[t.VariadicTuple[m.Infra.GitWorktreeIndexEntry]]
        paths = tuple(item.path.relative_to(state.repo_root) for item in inputs)
        baseline = {
            entry.path: entry
            for entry in cls._state_tree_entries(state.repo_root, state.base_oid, paths)
        }
        staged = (
            {
                entry.path: entry
                for entry in cls.state_snapshot_index(state.repo_root, paths)
            }
            if paths
            else {}
        )
        for before in inputs:
            path = before.path.relative_to(state.repo_root)
            preimage = cls._git_publication_entry(state.repo_root, before, write=False)
            if baseline.get(path) != preimage or staged.get(path) != preimage:
                return result.fail(
                    f"owned output overlaps pre-existing changes: {path}"
                )
        return result.ok(
            tuple(
                entry
                for after in outputs
                if (
                    entry := cls._git_publication_entry(
                        state.repo_root, after, write=True
                    )
                )
                is not None
            )
        )

    @classmethod
    def _git_commit_publications_locked(
        cls,
        state: m.Infra.GitPublicationState,
        publications: t.VariadicTuple[m.Infra.CodegenPhaseOutcome],
        publication_verifier: p.Infra.GitPublicationVerifier,
    ) -> p.Result[m.Infra.GitOidReport]:
        result = r[m.Infra.GitOidReport]
        current = cls._git_publication_current(state)
        if current.failure:
            return result.from_failure(current)
        inputs = cls._git_publication_preimages(state.repo_root, publications)
        observed = publication_verifier.publication_input_states(inputs, publications)
        if observed.failure:
            return result.from_failure(observed)
        entries = cls._git_publication_entries(state, inputs, observed.value)
        if entries.failure:
            return result.from_failure(entries)
        repo = cls._repo(state.repo_root)
        lock = LockedFD(state.index_before.path)
        lock.open(write=True, stream=False)
        try:
            with (
                cls.state_publication_index(
                    state.repo_root,
                    state.base_oid,
                    tuple(item.path.relative_to(state.repo_root) for item in inputs),
                    entries.value,
                ) as index_path,
                repo.git.custom_environment(GIT_INDEX_FILE=str(index_path)),
            ):
                index = IndexFile(repo, index_path)
                expected_tree = index.write_tree().hexsha
                if expected_tree == repo.commit(state.base_oid).tree.hexsha:
                    return result.ok(m.Infra.GitOidReport(oid=state.base_oid))
                commit = index.commit(
                    state.subject,
                    parent_commits=[repo.commit(state.base_oid)],
                    head=False,
                )
                if (
                    commit.tree.hexsha != expected_tree
                    or repo.git.write_tree() != expected_tree
                ):
                    return result.fail(
                        "commit hook changed authenticated owned outputs"
                    )
                return cls._git_publication_finalize(
                    state, inputs, publications, publication_verifier, commit.hexsha
                )
        finally:
            lock.rollback()

    @classmethod
    def _git_publication_finalize(
        cls,
        state: m.Infra.GitPublicationState,
        inputs: t.VariadicTuple[m.Cli.AtomicFileState],
        publications: t.VariadicTuple[m.Infra.CodegenPhaseOutcome],
        publication_verifier: p.Infra.GitPublicationVerifier,
        oid: str,
    ) -> p.Result[m.Infra.GitOidReport]:
        result = r[m.Infra.GitOidReport]
        verified = publication_verifier.publication_input_states(inputs, publications)
        if verified.failure:
            return result.from_failure(verified)
        original = cls._git_publication_current(state)
        if original.failure:
            return result.from_failure(original)
        request = m.Infra.GitLaneVerificationRequest(
            repo_root=state.repo_root,
            remote=state.remote,
            candidate=state.caller_oid,
            expected_tip=state.base_oid,
            ownership=state.ownership,
        )
        fresh = cls.git_verify_lane(request).flat_map(
            lambda tip: cls._git_lane_retained_ownership(request, tip.oid)
        )
        if fresh.failure:
            return result.from_failure(fresh)
        cls._git_publication_ref(state, oid)
        return result.ok(m.Infra.GitOidReport(oid=oid))

    @classmethod
    def _git_publication_ref(cls, state: m.Infra.GitPublicationState, oid: str) -> None:
        owned = f"refs/heads/{state.branch}"
        previous = (
            state.previous_oid if state.previous_oid is not None else "0" * len(oid)
        )
        commands = f"start\nverify {state.integration_ref} {state.base_oid}\n"
        if state.branch != state.caller_branch:
            commands += f"verify refs/heads/{state.caller_branch} {state.caller_oid}\n"
        commands += f"update {owned} {oid} {previous}\nprepare\ncommit\n"
        with FlextInfraUtilitiesGitWorktreeIO.git_stdin(
            commands.encode("utf-8")
        ) as stream:
            cls._repo(state.repo_root).git.update_ref("--stdin", istream=stream)


__all__: list[str] = ["FlextInfraUtilitiesGitSemanticPathsMixin"]
