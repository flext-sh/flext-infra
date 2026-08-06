"""Typed semantic Git operations for consumers outside ``_git/``."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from git import GitCommandError, Repo
from git import BaseIndexEntry

from flext_core import r
from flext_infra._utilities._git.repo import FlextInfraUtilitiesGitRepo
from flext_infra._utilities._git.worktree import FlextInfraUtilitiesGitWorktreeMixin
from flext_infra.constants import c
from flext_infra.models import m

if TYPE_CHECKING:
    from flext_infra import p

_SSH_SCHEMES: frozenset[str] = frozenset({"ssh", "git+ssh"})
_SENSITIVE_QUERY_KEYS: frozenset[str] = frozenset({
    "access_token",
    "api_key",
    "apikey",
    "auth",
    "authorization",
    "bearer",
    "client_secret",
    "id_token",
    "jwt",
    "key",
    "oauth_token",
    "password",
    "passwd",
    "private_key",
    "private_token",
    "refresh_token",
    "secret",
    "token",
})
_REDACTED_PLACEHOLDER: str = "REDACTED"
_GITLINK_MODE: str = "160000"


def _redact_query_component(component: str) -> str:
    """Redact sensitive query/fragment key values; leave non-query text alone."""
    if not component or "=" not in component:
        return component
    pairs = parse_qsl(component, keep_blank_values=True)
    if not pairs:
        return component
    redacted = _REDACTED_PLACEHOLDER
    changed = False
    out: list[tuple[str, str]] = []
    for key, value in pairs:
        if key.casefold() in _SENSITIVE_QUERY_KEYS:
            out.append((key, redacted))
            changed = True
        else:
            out.append((key, value))
    if not changed:
        return component
    return urlencode(out)


def _redact_origin_remote(url: str) -> str:
    """Strip credential userinfo and sensitive query/fragment tokens."""
    value = url.strip()
    try:
        parsed = urlsplit(value)
    except ValueError:
        scheme_separator = value.find("://")
        if scheme_separator < 0:
            return value
        authority_start = scheme_separator + 3
        authority_end = len(value)
        for separator in "/?#":
            position = value.find(separator, authority_start)
            if position >= 0:
                authority_end = min(authority_end, position)
        authority = value[authority_start:authority_end]
        _, at, host = authority.rpartition("@")
        head = value[:authority_start] + host if at else value[:authority_end]
        rest = value[authority_end:]
        path_part = rest
        query = ""
        fragment = ""
        hash_idx = path_part.find("#")
        if hash_idx >= 0:
            fragment = path_part[hash_idx + 1 :]
            path_part = path_part[:hash_idx]
        query_idx = path_part.find("?")
        if query_idx >= 0:
            query = path_part[query_idx + 1 :]
            path_part = path_part[:query_idx]
        redacted_query = _redact_query_component(query)
        redacted_fragment = _redact_query_component(fragment)
        if not at and redacted_query == query and redacted_fragment == fragment:
            return value
        rebuilt = head + path_part
        if query_idx >= 0:
            rebuilt = f"{rebuilt}?{redacted_query}"
        if hash_idx >= 0:
            rebuilt = f"{rebuilt}#{redacted_fragment}"
        return rebuilt

    userinfo, at, host = parsed.netloc.rpartition("@")
    if at:
        if parsed.scheme in _SSH_SCHEMES and ":" not in userinfo:
            host = f"{userinfo}@{host}"
        netloc = host
    else:
        netloc = parsed.netloc
    query = _redact_query_component(parsed.query)
    fragment = _redact_query_component(parsed.fragment)
    if (
        netloc == parsed.netloc
        and query == parsed.query
        and fragment == parsed.fragment
    ):
        return value
    return urlunsplit((parsed.scheme, netloc, parsed.path, query, fragment))


class FlextInfraUtilitiesGitSemanticMixin(
    FlextInfraUtilitiesGitRepo, FlextInfraUtilitiesGitWorktreeMixin
):
    """Monomorphic Request/Report Git ops used by work/layout/saga consumers."""

    @classmethod
    def git_list_worktrees(
        cls, request: m.Infra.GitRepoRequest
    ) -> p.Result[m.Infra.GitTextReport]:
        """List registered worktrees in porcelain form."""
        try:
            repo = git_repo(request.repo_root)
            text = repo.git.worktree("list", "--porcelain")
        except GitCommandError as exc:
            return r[m.Infra.GitTextReport].fail(str(exc))
        except (OSError, ValueError) as exc:
            return r[m.Infra.GitTextReport].fail(f"failed to list Git worktrees: {exc}")
        return r[m.Infra.GitTextReport].ok(m.Infra.GitTextReport(text=text))

    @classmethod
    def git_check_branch_format(
        cls, request: m.Infra.GitBranchRequest
    ) -> p.Result[m.Infra.GitBoolReport]:
        """Validate a branch name with ``git check-ref-format --branch``."""
        try:
            repo = git_repo(request.repo_root)
            repo.git.check_ref_format("--branch", request.branch)
        except GitCommandError:
            return r[m.Infra.GitBoolReport].ok(m.Infra.GitBoolReport(value=False))
        except (OSError, ValueError) as exc:
            return r[m.Infra.GitBoolReport].fail(
                f"failed to validate branch name: {exc}"
            )
        return r[m.Infra.GitBoolReport].ok(m.Infra.GitBoolReport(value=True))

    @classmethod
    def git_ref_exists(
        cls, request: m.Infra.GitRefRequest
    ) -> p.Result[m.Infra.GitBoolReport]:
        """Return whether an exact Git ref exists (exit 0/1 only)."""
        try:
            repo = git_repo(request.repo_root)
            repo.git.show_ref("--verify", "--quiet", request.reference)
        except GitCommandError:
            # show-ref exits 1 when the ref does not exist — not an error.
            return r[m.Infra.GitBoolReport].ok(m.Infra.GitBoolReport(value=False))
        except (OSError, ValueError) as exc:
            return r[m.Infra.GitBoolReport].fail(f"failed to inspect Git ref: {exc}")
        return r[m.Infra.GitBoolReport].ok(m.Infra.GitBoolReport(value=True))

    @classmethod
    def git_superproject_working_tree(
        cls, request: m.Infra.GitRepoRequest
    ) -> p.Result[m.Infra.GitTextReport]:
        """Capture ``rev-parse --show-superproject-working-tree`` stdout."""
        try:
            repo = git_repo(request.repo_root)
            text = repo.git.rev_parse("--show-superproject-working-tree")
        except GitCommandError as exc:
            return r[m.Infra.GitTextReport].fail(str(exc))
        except (OSError, ValueError) as exc:
            return r[m.Infra.GitTextReport].fail(
                f"failed to resolve superproject working tree: {exc}"
            )
        return r[m.Infra.GitTextReport].ok(m.Infra.GitTextReport(text=text))

    @classmethod
    def git_show_toplevel(
        cls, request: m.Infra.GitRepoRequest
    ) -> p.Result[m.Infra.GitRootReport]:
        """Resolve ``rev-parse --show-toplevel`` as a workspace root report."""
        try:
            repo = git_repo(request.repo_root)
            root = (
                Path(repo.working_tree_dir).resolve() if repo.working_tree_dir else None
            )
            if root is None:
                return r[m.Infra.GitRootReport].fail(
                    "failed to resolve Git top level: working tree is None"
                )
        except GitCommandError as exc:
            return r[m.Infra.GitRootReport].fail(str(exc))
        except (OSError, ValueError) as exc:
            return r[m.Infra.GitRootReport].fail(
                f"failed to resolve Git top level: {exc}"
            )
        return r[m.Infra.GitRootReport].ok(m.Infra.GitRootReport(workspace_root=root))

    @classmethod
    def git_current_branch(
        cls, request: m.Infra.GitRepoRequest
    ) -> p.Result[m.Infra.GitTextReport]:
        """Resolve the current non-detached branch name."""
        try:
            repo = git_repo(request.repo_root)
            branch = repo.active_branch.name
        except GitCommandError as exc:
            return r[m.Infra.GitTextReport].fail(str(exc))
        except (TypeError, OSError, ValueError) as exc:
            # active_branch raises TypeError on detached HEAD.
            return r[m.Infra.GitTextReport].fail(
                f"head branch is required from a detached HEAD: {exc}"
            )
        return r[m.Infra.GitTextReport].ok(m.Infra.GitTextReport(text=branch))

    @classmethod
    def git_symbolic_ref_short(
        cls, request: m.Infra.GitRepoRequest
    ) -> p.Result[m.Infra.GitTextReport]:
        """Resolve ``symbolic-ref --quiet --short HEAD``."""
        try:
            repo = git_repo(request.repo_root)
            text = repo.git.symbolic_ref("--quiet", "--short", c.Infra.GIT_HEAD)
        except GitCommandError as exc:
            return r[m.Infra.GitTextReport].fail(str(exc))
        except (OSError, ValueError) as exc:
            return r[m.Infra.GitTextReport].fail(
                f"failed to resolve symbolic-ref HEAD: {exc}"
            )
        return r[m.Infra.GitTextReport].ok(m.Infra.GitTextReport(text=text.strip()))

    @classmethod
    def git_resolve_commit(
        cls, request: m.Infra.GitCommitishRequest
    ) -> p.Result[m.Infra.GitOidReport]:
        """Resolve a commit-ish to an oid via ``rev-parse --verify``."""
        try:
            repo = git_repo(request.repo_root)
            oid = repo.commit(request.commitish).hexsha
        except GitCommandError as exc:
            return r[m.Infra.GitOidReport].fail(str(exc))
        except (OSError, ValueError) as exc:
            return r[m.Infra.GitOidReport].fail(f"cannot resolve commitish: {exc}")
        return r[m.Infra.GitOidReport].ok(m.Infra.GitOidReport(oid=oid))

    @classmethod
    def git_abbrev_ref_head(
        cls, request: m.Infra.GitRepoRequest
    ) -> p.Result[m.Infra.GitTextReport]:
        """Resolve ``rev-parse --abbrev-ref HEAD``."""
        try:
            repo = git_repo(request.repo_root)
            branch = repo.active_branch.name
        except GitCommandError as exc:
            return r[m.Infra.GitTextReport].fail(str(exc))
        except (TypeError, OSError, ValueError):
            # Detached HEAD — fall back to the proxy for the ``HEAD`` text.
            try:
                detached_repo = git_repo(request.repo_root)
                text = detached_repo.git.rev_parse("--abbrev-ref", c.Infra.GIT_HEAD)
            except GitCommandError as exc:
                return r[m.Infra.GitTextReport].fail(str(exc))
            return r[m.Infra.GitTextReport].ok(m.Infra.GitTextReport(text=text.strip()))
        return r[m.Infra.GitTextReport].ok(m.Infra.GitTextReport(text=branch))

    @classmethod
    def git_is_ancestor(
        cls, request: m.Infra.GitCommitishRequest
    ) -> p.Result[m.Infra.GitBoolReport]:
        """Return whether ``commitish`` is an ancestor of HEAD."""
        try:
            repo = git_repo(request.repo_root)
            ancestor = repo.commit(request.commitish)
            head = repo.commit(c.Infra.GIT_HEAD)
            result = repo.is_ancestor(ancestor, head)
        except GitCommandError as exc:
            return r[m.Infra.GitBoolReport].fail(str(exc))
        except (OSError, ValueError) as exc:
            return r[m.Infra.GitBoolReport].fail(f"failed to inspect ancestry: {exc}")
        return r[m.Infra.GitBoolReport].ok(m.Infra.GitBoolReport(value=result))

    @classmethod
    def git_merge_no_edit(
        cls, request: m.Infra.GitCommitishRequest
    ) -> p.Result[m.Infra.GitTextReport]:
        """Merge ``commitish`` into HEAD with ``--no-edit``."""
        try:
            repo = git_repo(request.repo_root)
            text = repo.git.merge("--no-edit", request.commitish)
        except GitCommandError as exc:
            return r[m.Infra.GitTextReport].fail(str(exc))
        except (OSError, ValueError) as exc:
            return r[m.Infra.GitTextReport].fail(
                f"merge failed for {request.commitish}: {exc}"
            )
        return r[m.Infra.GitTextReport].ok(m.Infra.GitTextReport(text=text))

    @classmethod
    def git_delete_ref(
        cls, request: m.Infra.GitDeleteRefRequest
    ) -> p.Result[m.Infra.GitBoolReport]:
        """CAS-delete a ref when it still points at ``expected_oid``."""
        try:
            repo = git_repo(request.repo_root)
            repo.git.update_ref("-d", request.reference, request.expected_oid)
        except GitCommandError as exc:
            return r[m.Infra.GitBoolReport].fail(str(exc))
        except (OSError, ValueError) as exc:
            return r[m.Infra.GitBoolReport].fail(
                f"failed to delete ref {request.reference}: {exc}"
            )
        return r[m.Infra.GitBoolReport].ok(m.Infra.GitBoolReport(value=True))

    @classmethod
    def git_fetch_origin(
        cls, request: m.Infra.GitRepoRequest
    ) -> p.Result[m.Infra.GitBoolReport]:
        """Fetch from origin."""
        try:
            repo = git_repo(request.repo_root)
            repo.remotes[c.Infra.GIT_DEFAULT_REMOTE].fetch()
        except GitCommandError as exc:
            return r[m.Infra.GitBoolReport].fail(str(exc))
        except (OSError, ValueError, AssertionError) as exc:
            return r[m.Infra.GitBoolReport].fail(f"failed to fetch origin: {exc}")
        return r[m.Infra.GitBoolReport].ok(m.Infra.GitBoolReport(value=True))

    @classmethod
    def git_push_upstream(
        cls, request: m.Infra.GitPushRequest
    ) -> p.Result[m.Infra.GitTextReport]:
        """Push HEAD to ``remote`` as ``refs/heads/<branch>`` with ``-u``."""
        try:
            repo = git_repo(request.repo_root)
            text = repo.git.push(
                "-u", request.remote, f"HEAD:refs/heads/{request.branch}"
            )
        except GitCommandError as exc:
            return r[m.Infra.GitTextReport].fail(str(exc))
        except (OSError, ValueError) as exc:
            return r[m.Infra.GitTextReport].fail(
                f"failed to push {request.branch}: {exc}"
            )
        return r[m.Infra.GitTextReport].ok(m.Infra.GitTextReport(text=text))

    @classmethod
    def git_rev_parse(
        cls, request: m.Infra.GitCommitishRequest
    ) -> p.Result[m.Infra.GitOidReport]:
        """Resolve an arbitrary rev-parse argument to stripped text oid."""
        try:
            repo = git_repo(request.repo_root)
            oid = repo.git.rev_parse(request.commitish).strip()
        except GitCommandError as exc:
            return r[m.Infra.GitOidReport].fail(str(exc))
        except (OSError, ValueError) as exc:
            return r[m.Infra.GitOidReport].fail(
                f"rev-parse failed for {request.commitish}: {exc}"
            )
        return r[m.Infra.GitOidReport].ok(m.Infra.GitOidReport(oid=oid))

    @classmethod
    def git_checkout_restore(
        cls, request: m.Infra.GitRepoRequest
    ) -> p.Result[m.Infra.GitBoolReport]:
        """Restore tracked paths via ``git checkout -- .``."""
        try:
            repo = git_repo(request.repo_root)
            repo.git.checkout("--", ".")
        except GitCommandError as exc:
            return r[m.Infra.GitBoolReport].fail(str(exc))
        except (OSError, ValueError) as exc:
            return r[m.Infra.GitBoolReport].fail(f"git checkout restore failed: {exc}")
        return r[m.Infra.GitBoolReport].ok(m.Infra.GitBoolReport(value=True))

    @classmethod
    def git_mv_path(
        cls, request: m.Infra.GitPathPairRequest
    ) -> p.Result[m.Infra.GitBoolReport]:
        """Move a tracked path with ``git mv``."""
        try:
            repo = git_repo(request.repo_root)
            repo.index.move([request.source, request.target])
        except GitCommandError as exc:
            return r[m.Infra.GitBoolReport].fail(str(exc))
        except (OSError, ValueError) as exc:
            return r[m.Infra.GitBoolReport].fail(f"git mv failed: {exc}")
        return r[m.Infra.GitBoolReport].ok(m.Infra.GitBoolReport(value=True))

    @classmethod
    def git_rm_cached(
        cls, request: m.Infra.GitRelativePathRequest
    ) -> p.Result[m.Infra.GitBoolReport]:
        """Untrack a path with ``git rm --cached``."""
        try:
            repo = git_repo(request.repo_root)
            repo.index.remove([request.relative_path], cached=True, r=True, f=True)
        except GitCommandError as exc:
            return r[m.Infra.GitBoolReport].fail(str(exc))
        except (OSError, ValueError) as exc:
            return r[m.Infra.GitBoolReport].fail(f"git rm --cached failed: {exc}")
        return r[m.Infra.GitBoolReport].ok(m.Infra.GitBoolReport(value=True))

    @classmethod
    def git_rm_path(
        cls, request: m.Infra.GitRelativePathRequest
    ) -> p.Result[m.Infra.GitBoolReport]:
        """Remove a tracked path with ``git rm``."""
        try:
            repo = git_repo(request.repo_root)
            repo.index.remove([request.relative_path], cached=False, r=True, f=True)
        except GitCommandError as exc:
            return r[m.Infra.GitBoolReport].fail(str(exc))
        except (OSError, ValueError) as exc:
            return r[m.Infra.GitBoolReport].fail(f"git rm failed: {exc}")
        return r[m.Infra.GitBoolReport].ok(m.Infra.GitBoolReport(value=True))

    @classmethod
    def git_is_tracked(
        cls, request: m.Infra.GitRelativePathRequest
    ) -> p.Result[m.Infra.GitBoolReport]:
        """Return whether a relative path is git-tracked."""
        try:
            repo = git_repo(request.repo_root)
            listed = repo.git.ls_files("-z", "--", request.relative_path)
        except GitCommandError:
            return r[m.Infra.GitBoolReport].ok(m.Infra.GitBoolReport(value=False))
        except (OSError, ValueError) as exc:
            return r[m.Infra.GitBoolReport].fail(
                f"failed to check tracked status: {exc}"
            )
        return r[m.Infra.GitBoolReport].ok(
            m.Infra.GitBoolReport(value=bool(listed.strip()))
        )

    @classmethod
    def git_head_numstat(
        cls, request: m.Infra.GitRepoRequest
    ) -> p.Result[m.Infra.GitNumstatReport]:
        """Capture HEAD subject and ``HEAD~1..HEAD`` numstat."""
        try:
            repo = git_repo(request.repo_root)
            subject = repo.git.log("-1", "--format=%s")
            numstat = repo.git.diff("--numstat", "HEAD~1", c.Infra.GIT_HEAD)
        except GitCommandError as exc:
            return r[m.Infra.GitNumstatReport].fail(str(exc))
        except (OSError, ValueError) as exc:
            return r[m.Infra.GitNumstatReport].fail(f"git numstat read failed: {exc}")
        return r[m.Infra.GitNumstatReport].ok(
            m.Infra.GitNumstatReport(subject=subject.strip(), numstat=numstat)
        )

    @classmethod
    def git_fingerprint_inputs(
        cls, request: m.Infra.GitRepoRequest
    ) -> p.Result[m.Infra.GitFingerprintInputsReport]:
        """Capture byte-exact fingerprint inputs for one worktree."""
        try:
            repo = git_repo(request.repo_root)
            paths_z, index_z, head = cls._git_capture_fingerprint(repo)
        except GitCommandError as exc:
            return r[m.Infra.GitFingerprintInputsReport].fail(str(exc))
        except (OSError, ValueError) as exc:
            return r[m.Infra.GitFingerprintInputsReport].fail(
                f"failed to capture fingerprint inputs: {exc}"
            )
        return r[m.Infra.GitFingerprintInputsReport].ok(
            m.Infra.GitFingerprintInputsReport(
                paths_z=paths_z, index_z=index_z, head=head
            )
        )

    @staticmethod
    def _git_capture_fingerprint(repo: Repo) -> tuple[bytes, bytes, bytes]:
        """Capture (paths_z, index_z, head) bytes for fingerprinting."""
        paths_z = repo.git.ls_files(
            "-z", "--cached", "--others", "--exclude-standard"
        ).encode(c.Cli.ENCODING_DEFAULT)
        index_z = repo.git.ls_files("--stage", "-z").encode(c.Cli.ENCODING_DEFAULT)
        try:
            head = repo.head.commit.hexsha.encode(c.Cli.ENCODING_DEFAULT)
        except (ValueError, OSError):
            head = b"UNBORN"
        return paths_z, index_z, head

    @classmethod
    def git_gitlink_spec(
        cls, request: m.Infra.GitRefRequest
    ) -> p.Result[m.Infra.GitOidReport]:
        """Read the gitlink oid for one submodule path from the index."""
        try:
            repo = git_repo(request.repo_root)
            entry = repo.index.entries.get((request.reference, 0))
            if entry is None:
                return r[m.Infra.GitOidReport].fail(
                    f"gitlink is missing from index: {request.reference}"
                )
            if entry.mode != c.Infra.GIT_MODE_GITLINK:
                return r[m.Infra.GitOidReport].fail(
                    f"path is not a gitlink: {request.reference}"
                )
            oid = entry.hexsha
        except GitCommandError as exc:
            return r[m.Infra.GitOidReport].fail(str(exc))
        except (OSError, ValueError) as exc:
            return r[m.Infra.GitOidReport].fail(f"failed to read gitlink: {exc}")
        return r[m.Infra.GitOidReport].ok(m.Infra.GitOidReport(oid=oid))

    @classmethod
    def git_update_index_gitlink(
        cls, request: m.Infra.GitUpdateIndexGitlinkRequest
    ) -> p.Result[m.Infra.GitBoolReport]:
        """Stage one gitlink (mode 160000) into the index."""
        try:
            repo = git_repo(request.repo_root)
            entry = BaseIndexEntry((
                c.Infra.GIT_MODE_GITLINK,
                bytes.fromhex(request.oid),
                c.Infra.GIT_STAGE_NORMAL,
                request.relative_path,
            ))
            repo.index.add([entry])
        except GitCommandError as exc:
            return r[m.Infra.GitBoolReport].fail(str(exc))
        except (OSError, ValueError) as exc:
            return r[m.Infra.GitBoolReport].fail(
                f"failed to update-index gitlink: {exc}"
            )
        return r[m.Infra.GitBoolReport].ok(m.Infra.GitBoolReport(value=True))

    @classmethod
    def git_rev_parse_parent(
        cls, request: m.Infra.GitCommitishRequest
    ) -> p.Result[m.Infra.GitOidReport]:
        """Resolve ``commitish^`` via rev-parse."""
        try:
            repo = git_repo(request.repo_root)
            oid = repo.commit(f"{request.commitish}^").hexsha
        except GitCommandError as exc:
            return r[m.Infra.GitOidReport].fail(str(exc))
        except (OSError, ValueError) as exc:
            return r[m.Infra.GitOidReport].fail(
                f"failed to resolve parent of {request.commitish}: {exc}"
            )
        return r[m.Infra.GitOidReport].ok(m.Infra.GitOidReport(oid=oid))

    @classmethod
    def git_add_lane_worktree(
        cls, request: m.Infra.GitWorktreeAddRequest
    ) -> p.Result[m.Infra.GitTextReport]:
        """Add a development lane worktree for an existing or new branch."""
        try:
            repo = git_repo(request.repo_root)
            text = cls._git_add_worktree_args(repo, request)
        except GitCommandError as exc:
            return r[m.Infra.GitTextReport].fail(str(exc))
        except (OSError, ValueError) as exc:
            return r[m.Infra.GitTextReport].fail(
                f"failed to add worktree for {request.branch}: {exc}"
            )
        return r[m.Infra.GitTextReport].ok(m.Infra.GitTextReport(text=text))

    @staticmethod
    def _git_add_worktree_args(
        repo: Repo, request: m.Infra.GitWorktreeAddRequest
    ) -> str:
        """Select and execute the correct ``git worktree add`` variant."""
        if request.local_branch_exists:
            return repo.git.worktree("add", str(request.lane), request.branch)
        if request.track_remote:
            return repo.git.worktree(
                "add",
                "--track",
                "-b",
                request.branch,
                str(request.lane),
                f"origin/{request.branch}",
            )
        return repo.git.worktree(
            "add", "-b", request.branch, str(request.lane), request.base
        )

    @classmethod
    def git_add_paths(
        cls, request: m.Infra.GitPathsRequest
    ) -> p.Result[m.Infra.GitBoolReport]:
        """Stage multiple paths via ``git add --force``."""
        try:
            repo = git_repo(request.repo_root)
            repo.index.add(list(request.paths), force=True)
        except GitCommandError as exc:
            return r[m.Infra.GitBoolReport].fail(str(exc))
        except (OSError, ValueError) as exc:
            return r[m.Infra.GitBoolReport].fail(f"git add failed: {exc}")
        return r[m.Infra.GitBoolReport].ok(m.Infra.GitBoolReport(value=True))

    @classmethod
    def git_restore_paths(
        cls, request: m.Infra.GitCheckoutPathsRequest
    ) -> p.Result[m.Infra.GitBoolReport]:
        """Restore tracked paths via ``git checkout --``."""
        try:
            repo = git_repo(request.repo_root)
            if request.paths:
                repo.index.checkout(paths=list(request.paths), force=True)
            else:
                repo.git.checkout("--", ".")
        except GitCommandError as exc:
            return r[m.Infra.GitBoolReport].fail(str(exc))
        except (OSError, ValueError) as exc:
            return r[m.Infra.GitBoolReport].fail(f"git restore failed: {exc}")
        return r[m.Infra.GitBoolReport].ok(m.Infra.GitBoolReport(value=True))

    @classmethod
    def git_commit(
        cls, request: m.Infra.GitCommitRequest
    ) -> p.Result[m.Infra.GitOidReport]:
        """Create a commit with the staged tree via ``git commit``."""
        try:
            repo = git_repo(request.repo_root)
            commit = repo.index.commit(request.message)
        except GitCommandError as exc:
            return r[m.Infra.GitOidReport].fail(str(exc))
        except (OSError, ValueError) as exc:
            return r[m.Infra.GitOidReport].fail(f"git commit failed: {exc}")
        return r[m.Infra.GitOidReport].ok(m.Infra.GitOidReport(oid=commit.hexsha))

    @classmethod
    def git_remote_url(
        cls, request: m.Infra.GitRemoteUrlRequest
    ) -> p.Result[m.Infra.GitTextReport]:
        """Resolve ``remote get-url <remote>`` as a text report."""
        try:
            repo = git_repo(request.repo_root)
            url = repo.remotes[request.remote].url
        except GitCommandError as exc:
            return r[m.Infra.GitTextReport].fail(str(exc))
        except (OSError, ValueError, IndexError, AssertionError) as exc:
            return r[m.Infra.GitTextReport].fail(f"failed to resolve remote URL: {exc}")
        return r[m.Infra.GitTextReport].ok(m.Infra.GitTextReport(text=url))

    @classmethod
    def git_identity(
        cls, request: m.Infra.GitRepoRequest
    ) -> p.Result[m.Infra.GitIdentityReport]:
        """Return consolidated Git identity for one repository path.

        One call replaces 6+ separate queries. Implemented over GitPython
        native OO API.
        """
        repo_result = git_open_repo(request.repo_root)
        if repo_result.failure:
            # Path is not a Git repository — return an identity report with
            # is_inside_work_tree=False so callers can classify as standalone.
            resolved = request.repo_root.expanduser().resolve()
            return r[m.Infra.GitIdentityReport].ok(
                m.Infra.GitIdentityReport(
                    repo_root=resolved,
                    head_oid="",
                    porcelain="",
                    dirty=False,
                    git_dir=resolved / ".git",
                    common_dir=resolved / ".git",
                    branch=None,
                    origin_remote=None,
                    superproject_root=None,
                    requested_path=request.repo_root,
                    is_worktree=False,
                    is_submodule=False,
                    has_submodules=False,
                    is_inside_work_tree=False,
                )
            )
        report = cls._collect_identity_facts(
            repo_result.value, requested_path=request.repo_root
        )
        return r[m.Infra.GitIdentityReport].ok(report)

    @staticmethod
    def _collect_identity_facts(
        repo: Repo, *, requested_path: Path | None = None
    ) -> m.Infra.GitIdentityReport:
        """Collect GitPython-native identity facts into one report."""
        head_oid = repo.head.commit.hexsha
        working_tree = Path(repo.working_tree_dir or str(repo.working_dir)).resolve()
        git_dir = Path(repo.git_dir).resolve()
        common_dir = Path(repo.common_dir).resolve()
        porcelain = repo.git.status("--porcelain", "--untracked-files=all")
        try:
            branch: str | None = repo.active_branch.name
        except TypeError:
            branch = None
        try:
            origin: str | None = repo.remotes["origin"].url
        except (IndexError, AssertionError):
            origin = None
        origin_remote = _redact_origin_remote(origin) if origin else None
        superproject: Path | None = None
        try:
            raw_super = repo.git.rev_parse("--show-superproject-working-tree").strip()
            if raw_super:
                superproject = Path(raw_super).resolve()
        except GitCommandError:
            pass

        is_worktree = git_dir != common_dir
        has_submodules = any(
            line.startswith(f"{_GITLINK_MODE} ") for line in porcelain.splitlines()
        )
        git_entry = working_tree / ".git"
        is_submodule = (
            superproject is not None and git_entry.exists() and not git_entry.is_dir()
        )

        return m.Infra.GitIdentityReport(
            repo_root=working_tree,
            head_oid=head_oid,
            porcelain=porcelain,
            dirty=bool(porcelain.strip()),
            git_dir=git_dir,
            common_dir=common_dir,
            branch=branch,
            origin_remote=origin_remote,
            superproject_root=superproject,
            requested_path=requested_path,
            is_worktree=is_worktree,
            is_submodule=is_submodule,
            has_submodules=has_submodules,
            is_inside_work_tree=bool(repo.working_tree_dir),
        )

    @classmethod
    def gitmodule_contract(
        cls, request: m.Infra.GitSubmoduleContractRequest
    ) -> p.Result[m.Infra.GitSubmoduleContractReport]:
        """Read the exact URL and branch for one declared Git submodule path."""
        try:
            repo = git_repo(request.repo_root)
            output = repo.git.config(
                "--file",
                c.Infra.GITMODULES,
                "--get-regexp",
                r"^submodule\..*\.path$",
            )
        except GitCommandError as exc:
            return r[m.Infra.GitSubmoduleContractReport].fail(str(exc))
        except (OSError, ValueError) as exc:
            return r[m.Infra.GitSubmoduleContractReport].fail(
                f"failed to read Git submodule declarations: {exc}"
            )
        matching_keys: list[str] = []
        for line in output.splitlines():
            if not line.strip():
                continue
            match line.split(maxsplit=1):
                case [key, path] if path == request.member_path:
                    matching_keys.append(key)
                case [_, _]:
                    continue
                case _:
                    return r[m.Infra.GitSubmoduleContractReport].fail(
                        "malformed Git submodule path entry"
                    )
        if len(matching_keys) != 1:
            return r[m.Infra.GitSubmoduleContractReport].fail(
                f"Git submodule path must be declared exactly once: {request.member_path}"
            )
        section = matching_keys[0].removesuffix(".path")
        try:
            url = repo.git.config(
                "--file", c.Infra.GITMODULES, "--get", f"{section}.url"
            )
            branch = repo.git.config(
                "--file", c.Infra.GITMODULES, "--get", f"{section}.branch"
            )
        except GitCommandError as exc:
            return r[m.Infra.GitSubmoduleContractReport].fail(str(exc))
        return r[m.Infra.GitSubmoduleContractReport].ok(
            m.Infra.GitSubmoduleContractReport(url=url, branch=branch)
        )


__all__: list[str] = ["FlextInfraUtilitiesGitSemanticMixin"]
