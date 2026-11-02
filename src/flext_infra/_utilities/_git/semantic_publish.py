"""Canonical Git responsibility mixin for ``u.Infra``.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from git import GitCommandError

from flext_infra import c, m, p, r
from flext_infra._utilities._git import (
    FlextInfraUtilitiesGitRepo,
    FlextInfraUtilitiesGitSemanticRefs,
)


class FlextInfraUtilitiesGitSemanticPublish(FlextInfraUtilitiesGitRepo):
    """Own semantic publish operations."""

    @classmethod
    def git_merge_no_edit(
        cls,
        request: p.Infra.GitCommitishRequest,
    ) -> p.Result[p.Infra.GitTextReport]:
        """Merge ``commitish`` into HEAD with an explicit merge commit.

        Returns:
            The resulting ``p.Result[p.Infra.GitTextReport]``.

        """
        try:
            repo = cls._repo(request.repo_root)
            text = repo.git.merge("--no-ff", "--no-edit", request.commitish)
        except GitCommandError as exc:
            return r[p.Infra.GitTextReport].fail(str(exc), exception=exc)
        except (OSError, ValueError) as exc:
            return r[p.Infra.GitTextReport].fail(
                f"merge failed for {request.commitish}: {exc}",
                exception=exc,
            )
        return r[p.Infra.GitTextReport].ok(m.Infra.GitTextReport(text=text))

    @classmethod
    def git_delete_ref(
        cls,
        request: p.Infra.GitDeleteRefRequest,
    ) -> p.Result[p.Infra.GitBoolReport]:
        """CAS-delete a ref when it still points at ``expected_oid``.

        Returns:
            The resulting ``p.Result[p.Infra.GitBoolReport]``.

        """
        if request.reference.startswith(c.Infra.GIT_REFS_HEADS):
            admitted = FlextInfraUtilitiesGitSemanticRefs.git_verify_lane(
                m.Infra.GitLaneVerificationRequest(
                    repo_root=request.repo_root,
                    operation="retire",
                    candidate=request.expected_oid,
                ),
            )
            if admitted.failure:
                return r[p.Infra.GitBoolReport].from_failure(admitted)
        try:
            repo = cls._repo(request.repo_root)
            repo.git.update_ref("-d", request.reference, request.expected_oid)
        except GitCommandError as exc:
            return r[p.Infra.GitBoolReport].fail(str(exc), exception=exc)
        except (OSError, ValueError) as exc:
            return r[p.Infra.GitBoolReport].fail(
                f"failed to delete ref {request.reference}: {exc}",
                exception=exc,
            )
        return r[p.Infra.GitBoolReport].ok(m.Infra.GitBoolReport(value=True))

    @classmethod
    def git_fetch_origin(
        cls,
        request: p.Infra.GitRepoRequest,
    ) -> p.Result[p.Infra.GitBoolReport]:
        """Fetch from origin.

        Returns:
            The resulting ``p.Result[p.Infra.GitBoolReport]``.

        """
        try:
            repo = cls._repo(request.repo_root)
            repo.remotes[c.Infra.GIT_DEFAULT_REMOTE].fetch()
        except GitCommandError as exc:
            return r[p.Infra.GitBoolReport].fail(str(exc), exception=exc)
        except (OSError, ValueError, AssertionError) as exc:
            return r[p.Infra.GitBoolReport].fail(
                f"failed to fetch origin: {exc}",
                exception=exc,
            )
        return r[p.Infra.GitBoolReport].ok(m.Infra.GitBoolReport(value=True))

    @classmethod
    def git_push_upstream(
        cls,
        request: p.Infra.GitPushRequest,
    ) -> p.Result[p.Infra.GitTextReport]:
        """Push ``source`` to ``remote`` as ``refs/heads/<branch>`` with ``-u``.

        Never forced: a remote branch that diverged rejects the push.

        Returns:
            The resulting ``p.Result[p.Infra.GitTextReport]``.

        """
        admitted = FlextInfraUtilitiesGitSemanticRefs.git_verify_lane(
            m.Infra.GitLaneVerificationRequest(
                repo_root=request.repo_root,
                remote=request.remote,
                candidate=request.source,
            ),
        )
        if admitted.failure:
            return r[p.Infra.GitTextReport].from_failure(admitted)
        try:
            repo = cls._repo(request.repo_root)
            text = repo.git.push(
                "-u",
                request.remote,
                f"{request.source}:refs/heads/{request.branch}",
            )
        except GitCommandError as exc:
            return r[p.Infra.GitTextReport].fail(str(exc), exception=exc)
        except (OSError, ValueError) as exc:
            return r[p.Infra.GitTextReport].fail(
                f"failed to push {request.branch}: {exc}",
                exception=exc,
            )
        return r[p.Infra.GitTextReport].ok(m.Infra.GitTextReport(text=text))

    @classmethod
    def git_remote_url(
        cls,
        request: p.Infra.GitRemoteUrlRequest,
    ) -> p.Result[p.Infra.GitTextReport]:
        """Resolve ``remote get-url <remote>`` as a text report.

        Returns:
            The resulting ``p.Result[p.Infra.GitTextReport]``.

        """
        try:
            repo = cls._repo(request.repo_root)
            url = repo.remotes[request.remote].url
        except GitCommandError as exc:
            return r[p.Infra.GitTextReport].fail(str(exc), exception=exc)
        except (OSError, ValueError, IndexError, AssertionError) as exc:
            return r[p.Infra.GitTextReport].fail(
                f"failed to resolve remote URL: {exc}",
                exception=exc,
            )
        return r[p.Infra.GitTextReport].ok(m.Infra.GitTextReport(text=url))

    @classmethod
    def git_fetch_remote(
        cls,
        request: p.Infra.GitRemoteRequest,
    ) -> p.Result[p.Infra.GitBoolReport]:
        """Fetch one named remote, pruning remote-tracking refs it deleted.

        Returns:
            The resulting ``p.Result[p.Infra.GitBoolReport]``.

        """
        try:
            repo = cls._repo(request.repo_root)
            repo.git.fetch("--prune", request.remote)
        except GitCommandError as exc:
            return r[p.Infra.GitBoolReport].fail(str(exc), exception=exc)
        except (OSError, ValueError) as exc:
            return r[p.Infra.GitBoolReport].fail(
                f"failed to fetch {request.remote}: {exc}",
                exception=exc,
            )
        return r[p.Infra.GitBoolReport].ok(m.Infra.GitBoolReport(value=True))

    @classmethod
    def git_delete_remote_branch(
        cls,
        request: p.Infra.GitRemoteBranchRequest,
    ) -> p.Result[p.Infra.GitBoolReport]:
        """Delete one remote branch, leased on ``expected_oid`` when given.

        The lease makes the deletion a compare-and-swap: a remote tip that
        moved since it was observed rejects the deletion.

        Returns:
            The resulting ``p.Result[p.Infra.GitBoolReport]``.

        """
        if request.expected_oid is None:
            return r[p.Infra.GitBoolReport].fail(
                "remote branch retirement requires its observed object identity",
            )
        admitted = FlextInfraUtilitiesGitSemanticRefs.git_verify_lane(
            m.Infra.GitLaneVerificationRequest(
                repo_root=request.repo_root,
                remote=request.remote,
                operation="retire",
                candidate=request.expected_oid,
            ),
        )
        if admitted.failure:
            return r[p.Infra.GitBoolReport].from_failure(admitted)
        ref = f"refs/heads/{request.branch}"
        lease = (f"--force-with-lease={ref}:{request.expected_oid}",)
        try:
            repo = cls._repo(request.repo_root)
            repo.git.push(*lease, request.remote, f":{ref}")
        except GitCommandError as exc:
            return r[p.Infra.GitBoolReport].fail(str(exc), exception=exc)
        except (OSError, ValueError) as exc:
            return r[p.Infra.GitBoolReport].fail(
                f"failed to delete remote branch {request.branch}: {exc}",
                exception=exc,
            )
        return r[p.Infra.GitBoolReport].ok(m.Infra.GitBoolReport(value=True))

    @classmethod
    def git_merge_ff_only(
        cls,
        request: p.Infra.GitCommitishRequest,
    ) -> p.Result[p.Infra.GitTextReport]:
        """Fast-forward HEAD to ``commitish``; anything else is refused.

        Returns:
            The resulting ``p.Result[p.Infra.GitTextReport]``.

        """
        try:
            repo = cls._repo(request.repo_root)
            text = repo.git.merge("--ff-only", request.commitish)
        except GitCommandError as exc:
            return r[p.Infra.GitTextReport].fail(str(exc), exception=exc)
        except (OSError, ValueError) as exc:
            return r[p.Infra.GitTextReport].fail(
                f"fast-forward failed for {request.commitish}: {exc}",
                exception=exc,
            )
        return r[p.Infra.GitTextReport].ok(m.Infra.GitTextReport(text=text))

    @classmethod
    def git_create_branch(
        cls,
        request: p.Infra.GitBranchCreateRequest,
    ) -> p.Result[p.Infra.GitBoolReport]:
        """Create a new branch at ``start``; an existing name is refused.

        With ``switch`` the worktree moves onto the new branch and carries
        its uncommitted changes along.

        Returns:
            The resulting ``p.Result[p.Infra.GitBoolReport]``.

        """
        admitted = FlextInfraUtilitiesGitSemanticRefs.git_verify_lane(
            m.Infra.GitLaneVerificationRequest(
                repo_root=request.repo_root,
                operation="create",
                candidate=request.start,
            ),
        )
        if admitted.failure:
            return r[p.Infra.GitBoolReport].from_failure(admitted)
        try:
            repo = cls._repo(request.repo_root)
            if request.switch:
                repo.git.switch("--create", request.branch, request.start)
            else:
                repo.git.branch(request.branch, request.start)
        except GitCommandError as exc:
            return r[p.Infra.GitBoolReport].fail(str(exc), exception=exc)
        except (OSError, ValueError) as exc:
            return r[p.Infra.GitBoolReport].fail(
                f"failed to create branch {request.branch}: {exc}",
                exception=exc,
            )
        return r[p.Infra.GitBoolReport].ok(m.Infra.GitBoolReport(value=True))

    @classmethod
    def git_switch_branch(
        cls,
        request: p.Infra.GitBranchRequest,
    ) -> p.Result[p.Infra.GitBoolReport]:
        """Switch the worktree to an existing branch; local changes block it.

        Returns:
            The resulting ``p.Result[p.Infra.GitBoolReport]``.

        """
        try:
            repo = cls._repo(request.repo_root)
            repo.git.switch(request.branch)
        except GitCommandError as exc:
            return r[p.Infra.GitBoolReport].fail(str(exc), exception=exc)
        except (OSError, ValueError) as exc:
            return r[p.Infra.GitBoolReport].fail(
                f"failed to switch to {request.branch}: {exc}",
                exception=exc,
            )
        return r[p.Infra.GitBoolReport].ok(m.Infra.GitBoolReport(value=True))

    @classmethod
    def git_stash_drop(
        cls,
        request: p.Infra.GitStashDropRequest,
    ) -> p.Result[p.Infra.GitBoolReport]:
        """Drop exactly the stash entry whose commit is ``oid``.

        Stash indexes shift on every drop, so the entry is located by its
        commit; an oid no longer stashed is a failure, never a guess.

        Returns:
            The resulting ``p.Result[p.Infra.GitBoolReport]``.

        """
        listed = FlextInfraUtilitiesGitSemanticRefs.git_stash_oids(
            m.Infra.GitRepoRequest(repo_root=request.repo_root)
        )
        if listed.failure:
            return r[p.Infra.GitBoolReport].from_failure(listed)
        if request.oid not in listed.value.oids:
            return r[p.Infra.GitBoolReport].fail(f"stash entry {request.oid} not found")
        index = list(listed.value.oids).index(request.oid)
        try:
            repo = cls._repo(request.repo_root)
            repo.git.stash("drop", f"stash@{{{index}}}")
        except GitCommandError as exc:
            return r[p.Infra.GitBoolReport].fail(str(exc), exception=exc)
        except (OSError, ValueError) as exc:
            return r[p.Infra.GitBoolReport].fail(
                f"failed to drop stash {request.oid}: {exc}",
                exception=exc,
            )
        return r[p.Infra.GitBoolReport].ok(m.Infra.GitBoolReport(value=True))


__all__: list[str] = ["FlextInfraUtilitiesGitSemanticPublish"]
