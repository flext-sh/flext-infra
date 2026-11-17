"""Canonical Git responsibility mixin for ``u.Infra``.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

from git import BadName, GitCommandError

from flext_infra import c, m, p, r
from flext_infra._utilities._git import FlextInfraUtilitiesGitRepo


class FlextInfraUtilitiesGitSemanticRefs(FlextInfraUtilitiesGitRepo):
    """Own semantic refs operations."""

    @classmethod
    def git_list_worktrees(
        cls,
        request: p.Infra.GitRepoRequest,
    ) -> p.Result[p.Infra.GitWorktreeListReport]:
        """Read Git's canonical worktree registry, parsed once for every consumer.

        Returns:
            The resulting ``p.Result[p.Infra.GitWorktreeListReport]``.

        """
        repo_root = request.repo_root.expanduser().resolve()
        try:
            repo = cls._repo(repo_root)
            porcelain = repo.git.worktree(c.Action.LIST, "--porcelain")
            entries = cls._worktree_registry(repo, porcelain)
        except GitCommandError as exc:
            return r[p.Infra.GitWorktreeListReport].fail(str(exc), exception=exc)
        except (OSError, ValueError) as exc:
            return r[p.Infra.GitWorktreeListReport].fail(
                f"failed to list Git worktrees: {exc}",
                exception=exc,
            )
        return r[p.Infra.GitWorktreeListReport].ok(
            m.Infra.GitWorktreeListReport.model_validate({
                "root": (repo_root),
                "entries": (entries),
                "porcelain": (porcelain),
            }),
        )

    @classmethod
    def git_check_branch_format(
        cls,
        request: p.Infra.GitBranchRequest,
    ) -> p.Result[p.Infra.GitBoolReport]:
        """Validate a branch name with ``git check-ref-format --branch``.

        Returns:
            The resulting ``p.Result[p.Infra.GitBoolReport]``.

        """
        try:
            repo = cls._repo(request.repo_root)
            repo.git.check_ref_format("--branch", request.branch)
        except GitCommandError as exc:
            # check-ref-format documents exit 1 for an invalid name; any other
            # status is a real failure.
            if exc.status == c.Infra.GIT_EXIT_NEGATIVE:
                return r[p.Infra.GitBoolReport].ok(m.Infra.GitBoolReport(value=False))
            return r[p.Infra.GitBoolReport].fail(
                f"failed to validate branch name: {exc}",
                exception=exc,
            )
        except (OSError, ValueError) as exc:
            return r[p.Infra.GitBoolReport].fail(
                f"failed to validate branch name: {exc}",
                exception=exc,
            )
        return r[p.Infra.GitBoolReport].ok(m.Infra.GitBoolReport(value=True))

    @classmethod
    def git_ref_exists(
        cls,
        request: p.Infra.GitRefRequest,
    ) -> p.Result[p.Infra.GitBoolReport]:
        """Return whether an exact Git ref exists (exit 0/1 only).

        Returns:
            Whether an exact Git ref exists (exit 0/1 only).

        """
        try:
            repo = cls._repo(request.repo_root)
            repo.git.show_ref("--verify", "--quiet", request.reference)
        except GitCommandError as exc:
            # show-ref documents exit 1 for a missing ref; any other status is
            # a real failure.
            if exc.status == c.Infra.GIT_EXIT_NEGATIVE:
                return r[p.Infra.GitBoolReport].ok(m.Infra.GitBoolReport(value=False))
            return r[p.Infra.GitBoolReport].fail(
                f"failed to inspect Git ref: {exc}",
                exception=exc,
            )
        except (OSError, ValueError) as exc:
            return r[p.Infra.GitBoolReport].fail(
                f"failed to inspect Git ref: {exc}",
                exception=exc,
            )
        return r[p.Infra.GitBoolReport].ok(m.Infra.GitBoolReport(value=True))

    @classmethod
    def git_superproject_working_tree(
        cls,
        request: p.Infra.GitRepoRequest,
    ) -> p.Result[p.Infra.GitTextReport]:
        """Capture ``rev-parse --show-superproject-working-tree`` stdout.

        Returns:
            The resulting ``p.Result[p.Infra.GitTextReport]``.

        """
        try:
            repo = cls._repo(request.repo_root)
            text = repo.git.rev_parse("--show-superproject-working-tree")
        except GitCommandError as exc:
            return r[p.Infra.GitTextReport].fail(str(exc), exception=exc)
        except (OSError, ValueError) as exc:
            return r[p.Infra.GitTextReport].fail(
                f"failed to resolve superproject working tree: {exc}",
                exception=exc,
            )
        return r[p.Infra.GitTextReport].ok(m.Infra.GitTextReport(text=text))

    @classmethod
    def git_show_toplevel(
        cls,
        request: p.Infra.GitRepoRequest,
    ) -> p.Result[p.Infra.GitRootReport]:
        """Report the resolved top-level directory of the request's worktree.

        Returns:
            The resulting ``p.Result[p.Infra.GitRootReport]``.

        """
        opened = cls._open_repo(request.repo_root)
        if opened.failure:
            return r[p.Infra.GitRootReport].from_failure(opened)
        repo = opened.value
        try:
            root = (
                Path(repo.working_tree_dir).resolve() if repo.working_tree_dir else None
            )
            if root is None:
                return r[p.Infra.GitRootReport].fail(
                    "failed to resolve Git top level: working tree is None",
                )
        except GitCommandError as exc:
            return r[p.Infra.GitRootReport].fail(str(exc), exception=exc)
        except (OSError, ValueError) as exc:
            return r[p.Infra.GitRootReport].fail(
                f"failed to resolve Git top level: {exc}",
                exception=exc,
            )
        return r[p.Infra.GitRootReport].ok(m.Infra.GitRootReport(repository_root=root))

    @classmethod
    def git_current_branch(
        cls,
        request: p.Infra.GitRepoRequest,
    ) -> p.Result[p.Infra.GitTextReport]:
        """Resolve the current non-detached branch name.

        Returns:
            The resulting ``p.Result[p.Infra.GitTextReport]``.

        """
        try:
            repo = cls._repo(request.repo_root)
            branch = repo.active_branch.name
        except GitCommandError as exc:
            return r[p.Infra.GitTextReport].fail(str(exc), exception=exc)
        except (TypeError, OSError, ValueError) as exc:
            # active_branch raises TypeError on detached HEAD.
            return r[p.Infra.GitTextReport].fail(
                f"head branch is required from a detached HEAD: {exc}",
                exception=exc,
            )
        return r[p.Infra.GitTextReport].ok(m.Infra.GitTextReport(text=branch))

    @classmethod
    def git_resolve_commit(
        cls,
        request: p.Infra.GitCommitishRequest,
    ) -> p.Result[p.Infra.GitOidReport]:
        """Resolve a commit-ish to its commit oid, failing on a non-commit name.

        Returns:
            The resulting ``p.Result[p.Infra.GitOidReport]``.

        """
        try:
            repo = cls._repo(request.repo_root)
            oid = repo.commit(request.commitish).hexsha
        except (BadName, GitCommandError) as exc:
            return r[p.Infra.GitOidReport].fail(str(exc), exception=exc)
        except (OSError, ValueError) as exc:
            return r[p.Infra.GitOidReport].fail(
                f"cannot resolve commitish: {exc}",
                exception=exc,
            )
        return r[p.Infra.GitOidReport].ok(m.Infra.GitOidReport(oid=oid))

    @classmethod
    def git_is_ancestor(
        cls,
        request: p.Infra.GitAncestryRequest,
    ) -> p.Result[p.Infra.GitBoolReport]:
        """Return whether ``ancestor`` is an ancestor of ``descendant``.

        One owner proves ancestry for any pair. ``descendant`` defaults to
        ``HEAD``, so the HEAD-bound proof existing consumers relied on is a
        use of this verb, not a separate one.

        Returns:
            Whether ``ancestor`` is an ancestor of ``descendant``.

        """
        try:
            repo = cls._repo(request.repo_root)
            result = repo.is_ancestor(
                repo.commit(request.ancestor),
                repo.commit(request.descendant),
            )
        except (BadName, GitCommandError) as exc:
            return r[p.Infra.GitBoolReport].fail(str(exc), exception=exc)
        except (OSError, ValueError) as exc:
            return r[p.Infra.GitBoolReport].fail(
                f"failed to inspect ancestry: {exc}",
                exception=exc,
            )
        return r[p.Infra.GitBoolReport].ok(m.Infra.GitBoolReport(value=result))

    @classmethod
    def git_rev_parse(
        cls,
        request: p.Infra.GitCommitishRequest,
    ) -> p.Result[p.Infra.GitOidReport]:
        """Resolve an arbitrary rev-parse argument to stripped text oid.

        Returns:
            The resulting ``p.Result[p.Infra.GitOidReport]``.

        """
        try:
            repo = cls._repo(request.repo_root)
            oid = repo.git.rev_parse(request.commitish).strip()
        except GitCommandError as exc:
            return r[p.Infra.GitOidReport].fail(str(exc), exception=exc)
        except (OSError, ValueError) as exc:
            return r[p.Infra.GitOidReport].fail(
                f"rev-parse failed for {request.commitish}: {exc}",
                exception=exc,
            )
        return r[p.Infra.GitOidReport].ok(m.Infra.GitOidReport(oid=oid))

    @classmethod
    def git_ref_heads(
        cls,
        request: p.Infra.GitRefHeadsRequest,
    ) -> p.Result[p.Infra.GitRefHeadsReport]:
        """Map every ref below ``namespace`` to its tip oid.

        Names are relative to the namespace; the symbolic remote ``HEAD`` is
        an alias of another listed ref and is left out.

        Returns:
            The resulting ``p.Result[p.Infra.GitRefHeadsReport]``.

        """
        prefix = f"{request.namespace.rstrip('/')}/"
        try:
            repo = cls._repo(request.repo_root)
            text = repo.git.for_each_ref("--format=%(refname)%00%(objectname)", prefix)
        except GitCommandError as exc:
            return r[p.Infra.GitRefHeadsReport].fail(str(exc), exception=exc)
        except (OSError, ValueError) as exc:
            return r[p.Infra.GitRefHeadsReport].fail(
                f"failed to list refs below {request.namespace}: {exc}",
                exception=exc,
            )
        heads = {
            name.removeprefix(prefix): oid
            for name, _, oid in (line.partition("\0") for line in text.splitlines())
            if name.removeprefix(prefix) != c.Infra.GIT_HEAD
        }
        return r[p.Infra.GitRefHeadsReport].ok(m.Infra.GitRefHeadsReport(heads=heads))

    @classmethod
    def git_stash_oids(
        cls,
        request: p.Infra.GitRepoRequest,
    ) -> p.Result[p.Infra.GitOidListReport]:
        """List the stash commits, newest (``stash@{0}``) first.

        Returns:
            The resulting ``p.Result[p.Infra.GitOidListReport]``.

        """
        try:
            repo = cls._repo(request.repo_root)
            text = repo.git.stash(c.Action.LIST, "--format=%H")
        except GitCommandError as exc:
            return r[p.Infra.GitOidListReport].fail(str(exc), exception=exc)
        except (OSError, ValueError) as exc:
            return r[p.Infra.GitOidListReport].fail(
                f"failed to list stash entries: {exc}",
                exception=exc,
            )
        return r[p.Infra.GitOidListReport].ok(
            m.Infra.GitOidListReport(oids=tuple(text.split())),
        )

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
        listed = cls.git_stash_oids(m.Infra.GitRepoRequest(repo_root=request.repo_root))
        if listed.failure:
            return r[p.Infra.GitBoolReport].from_failure(listed)
        if request.oid not in listed.value.oids:
            return r[p.Infra.GitBoolReport].fail(f"stash entry {request.oid} not found")
        index = listed.value.oids.index(request.oid)
        try:
            cls._repo(request.repo_root).git.stash("drop", f"stash@{{{index}}}")
        except GitCommandError as exc:
            return r[p.Infra.GitBoolReport].fail(str(exc), exception=exc)
        except (OSError, ValueError) as exc:
            return r[p.Infra.GitBoolReport].fail(
                f"failed to drop stash {request.oid}: {exc}",
                exception=exc,
            )
        return r[p.Infra.GitBoolReport].ok(m.Infra.GitBoolReport(value=True))

    @classmethod
    def git_remote_branch_oid(
        cls,
        request: p.Infra.GitRemoteBranchRequest,
    ) -> p.Result[p.Infra.GitTextReport]:
        """Ask the remote itself for one branch tip; empty text means absent.

        Unlike a remote-tracking ref this is the live remote state, so it
        proves a publication rather than remembering one.

        Returns:
            The resulting ``p.Result[p.Infra.GitTextReport]``.

        """
        try:
            repo = cls._repo(request.repo_root)
            text = repo.git.ls_remote(
                "--heads",
                request.remote,
                f"refs/heads/{request.branch}",
            )
        except GitCommandError as exc:
            return r[p.Infra.GitTextReport].fail(str(exc), exception=exc)
        except (OSError, ValueError) as exc:
            return r[p.Infra.GitTextReport].fail(
                f"failed to query {request.remote} for {request.branch}: {exc}",
                exception=exc,
            )
        output = text if isinstance(text, str) else str(text)
        return r[p.Infra.GitTextReport].ok(
            m.Infra.GitTextReport(text=output.partition("\t")[0].strip()),
        )

    @classmethod
    def git_merge_is_noop(
        cls,
        request: p.Infra.GitMergeProbeRequest,
    ) -> p.Result[p.Infra.GitBoolReport]:
        """Whether merging ``commitish`` into ``base`` leaves its tree unchanged.

        This proves a squash- or rebase-merged branch is already contained in
        ``base`` without touching the index or worktree; a conflicting merge
        is not a no-op.

        Returns:
            The resulting ``p.Result[p.Infra.GitBoolReport]``.

        """
        try:
            repo = cls._repo(request.repo_root)
            merged = repo.git.merge_tree(
                "--write-tree",
                request.base,
                request.commitish,
            ).splitlines()[0]
            base_tree = repo.git.rev_parse(f"{request.base}^{{tree}}").strip()
        except GitCommandError as exc:
            if exc.status == c.Infra.GIT_EXIT_NEGATIVE:
                return r[p.Infra.GitBoolReport].ok(m.Infra.GitBoolReport(value=False))
            return r[p.Infra.GitBoolReport].fail(str(exc), exception=exc)
        except (OSError, ValueError, IndexError) as exc:
            return r[p.Infra.GitBoolReport].fail(
                f"merge probe failed for {request.commitish}: {exc}",
                exception=exc,
            )
        return r[p.Infra.GitBoolReport].ok(
            m.Infra.GitBoolReport(value=merged.strip() == base_tree),
        )

    @classmethod
    def git_last_activity(
        cls,
        request: p.Infra.GitRepoRequest,
    ) -> p.Result[p.Infra.GitTimestampReport]:
        """Newest of the HEAD commit time and this worktree's last HEAD move.

        The HEAD reflog is per worktree, so checkouts, commits, resets and
        rebases in one linked worktree never age or refresh another.

        Returns:
            The resulting ``p.Result[p.Infra.GitTimestampReport]``.

        """
        return cls.git_ref_last_activity(
            m.Infra.GitCommitishRequest(repo_root=request.repo_root, commitish="HEAD"),
        )

    @classmethod
    def git_ref_last_activity(
        cls,
        request: p.Infra.GitCommitishRequest,
    ) -> p.Result[p.Infra.GitTimestampReport]:
        """Read the newest commit/ref movement for one explicit reference.

        Returns:
            Activity evidence, never an ownership or abandonment decision.

        """
        try:
            repo = cls._repo(request.repo_root)
            committed = int(
                repo.git.log("-1", "--format=%ct", request.commitish).strip(),
            )
            moved = repo.git.log(
                "--walk-reflogs",
                "-1",
                "--date=unix",
                "--format=%gd",
                request.commitish,
            ).strip()
        except GitCommandError as exc:
            return r[p.Infra.GitTimestampReport].fail(str(exc), exception=exc)
        except (OSError, ValueError) as exc:
            return r[p.Infra.GitTimestampReport].fail(
                f"failed to read last activity: {exc}",
                exception=exc,
            )
        stamp = moved.partition("@{")[2].rstrip("}")
        latest = max(committed, int(stamp)) if stamp.isdigit() else committed
        return r[p.Infra.GitTimestampReport].ok(
            m.Infra.GitTimestampReport(epoch_seconds=latest),
        )


__all__: list[str] = ["FlextInfraUtilitiesGitSemanticRefs"]
