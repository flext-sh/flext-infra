"""Build the native process boundary for isolated pytest children.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

from flext_infra import c, m, p, t, u


_PRIVATE_PATHS = tuple(Path(path) for path in ("/dev", "/proc", "/run", "/sys"))


def isolated_pytest_command(
    command: t.StrTuple,
    *,
    repository_root: Path,
    report_dir: Path,
    database: Path | None,
    options: p.Cli.ProcessOptions,
) -> t.StrTuple:
    """Run the child with a private home and network, preserving owned outputs.

    Admission, leases and process evidence remain with the host runner.
    The native database directory stays writable for SQLite's sidecars.

    Returns:
        The Bubblewrap and pytest argument vector.

    Raises:
        FileNotFoundError: If the configured isolation tool is unavailable.
        ValueError: If the persistent database would expose host or source state.

    """
    launcher = shutil.which("bwrap")
    if launcher is None:
        msg = "pytest sandbox requires the installed Bubblewrap executable"
        raise FileNotFoundError(msg)
    host_home = Path.home().resolve()
    root = repository_root.resolve()
    identity = u.Infra.git_identity(
        m.Infra.GitRepoRequest(repo_root=root),
        include_status=False,
    ).unwrap()
    inherited = u.Cli.process_env()
    default_mise = (
        Path(inherited.get("XDG_DATA_HOME", str(host_home / ".local/share"))) / "mise"
    ).resolve()
    mise = Path(
        inherited.get(c.Infra.MISE_BOOTSTRAP_STORAGE_ROOT_VARIABLE, str(default_mise))
    ).resolve()
    readonly = (
        Path("/usr"),
        Path("/bin"),
        Path("/lib"),
        Path("/lib64"),
        Path("/etc/ld.so.cache"),
        Path("/etc/passwd"),
        Path("/etc/group"),
        Path("/etc/nsswitch.conf"),
        Path(sys.base_prefix),
        Path(sys.executable).parent.parent,
        default_mise / "installs",
        mise / "installs",
        host_home / ".local/bin/mise",
        root,
        identity.common_dir,
    )
    report = report_dir.resolve()
    if report == root or not report.is_relative_to(root):
        msg = f"pytest reports must remain within the selected checkout: {report_dir}"
        raise ValueError(msg)
    writable = [report]
    environment = {
        key: inherited[key]
        for key in ("PATH", "LANG", "LC_ALL", "CI", "VIRTUAL_ENV", "RUNTIME_ROOT")
        if key in inherited
    }
    if options.env is not None:
        environment.update(options.env)
    environment.update(
        {
            "HOME": str(host_home),
            "TMPDIR": "/tmp",
            "XDG_RUNTIME_DIR": "/run",
            "COVERAGE_FILE": str(report / ".coverage"),
            c.Infra.MISE_BOOTSTRAP_STORAGE_ROOT_VARIABLE: str(mise),
        }
    )
    if database is not None:
        directory = database.parent.resolve()
        if directory == Path("/tmp") or any(
            anchor.is_relative_to(directory) or directory.is_relative_to(anchor)
            for anchor in (root, *_PRIVATE_PATHS)
        ) or host_home.is_relative_to(directory):
            msg = f"pytest database requires a separate writable directory: {database}"
            raise ValueError(msg)
        writable.append(directory)
        environment[c.Infra.PYTEST_ENV_TESTMON_DATAFILE] = str(directory / database.name)
    readonly_binds = tuple(
        value
        for path in dict.fromkeys(readonly)
        if path.exists()
        for value in ("--ro-bind", str(path), str(path))
    )
    writable_binds = tuple(
        value for path in writable for value in ("--bind", str(path), str(path))
    )
    environment_args = tuple(
        value for key, item in environment.items() for value in ("--setenv", key, item)
    )
    return (
        launcher,
        "--unshare-user",
        "--unshare-net",
        "--unshare-pid",
        "--unshare-ipc",
        "--unshare-uts",
        "--disable-userns",
        "--assert-userns-disabled",
        "--die-with-parent",
        "--new-session",
        "--cap-drop",
        "ALL",
        "--clearenv",
        "--proc",
        "/proc",
        "--dev",
        "/dev",
        "--tmpfs",
        "/tmp",
        "--tmpfs",
        "/run",
        "--tmpfs",
        str(host_home),
        *readonly_binds,
        *writable_binds,
        *environment_args,
        "--chdir",
        str(root),
        "--",
        *command,
        "-o",
        "cache_dir=/tmp/.pytest_cache",
    )


__all__ = ["isolated_pytest_command"]
