# AUTO-GENERATED FILE — DO NOT EDIT MANUALLY.
# Regenerate with: make gen
#
"""Github package."""

from __future__ import annotations

import typing as _t

from flext_core.lazy import install_lazy_exports

if _t.TYPE_CHECKING:
    import flext_infra.github.cli as _flext_infra_github_cli

    cli = _flext_infra_github_cli
    from flext_core.decorators import FlextDecorators as d
    from flext_core.exceptions import FlextExceptions as e
    from flext_core.handlers import FlextHandlers as h
    from flext_core.mixins import FlextMixins as x
    from flext_core.result import FlextResult as r
    from flext_core.service import FlextService as s
    from flext_infra.github.cli import FlextInfraCliGithub
_LAZY_IMPORTS = {
    "FlextInfraCliGithub": ("flext_infra.github.cli", "FlextInfraCliGithub"),
    "cli": "flext_infra.github.cli",
    "d": ("flext_core.decorators", "FlextDecorators"),
    "e": ("flext_core.exceptions", "FlextExceptions"),
    "h": ("flext_core.handlers", "FlextHandlers"),
    "r": ("flext_core.result", "FlextResult"),
    "s": ("flext_core.service", "FlextService"),
    "x": ("flext_core.mixins", "FlextMixins"),
}

__all__ = [
    "FlextInfraCliGithub",
    "cli",
    "d",
    "e",
    "h",
    "r",
    "s",
    "x",
]


install_lazy_exports(__name__, globals(), _LAZY_IMPORTS)
