"""Typed semantic Git operations for consumers outside ``_git/``."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from flext_core import r
from flext_infra._utilities._git.repo import git_capture, git_capture_bytes, git_run
from flext_infra._utilities._git.worktree import FlextInfraUtilitiesGitWorktreeMixin
from flext_infra.models import m

if TYPE_CHECKING:
    from flext_infra.protocols import p


class FlextInfraUtilitiesGitSemanticMixin(FlextInfraUtilitiesGitWorktreeMixin):
    """Monomorphic Request/Report Git ops used by work/layout/saga consumers."""

    @classmethod
    def git_list_worktrees(
        cls, request: m.Infra.GitRepoRequest
    ) -> p.Result[m.Infra.GitTextReport]:
        """List registered worktrees in porcelain form."""
        listed = git_capture(
            request.repo_root, ("worktree", "list", "--porcelain")
        )
        if listed.failure:
            return r[m.Infra.GitTextReport].fail(
                listed.error or "failed to list Git worktrees"
            )
        return r[m.Infra.GitTextReport].ok(m.Infra.GitTextReport(text=listed.value))

    @classmethod
    def git_check_branch_format(
        cls, request: m.Infra.GitBranchRequest
    ) -> p.Result[m.Infra.GitBoolReport]:
        """Validate a branch name with ``git check-ref-format --branch``."""
        checked = git_capture(
            request.repo_root, ("check-ref-format", "--branch", request.branch)
        )
        if checked.failure:
            return r[m.Infra.GitBoolReport].fail(
                checked.error or f"invalid branch name: {request.branch}"
            )
        return r[m.Infra.GitBoolReport].ok(m.Infra.GitBoolReport(value=True))

    @classmethod
    def git_ref_exists(
        cls, request: m.Infra.GitRefRequest
    ) -> p.Result[m.Infra.GitBoolReport]:
        """Return whether an exact Git ref exists (exit 0/1 only)."""
        checked = git_run(
            request.repo_root,
            ("show-ref", "--verify", "--quiet", request.reference),
        )
        if checked.failure:
            return r[m.Infra.GitBoolReport].fail(
                checked.error or f"failed to inspect Git ref: {request.reference}"
            )
        if checked.value.exit_code not in {0, 1}:
            detail = (checked.value.stderr or checked.value.stdout).strip()
            return r[m.Infra.GitBoolReport].fail(
                detail or f"failed to inspect Git ref: {request.reference}"
            )
        return r[m.Infra.GitBoolReport].ok(
            m.Infra.GitBoolReport(value=checked.value.exit_code == 0)
        )

    @classmethod
    def git_superproject_working_tree(
        cls, request: m.Infra.GitRepoRequest
    ) -> p.Result[m.Infra.GitTextReport]:
        """Capture ``rev-parse --show-superproject-working-tree`` stdout."""
        captured = git_capture(
            request.repo_root, ("rev-parse", "--show-superproject-working-tree")
        )
        if captured.failure:
            return r[m.Infra.GitTextReport].fail(
                captured.error or "failed to resolve superproject working tree"
            )
        return r[m.Infra.GitTextReport].ok(m.Infra.GitTextReport(text=captured.value))

    @classmethod
    def git_show_toplevel(
        cls, request: m.Infra.GitRepoRequest
    ) -> p.Result[m.Infra.GitRootReport]:
        """Resolve ``rev-parse --show-toplevel`` as a workspace root report."""
        captured = git_capture(request.repo_root, ("rev-parse", "--show-toplevel"))
        if captured.failure:
            return r[m.Infra.GitRootReport].fail(
                captured.error or "failed to resolve Git top level"
            )
        return r[m.Infra.GitRootReport].ok(
            m.Infra.GitRootReport(
                workspace_root=Path(captured.value.strip()).resolve()
            )
        )

    @classmethod
    def git_current_branch(
        cls, request: m.Infra.GitRepoRequest
    ) -> p.Result[m.Infra.GitTextReport]:
        """Resolve the current non-detached branch name."""
        captured = git_capture(request.repo_root, ("branch", "--show-current"))
        if captured.failure:
            return r[m.Infra.GitTextReport].fail(
                captured.error or "failed to resolve current branch"
            )
        head = captured.value.strip()
        if not head:
            return r[m.Infra.GitTextReport].fail(
                "head branch is required from a detached HEAD"
            )
        return r[m.Infra.GitTextReport].ok(m.Infra.GitTextReport(text=head))

    @classmethod
    def git_symbolic_ref_short(
        cls, request: m.Infra.GitRepoRequest
    ) -> p.Result[m.Infra.GitTextReport]:
        """Resolve ``symbolic-ref --quiet --short HEAD``."""
        captured = git_capture(
            request.repo_root, ("symbolic-ref", "--quiet", "--short", "HEAD")
        )
        if captured.failure:
            return r[m.Infra.GitTextReport].fail(
                captured.error or "failed to resolve symbolic-ref HEAD"
            )
        return r[m.Infra.GitTextReport].ok(
            m.Infra.GitTextReport(text=captured.value.strip())
        )

    @classmethod
    def git_resolve_commit(
        cls, request: m.Infra.GitCommitishRequest
    ) -> p.Result[m.Infra.GitOidReport]:
        """Resolve a commit-ish to an oid via ``rev-parse --verify``."""
        captured = git_capture(
            request.repo_root,
            ("rev-parse", "--verify", f"{request.commitish}^{{commit}}"),
        )
        if captured.failure:
            return r[m.Infra.GitOidReport].fail(
                captured.error or f"cannot resolve commitish: {request.commitish}"
            )
        return r[m.Infra.GitOidReport].ok(
            m.Infra.GitOidReport(oid=captured.value.strip())
        )

    @classmethod
    def git_abbrev_ref_head(
        cls, request: m.Infra.GitRepoRequest
    ) -> p.Result[m.Infra.GitTextReport]:
        """Resolve ``rev-parse --abbrev-ref HEAD``."""
        captured = git_capture(
            request.repo_root, ("rev-parse", "--abbrev-ref", "HEAD")
        )
        if captured.failure:
            return r[m.Infra.GitTextReport].fail(
                captured.error or "failed to resolve abbrev-ref HEAD"
            )
        return r[m.Infra.GitTextReport].ok(
            m.Infra.GitTextReport(text=captured.value.strip())
        )

    @classmethod
    def git_is_ancestor(
        cls, request: m.Infra.GitCommitishRequest
    ) -> p.Result[m.Infra.GitBoolReport]:
        """Return whether ``commitish`` is an ancestor of HEAD."""
        checked = git_run(
            request.repo_root,
            ("merge-base", "--is-ancestor", request.commitish, "HEAD"),
        )
        if checked.failure:
            return r[m.Infra.GitBoolReport].fail(
                checked.error or "failed to inspect ancestry"
            )
        if checked.value.exit_code not in {0, 1}:
            detail = (checked.value.stderr or checked.value.stdout).strip()
            return r[m.Infra.GitBoolReport].fail(
                detail or "failed to inspect ancestry"
            )
        return r[m.Infra.GitBoolReport].ok(
            m.Infra.GitBoolReport(value=checked.value.exit_code == 0)
        )

    @classmethod
    def git_merge_no_edit(
        cls, request: m.Infra.GitCommitishRequest
    ) -> p.Result[m.Infra.GitTextReport]:
        """Merge ``commitish`` into HEAD with ``--no-edit``."""
        merged = git_capture(
            request.repo_root, ("merge", "--no-edit", request.commitish)
        )
        if merged.failure:
            return r[m.Infra.GitTextReport].fail(
                merged.error or f"merge failed for {request.commitish}"
            )
        return r[m.Infra.GitTextReport].ok(m.Infra.GitTextReport(text=merged.value))

    @classmethod
    def git_delete_ref(
        cls, request: m.Infra.GitDeleteRefRequest
    ) -> p.Result[m.Infra.GitBoolReport]:
        """CAS-delete a ref when it still points at ``expected_oid``."""
        deleted = git_capture(
            request.repo_root,
            ("update-ref", "-d", request.reference, request.expected_oid),
        )
        if deleted.failure:
            return r[m.Infra.GitBoolReport].fail(
                deleted.error or f"failed to delete ref {request.reference}"
            )
        return r[m.Infra.GitBoolReport].ok(m.Infra.GitBoolReport(value=True))

    @classmethod
    def git_fetch_origin(
        cls, request: m.Infra.GitRepoRequest
    ) -> p.Result[m.Infra.GitBoolReport]:
        """Fetch from origin."""
        fetched = git_capture(request.repo_root, ("fetch", "origin"))
        if fetched.failure:
            return r[m.Infra.GitBoolReport].fail(
                fetched.error or "failed to fetch origin"
            )
        return r[m.Infra.GitBoolReport].ok(m.Infra.GitBoolReport(value=True))

    @classmethod
    def git_push_upstream(
        cls, request: m.Infra.GitPushRequest
    ) -> p.Result[m.Infra.GitTextReport]:
        """Push HEAD to ``remote`` as ``refs/heads/<branch>`` with ``-u``."""
        pushed = git_capture(
            request.repo_root,
            (
                "push",
                "-u",
                request.remote,
                f"HEAD:refs/heads/{request.branch}",
            ),
        )
        if pushed.failure:
            return r[m.Infra.GitTextReport].fail(
                pushed.error or f"failed to push {request.branch}"
            )
        return r[m.Infra.GitTextReport].ok(m.Infra.GitTextReport(text=pushed.value))

    @classmethod
    def git_rev_parse(
        cls, request: m.Infra.GitCommitishRequest
    ) -> p.Result[m.Infra.GitOidReport]:
        """Resolve an arbitrary rev-parse argument to stripped text oid."""
        captured = git_capture(request.repo_root, ("rev-parse", request.commitish))
        if captured.failure:
            return r[m.Infra.GitOidReport].fail(
                captured.error or f"rev-parse failed for {request.commitish}"
            )
        return r[m.Infra.GitOidReport].ok(
            m.Infra.GitOidReport(oid=captured.value.strip())
        )

    @classmethod
    def git_checkout_restore(
        cls, request: m.Infra.GitRepoRequest
    ) -> p.Result[m.Infra.GitBoolReport]:
        """Restore tracked paths via ``git checkout -- .``."""
        restored = git_run(request.repo_root, ("checkout", "--", "."))
        if restored.failure:
            return r[m.Infra.GitBoolReport].fail(
                restored.error or "git checkout restore failed"
            )
        if restored.value.exit_code != 0:
            detail = (restored.value.stderr or restored.value.stdout).strip()
            return r[m.Infra.GitBoolReport].fail(
                detail or "git checkout restore failed"
            )
        return r[m.Infra.GitBoolReport].ok(m.Infra.GitBoolReport(value=True))

    @classmethod
    def git_mv_path(
        cls, request: m.Infra.GitPathPairRequest
    ) -> p.Result[m.Infra.GitBoolReport]:
        """Move a tracked path with ``git mv``."""
        moved = git_run(request.repo_root, ("mv", request.source, request.target))
        if moved.failure:
            return r[m.Infra.GitBoolReport].fail(
                moved.error or "git mv execution failed"
            )
        if moved.value.exit_code != 0:
            detail = (moved.value.stderr or moved.value.stdout).strip()
            return r[m.Infra.GitBoolReport].fail(detail or "git mv failed")
        return r[m.Infra.GitBoolReport].ok(m.Infra.GitBoolReport(value=True))

    @classmethod
    def git_rm_cached(
        cls, request: m.Infra.GitRelativePathRequest
    ) -> p.Result[m.Infra.GitBoolReport]:
        """Untrack a path with ``git rm --cached``."""
        untracked = git_run(
            request.repo_root,
            (
                "rm",
                "-r",
                "--cached",
                "--quiet",
                "--force",
                "--",
                request.relative_path,
            ),
        )
        if untracked.failure:
            return r[m.Infra.GitBoolReport].fail(
                untracked.error or "git rm execution failed"
            )
        if untracked.value.exit_code != 0:
            detail = (untracked.value.stderr or untracked.value.stdout).strip()
            return r[m.Infra.GitBoolReport].fail(detail or "git rm --cached failed")
        return r[m.Infra.GitBoolReport].ok(m.Infra.GitBoolReport(value=True))

    @classmethod
    def git_rm_path(
        cls, request: m.Infra.GitRelativePathRequest
    ) -> p.Result[m.Infra.GitBoolReport]:
        """Remove a tracked path with ``git rm``."""
        removed = git_run(
            request.repo_root, ("rm", "-q", "--", request.relative_path)
        )
        if removed.failure:
            return r[m.Infra.GitBoolReport].fail(
                removed.error or "git rm execution failed"
            )
        if removed.value.exit_code != 0:
            detail = (removed.value.stderr or removed.value.stdout).strip()
            return r[m.Infra.GitBoolReport].fail(detail or "git rm failed")
        return r[m.Infra.GitBoolReport].ok(m.Infra.GitBoolReport(value=True))

    @classmethod
    def git_is_tracked(
        cls, request: m.Infra.GitRelativePathRequest
    ) -> p.Result[m.Infra.GitBoolReport]:
        """Return whether a relative path is git-tracked."""
        listed = git_capture(
            request.repo_root, ("ls-files", "-z", "--", request.relative_path)
        )
        if listed.failure:
            return r[m.Infra.GitBoolReport].ok(m.Infra.GitBoolReport(value=False))
        return r[m.Infra.GitBoolReport].ok(
            m.Infra.GitBoolReport(value=bool(listed.value.strip()))
        )

    @classmethod
    def git_head_numstat(
        cls, request: m.Infra.GitRepoRequest
    ) -> p.Result[m.Infra.GitNumstatReport]:
        """Capture HEAD subject and ``HEAD~1..HEAD`` numstat."""
        subject_result = git_run(
            request.repo_root, ("log", "-1", "--format=%s"), timeout=30
        )
        if subject_result.failure:
            return r[m.Infra.GitNumstatReport].fail(
                subject_result.error or "git subject read failed"
            )
        if subject_result.value.exit_code != 0:
            return r[m.Infra.GitNumstatReport].fail(
                (subject_result.value.stderr or subject_result.value.stdout).strip()
                or "git subject read failed"
            )
        numstat_result = git_run(
            request.repo_root,
            ("diff", "--numstat", "HEAD~1", "HEAD"),
            timeout=30,
        )
        if numstat_result.failure:
            return r[m.Infra.GitNumstatReport].fail(
                numstat_result.error or "git numstat read failed"
            )
        if numstat_result.value.exit_code != 0:
            return r[m.Infra.GitNumstatReport].fail(
                (numstat_result.value.stderr or numstat_result.value.stdout).strip()
                or "git numstat read failed"
            )
        return r[m.Infra.GitNumstatReport].ok(
            m.Infra.GitNumstatReport(
                subject=subject_result.value.stdout.strip(),
                numstat=numstat_result.value.stdout,
            )
        )

    @classmethod
    def git_fingerprint_inputs(
        cls, request: m.Infra.GitRepoRequest
    ) -> p.Result[m.Infra.GitFingerprintInputsReport]:
        """Capture byte-exact fingerprint inputs for one worktree."""
        root = request.repo_root.expanduser().resolve()
        inside_result = git_capture(root, ("rev-parse", "--is-inside-work-tree"))
        if inside_result.failure or inside_result.value.strip() != "true":
            return r[m.Infra.GitFingerprintInputsReport].fail(
                inside_result.error or f"not a Git worktree: {root}"
            )
        paths_result = git_capture_bytes(
            root, ("ls-files", "-z", "--cached", "--others", "--exclude-standard")
        )
        if paths_result.failure:
            return r[m.Infra.GitFingerprintInputsReport].from_failure(paths_result)
        index_result = git_capture_bytes(root, ("ls-files", "--stage", "-z"))
        if index_result.failure:
            return r[m.Infra.GitFingerprintInputsReport].from_failure(index_result)
        head_result = git_capture_bytes(root, ("rev-parse", "--verify", "HEAD"))
        head = head_result.value.strip() if head_result.success else b"UNBORN"
        return r[m.Infra.GitFingerprintInputsReport].ok(
            m.Infra.GitFingerprintInputsReport(
                paths_z=paths_result.value,
                index_z=index_result.value,
                head=head,
            )
        )

    @classmethod
    def git_update_index_gitlink(
        cls, request: m.Infra.GitUpdateIndexGitlinkRequest
    ) -> p.Result[m.Infra.GitBoolReport]:
        """Stage one gitlink (mode 160000) into the index."""
        updated = git_capture(
            request.repo_root,
            (
                "update-index",
                "--add",
                "--cacheinfo",
                "160000",
                request.oid,
                request.relative_path,
            ),
        )
        if updated.failure:
            return r[m.Infra.GitBoolReport].fail(
                updated.error or "failed to update-index gitlink"
            )
        return r[m.Infra.GitBoolReport].ok(m.Infra.GitBoolReport(value=True))

    @classmethod
    def git_rev_parse_parent(
        cls, request: m.Infra.GitCommitishRequest
    ) -> p.Result[m.Infra.GitOidReport]:
        """Resolve ``commitish^`` via rev-parse."""
        captured = git_capture(
            request.repo_root, ("rev-parse", f"{request.commitish}^")
        )
        if captured.failure:
            return r[m.Infra.GitOidReport].fail(
                captured.error or f"failed to resolve parent of {request.commitish}"
            )
        return r[m.Infra.GitOidReport].ok(
            m.Infra.GitOidReport(oid=captured.value.strip())
        )

    @classmethod
    def git_add_lane_worktree(
        cls, request: m.Infra.GitWorktreeAddRequest
    ) -> p.Result[m.Infra.GitTextReport]:
        """Add a development lane worktree for an existing or new branch."""
        if request.local_branch_exists:
            arguments = (
                "worktree",
                "add",
                str(request.lane),
                request.branch,
            )
        elif request.track_remote:
            arguments = (
                "worktree",
                "add",
                "--track",
                "-b",
                request.branch,
                str(request.lane),
                f"origin/{request.branch}",
            )
        else:
            arguments = (
                "worktree",
                "add",
                "-b",
                request.branch,
                str(request.lane),
                request.base,
            )
        added = git_capture(request.repo_root, arguments)
        if added.failure:
            return r[m.Infra.GitTextReport].fail(
                added.error or f"failed to add worktree for {request.branch}"
            )
        return r[m.Infra.GitTextReport].ok(m.Infra.GitTextReport(text=added.value))


__all__: list[str] = ["FlextInfraUtilitiesGitSemanticMixin"]
