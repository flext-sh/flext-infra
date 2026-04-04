# AUTO-GENERATED FILE — DO NOT EDIT MANUALLY.
# Regenerate with: make gen
#
"""Github package."""

from __future__ import annotations

import typing as _t

from flext_core.lazy import install_lazy_exports

if _t.TYPE_CHECKING:
    import flext_infra._constants.github as _flext_infra__constants_github

    _constants = _flext_infra__constants_github
    import flext_infra.github.cli as _flext_infra_github_cli
    from flext_infra._constants.github import FlextInfraGithubConstants

    cli = _flext_infra_github_cli
    import flext_infra.github.service as _flext_infra_github_service
    from flext_infra.github.cli import FlextInfraCliGithub

    service = _flext_infra_github_service
    from flext_core.constants import FlextConstants as c
    from flext_core.decorators import FlextDecorators as d
    from flext_core.exceptions import FlextExceptions as e
    from flext_core.handlers import FlextHandlers as h
    from flext_core.mixins import FlextMixins as x
    from flext_core.models import FlextModels as m
    from flext_core.protocols import FlextProtocols as p
    from flext_core.result import FlextResult as r
    from flext_core.typings import FlextTypes as t
    from flext_core.utilities import FlextUtilities as u
    from flext_infra.github.service import (
        FlextInfraGithubService,
        FlextInfraGithubService as s,
    )
_LAZY_IMPORTS = {
    "FlextInfraCliGithub": "flext_infra.github.cli",
    "FlextInfraGithubConstants": "flext_infra._constants.github",
    "FlextInfraGithubService": "flext_infra.github.service",
    "_constants": "flext_infra._constants.github",
    "c": ("flext_core.constants", "FlextConstants"),
    "cli": "flext_infra.github.cli",
    "d": ("flext_core.decorators", "FlextDecorators"),
    "e": ("flext_core.exceptions", "FlextExceptions"),
    "h": ("flext_core.handlers", "FlextHandlers"),
    "m": ("flext_core.models", "FlextModels"),
    "p": ("flext_core.protocols", "FlextProtocols"),
    "r": ("flext_core.result", "FlextResult"),
    "s": ("flext_infra.github.service", "FlextInfraGithubService"),
    "service": "flext_infra.github.service",
    "t": ("flext_core.typings", "FlextTypes"),
    "u": ("flext_core.utilities", "FlextUtilities"),
    "x": ("flext_core.mixins", "FlextMixins"),
}

__all__ = [
    "FlextInfraCliGithub",
    "FlextInfraGithubConstants",
    "FlextInfraGithubService",
    "_constants",
    "c",
    "cli",
    "d",
    "e",
    "h",
    "m",
    "p",
    "r",
    "s",
    "service",
    "t",
    "u",
    "x",
]


install_lazy_exports(__name__, globals(), _LAZY_IMPORTS)
