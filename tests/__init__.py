# AUTO-GENERATED FILE — Regenerate with: make gen
"""Tests package."""

from __future__ import annotations

import typing as _t

from flext_core.lazy import build_lazy_import_map, install_lazy_exports

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
_LAZY_IMPORTS = build_lazy_import_map(
    {
        ".constants": ("TestsFlextInfraConstants",),
        ".helpers": ("TestsFlextInfraHelpers",),
        ".models": ("TestsFlextInfraModels",),
        ".protocols": ("TestsFlextInfraProtocols",),
        ".typings": ("TestsFlextInfraTypes",),
        ".utilities": ("TestsFlextInfraUtilities",),
    },
    alias_groups={
        ".constants": (("c", "TestsFlextInfraConstants"),),
        ".models": (("m", "TestsFlextInfraModels"),),
        ".protocols": (("p", "TestsFlextInfraProtocols"),),
        ".typings": (("t", "TestsFlextInfraTypes"),),
        ".utilities": (("u", "TestsFlextInfraUtilities"),),
        "flext_core.decorators": (("d", "FlextDecorators"),),
        "flext_core.exceptions": (("e", "FlextExceptions"),),
        "flext_core.handlers": (("h", "FlextHandlers"),),
        "flext_core.mixins": (("x", "FlextMixins"),),
        "flext_core.result": (("r", "FlextResult"),),
        "flext_core.service": (("s", "FlextService"),),
    },
)

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
