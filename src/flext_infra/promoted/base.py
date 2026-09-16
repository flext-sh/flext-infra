"""Promoted-command framework: constants, errors, and workspace resolution.

The framework is workspace-agnostic: every repository fact (root, scripts
directory, fallback roots, local interpreter) arrives through one typed
``WorkspaceSpec`` projection resolved by the calling workspace, never through
an import of workspace-local paths.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import TYPE_CHECKING

from flext_infra import c, settings, u

if TYPE_CHECKING:
    from flext_infra import p

HEADER_START = "/// cosmos-command"
HEADER_END = "///"
COMMAND_SUFFIXES = frozenset({".sh", ".py"})
# Generator-owned package markers (`make gen` lazy-init) are Python packaging
# structure inside a verb directory, never a public command.
PACKAGE_MARKERS = frozenset({"__init__.py"})
IGNORED_DIRS = frozenset({"__pycache__", "hooks", "legado", "lib"})
# Incident mutations retain their domain-specific safety parameters.
INCIDENT_MUTATION_REQUIRED_PARAMS = frozenset({"EMERGENCY", "BREAKING_GLASS_BEAD"})


class RegistryError(Exception):
    """Raised when command metadata or invocation is invalid."""


class MissingHeaderError(RegistryError):
    """Raised when a file carries no ``cosmos-command`` header at all.

    A file with no header is simply not a promoted command; a file whose
    header is present but invalid is a defect. Only the first is an answer,
    so the two never share an exception type.
    """


def workspace_python_cmd() -> Path | None:
    """Return the active workspace interpreter from ``VIRTUAL_ENV`` when set."""
    venv = settings.Infra.virtual_env
    if not venv:
        return None
    candidate = Path(sys.executable)
    return candidate if candidate.exists() else None


def workspace_venv() -> Path:
    """Return the one workspace virtual-environment directory.

    The active ``VIRTUAL_ENV`` is the single source of truth: ``make`` (root or
    standalone member) always exports it to the one venv for the current
    context, so an inherited command runs on the same environment regardless
    of which project owns it. When no ``VIRTUAL_ENV`` is active, the
    interpreter already running the dispatcher is authoritative.
    """
    venv = settings.Infra.virtual_env
    if venv and Path(sys.executable).is_file():
        return Path(venv)
    return Path(sys.prefix)


def workspace_python() -> Path:
    """Return the interpreter of the one workspace virtual environment."""
    return Path(sys.executable)


def local_python_cmd(spec: p.Infra.Promoted.WorkspaceSpec) -> Path:
    """Honor the active workspace ``VIRTUAL_ENV`` first, then the declared local ``.venv``."""
    workspace_python = workspace_python_cmd()
    if workspace_python is not None:
        return workspace_python
    return spec.local_python if spec.local_python.exists() else Path(sys.executable)


def find_owner_root(start: Path) -> Path | None:
    """Return ``start`` or its nearest ancestor owning ``scripts/`` + ``pyproject.toml``.

    ``start`` itself is a candidate: a project root is its own owner, so
    discovery from the repository working directory resolves instead of
    walking past it.
    """
    resolved = start.resolve()
    for candidate in (resolved, *resolved.parents):
        if (candidate / c.Infra.DIR_SCRIPTS).is_dir() and (
            candidate / c.Infra.PYPROJECT_FILENAME
        ).is_file():
            return candidate
    return None


def env_enabled(name: str) -> bool:
    """Return whether an environment flag is enabled."""
    return (u.Infra.env_lookup(name) or "N").upper() in {"1", "Y", "YES", "TRUE"}


def resolve_workspace_spec(root: Path) -> p.Infra.Promoted.WorkspaceSpec:
    """Resolve one workspace spec from its repository root.

    Mirrors the per-repository workspace shims this framework replaces: the
    root fixes the scripts directory, the declared local ``.venv`` interpreter
    and the submodule/consumer fallback roots; everything env-derived is read
    at use time, never frozen into the spec.
    """
    from flext_infra import m

    return m.Infra.Promoted.WorkspaceSpec(
        root=root,
        scripts=root / c.Infra.DIR_SCRIPTS,
        local_python=root / ".venv" / "bin" / "python",
    )


def discovered_workspace_spec() -> p.Infra.Promoted.WorkspaceSpec:
    """Resolve the spec for the workspace owning the current working directory.

    Raises:
        RegistryError: When no ``scripts/`` plus ``pyproject.toml`` owner
            boundary exists above the working directory.

    """
    root = find_owner_root(Path.cwd())
    if root is None:
        msg = "nenhum diretorio scripts encontrado"
        raise RegistryError(msg)
    return resolve_workspace_spec(root)
