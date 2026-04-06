"""Git operations utilities for repository interaction."""

from __future__ import annotations

from pathlib import Path

from flext_cli import u
from flext_infra import c, r, t


class FlextInfraUtilitiesGit:
    """Static Git operations utilities."""

    @staticmethod
    def git_run(cmd: t.StrSequence, cwd: Path | None = None) -> r[str]:
        return u.Cli.capture([c.Infra.GIT, *cmd], cwd=cwd)

    @staticmethod
    def git_run_checked(cmd: t.StrSequence, cwd: Path | None = None) -> r[bool]:
        return u.Cli.run_checked([c.Infra.GIT, *cmd], cwd=cwd)

    @staticmethod
    def git_is_repo(path: Path) -> bool:
        return u.Cli.run_checked(
            [c.Infra.GIT, "rev-parse", "--is-inside-work-tree"], cwd=path
        ).is_success

    @staticmethod
    def git_current_branch(repo_root: Path) -> r[str]:
        return u.Cli.capture(
            [c.Infra.GIT, "rev-parse", "--abbrev-ref", "HEAD"], cwd=repo_root
        )

    @staticmethod
    def git_has_changes(repo_root: Path) -> r[bool]:
        return u.Cli.capture([c.Infra.GIT, "status", "--porcelain"], cwd=repo_root).map(
            lambda v: bool(v.strip())
        )

    @staticmethod
    def git_diff_names(repo_root: Path, *, cached: bool = False) -> r[str]:
        cmd = [c.Infra.GIT, "diff", "--name-only"]
        if cached:
            cmd.insert(2, "--cached")
        return u.Cli.capture(cmd, cwd=repo_root)

    @staticmethod
    def git_checkout(
        repo_root: Path,
        branch: str,
        *,
        create: bool = False,
        track: str | None = None,
    ) -> r[bool]:
        cmd = [c.Infra.GIT, "checkout"]
        if create:
            cmd.append("-B")
        cmd.append(branch)
        if track:
            cmd.append(track)
        return u.Cli.run_checked(cmd, cwd=repo_root)

    @staticmethod
    def git_fetch(repo_root: Path, remote: str = "", branch: str = "") -> r[bool]:
        cmd = [c.Infra.GIT, "fetch"]
        if remote:
            cmd.append(remote)
        if branch:
            cmd.append(branch)
        return u.Cli.run_checked(cmd, cwd=repo_root)

    @staticmethod
    def git_add(repo_root: Path, *paths: str) -> r[bool]:
        return u.Cli.run_checked(
            [c.Infra.GIT, "add", *(paths or ["-A"])], cwd=repo_root
        )

    @staticmethod
    def git_commit(repo_root: Path, msg: str) -> r[bool]:
        return u.Cli.run_checked([c.Infra.GIT, "commit", "-m", msg], cwd=repo_root)

    @staticmethod
    def git_push(
        repo_root: Path,
        remote: str = "",
        branch: str = "",
        *,
        upstream: bool = False,
    ) -> r[bool]:
        cmd = [c.Infra.GIT, "push"]
        if upstream:
            cmd.append("-u")
        if remote:
            cmd.append(remote)
        if branch:
            cmd.append(branch)
        return u.Cli.run_checked(cmd, cwd=repo_root)

    @staticmethod
    def git_pull(
        repo_root: Path,
        *,
        rebase: bool = False,
        remote: str = "",
        branch: str = "",
    ) -> r[bool]:
        cmd = [c.Infra.GIT, "pull"]
        if rebase:
            cmd.append("--rebase")
        if remote:
            cmd.append(remote)
        if branch:
            cmd.append(branch)
        return u.Cli.run_checked(cmd, cwd=repo_root)

    @staticmethod
    def git_tag_exists(repo_root: Path, tag: str) -> r[bool]:
        return u.Cli.capture([c.Infra.GIT, "tag", "-l", tag], cwd=repo_root).map(
            lambda v: v.strip() == tag
        )

    @staticmethod
    def git_create_tag(repo_root: Path, tag: str, msg: str = "") -> r[bool]:
        return u.Cli.run_checked(
            [c.Infra.GIT, "tag", "-a", tag, "-m", msg or f"release: {tag}"],
            cwd=repo_root,
        )


__all__ = ["FlextInfraUtilitiesGit"]
