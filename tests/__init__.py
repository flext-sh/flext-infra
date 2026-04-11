# AUTO-GENERATED FILE — Regenerate with: make gen
"""Tests package."""

from __future__ import annotations

import typing as _t

from flext_core.lazy import (
    build_lazy_import_map,
    install_lazy_exports,
    merge_lazy_imports,
)

if _t.TYPE_CHECKING:
    from flext_tests import (
        d,
        e,
        h,
        r,
        reset_settings,
        s,
        settings,
        settings_factory,
        td,
        tf,
        tk,
        tm,
        tv,
        x,
    )

    from tests._constants.domain import TestsFlextInfraConstantsDomain
    from tests._constants.fixtures import TestsFlextInfraConstantsFixtures
    from tests.constants import TestsFlextInfraConstants, c
    from tests.models import TestsFlextInfraModels, m
    from tests.protocols import TestsFlextInfraProtocols, p
    from tests.typings import TestsFlextInfraTypes, t
    from tests.unit._utilities.test_discovery_consolidated import (
        TestsFlextInfraUtilitiesDiscoveryConsolidated,
    )
    from tests.unit._utilities.test_formatting import (
        TestsFlextInfraUtilitiesFormattingRunRuffFix,
    )
    from tests.unit._utilities.test_iteration import TestIterWorkspacePythonModules
    from tests.unit._utilities.test_safety import (
        TestSafetyCheckpoint,
        TestSafetyRollback,
    )
    from tests.unit._utilities.test_scanning import TestScanModels
    from tests.utilities import TestsFlextInfraUtilities, u
_LAZY_IMPORTS = merge_lazy_imports(
    (
        "._constants",
        ".integration",
        ".refactor",
        ".unit",
    ),
    build_lazy_import_map(
        {
            ".constants": (
                "TestsFlextInfraConstants",
                "c",
            ),
            ".models": (
                "TestsFlextInfraModels",
                "m",
            ),
            ".protocols": (
                "TestsFlextInfraProtocols",
                "p",
            ),
            ".typings": (
                "TestsFlextInfraTypes",
                "t",
            ),
            ".utilities": (
                "TestsFlextInfraUtilities",
                "u",
            ),
            "flext_tests": (
                "d",
                "e",
                "h",
                "r",
                "reset_settings",
                "s",
                "settings",
                "settings_factory",
                "td",
                "tf",
                "tk",
                "tm",
                "tv",
                "x",
            ),
        },
    ),
    exclude_names=(
        "cleanup_submodule_namespace",
        "install_lazy_exports",
        "lazy_getattr",
        "logger",
        "merge_lazy_imports",
        "output",
        "output_reporting",
    ),
    module_name=__name__,
)


install_lazy_exports(__name__, globals(), _LAZY_IMPORTS)

__all__ = [
    "TestIterWorkspacePythonModules",
    "TestSafetyCheckpoint",
    "TestSafetyRollback",
    "TestScanModels",
    "TestsFlextInfraConstants",
    "TestsFlextInfraConstantsDomain",
    "TestsFlextInfraConstantsFixtures",
    "TestsFlextInfraModels",
    "TestsFlextInfraProtocols",
    "TestsFlextInfraTypes",
    "TestsFlextInfraUtilities",
    "TestsFlextInfraUtilitiesDiscoveryConsolidated",
    "TestsFlextInfraUtilitiesFormattingRunRuffFix",
    "c",
    "d",
    "e",
    "h",
    "m",
    "p",
    "r",
    "reset_settings",
    "s",
    "settings",
    "settings_factory",
    "t",
    "td",
    "tf",
    "tk",
    "tm",
    "tv",
    "u",
    "x",
]
