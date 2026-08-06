"""Canonical Git worktree, checkpoint, and patch operations for ``u.Infra``."""

from __future__ import annotations

import tempfile
from collections.abc import Generator
from typing import BinaryIO
from contextlib import contextmanager
from pathlib import Path
from typing import TYPE_CHECKING
from urllib.parse import urlparse

from git import GitCommandError

from flext_cli import u
from flext_core import r
from flext_infra._utilities._git.repo import FlextInfraUtilitiesGitRepo
from flext_infra.constants import c
from flext_infra.models import m
from flext_infra.typings import t

if TYPE_CHECKING:
    from flext_infra import p


@contextmanager
def _git_stdin(data: bytes | None) -> Generator[BinaryIO | None]:
    """Yield a fileno-backed stdin for one GitPython proxy ``istream`` call."""
    if data is None:
        yield None
        return
    with tempfile.TemporaryFile() as stream:
        stream.write(data)
        stream.seek(0)
        yield stream


class FlextInfraUtilitiesGitWorktreeMixin(FlextInfraUtilitiesGitRepo):
    """Extend the existing Git utility owner with isolated mutation primitives.

    Public argv helpers are forbidden — use typed ``git_*`` Request/Report
    methods. All Git interaction flows through GitPython's object-oriented API
    (``Repo``, ``IndexFile``, ``BaseIndexEntry``) or the ``repo.git.<cmd>``
    proxy — never ``Git(path).execute(tuple)``.
    """

    @classmethod
    def git_status(
        cls, request: m.Infra.GitStatusRequest
    ) -> p.Result[m.Infra.GitStatusReport]:
        """Capture porcelain status for one repository."""
        repo_path = request.repo_root.expanduser().resolve()
        try:
            repo = cls._repo(repo_path)
            porcelain = repo.git.status("--porcelain", "--untracked-files=all")
        except GitCommandError as exc:
            return r[m.Infra.GitStatusReport].fail(str(exc))
        except (OSError, ValueError) as exc:
            return r[m.Infra.GitStatusReport].fail(f"git status failed: {exc}")
        return r[m.Infra.GitStatusReport].ok(
            m.Infra.GitStatusReport(
                repo_root=repo_path, porcelain=porcelain, dirty=bool(porcelain.strip())
            )
        )

    @classmethod
    def git_repository_head(
        cls, request: m.Infra.GitRepoRequest
    ) -> p.Result[m.Infra.GitOidReport]:
        """Capture the current repository HEAD as a typed oid report."""
        oid = cls._git_head_oid(request.repo_root)
        if oid.failure:
            return r[m.Infra.GitOidReport].fail(oid.error or "failed to resolve HEAD")
        return r[m.Infra.GitOidReport].ok(m.Infra.GitOidReport(oid=oid.value))

    @classmethod
    def git_workspace_root(
        cls, request: m.Infra.GitRepoRequest
    ) -> p.Result[m.Infra.GitRootReport]:
        """Resolve the superproject root or the repository's own top level."""
        root = cls._git_workspace_root_path(request.repo_root)
        if root.failure:
            return r[m.Infra.GitRootReport].fail(
                root.error or "failed to resolve workspace root"
            )
        return r[m.Infra.GitRootReport].ok(
            m.Infra.GitRootReport(workspace_root=root.value)
        )

    @classmethod
    def git_primary_worktree_root(
        cls, request: m.Infra.GitRepoRequest
    ) -> p.Result[m.Infra.GitPrimaryRootReport]:
        """Resolve the primary worktree from Git's canonical storage topology."""
        primary = cls._git_primary_worktree_root_path(request.repo_root)
        if primary.failure:
            return r[m.Infra.GitPrimaryRootReport].fail(
                primary.error or "failed to resolve primary worktree"
            )
        return r[m.Infra.GitPrimaryRootReport].ok(
            m.Infra.GitPrimaryRootReport(primary_root=primary.value)
        )

    @classmethod
    def _git_head_oid(cls, repo_root: Path) -> p.Result[str]:
        """Private Path-based HEAD oid resolver for facet-internal callers."""
        opened = cls._open_repo(repo_root)
        if opened.failure:
            return r[str].fail(opened.error or "failed to open git repository")
        try:
            return r[str].ok(opened.value.head.commit.hexsha)
        except (ValueError, TypeError, OSError) as exc:
            return r[str].fail(f"failed to resolve HEAD: {exc}")

    @classmethod
    def _git_workspace_root_path(cls, repository_path: Path) -> p.Result[Path]:
        """Private Path-based workspace/superproject resolver."""
        try:
            repo = cls._repo(repository_path)
            superproject = repo.git.rev_parse(
                "--show-superproject-working-tree"
            ).strip()
        except GitCommandError:
            # Not inside any superproject — check if we're in a worktree at all.
            try:
                fallback_repo = cls._repo(repository_path)
                inside = fallback_repo.git.rev_parse("--is-inside-work-tree").strip()
            except GitCommandError:
                return r[Path].ok(repository_path.expanduser().resolve())
            if inside != "true":
                return r[Path].ok(repository_path.expanduser().resolve())
            return r[Path].fail("failed to resolve Git superproject")
        except (OSError, ValueError) as exc:
            return r[Path].fail(f"failed to resolve workspace root: {exc}")
        if superproject:
            return r[Path].ok(Path(superproject).resolve())
        try:
            top_level = repo.git.rev_parse("--show-toplevel").strip()
        except GitCommandError as exc:
            return r[Path].fail(str(exc))
        return r[Path].ok(Path(top_level).resolve())

    @classmethod
    def _git_primary_worktree_root_path(cls, repository_path: Path) -> p.Result[Path]:
        """Private Path-based primary worktree resolver."""
        try:
            repo = cls._repo(repository_path)
            common_dir_text = repo.git.rev_parse(
                "--path-format=absolute", "--git-common-dir"
            ).strip()
            common_dir = Path(common_dir_text).resolve()
            configured_output = repo.git.config(
                "--path", "--get", "core.worktree", with_exceptions=False
            ).strip()
        except GitCommandError as exc:
            return r[Path].fail(str(exc))
        except (OSError, ValueError) as exc:
            return r[Path].fail(f"failed to resolve primary worktree: {exc}")

        if configured_output:
            configured = Path(configured_output)
            primary_root = (
                configured if configured.is_absolute() else common_dir / configured
            ).resolve()
        elif common_dir.name == c.Infra.GIT_DIR:
            primary_root = common_dir.parent
        else:
            try:
                git_dir_text = repo.git.rev_parse(
                    "--path-format=absolute", "--git-dir"
                ).strip()
                git_dir = Path(git_dir_text).resolve()
            except GitCommandError as exc:
                return r[Path].fail(str(exc))
            if git_dir != common_dir:
                listed = repo.git.worktree("list", "--porcelain")
                registered = tuple(
                    Path(line.removeprefix("worktree ").strip()).resolve()
                    for line in listed.splitlines()
                    if line.startswith("worktree ")
                )
                if not registered:
                    return r[Path].fail(
                        f"Git worktree registry is empty for {repository_path}"
                    )
                primary_root = registered[0]
                # Verify primary_root is a real worktree top-level by opening
                # a separate repo context against it.
                primary_repo_result = cls._open_repo(primary_root)
                if primary_repo_result.failure:
                    caller_top = repo.git.rev_parse("--show-toplevel").strip()
                    caller_root = Path(caller_top).resolve()
                    if caller_root not in registered:
                        return r[Path].fail(
                            "current worktree is absent from Git's canonical registry: "
                            f"{caller_root}"
                        )
                    primary_root = caller_root
            else:
                caller_top = repo.git.rev_parse("--show-toplevel").strip()
                primary_root = Path(caller_top).resolve()

        # Verify the resolved primary_root is a valid worktree top-level.
        primary_repo_result = cls._open_repo(primary_root)
        if primary_repo_result.failure:
            return r[Path].fail(
                f"invalid primary worktree: {primary_root}: {primary_repo_result.error}"
            )
        try:
            resolved_top = Path(
                primary_repo_result.value.git.rev_parse("--show-toplevel").strip()
            ).resolve()
        except GitCommandError as exc:
            return r[Path].fail(f"invalid primary worktree: {primary_root}: {exc}")
        if resolved_top != primary_root:
            return r[Path].fail(
                f"Git primary worktree mismatch: {primary_root} != {resolved_top}"
            )
        return r[Path].ok(primary_root)

    @staticmethod
    def git_remote_identity(url: str) -> str:
        """Normalize remotes to owner/repo identity across HTTPS, SSH, and aliases.

        CI deploy-key init rewrites private member ``origin`` to an SSH URL that
        may use a Host alias (for example ``git@charts-github:org/repo.git``)
        while the workspace manifest and ``.gitmodules`` keep HTTPS on
        ``github.com``. Compare the repository path only so gen does not
        false-fail after a successful private checkout.
        """
        value = url.strip().removesuffix(".git")
        remote_path = ""
        if value.startswith("git@"):
            host_path = value.removeprefix("git@")
            if ":" in host_path:
                _host, remote_path = host_path.split(":", 1)
        else:
            parsed = urlparse(value)
            if parsed.scheme in {"http", "https", "ssh"} and parsed.netloc:
                remote_path = parsed.path.lstrip("/")
            else:
                remote_path = value
        parts = [part for part in remote_path.split("/") if part]
        match parts:
            case [*_, owner, repo]:
                return f"{owner}/{repo}".lower()
            case _:
                return remote_path.lower()

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
        try:
            repo = cls._repo(repository_root)
            output = repo.git.config(
                "--file",
                c.Infra.GITMODULES,
                "--get-regexp",
                r"^submodule\..*\.path$",
                with_exceptions=False,
            )
        except GitCommandError as exc:
            return r[t.SequenceOf[Path]].fail(str(exc))
        except (OSError, ValueError) as exc:
            return r[t.SequenceOf[Path]].fail(
                f"failed to read Git submodule declarations: {exc}"
            )
        if not output.strip():
            return r[t.SequenceOf[Path]].ok(())
        paths: t.MutableSequenceOf[Path] = []
        for raw_line in output.splitlines():
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
    def gitmodule_contract(
        cls, request: m.Infra.GitSubmoduleContractRequest
    ) -> p.Result[m.Infra.GitSubmoduleContractReport]:
        """Read the exact declared URL and branch for one submodule path.

        The path must be declared exactly once in ``.gitmodules``; a missing
        URL or branch fails closed.
        """
        try:
            repo = cls._repo(request.repo_root)
            entries = repo.git.config(
                "--file", c.Infra.GITMODULES, "--get-regexp", r"^submodule\..*\.path$"
            )
        except GitCommandError as exc:
            return r[m.Infra.GitSubmoduleContractReport].fail(str(exc))
        except (OSError, ValueError) as exc:
            return r[m.Infra.GitSubmoduleContractReport].fail(
                f"failed to read Git submodule paths: {exc}"
            )
        matching_sections: t.MutableSequenceOf[str] = []
        for line in entries.splitlines():
            if not line.strip():
                continue
            match line.split(maxsplit=1):
                case [key, path] if path == request.member_path:
                    matching_sections.append(key.removesuffix(".path"))
                case [_, _]:
                    continue
                case _:
                    return r[m.Infra.GitSubmoduleContractReport].fail(
                        "malformed Git submodule path entry"
                    )
        if len(matching_sections) != 1:
            return r[m.Infra.GitSubmoduleContractReport].fail(
                "Git submodule path must be declared exactly once: "
                f"{request.member_path}"
            )
        section = matching_sections[0]
        try:
            url = repo.git.config(
                "--file", c.Infra.GITMODULES, "--get", f"{section}.url"
            ).strip()
        except GitCommandError:
            url = ""
        except (OSError, ValueError) as exc:
            return r[m.Infra.GitSubmoduleContractReport].fail(
                f"failed to read Git submodule URL: {exc}"
            )
        if not url:
            return r[m.Infra.GitSubmoduleContractReport].fail(
                f"Git submodule URL is missing: {request.member_path}"
            )
        try:
            branch = repo.git.config(
                "--file", c.Infra.GITMODULES, "--get", f"{section}.branch"
            ).strip()
        except GitCommandError:
            branch = ""
        except (OSError, ValueError) as exc:
            return r[m.Infra.GitSubmoduleContractReport].fail(
                f"failed to read Git submodule branch: {exc}"
            )
        if not branch:
            return r[m.Infra.GitSubmoduleContractReport].fail(
                f"Git submodule branch is missing: {request.member_path}"
            )
        return r[m.Infra.GitSubmoduleContractReport].ok(
            m.Infra.GitSubmoduleContractReport(url=url, branch=branch)
        )

    @classmethod
    def git_submodule_paths(cls, workspace_root: Path) -> p.Result[t.SequenceOf[Path]]:
        """Resolve every initialized recursive submodule path."""
        try:
            repo = cls._repo(workspace_root)
            status = repo.git.submodule("status", "--recursive")
        except GitCommandError as exc:
            return r[t.SequenceOf[Path]].fail(str(exc))
        except (OSError, ValueError) as exc:
            return r[t.SequenceOf[Path]].fail(
                f"failed to discover Git submodules: {exc}"
            )
        paths: t.MutableSequenceOf[Path] = []
        for raw_line in status.splitlines():
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
        head_result = cls._git_head_oid(source_root)
        if head_result.failure:
            return head_result
        # An isolated transaction is a generator-validation boundary, not a user
        # checkout. Host post-checkout hooks may depend on a toolchain which the
        # generated project is about to declare, so they cannot be its prerequisite.
        # Transaction validators still exercise the generated artifact explicitly.
        try:
            repo = cls._repo(source_root)
            repo.git.execute([
                c.Infra.GIT,
                "-c",
                "core.hooksPath=/dev/null",
                "worktree",
                "add",
                "--detach",
                str(worktree_root),
                head_result.value,
            ])
        except GitCommandError as exc:
            return r[str].fail(str(exc))
        except (OSError, ValueError) as exc:
            return r[str].fail(f"failed to add detached worktree: {exc}")
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
        try:
            repo = cls._repo(source_root)
            untracked = repo.git.ls_files("--others", "--exclude-standard", "-z")
        except GitCommandError as exc:
            return r[bool].fail(str(exc))
        except (OSError, ValueError) as exc:
            return r[bool].fail(f"failed to list untracked files: {exc}")
        for raw_path in untracked.split("\0"):
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
        try:
            repo = cls._repo(source_root)
            patch_bytes = repo.git.diff(
                "--binary", c.Infra.GIT_HEAD, "--", ".", *pathspecs
            ).encode(c.Cli.ENCODING_DEFAULT)
        except GitCommandError as exc:
            return r[bool].fail(str(exc))
        except (OSError, ValueError) as exc:
            return r[bool].fail(f"failed to capture dirty patch: {exc}")
        if patch_bytes:
            # git apply rejects a patch whose final line lacks the terminating
            # newline ("corrupt patch"); `git diff --binary` can emit exactly
            # that, so restore the single trailing newline the format requires.
            if not patch_bytes.endswith(b"\n"):
                patch_bytes += b"\n"
            try:
                worktree_repo = cls._repo(worktree_root)
                with _git_stdin(patch_bytes) as istream:
                    worktree_repo.git.apply("--binary", "-", istream=istream)
            except GitCommandError as exc:
                return r[bool].fail(str(exc))
            except (OSError, ValueError) as exc:
                return r[bool].fail(f"dirty patch did not apply: {exc}")
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
        try:
            commit_sha = cls._git_create_checkpoint_commit(
                worktree_root, gitlink_exclusions, excluded, message
            )
        except GitCommandError as exc:
            return r[str].fail(str(exc))
        except (OSError, ValueError) as exc:
            return r[str].fail(f"failed to create checkpoint: {exc}")
        return r[str].ok(commit_sha)

    @classmethod
    def _git_create_checkpoint_commit(
        cls,
        worktree_root: Path,
        gitlink_exclusions: tuple[str, ...],
        excluded: t.SequenceOf[Path],
        message: str,
    ) -> str:
        """Stage all state and create a synthetic checkpoint commit-tree."""
        repo = cls._repo(worktree_root)
        if excluded:
            tracked_output = repo.git.ls_files(
                "-z",
                "--cached",
                "--others",
                "--exclude-standard",
                "--",
                ".",
                *(f":(exclude){path.as_posix()}" for path in excluded),
            )
            tracked_paths = tuple(path for path in tracked_output.split("\0") if path)
            if tracked_paths:
                repo.git.add("-A", "-f", "--", *tracked_paths, *gitlink_exclusions)
        else:
            # `-f` matches the tracked-paths branch and the operation delta:
            # the checkpoint must capture ignored-but-tracked paths.
            repo.git.add("-A", "-f", "--", *gitlink_exclusions)
        tree = repo.git.write_tree().strip()
        parent_result = cls._git_head_oid(worktree_root)
        if parent_result.failure:
            raise OSError(parent_result.error or "failed to resolve checkpoint parent")
        parent = parent_result.value
        identity_output = repo.git.show("-s", "--format=%an%x00%ae", parent).rstrip(
            "\n"
        )
        identity = identity_output.split("\0")
        match identity:
            case [author_name, author_email] if (
                author_name.strip() and author_email.strip()
            ):
                pass
            case _:
                detail = "checkpoint parent has invalid author identity"
                raise OSError(detail)
        commit_sha = str(
            repo.git.execute([
                c.Infra.GIT,
                "-c",
                f"user.name={author_name}",
                "-c",
                f"user.email={author_email}",
                "commit-tree",
                tree,
                "-p",
                parent,
                "-m",
                message,
            ])
        ).strip()
        repo.git.update_ref(c.Infra.GIT_HEAD, commit_sha)
        return commit_sha

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
        head_result = cls._git_head_oid(repository.worktree_root)
        if head_result.failure or head_result.value != repository.checkpoint_sha:
            return r[m.Infra.RepositoryDelta].fail(
                head_result.error
                if head_result.failure
                else "isolated command moved repository HEAD"
            )
        exclusions = cls._transaction_exclusion_pathspecs()
        try:
            repo = cls._repo(repository.worktree_root)
            repo.git.add("-A", "-f", *exclusions)
            for path, source_head in (source_gitlinks or {}).items():
                repo.git.update_index(
                    "--add",
                    "--cacheinfo",
                    c.Infra.GIT_CACHEINFO_GITLINK,
                    source_head,
                    path,
                )
            # Gitlinks are owned by `make setup`, which fast-forwards each
            # declared submodule to its branch tip. Including them here made
            # every verb that runs after setup report "pending changes" for
            # pointers it never touched, so `gen` aborted before applying.
            names_output = repo.git.diff(
                "--cached",
                "--name-only",
                "-z",
                "--ignore-submodules=all",
                repository.checkpoint_sha,
                "--",
                *exclusions,
            )
            patch_bytes = repo.git.diff(
                "--cached",
                "--binary",
                "--ignore-submodules=all",
                repository.checkpoint_sha,
                "--",
                *exclusions,
            ).encode(c.Cli.ENCODING_DEFAULT)
        except GitCommandError as exc:
            return r[m.Infra.RepositoryDelta].fail(str(exc))
        except (OSError, ValueError) as exc:
            return r[m.Infra.RepositoryDelta].fail(
                f"failed to capture operation patch: {exc}"
            )
        # git apply rejects a patch whose final line has no terminating newline
        # ("corrupt patch"). `git diff --binary` can emit exactly that when the
        # last hunk ends on a context line, so restore the single trailing
        # newline the patch format requires before the delta is applied.
        if patch_bytes and not patch_bytes.endswith(b"\n"):
            patch_bytes += b"\n"
        return r[m.Infra.RepositoryDelta].ok(
            m.Infra.RepositoryDelta(
                relative_path=repository.relative_path,
                source_root=repository.source_root,
                worktree_root=repository.worktree_root,
                checkpoint_sha=repository.checkpoint_sha,
                changed_files=tuple(name for name in names_output.split("\0") if name),
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
        direction: list[str] = ["--reverse"] if reverse else []
        try:
            repo = cls._repo(repository_root)
            with _git_stdin(patch) as istream:
                repo.git.apply("--check", "--binary", *direction, "-", istream=istream)
        except GitCommandError as exc:
            return r[bool].fail(str(exc))
        except (OSError, ValueError) as exc:
            return r[bool].fail(f"git apply --check failed: {exc}")
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
                try:
                    repo = cls._repo(repository_root)
                    repo.git.update_index(
                        "--add",
                        "--cacheinfo",
                        c.Infra.GIT_CACHEINFO_GITLINK,
                        commit,
                        current.as_posix(),
                    )
                except GitCommandError as exc:
                    return r[bool].fail(str(exc))
                except (OSError, ValueError) as exc:
                    return r[bool].fail(f"failed to apply gitlink: {current}: {exc}")
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
        try:
            repo = cls._repo(delta.source_root)
            with _git_stdin(delta.patch) as istream:
                repo.git.apply("--binary", "-", istream=istream)
        except GitCommandError:
            # Rollback: restore original ignored files.
            for path, content in original.items():
                target = delta.source_root / path
                if target.exists():
                    target.unlink()
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(content)
            return r[bool].fail("git apply failed on ignored additions")
        except (OSError, ValueError) as exc:
            return r[bool].fail(f"git apply failed: {exc}")
        return r[bool].ok(True)

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
        try:
            repo = cls._repo(delta.source_root)
            with _git_stdin(delta.patch) as istream:
                repo.git.apply("--binary", "-", istream=istream)
        except GitCommandError:
            converged_result = cls._git_source_has_patch(delta)
            if converged_result.success:
                return cls._git_apply_gitlinks(delta.source_root, delta.patch)
            return r[bool].fail("git apply failed")
        except (OSError, ValueError) as exc:
            return r[bool].fail(f"git apply failed: {exc}")
        return cls._git_apply_gitlinks(delta.source_root, delta.patch)

    @classmethod
    def git_remove_worktree(
        cls, source_root: Path, worktree_root: Path
    ) -> p.Result[bool]:
        """Remove one explicitly selected temporary worktree and prune metadata."""
        try:
            repo = cls._repo(source_root)
            repo.git.worktree("remove", "--force", str(worktree_root))
            repo.git.worktree("prune")
        except GitCommandError as exc:
            return r[bool].fail(str(exc))
        except (OSError, ValueError) as exc:
            return r[bool].fail(f"failed to remove worktree: {exc}")
        return r[bool].ok(True)

    @classmethod
    def git_remove_clean_worktree(
        cls, source_root: Path, worktree_root: Path
    ) -> p.Result[bool]:
        """Remove an explicitly selected clean worktree and prune metadata."""
        try:
            repo = cls._repo(source_root)
            repo.git.worktree("remove", str(worktree_root))
            repo.git.worktree("prune")
        except GitCommandError as exc:
            return r[bool].fail(str(exc))
        except (OSError, ValueError) as exc:
            return r[bool].fail(f"failed to remove clean worktree: {exc}")
        return r[bool].ok(True)


__all__: list[str] = ["FlextInfraUtilitiesGitWorktreeMixin"]
