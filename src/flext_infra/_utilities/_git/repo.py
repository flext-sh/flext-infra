"""GitPython repository open and execute helpers for the private git facet."""

from __future__ import annotations

import shutil
import tempfile
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import TYPE_CHECKING, BinaryIO, Literal, Protocol, cast

from git import (
    Git,
    GitCommandError,
    GitCommandNotFound,
    InvalidGitRepositoryError,
    NoSuchPathError,
    Repo,
)

from flext_cli import m
from flext_core import r
from flext_infra.constants import c
from flext_infra.typings import t

if TYPE_CHECKING:
    from flext_infra import p


@contextmanager
def _git_optional_stdin(input_data: bytes | None) -> Iterator[BinaryIO | None]:
    """Yield a fileno-backed stdin stream for one GitPython execute call.

    ``Git.execute`` forwards ``istream`` straight to ``Popen(stdin=...)``, so
    an in-memory ``BytesIO`` aborts with ``io.UnsupportedOperation: fileno`` —
    the patch transport must ride a real (temporary) file descriptor.
    """
    if input_data is None:
        yield None
        return
    with tempfile.TemporaryFile() as stream:
        stream.write(input_data)
        stream.seek(0)
        yield stream


class _GitExtendedExecute[TStdout](Protocol):
    """Extended-output call shape of ``Git.execute`` for one stdout channel.

    GitPython publishes overloads that omit every keyword this facet depends on,
    so the concrete callable is narrowed to this contract at each call site.
    ``TStdout`` must agree with ``stdout_as_string``: ``str`` when it is ``True``,
    ``bytes`` when it is ``False``.
    """

    def __call__(
        self,
        command: t.StrSequence,
        *,
        istream: BinaryIO | None,
        with_extended_output: Literal[True],
        with_exceptions: bool,
        stdout_as_string: bool,
        kill_after_timeout: float | None,
        universal_newlines: bool,
        strip_newline_in_stdout: bool,
    ) -> tuple[int, TStdout, str]: ...


def git_refresh_binary() -> p.Result[bool]:
    """Point GitPython at the absolute path of the canonical git binary."""
    # Git.refresh resolves relative names against cwd; always pass an absolute path.
    resolved = shutil.which(c.Infra.GIT)
    if resolved is None:
        return r[bool].fail(f"git executable not found on PATH: {c.Infra.GIT}")
    try:
        Git.refresh(resolved)
    except (FileNotFoundError, OSError) as exc:
        return r[bool].fail(f"git binary refresh failed: {exc}")
    return r[bool].ok(True)


def git_open_repo(repo_root: Path) -> p.Result[Repo]:
    """Open one non-bare worktree repository at ``repo_root``."""
    resolved = repo_root.expanduser().resolve()
    try:
        refreshed = git_refresh_binary()
        if refreshed.failure:
            return r[Repo].fail(refreshed.error or "git binary unavailable")
        repo = Repo(resolved)
    except (
        GitCommandNotFound,
        ImportError,
        InvalidGitRepositoryError,
        NoSuchPathError,
        OSError,
        ValueError,
    ) as exc:
        return r[Repo].fail(f"cannot open git repository at {resolved}: {exc}")
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
    """Execute ``git <arguments>`` via cwd-bound GitPython returning text output.

    Does not require an existing worktree — preserves Cli cwd semantics including
    ``git init --bare`` on a non-repo directory.
    """
    resolved = repo_root.expanduser().resolve()
    refreshed = git_refresh_binary()
    if refreshed.failure:
        return r[m.Cli.CommandOutput].fail(refreshed.error or "git binary unavailable")
    command: tuple[str, ...] = (c.Infra.GIT, *arguments)
    execute = cast("_GitExtendedExecute[str]", Git(working_dir=str(resolved)).execute)
    try:
        with _git_optional_stdin(input_data) as istream:
            status, stdout, stderr = execute(
                command,
                istream=istream,
                with_extended_output=True,
                with_exceptions=False,
                stdout_as_string=True,
                kill_after_timeout=None if timeout is None else float(timeout),
                universal_newlines=False,
                strip_newline_in_stdout=False,
            )
    except (GitCommandError, GitCommandNotFound, OSError, ValueError) as exc:
        return r[m.Cli.CommandOutput].fail(f"git execution failed: {exc}")
    return r[m.Cli.CommandOutput].ok(
        m.Cli.CommandOutput(stdout=stdout, stderr=stderr, exit_code=status)
    )


