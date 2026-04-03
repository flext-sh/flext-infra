# AUTO-GENERATED FILE — DO NOT EDIT MANUALLY.
# Regenerate with: make gen
#
"""Basemk package."""

from __future__ import annotations

import typing as _t

from flext_core.constants import FlextConstants as c
from flext_core.decorators import FlextDecorators as d
from flext_core.exceptions import FlextExceptions as e
from flext_core.handlers import FlextHandlers as h
from flext_core.lazy import install_lazy_exports
from flext_core.mixins import FlextMixins as x
from flext_core.models import FlextModels as m
from flext_core.protocols import FlextProtocols as p
from flext_core.result import FlextResult as r
from flext_core.service import FlextService as s
from flext_core.typings import FlextTypes as t
from flext_core.utilities import FlextUtilities as u
from flext_infra.basemk._constants import FlextInfraBasemkConstants
from flext_infra.basemk._models import FlextInfraBasemkModels
from flext_infra.basemk.cli import FlextInfraCliBasemk
from flext_infra.basemk.engine import FlextInfraBaseMkTemplateEngine
from flext_infra.basemk.generator import FlextInfraBaseMkGenerator

if _t.TYPE_CHECKING:
    import flext_infra.basemk._constants as _flext_infra_basemk__constants

    _constants = _flext_infra_basemk__constants
    import flext_infra.basemk._models as _flext_infra_basemk__models

    _models = _flext_infra_basemk__models
    import flext_infra.basemk.cli as _flext_infra_basemk_cli

    cli = _flext_infra_basemk_cli
    import flext_infra.basemk.engine as _flext_infra_basemk_engine

    engine = _flext_infra_basemk_engine
    import flext_infra.basemk.generator as _flext_infra_basemk_generator

    generator = _flext_infra_basemk_generator

    _ = (
        FlextInfraBaseMkGenerator,
        FlextInfraBaseMkTemplateEngine,
        FlextInfraBasemkConstants,
        FlextInfraBasemkModels,
        FlextInfraCliBasemk,
        _constants,
        _models,
        c,
        cli,
        d,
        e,
        engine,
        generator,
        h,
        m,
        p,
        r,
        s,
        t,
        u,
        x,
    )
_LAZY_IMPORTS = {
    "FlextInfraBaseMkGenerator": "flext_infra.basemk.generator",
    "FlextInfraBaseMkTemplateEngine": "flext_infra.basemk.engine",
    "FlextInfraBasemkConstants": "flext_infra.basemk._constants",
    "FlextInfraBasemkModels": "flext_infra.basemk._models",
    "FlextInfraCliBasemk": "flext_infra.basemk.cli",
    "_constants": "flext_infra.basemk._constants",
    "_models": "flext_infra.basemk._models",
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
    "FlextInfraBasemkModels",
    "FlextInfraCliBasemk",
    "_constants",
    "_models",
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
