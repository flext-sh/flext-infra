# AUTO-GENERATED FILE — Regenerate with: make gen
"""Tests package.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_core.lazy import defer_lazy_instances, install_lazy_exports

if TYPE_CHECKING:
    from flext_tests import td, tf, tk, tm

    from flext_infra import config, d, e, h, infra, r, settings, x
    from tests.base import TestsFlextInfraServiceBase, s
    from tests.constants import TestsFlextInfraConstants, c
    from tests.models import TestsFlextInfraModels, m
    from tests.protocols import TestsFlextInfraProtocols, p
    from tests.typings import TestsFlextInfraTypes, t
    from tests.utilities import TestsFlextInfraUtilities, u


__all__: tuple[str, ...] = (
    "TestsFlextInfraConstants",
    "TestsFlextInfraModels",
    "TestsFlextInfraProtocols",
    "TestsFlextInfraServiceBase",
    "TestsFlextInfraTypes",
    "TestsFlextInfraUtilities",
    "c",
    "config",
    "d",
    "e",
    "h",
    "infra",
    "m",
    "p",
    "r",
    "s",
    "settings",
    "t",
    "td",
    "tf",
    "tk",
    "tm",
    "u",
    "x",
)

install_lazy_exports(
    __name__,
    globals(),
    {
        "TestsFlextInfraConstants": ".constants",
        "TestsFlextInfraModels": ".models",
        "TestsFlextInfraProtocols": ".protocols",
        "TestsFlextInfraServiceBase": ".base",
        "TestsFlextInfraTypes": ".typings",
        "TestsFlextInfraUtilities": ".utilities",
        "c": ".constants",
        "config": "flext_infra",
        "d": "flext_infra",
        "e": "flext_infra",
        "h": "flext_infra",
        "infra": "flext_infra",
        "m": ".models",
        "p": ".protocols",
        "r": "flext_infra",
        "s": ".base",
        "settings": "flext_infra",
        "t": ".typings",
        "td": "flext_tests",
        "tf": "flext_tests",
        "tk": "flext_tests",
        "tm": "flext_tests",
        "u": ".utilities",
        "x": "flext_infra",
    },
    public_exports=__all__,
)

defer_lazy_instances(
    __name__,
    globals(),
    {"config": "flext_infra", "settings": "flext_infra"},
    ("config", "settings"),
)
