"""Promoted-command framework: promoted command execution on the workspace process boundary."""

from __future__ import annotations

import os
import shutil
import sys
from collections.abc import MutableMapping
from pathlib import Path
from typing import TYPE_CHECKING

from flext_infra.promoted.base import (
    RegistryError,
    find_owner_root,
    local_python_cmd,
    workspace_python,
    workspace_venv,
)
from flext_infra.promoted.invocation import param_value

if TYPE_CHECKING:
    from flext_infra import p, t


def run(command: p.Infra.Promoted.Command) -> int:
    """Run one promoted command in its canonical command environment.

    Returns:
        The command's exact subprocess exit code.

    Raises:
        RegistryError: If the owner interpreter or command process is unavailable.

    """
    from flext_infra import u

    cwd = command_cwd(command)
    env = command_env(command, cwd)
    argv: t.StrSequence
    if command.path.suffix == ".py":
        # NOTE (multi-agent, cosmos-main-iz7g.1.7.2): inherited commands must
        # use its dependency graph without unsafe command-directory imports.
        argv = (str(workspace_python()), "-P", str(command.path))
    else:
        bash = shutil.which("bash")
        if bash is None:
            msg = "bash nao encontrado no PATH; comandos .sh exigem bash"
            raise RegistryError(msg)
        argv = (bash, str(command.path))
    # Stream the child live (capture=False): stdout/stderr reach the terminal
    # unbuffered and Ctrl-C/SIGINT and the exact exit code propagate unchanged,
    # which a captured run cannot provide for long-running makes/rollouts.
    result = u.Cli.run_raw(
        argv, cwd=cwd, env=env, remove_env_keys=("PYTHONPATH",), capture=False
    )
    if result.failure:
        raise RegistryError(result.error or "command process could not start")
    output: p.Cli.CommandOutput = result.value
    # flext-cli carries the causal completion state instead of a bare status:
    # the raw OS return code lives on the process outcome.
    exit_code: int = output.outcome.raw_return_code
    return exit_code


def command_env(
    command: p.Infra.Promoted.Command, project_root: Path
) -> MutableMapping[str, str]:
    """Return the canonical environment for a promoted command.

    Raises:
        RegistryError: If the owner project's declared interpreter is absent.

    """
    env = os.environ.copy()
    # cosmos-main-iz7g.1: execute exactly the parameter values already validated
    # by the dispatcher, including declarative defaults from the command header.
    env.update({param.name: param_value(param, command) for param in command.params})
    env["WHAT"] = command.what
    env["COSMOS_COMMAND_DISPATCHED"] = "Y"
    env["COSMOS_COMMAND_VERB"] = command.verb
    env["COSMOS_COMMAND_WHAT"] = command.what
    env["COSMOS_COMMAND_DOMAIN"] = command.domain
    env["COSMOS_COMMAND_PATH"] = str(command.path.resolve())
    # The single workspace venv is authoritative for every inherited command;
    # the owner root only fixes the command's working directory, never its
    # interpreter (one workspace, one venv).
    project_venv = workspace_venv()
    project_python = workspace_python()
    if not project_python.is_file():
        msg = (
            f"Workspace Python is missing: {project_python}; "
            "run make setup at the workspace root"
        )
        raise RegistryError(msg)
    env["VIRTUAL_ENV"] = str(project_venv)
    env["UV_PROJECT_ENVIRONMENT"] = str(project_venv)
    env["PYTHON"] = str(project_python)
    env["PATH"] = f"{project_venv / 'bin'}{os.pathsep}{env['PATH']}"
    env["COSMOS_SUBMODULE_ROOT"] = str(project_root.resolve())
    env.pop("PYTHONPATH", None)
    return env


def command_cwd(command: p.Infra.Promoted.Command) -> Path:
    """Return the command owner root or fail when ownership is undeclared.

    Raises:
        RegistryError: If no scripts/ plus pyproject.toml owner boundary exists.

    """
    project_root = project_root_for(command.path)
    if project_root is None:
        msg = f"Command owner project is unknown: {command.path}"
        raise RegistryError(msg)
    return project_root


def project_root_for(command_path: Path) -> Path | None:
    """Return the project root that owns one promoted command."""
    # cosmos-main-iz7g.1: ownership follows the nearest scripts/ + pyproject
    # boundary, so injected consumer roots keep their independent working dir.
    return find_owner_root(command_path)


def ensure_local_python(spec: p.Infra.Promoted.WorkspaceSpec) -> None:
    """Fail loud unless make runs on a virtualenv interpreter.

    Any active virtualenv is accepted (single-venv workspaces run the dispatcher
    from the workspace ``.venv``). Only a bare system interpreter with a declared
    local ``.venv`` present is rejected, so ``make`` never runs off dependency-less
    system Python.

    Raises:
        RegistryError: When a bare system interpreter is active while the
            declared local ``.venv`` is missing, or when the active
            interpreter differs from the expected one.

    """
    if sys.prefix != sys.base_prefix:
        return
    expected = local_python_cmd(spec)
    if expected == spec.local_python and not spec.local_python.is_file():
        msg = f"Python local ausente: {spec.local_python}; crie/sincronize .venv antes de usar make"
        raise RegistryError(msg)
    if Path(sys.executable).resolve() != expected.resolve():
        msg = f"Python ativo nao e o esperado: {expected}; use make com PATH da .venv"
        raise RegistryError(msg)


def env_value(name: str, default: str = "") -> str:
    """Return a stripped environment value used by promoted Python commands."""
    return os.environ.get(name, default).strip()


def require_env(name: str, usage: str | None = None) -> str:
    """Return a required environment value or fail with the command contract code.

    Raises:
        SystemExit: If the environment variable is unset or empty.

    """
    value = env_value(name)
    if value:
        return value
    if usage is not None:
        sys.stderr.write(f"{usage}\n")
    raise SystemExit(2)
