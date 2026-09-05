"""Strict isolated subprocess environment for Mise artifact generation."""

from __future__ import annotations

import os
from pathlib import Path
from typing import TYPE_CHECKING, Final

from flext_core import r
from flext_infra import c, m, t, u

if TYPE_CHECKING:
    from flext_infra import p

CREDENTIAL_SOURCE: Final[str] = "source: credential_command"


def prepare_isolation(scratch: Path) -> p.Result[bool]:
    """Create fresh private config/cache/home paths with fallback auth disabled."""
    if not os.environ.get("PATH"):
        return r[bool].fail("PATH is required for isolated Mise execution")
    directories = (
        scratch / "seed" / "bin",
        scratch / "receipt" / "bin",
        *(
            scratch / name
            for name in (
                "home",
                "appdata",
                "xdg-config",
                "xdg-data",
                "xdg-cache",
                "xdg-state",
                "gh-config",
                "config",
                "data",
                "cache",
                "state",
                "tmp",
                "system-config",
                "system-data",
                "system-installs",
                "system-shims",
                "installs",
                "shims",
            )
        ),
    )
    try:
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=False)
    except OSError as exc:
        return r[bool].fail_op("create isolated Mise runtime", exc)
    for path, content in (
        (scratch / "global-config.toml", b""),
        (scratch / "system-config" / "config.toml", b""),
        (scratch / "gitconfig", b""),
        (scratch / "netrc", b""),
    ):
        written = u.Cli.atomic_create_binary_file_guarded(
            path, content, permission_mode=0o600
        )
        if written.failure:
            return r[bool].from_failure(written)
    return r[bool].ok(True)


def environment(scratch: Path) -> dict[str, str]:
    """Build the complete child environment with every fallback disabled."""
    isolated = {
        "HOME": str(scratch / "home"),
        "USERPROFILE": str(scratch / "home"),
        "APPDATA": str(scratch / "appdata"),
        "LOCALAPPDATA": str(scratch / "appdata"),
        "XDG_DATA_HOME": str(scratch / "xdg-data"),
        "XDG_CACHE_HOME": str(scratch / "xdg-cache"),
        "XDG_STATE_HOME": str(scratch / "xdg-state"),
        "XDG_CONFIG_HOME": str(scratch / "xdg-config"),
        "GH_CONFIG_DIR": str(scratch / "gh-config"),
        "NETRC": str(scratch / "netrc"),
        "GIT_CONFIG_NOSYSTEM": "1",
        "GIT_CONFIG_GLOBAL": str(scratch / "gitconfig"),
        "GIT_CEILING_DIRECTORIES": str(scratch.parent),
        "GIT_TERMINAL_PROMPT": "0",
        "LANG": "C",
        "LC_ALL": "C",
        "PATH": os.environ["PATH"],
        "MISE_SAFE": "1",
        "MISE_PARANOID": "true",
        "MISE_NO_ENV": "1",
        "MISE_NO_HOOKS": "1",
        "MISE_AUTO_ENV": "false",
        "MISE_AUTO_INSTALL": "false",
        "MISE_EXEC_AUTO_INSTALL": "false",
        "MISE_TASK_RUN_AUTO_INSTALL": "false",
        "MISE_AUTO_UPDATE": "false",
        "MISE_HTTP_RETRIES": "0",
        "MISE_NETRC": "false",
        "MISE_NETRC_FILE": str(scratch / "netrc"),
        "MISE_NOT_FOUND_AUTO_INSTALL": "false",
        "MISE_NOT_FOUND_SYSTEM_FALLBACK": "false",
        "MISE_OVERRIDE_CONFIG_FILENAMES": ".mise.toml",
        "MISE_OVERRIDE_TOOL_VERSIONS_FILENAMES": "none",
        "MISE_GLOBAL_CONFIG_FILE": str(scratch / "global-config.toml"),
        "MISE_CONFIG_DIR": str(scratch / "config"),
        "MISE_DATA_DIR": str(scratch / "data"),
        "MISE_CACHE_DIR": str(scratch / "cache"),
        "MISE_STATE_DIR": str(scratch / "state"),
        "MISE_TMP_DIR": str(scratch / "tmp"),
        "MISE_INSTALLS_DIR": str(scratch / "installs"),
        "MISE_SHIMS_DIR": str(scratch / "shims"),
        "MISE_GLOBAL_CONFIG_ROOT": str(scratch),
        "MISE_SYSTEM_CONFIG_DIR": str(scratch / "system-config"),
        "MISE_SYSTEM_CONFIG_FILE": str(scratch / "system-config" / "config.toml"),
        "MISE_SYSTEM_DATA_DIR": str(scratch / "system-data"),
        "MISE_SYSTEM_INSTALLS_DIR": str(scratch / "system-installs"),
        "MISE_SYSTEM_SHIMS_DIR": str(scratch / "system-shims"),
        "MISE_CEILING_PATHS": str(scratch.parent),
        "MISE_TRUSTED_CONFIG_PATHS": str(scratch),
        "MISE_GITHUB_GH_CLI_TOKENS": "false",
        "MISE_GITHUB_USE_GIT_CREDENTIALS": "false",
        "MISE_GITHUB_OAUTH_CLIENT_ID": "",
        "MISE_GITHUB_OAUTH_EXPORT_ENV": "",
        "MISE_GITHUB_OAUTH_OPEN_BROWSER": "false",
        "TMPDIR": str(scratch / "tmp"),
        "TMP": str(scratch / "tmp"),
        "TEMP": str(scratch / "tmp"),
    }
    for name in ("COMSPEC", "PATHEXT", "SYSTEMROOT", "WINDIR"):
        if value := os.environ.get(name):
            isolated[name] = value
    return isolated


