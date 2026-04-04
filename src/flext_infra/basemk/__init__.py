# AUTO-GENERATED FILE — DO NOT EDIT MANUALLY.
# Regenerate with: make gen
#
"""Basemk package."""

from __future__ import annotations

import typing as _t

from flext_core.lazy import install_lazy_exports

if _t.TYPE_CHECKING:
    import flext_infra.basemk._constants as _flext_infra_basemk__constants

    _constants = _flext_infra_basemk__constants
    import flext_infra.basemk.cli as _flext_infra_basemk_cli
    from flext_infra.basemk._constants import FlextInfraBasemkConstants

    cli = _flext_infra_basemk_cli
    import flext_infra.basemk.engine as _flext_infra_basemk_engine
    from flext_infra.basemk.cli import FlextInfraCliBasemk

    engine = _flext_infra_basemk_engine
    import flext_infra.basemk.generator as _flext_infra_basemk_generator
    from flext_infra.basemk.engine import FlextInfraBaseMkTemplateEngine

    generator = _flext_infra_basemk_generator
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
    from flext_infra.basemk.generator import FlextInfraBaseMkGenerator
_LAZY_IMPORTS = {
    "FlextInfraBaseMkGenerator": "flext_infra.basemk.generator",
    "FlextInfraBaseMkTemplateEngine": "flext_infra.basemk.engine",
    "FlextInfraBasemkConstants": "flext_infra.basemk._constants",
    "FlextInfraCliBasemk": "flext_infra.basemk.cli",
    "_constants": "flext_infra.basemk._constants",
    "c": ("flext_core.constants", "FlextConstants"),
    "cli": "flext_infra.basemk.cli",
    "d": ("flext_core.decorators", "FlextDecorators"),
    "e": ("flext_core.exceptions", "FlextExceptions"),
    "engine": "flext_infra.basemk.engine",
    "generator": "flext_infra.basemk.generator",
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
    "FlextInfraBaseMkGenerator",
    "FlextInfraBaseMkTemplateEngine",
    "FlextInfraBasemkConstants",
    "FlextInfraCliBasemk",
    "_constants",
    "c",
    "cli",
    "d",
    "e",
    "engine",
    "generator",
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
