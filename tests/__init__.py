# AUTO-GENERATED FILE — Regenerate with: make gen
"""Tests package."""

from __future__ import annotations

import typing as _t

from flext_core.lazy import install_lazy_exports

if _t.TYPE_CHECKING:
    from tests.constants import TestsFlextInfraConstants, TestsFlextInfraConstants as c
    from tests.helpers import TestsFlextInfraHelpers
    from tests.models import TestsFlextInfraModels, TestsFlextInfraModels as m
    from tests.protocols import TestsFlextInfraProtocols, TestsFlextInfraProtocols as p
    from tests.typings import TestsFlextInfraTypes, TestsFlextInfraTypes as t
    from tests.utilities import TestsFlextInfraUtilities, TestsFlextInfraUtilities as u

    from flext_core.decorators import FlextDecorators as d
    from flext_core.exceptions import FlextExceptions as e
    from flext_core.handlers import FlextHandlers as h
    from flext_core.mixins import FlextMixins as x
    from flext_core.result import FlextResult as r
    from flext_core.service import FlextService as s
_LAZY_IMPORTS = {
    "TestsFlextInfraConstants": ".constants",
    "TestsFlextInfraHelpers": ".helpers",
    "TestsFlextInfraModels": ".models",
    "TestsFlextInfraProtocols": ".protocols",
    "TestsFlextInfraTypes": ".typings",
    "TestsFlextInfraUtilities": ".utilities",
    "c": (".constants", "TestsFlextInfraConstants"),
    "d": ("flext_core.decorators", "FlextDecorators"),
    "e": ("flext_core.exceptions", "FlextExceptions"),
    "h": ("flext_core.handlers", "FlextHandlers"),
    "m": (".models", "TestsFlextInfraModels"),
    "p": (".protocols", "TestsFlextInfraProtocols"),
    "r": ("flext_core.result", "FlextResult"),
    "s": ("flext_core.service", "FlextService"),
    "t": (".typings", "TestsFlextInfraTypes"),
    "u": (".utilities", "TestsFlextInfraUtilities"),
    "x": ("flext_core.mixins", "FlextMixins"),
}

__all__ = [
    "TestsFlextInfraConstants",
    "TestsFlextInfraHelpers",
    "TestsFlextInfraModels",
    "TestsFlextInfraProtocols",
    "TestsFlextInfraTypes",
    "TestsFlextInfraUtilities",
    "c",
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
