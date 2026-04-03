# AUTO-GENERATED FILE — DO NOT EDIT MANUALLY.
# Regenerate with: make gen
#
"""Github package."""

from __future__ import annotations

import typing as _t

from flext_core.lazy import install_lazy_exports

if _t.TYPE_CHECKING:
    import flext_infra.github._constants as _flext_infra_github__constants

    _constants = _flext_infra_github__constants
    import flext_infra.github._models as _flext_infra_github__models
    from flext_infra.github._constants import FlextInfraGithubConstants

    _models = _flext_infra_github__models
    import flext_infra.github.cli as _flext_infra_github_cli
    from flext_infra.github._models import FlextInfraGithubModels

    cli = _flext_infra_github_cli
    from flext_core.constants import FlextConstants as c
    from flext_core.decorators import FlextDecorators as d
    from flext_core.exceptions import FlextExceptions as e
    from flext_core.handlers import FlextHandlers as h
    from flext_core.mixins import FlextMixins as x
    from flext_core.models import FlextModels as m
    from flext_core.protocols import FlextProtocols as p
    from flext_core.result import FlextResult as r
    from flext_core.service import FlextService as s
    from flext_core.typings import FlextTypes as t
    from flext_core.utilities import FlextUtilities as u
    from flext_infra.github.cli import FlextInfraCliGithub
_LAZY_IMPORTS = {
    "FlextInfraCliGithub": "flext_infra.github.cli",
    "FlextInfraGithubConstants": "flext_infra.github._constants",
    "FlextInfraGithubModels": "flext_infra.github._models",
    "_constants": "flext_infra.github._constants",
    "_models": "flext_infra.github._models",
    "c": ("flext_core.constants", "FlextConstants"),
    "cli": "flext_infra.github.cli",
    "d": ("flext_core.decorators", "FlextDecorators"),
    "e": ("flext_core.exceptions", "FlextExceptions"),
    "h": ("flext_core.handlers", "FlextHandlers"),
    "m": ("flext_core.models", "FlextModels"),
    "p": ("flext_core.protocols", "FlextProtocols"),
    "r": ("flext_core.result", "FlextResult"),
    "s": ("flext_core.service", "FlextService"),
    "t": ("flext_core.typings", "FlextTypes"),
    "u": ("flext_core.utilities", "FlextUtilities"),
    "x": ("flext_core.mixins", "FlextMixins"),
}

__all__ = [
    "FlextInfraCliGithub",
    "FlextInfraGithubConstants",
    "FlextInfraGithubModels",
    "_constants",
    "_models",
    "c",
    "cli",
    "d",
    "e",
    "h",
    "m",
    "p",
    "r",
    "s",
    "t",
    "u",
    "x",
]


install_lazy_exports(__name__, globals(), _LAZY_IMPORTS)