def git_execute_bytes(
    repo_root: Path,
    arguments: t.StrSequence,
    *,
    input_data: bytes | None = None,
    timeout: int | None = None,
) -> p.Result[m.Cli.CommandBytesOutput]:
    """Execute ``git <arguments>`` via cwd-bound GitPython returning byte output.

    Does not require an existing worktree — preserves Cli cwd semantics.
    """
    resolved = repo_root.expanduser().resolve()
    refreshed = git_refresh_binary()
    if refreshed.failure:
        return r[m.Cli.CommandBytesOutput].fail(
            refreshed.error or "git binary unavailable"
        )
    command: tuple[str, ...] = (c.Infra.GIT, *arguments)
    execute = cast("_GitExtendedExecute[bytes]", Git(working_dir=str(resolved)).execute)
    try:
        with _git_optional_stdin(input_data) as istream:
            status, stdout, stderr = execute(
                command,
                istream=istream,
                with_extended_output=True,
                with_exceptions=False,
                stdout_as_string=False,
                kill_after_timeout=None if timeout is None else float(timeout),
                universal_newlines=False,
                strip_newline_in_stdout=False,
            )
    except (GitCommandError, GitCommandNotFound, OSError, ValueError) as exc:
        return r[m.Cli.CommandBytesOutput].fail(f"git execution failed: {exc}")
    return r[m.Cli.CommandBytesOutput].ok(
        m.Cli.CommandBytesOutput(
            stdout=stdout,
            stderr=stderr.encode(c.Cli.ENCODING_DEFAULT),
            exit_code=status,
        )
    )


def git_run(
    repo_root: Path,
    arguments: t.StrSequence,
    *,
    input_data: bytes | None = None,
    timeout: int | None = None,
) -> p.Result[m.Cli.CommandOutput]:
    """Private: run one Git command via cwd-bound execute (text)."""
    result = git_execute_text(
        repo_root, arguments, input_data=input_data, timeout=timeout
    )
    if result.failure:
        return r[m.Cli.CommandOutput].fail(
            result.error or "git command execution failed"
        )
    return r[m.Cli.CommandOutput].ok(result.value)


def git_capture(repo_root: Path, arguments: t.StrSequence) -> p.Result[str]:
    """Private: capture stdout from one successful Git command."""
    result = git_run(repo_root, arguments)
    if result.failure:
        return r[str].fail(result.error or "git command execution failed")
    output = result.value
    if output.exit_code != 0:
        detail = (output.stderr or output.stdout).strip()
        return r[str].fail(detail or f"git command exited {output.exit_code}")
    return r[str].ok(output.stdout)


def git_capture_bytes(repo_root: Path, arguments: t.StrSequence) -> p.Result[bytes]:
    """Private: capture byte-exact stdout from one successful Git command."""
    # mro-45r9: patch transport stays binary until the human error boundary.
    result = git_execute_bytes(repo_root, arguments)
    if result.failure:
        return r[bytes].fail(result.error or "git command execution failed")
    output = result.value
    if output.exit_code != 0:
        detail = (output.stderr or output.stdout).decode(
            c.Cli.ENCODING_DEFAULT, errors="replace"
        )
        return r[bytes].fail(detail.strip() or f"git command exited {output.exit_code}")
    return r[bytes].ok(output.stdout)
