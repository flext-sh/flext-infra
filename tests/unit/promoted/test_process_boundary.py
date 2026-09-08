"""Exercise the promoted dispatcher at its real process boundary."""

from __future__ import annotations

import os
import select
import signal
import sys
from contextlib import suppress
from pathlib import Path
from typing import TYPE_CHECKING, Final

import pytest

if TYPE_CHECKING:
    from collections.abc import Mapping


_ROOT: Final = Path(__file__).resolve().parents[2]
# The one workspace interpreter is the interpreter running this suite.
_PYTHON: Final = Path(sys.executable)
_NONZERO_EXIT: Final = 37
# The child imports flext_infra before it can reach a barrier, so the wait
# has to cover a cold interpreter start on a loaded machine, not an idle one.
# Sized under the suite's own per-test timeout so a genuine hang still fails as
# a hang rather than as a barrier that was never reached.
_BARRIER_TIMEOUT: Final = 25.0
_PROBE: Final = """\
import sys
from pathlib import Path

from flext_infra import m
from flext_infra.promoted import run

Command = m.Infra.Promoted.Command

raise SystemExit(
    run(
        Command(
            verb="probe",
            what="probe",
            domain="probe",
            summary="probe",
            description="probe",
            example="probe",
            path=Path(sys.argv[1]),
            mutates=False,
            aliases=(),
            params=(),
            rules=(),
        )
    )
)
"""


def _probe_env() -> dict[str, str]:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(_ROOT / "src")
    return env


def _write_command(tmp_path: Path, source: str) -> Path:
    command = tmp_path / "scripts" / "probe" / "probe.py"
    command.parent.mkdir(parents=True)
    command.write_text(source, encoding="utf-8")
    (tmp_path / "pyproject.toml").write_text(
        "[project]\nname='probe'\n", encoding="utf-8"
    )
    venv_bin = tmp_path / ".venv" / "bin"
    venv_bin.mkdir(parents=True)
    (venv_bin / "python").symlink_to(_PYTHON)
    return command


def _read_ready(
    streams: Mapping[int, str], timeout: float = _BARRIER_TIMEOUT
) -> tuple[str, str]:
    stdout = ""
    stderr = ""
    pending = dict(streams)
    while pending:
        ready, _, _ = select.select(tuple(pending), (), (), timeout)
        if not ready:
            pytest.fail(f"timed out waiting for live output: {pending.values()}")
        for descriptor in ready:
            chunk = os.read(descriptor, 4096).decode()
            if pending.pop(descriptor) == "stdout":
                stdout += chunk
            else:
                stderr += chunk
    return stdout, stderr


def _wait_status(pid: int) -> int:
    _, status = os.waitpid(pid, 0)
    return os.waitstatus_to_exitcode(status)


def _spawn_probe(
    command: Path,
    *,
    env: Mapping[str, str],
    stdout: int | None = None,
    stderr: int | None = None,
    process_group: bool = False,
) -> int:
    file_actions: list[tuple[int, int, int]] = []
    if stdout is not None:
        file_actions.append((os.POSIX_SPAWN_DUP2, stdout, 1))
    if stderr is not None:
        file_actions.append((os.POSIX_SPAWN_DUP2, stderr, 2))
    argv = (_PYTHON, "-P", "-c", _PROBE, command)
    if process_group:
        return os.posix_spawn(
            _PYTHON, argv, env, file_actions=file_actions, setpgroup=0
        )
    return os.posix_spawn(_PYTHON, argv, env, file_actions=file_actions)


