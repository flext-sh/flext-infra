"""Workspace member child-process context."""

from __future__ import annotations

from pathlib import Path

from flext_infra import c, t, u


def project_child_command(
    project: str, verb: str, make_args: t.StrSequence, *, workspace_root: Path
) -> t.StrSequence:
    """Build the member Make command with explicit workspace context."""
    return (
        c.Infra.MAKE,
        "-C",
        project,
        verb,
        f"MAKE_PROFILE={c.Infra.MakeProfile.WORKSPACE_MEMBER.value}",
        f"WORKSPACE_ROOT={workspace_root}",
        *make_args,
    )


def project_child_env() -> t.StrMapping:
    """Return sanitized child process environment overrides."""
    inherited = u.Cli.process_env()
    path = inherited.get(c.Infra.ORCHESTRATOR_ENV_PATH, "")
    blocked_path_entries = frozenset(
        entry
        for entry in (inherited.get(c.Infra.ORCHESTRATOR_ENV_MISE_SHIMS, ""),)
        if entry
    )
    path_entries = tuple(
        entry
        for entry in path.split(c.Infra.ORCHESTRATOR_ENV_PATH_SEPARATOR)
        if entry and entry not in blocked_path_entries
    )
    env: dict[str, str] = {c.Infra.ORCHESTRATOR_ENV_NO_COLOR: "1"}
    if path_entries:
        env[c.Infra.ORCHESTRATOR_ENV_PATH] = (
            c.Infra.ORCHESTRATOR_ENV_PATH_SEPARATOR.join(path_entries)
        )
    return env


__all__ = ["project_child_command", "project_child_env"]
