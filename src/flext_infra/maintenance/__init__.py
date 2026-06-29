# AUTO-GENERATED FILE — Regenerate with: make gen
"""Maintenance package."""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_core.lazy import build_lazy_import_map, install_lazy_exports

if TYPE_CHECKING:
    from flext_infra.maintenance.python_version import (
        FlextInfraPythonVersionEnforcer as FlextInfraPythonVersionEnforcer,
    )
_LAZY_IMPORTS = build_lazy_import_map(
    {
        ".python_version": ("FlextInfraPythonVersionEnforcer",),
    },
)


install_lazy_exports(
    __name__,
    globals(),
    _LAZY_IMPORTS,
    publish_all=False,
)
