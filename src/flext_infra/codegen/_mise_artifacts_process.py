"""Strict isolated subprocess environment for Mise artifact generation."""

from __future__ import annotations

import os
from pathlib import Path
from typing import TYPE_CHECKING

from flext_core import r
from flext_infra import c, t, u

if TYPE_CHECKING:
    from flext_infra import p


def prepare_isolation(scratch: Path) -> p.Result[bool]:
    """Create fresh private config/cache/home paths with fallback auth disabled."""

    def directory_key(path: Path) -> tuple[int, str]:
        return len(path.parts), path.as_posix()

    if not os.environ.get("PATH"):
        return r[bool].fail("PATH is required for isolated Mise execution")
    if scratch.exists() or scratch.is_symlink():
        return r[bool].fail(f"isolated Mise runtime already exists: {scratch}")
    empty_files = tuple(
        scratch / relative for relative in c.Infra.MISE_BOOTSTRAP_EMPTY_FILES
    )
    transient_directories = {
        scratch / relative
        for _name, relative in c.Infra.MISE_BOOTSTRAP_TRANSIENT_ENVIRONMENT
        if scratch / relative not in empty_files
    }
    persistent_root = scratch / "data"
    persistent_directories = {
        persistent_root / relative
        for _name, relative in c.Infra.MISE_BOOTSTRAP_PERSISTENT_ENVIRONMENT
    }
    directories = sorted(
        {
            scratch / "seed" / "bin",
            scratch / "receipt" / "bin",
            scratch / "runtime",
            *(path.parent for path in empty_files),
            *transient_directories,
            *persistent_directories,
        },
        key=directory_key,
    )
    for directory in directories:
        planned = u.Cli.atomic_plan_directory_chain(directory)
        if planned.failure:
            return r[bool].from_failure(planned)
        created = u.Cli.atomic_create_directory_chain_guarded(
            planned.value, permission_mode=0o700
        )
        if created.failure:
            return r[bool].from_failure(created)
    for path in empty_files:
        written = write_new(path, b"", 0o600)
        if written.failure:
            return written
    return r[bool].ok(True)


def environment(scratch: Path) -> dict[str, str]:
    """Build the complete child environment with every fallback disabled."""
    isolated = dict(c.Infra.MISE_BOOTSTRAP_FIXED_ENVIRONMENT)
    isolated.update({
        name: str(scratch / relative)
        for name, relative in c.Infra.MISE_BOOTSTRAP_TRANSIENT_ENVIRONMENT
    })
    persistent_root = scratch / "data"
    isolated.update({
        name: str(persistent_root / relative)
        for name, relative in c.Infra.MISE_BOOTSTRAP_PERSISTENT_ENVIRONMENT
    })
    isolated.update({
        "GIT_CEILING_DIRECTORIES": str(scratch.parent),
        "MISE_CEILING_PATHS": str(scratch.parent),
        "MISE_TRUSTED_CONFIG_PATHS": str(scratch),
        "MISE_INSTALL_PATH": str(
            scratch / "runtime" / ("mise.exe" if os.name == "nt" else "mise")
        ),
    })
    for name in c.Infra.MISE_BOOTSTRAP_PASSTHROUGH_ENVIRONMENT:
        if value := os.environ.get(name):
            isolated[name] = value
    return isolated


def no_config_environment(environment_values: t.StrMapping) -> dict[str, str]:
    """Select Mise's documented config-free mode for runtime-only commands."""
    result = dict(environment_values)
    result["MISE_NO_CONFIG"] = "1"
    return result


def run(
    command: t.StrSequence, *, cwd: Path, env: t.StrMapping, operation: str
) -> p.Result[str]:
    """Run one Mise process and reject nonzero status or any Mise warning."""
    executed = u.Cli.run_raw(
        command,
        cwd=cwd,
        env=env,
        remove_env_keys=tuple(os.environ),
        timeout=c.Infra.TIMEOUT_LONG,
    )
    if executed.failure:
        return r[str].fail(executed.error or f"{operation} failed to execute")
    command_output = executed.value
    output = command_output.stdout + command_output.stderr
    if not u.Cli.process_succeeded(command_output.outcome):
        detail = output.strip() or f"exit {command_output.outcome.raw_return_code}"
        return r[str].fail(f"{operation} failed: {detail}")
    if "mise WARN" in output:
        return r[str].fail(f"{operation} emitted a warning: {output.strip()}")
    return r[str].ok(command_output.stdout.strip())


def write_new(path: Path, content: bytes, mode: int) -> p.Result[bool]:
    """Create exact isolated state through the canonical atomic owner."""
    before = u.Cli.atomic_read_binary_file_state(path, required=False)
    if before.failure:
        return r[bool].from_failure(before)
    return u.Cli.atomic_write_binary_file_guarded(
        before.value, content, permission_mode=mode
    )


__all__: list[str] = [
    "environment",
    "no_config_environment",
    "prepare_isolation",
    "run",
    "write_new",
]
