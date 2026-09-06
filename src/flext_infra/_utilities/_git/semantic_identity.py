"""Canonical Git responsibility mixin for ``u.Infra``."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from git import (
    GitCommandError,
    GitCommandNotFound,
    InvalidGitRepositoryError,
    NoSuchPathError,
    Repo,
)

from flext_core import r
from flext_infra.models import m

from ..._utilities._git.remote import redact_origin_remote
from ..._utilities._git.repo import FlextInfraUtilitiesGitRepo
from ..._utilities._git.semantic_worktree import (
    FlextInfraUtilitiesGitSemanticWorktreeMixin,
)

if TYPE_CHECKING:
    from flext_infra import p

_GITLINK_MODE = "160000"


class FlextInfraUtilitiesGitSemanticIdentityMixin(
    FlextInfraUtilitiesGitSemanticWorktreeMixin
):
    """Own semantic identity operations."""

    @classmethod
    def git_identity(
        cls, request: m.Infra.GitRepoRequest
    ) -> p.Result[m.Infra.GitIdentityReport]:
        """Return consolidated Git identity for one repository path.

        One call replaces 6+ separate queries. Implemented over GitPython
        native OO API.
        """
        try:
            repo = cls._repo(request.repo_root)
            if not repo.head.is_valid():
                return r[m.Infra.GitIdentityReport].fail(
                    f"Git repository has no committed HEAD: {request.repo_root.resolve()}"
                )
            primary = cls._git_primary_worktree_root_path(request.repo_root)
            if primary.failure:
                return r[m.Infra.GitIdentityReport].from_failure(primary)
            report = cls._collect_identity_facts(
                repo, primary_root=primary.value, requested_path=request.repo_root
            )
        except GitCommandError as exc:
            return r[m.Infra.GitIdentityReport].fail(str(exc), exception=exc)
        except (OSError, ValueError) as exc:
            return r[m.Infra.GitIdentityReport].fail(
                f"failed to resolve Git identity: {exc}", exception=exc
            )
        return r[m.Infra.GitIdentityReport].ok(report)

    @classmethod
    def git_is_inside_work_tree(
        cls, request: m.Infra.GitRepoRequest
    ) -> p.Result[m.Infra.GitBoolReport]:
        """Return whether ``repo_root`` sits inside a Git work tree.

        Three-way contract mirroring ``rev-parse --is-inside-work-tree``:
        ``ok(False)`` when no repository owns the path (the expected
        non-error case), ``fail`` only on genuine probe errors.
        """
        refreshed = FlextInfraUtilitiesGitRepo.refresh_binary()
        if refreshed.failure:
            return r[m.Infra.GitBoolReport].from_failure(refreshed)
        resolved = request.repo_root.expanduser().resolve()
        try:
            # Why (flext-infra-c3h): same nested-path contract as git_open_repo.
            repo = Repo(resolved, search_parent_directories=True)
        except (InvalidGitRepositoryError, NoSuchPathError):
            return r[m.Infra.GitBoolReport].ok(m.Infra.GitBoolReport(value=False))
        except (GitCommandNotFound, OSError, ValueError) as exc:
            return r[m.Infra.GitBoolReport].fail(
                f"failed to probe Git work tree: {exc}", exception=exc
            )
        return r[m.Infra.GitBoolReport].ok(
            m.Infra.GitBoolReport(
                value=not repo.bare and repo.working_tree_dir is not None
            )
        )

    @classmethod
    def _collect_identity_facts(
        cls, repo: Repo, *, primary_root: Path, requested_path: Path | None = None
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
        remotes = {remote.name: remote.url for remote in repo.remotes}
        origin = remotes.get("origin")
        upstream = remotes.get("upstream")
        origin_remote = redact_origin_remote(origin) if origin else None
        upstream_remote = redact_origin_remote(upstream) if upstream else None
        raw_super = repo.git.rev_parse("--show-superproject-working-tree").strip()
        if not raw_super and primary_root != working_tree:
            primary_repo = cls._repo(primary_root)
            raw_super = primary_repo.git.rev_parse(
                "--show-superproject-working-tree"
            ).strip()
        superproject = Path(raw_super).resolve() if raw_super else None

        is_worktree = git_dir != common_dir
        # Gitlink modes live in the index, never in `status --porcelain` (which
        # emits XY status codes and paths, never file modes). Reading them from
        # the porcelain text made has_submodules unconditionally False, so a
        # real submodule superproject was never recognized as one.
        staged_entries = repo.git.ls_files("--stage")
        has_submodules = any(
            line.startswith(f"{_GITLINK_MODE} ") for line in staged_entries.splitlines()
        )
        # Why (flext-2cafk / ai-hub-n1nh.5): git rev-parse --show-superproject-
        # working-tree already means "this working tree is a submodule".
        # Requiring .git to be a gitfile excluded absorbed/converted submodules
        # whose .git is a real directory (cosmos-charts under cosmos-main), so
        # is_submodule stayed False and ai-hub demoted them to unmanaged.
        is_submodule = superproject is not None
        is_attached_submodule = (
            superproject is not None and working_tree.is_relative_to(superproject)
        )

        return m.Infra.GitIdentityReport(
            repo_root=working_tree,
            primary_root=primary_root,
            head_oid=head_oid,
            porcelain=porcelain,
            dirty=bool(porcelain.strip()),
            git_dir=git_dir,
            common_dir=common_dir,
            branch=branch,
            origin_remote=origin_remote,
            upstream_remote=upstream_remote,
            is_inside_work_tree=True,
            superproject_root=superproject,
            requested_path=requested_path,
            is_worktree=is_worktree,
            is_submodule=is_submodule,
            is_attached_submodule=is_attached_submodule,
            has_submodules=has_submodules,
        )


__all__: list[str] = ["FlextInfraUtilitiesGitSemanticIdentityMixin"]
