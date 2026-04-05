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
    import flext_infra.github.service as _flext_infra_github_service
    from flext_infra.github.cli import FlextInfraCliGithub

    service = _flext_infra_github_service
    from flext_core.decorators import FlextDecorators as d
    from flext_core.exceptions import FlextExceptions as e
    from flext_core.handlers import FlextHandlers as h
    from flext_core.mixins import FlextMixins as x
    from flext_core.result import FlextResult as r
    from flext_infra.github.service import (
        FlextInfraGithubService,
        FlextInfraGithubService as s,
    )
_LAZY_IMPORTS = {
    "FlextInfraCliGithub": "flext_infra.github.cli",
    "FlextInfraGithubService": "flext_infra.github.service",
    "cli": "flext_infra.github.cli",
    "d": ("flext_core.decorators", "FlextDecorators"),
    "e": ("flext_core.exceptions", "FlextExceptions"),
    "h": ("flext_core.handlers", "FlextHandlers"),
    "r": ("flext_core.result", "FlextResult"),
    "s": ("flext_infra.github.service", "FlextInfraGithubService"),
    "service": "flext_infra.github.service",
    "x": ("flext_core.mixins", "FlextMixins"),
}

__all__ = [
    "FlextInfraCliGithub",
    "FlextInfraGithubService",
    "cli",
    "d",
    "e",
    "h",
    "r",
    "s",
    "service",
    "x",
]


install_lazy_exports(__name__, globals(), _LAZY_IMPORTS)