def test_run_streams_stdout_and_stderr_before_child_completion(tmp_path: Path) -> None:
    """Expose both streams while the child remains blocked before completion."""
    ready_fifo = tmp_path / "ready.fifo"
    release_fifo = tmp_path / "release.fifo"
    os.mkfifo(ready_fifo)
    os.mkfifo(release_fifo)
    command = _write_command(
        tmp_path,
        "import os, sys\n"
        "print('stdout-live', flush=True)\n"
        "print('stderr-live', file=sys.stderr, flush=True)\n"
        "with open(os.environ['READY_FIFO'], 'w') as ready: ready.write('1')\n"
        "open(os.environ['RELEASE_FIFO']).read(1)\n",
    )
    env = _probe_env()
    env["READY_FIFO"] = str(ready_fifo)
    env["RELEASE_FIFO"] = str(release_fifo)
    ready_read = os.open(ready_fifo, os.O_RDONLY | os.O_NONBLOCK)
    release_write = os.open(release_fifo, os.O_RDWR | os.O_NONBLOCK)
    stdout_read, stdout_write = os.pipe()
    stderr_read, stderr_write = os.pipe()
    pid = _spawn_probe(command, env=env, stdout=stdout_write, stderr=stderr_write)
    os.close(stdout_write)
    os.close(stderr_write)
    try:
        ready, _, _ = select.select((ready_read,), (), (), _BARRIER_TIMEOUT)
        if not ready:
            pytest.fail("child did not reach the completion barrier")
        if os.read(ready_read, 1) != b"1":
            pytest.fail("child completion barrier emitted an invalid marker")
        stdout, stderr = _read_ready({stdout_read: "stdout", stderr_read: "stderr"})
        if stdout != "stdout-live\n":
            pytest.fail(f"stdout was not streamed live: {stdout!r}")
        if stderr != "stderr-live\n":
            pytest.fail(f"stderr was not streamed live: {stderr!r}")
        os.write(release_write, b"1")
        if _wait_status(pid) != 0:
            pytest.fail("successful child exit status was not preserved")
    finally:
        os.close(ready_read)
        os.close(release_write)
        os.close(stdout_read)
        os.close(stderr_read)
        with suppress(ProcessLookupError):
            os.kill(pid, signal.SIGKILL)
        with suppress(ChildProcessError):
            os.waitpid(pid, 0)


def test_run_returns_exact_nonzero_exit_status(tmp_path: Path) -> None:
    """Return the child's raw nonzero code without normalization."""
    command = _write_command(tmp_path, f"raise SystemExit({_NONZERO_EXIT})\n")
    exit_code = _wait_status(_spawn_probe(command, env=_probe_env()))
    if exit_code != _NONZERO_EXIT:
        pytest.fail(f"expected {_NONZERO_EXIT}, got {exit_code}")


def test_run_sigint_terminates_child_without_residual_process(tmp_path: Path) -> None:
    """Propagate terminal SIGINT and reap the promoted child process."""
    child_pid = tmp_path / "child.pid"
    ready_fifo = tmp_path / "sigint-ready.fifo"
    os.mkfifo(ready_fifo)
    command = _write_command(
        tmp_path,
        "import os, signal\n"
        "from pathlib import Path\n"
        "Path(os.environ['CHILD_PID']).write_text(str(os.getpid()))\n"
        "with open(os.environ['READY_FIFO'], 'w') as ready: ready.write('1')\n"
        "signal.pause()\n",
    )
    env = _probe_env()
    env["CHILD_PID"] = str(child_pid)
    env["READY_FIFO"] = str(ready_fifo)
    ready_read = os.open(ready_fifo, os.O_RDONLY | os.O_NONBLOCK)
    pid = _spawn_probe(command, env=env, process_group=True)
    try:
        ready, _, _ = select.select((ready_read,), (), (), _BARRIER_TIMEOUT)
        if not ready:
            pytest.fail("child did not reach the SIGINT barrier")
        if os.read(ready_read, 1) != b"1":
            pytest.fail("child SIGINT barrier emitted an invalid marker")
        child = int(child_pid.read_text(encoding="utf-8"))
        os.killpg(pid, signal.SIGINT)
        if _wait_status(pid) == 0:
            pytest.fail("SIGINT was normalized to success")
        with pytest.raises(ProcessLookupError):
            os.kill(child, 0)
    finally:
        os.close(ready_read)
        with suppress(ProcessLookupError):
            os.killpg(pid, signal.SIGKILL)
        with suppress(ChildProcessError):
            os.waitpid(pid, 0)


def test_run_works_without_owner_venv_on_workspace_interpreter(tmp_path: Path) -> None:
    """Run a command whose owner has no .venv on the workspace interpreter.

    One-venv contract: a missing owner .venv is not an error; the command
    runs on the single workspace interpreter and its exit status is preserved.
    """
    command = _write_command(tmp_path, "raise SystemExit(0)\n")
    (tmp_path / ".venv" / "bin" / "python").unlink()
    exit_code = _wait_status(_spawn_probe(command, env=_probe_env()))
    if exit_code != 0:
        pytest.fail(
            f"command must run on the workspace interpreter without an owner venv, got {exit_code}"
        )