def credential_environment(scratch: Path, command: str) -> dict[str, str]:
    """Select one declared credential command on top of strict isolation."""
    result = environment(scratch)
    result["MISE_GITHUB_CREDENTIAL_COMMAND"] = command
    return result


def validate_credential_source(
    launcher: Path, *, cwd: Path, env: t.StrMapping, timeout_seconds: int
) -> p.Result[bool]:
    """Prove masked token resolution selected only the declared command."""
    resolved = run(
        (str(launcher), "token", "github"),
        cwd=cwd,
        env=env,
        operation="Mise GitHub credential source preflight",
        timeout_seconds=timeout_seconds,
    )
    if resolved.failure:
        return r[bool].from_failure(resolved)
    if CREDENTIAL_SOURCE not in resolved.value or "(none)" in resolved.value:
        return r[bool].fail("Mise did not select the declared credential command")
    return r[bool].ok(True)


def run(
    command: t.StrSequence,
    *,
    cwd: Path,
    env: t.StrMapping,
    operation: str,
    timeout_seconds: int,
) -> p.Result[str]:
    """Run one Mise process and reject nonzero status or any Mise warning."""
    u.Cli.info(f"mise-toolchain: start operation={operation}")
    executed = u.Cli.run_raw(
        command,
        cwd=cwd,
        env=env,
        remove_env_keys=tuple(os.environ),
        timeout=timeout_seconds,
    )
    if executed.failure:
        return r[str].from_failure(executed)
    output = executed.value.stdout + executed.value.stderr
    if not u.Cli.process_succeeded(executed.value.outcome):
        return _process_failure(
            operation,
            exit_code=executed.value.outcome.raw_return_code,
            stdout=executed.value.stdout,
            stderr=executed.value.stderr,
        )
    if "mise WARN" in output:
        return r[str].fail(f"{operation} emitted a warning: {output.strip()}")
    u.Cli.info(f"mise-toolchain: complete operation={operation}")
    return r[str].ok(executed.value.stdout.strip())


def run_live(
    command: t.StrSequence,
    *,
    cwd: Path,
    env: t.StrMapping,
    operation: str,
    output_path: Path,
    timeout_seconds: int,
) -> p.Result[str]:
    """Run one bounded Mise process with live and durable combined output."""
    u.Cli.info(f"mise-toolchain: start operation={operation}")
    executed = u.Cli.run_to_file(
        command,
        output_path,
        cwd=cwd,
        env=env,
        remove_env_keys=tuple(os.environ),
        live=True,
        timeout=timeout_seconds,
    )
    if executed.failure:
        return r[str].from_failure(executed)
    output = u.Cli.files_read_text(output_path)
    if output.failure:
        return r[str].from_failure(output)
    outcome = executed.value
    if not u.Cli.process_succeeded(outcome):
        return _process_failure(
            operation,
            exit_code=outcome.raw_return_code,
            stdout=output.value,
            stderr="",
            combined=True,
        )
    if "mise WARN" in output.value:
        return r[str].fail(f"{operation} emitted a warning: {output.value.strip()}")
    u.Cli.info(f"mise-toolchain: complete operation={operation}")
    return r[str].ok(output.value.strip())


def _process_failure(
    operation: str, *, exit_code: int, stdout: str, stderr: str, combined: bool = False
) -> p.Result[str]:
    """Preserve one child status and its exact captured diagnostic channels."""
    classification = u.Infra.classify_process_exit(exit_code)
    outcome = m.Infra.ProcessExit(exit_code=exit_code, classification=classification)
    if combined:
        diagnostics = f"combined_stdout_stderr:\n{stdout}"
    else:
        diagnostics = f"stdout:\n{stdout}\nstderr:\n{stderr}"
    return r[str].fail(
        f"{operation} failed: exit_code={exit_code} "
        f"classification={classification}\n{diagnostics}",
        error_code=c.Infra.PROCESS_EXIT_ERROR_CODE,
        error_data=outcome,
    )


__all__: list[str] = [
    "credential_environment",
    "environment",
    "prepare_isolation",
    "run",
    "run_live",
    "validate_credential_source",
]
