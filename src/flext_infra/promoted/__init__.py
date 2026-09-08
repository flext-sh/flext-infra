"""Flext Infra.promoted package.

One fleet owner of the promoted-command dispatch framework: header discovery,
registry validation, help rendering, dry-run gating, and process-boundary
execution for ``scripts/<verb>/<WHAT>`` commands.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_core.lazy import build_lazy_import_map, install_lazy_exports

if TYPE_CHECKING:
    from .base import MissingHeaderError, RegistryError
    from .discovery import discover
    from .dispatcher import main, promoted_main, run_dispatch
    from .executor import env_value, require_env, run
    from .registry import Registry

__all__: tuple[str, ...] = (
    "MissingHeaderError",
    "Registry",
    "RegistryError",
    "discover",
    "env_value",
    "main",
    "promoted_main",
    "require_env",
    "run",
    "run_dispatch",
)

_LAZY_IMPORTS = build_lazy_import_map(
    {
        ".base": ("MissingHeaderError", "RegistryError"),
        ".dispatcher": ("main", "promoted_main", "run_dispatch"),
        ".discovery": ("discover",),
        ".executor": ("env_value", "require_env", "run"),
        ".registry": ("Registry",),
    },
    sort_keys=False,
)

install_lazy_exports(__name__, globals(), _LAZY_IMPORTS, public_exports=__all__)
