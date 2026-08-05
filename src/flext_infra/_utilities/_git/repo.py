"""GitPython repository open and execute helpers for the private git facet."""

from __future__ import annotations

import io
import shutil
from pathlib import Path
from typing import TYPE_CHECKING, cast

from git import Git, GitCommandError, InvalidGitRepositoryError, NoSuchPathError, Repo

from flext_cli import m
from flext_core import r
from flext_infra.constants import c

if TYPE_CHECKING:
    from flext_infra import p, t


def git_refresh_binary() -> None:
    """Point GitPython at the absolute path of the canonical git binary."""
    # Git.refresh resolves relative names against cwd; always pass an absolute path.
    resolved = shutil.which(c.Infra.GIT)
    if resolved is None:
        msg = f"git executable not found on PATH: {c.Infra.GIT}"
        raise FileNotFoundError(msg)
    Git.refresh(resolved)


def git_open_repo(repo_root: Path) -> p.Result[Repo]:
    """Open one non-bare worktree repository at ``repo_root``."""
    git_refresh_binary()
    resolved = repo_root.expanduser().resolve()
    try:
        repo = Repo(resolved)
    except (InvalidGitRepositoryError, NoSuchPathError, OSError, ValueError) as exc:
        return r[Repo].fail(f"invalid git repository at {resolved}: {exc}")
    if repo.bare or repo.working_tree_dir is None:
        return r[Repo].fail(f"bare or worktree-less repository at {resolved}")
    return r[Repo].ok(repo)


def git_execute_text(
    repo_root: Path,
    arguments: t.StrSequence,
    *,
    input_data: bytes | None = None,
    timeout: int | None = None,
) -> p.Result[m.Cli.CommandOutput]:
    """Execute ``git <arguments>`` via GitPython returning text CommandOutput."""
    opened = git_open_repo(repo_root)
    if opened.failure:
        return r[m.Cli.CommandOutput].fail(
            opened.error or "failed to open git repository"
        )
    command: tuple[str, ...] = (c.Infra.GIT, *tuple(arguments))
    try:
        status, stdout, stderr = cast(
            "tuple[int, str | bytes, str]",
            opened.value.git.execute(
                command,
                istream=None if input_data is None else io.BytesIO(input_data),
                with_extended_output=True,
                with_exceptions=False,
                stdout_as_string=True,
                kill_after_timeout=None if timeout is None else float(timeout),
                universal_newlines=False,
                strip_newline_in_stdout=False,
            ),
        )
    except (GitCommandError, OSError, ValueError) as exc:
        return r[m.Cli.CommandOutput].fail(f"git execution failed: {exc}")
    out_s = (
        stdout if isinstance(stdout, str) else bytes(stdout).decode("utf-8", "replace")
    )
    err_s = (
        stderr if isinstance(stderr, str) else bytes(stderr).decode("utf-8", "replace")
    )
    return r[m.Cli.CommandOutput].ok(
        m.Cli.CommandOutput(stdout=out_s, stderr=err_s, exit_code=int(status))
    )


def git_execute_bytes(
    repo_root: Path,
    arguments: t.StrSequence,
    *,
    input_data: bytes | None = None,
    timeout: int | None = None,
) -> p.Result[m.Cli.CommandBytesOutput]:
    """Execute ``git <arguments>`` via GitPython returning byte CommandBytesOutput."""
    opened = git_open_repo(repo_root)
    if opened.failure:
        return r[m.Cli.CommandBytesOutput].fail(
            opened.error or "failed to open git repository"
        )
    command: tuple[str, ...] = (c.Infra.GIT, *tuple(arguments))
    try:
        status, stdout, stderr = cast(
            "tuple[int, str | bytes, str]",
            opened.value.git.execute(
                command,
                istream=None if input_data is None else io.BytesIO(input_data),
                with_extended_output=True,
                with_exceptions=False,
                stdout_as_string=False,
                kill_after_timeout=None if timeout is None else float(timeout),
                universal_newlines=False,
                strip_newline_in_stdout=False,
            ),
        )
    except (GitCommandError, OSError, ValueError) as exc:
        return r[m.Cli.CommandBytesOutput].fail(f"git execution failed: {exc}")
    out_b = stdout if isinstance(stdout, bytes) else str(stdout).encode("utf-8")
    err_b = stderr.encode("utf-8") if isinstance(stderr, str) else bytes(stderr)
    return r[m.Cli.CommandBytesOutput].ok(
        m.Cli.CommandBytesOutput(stdout=out_b, stderr=err_b, exit_code=int(status))
    )
