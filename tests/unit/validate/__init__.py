# AUTO-GENERATED FILE — Regenerate with: make gen
"""Tests.unit.validate package."""

from __future__ import annotations

from typing import TYPE_CHECKING

from types import MappingProxyType

from flext_core.lazy import build_lazy_import_map, install_lazy_exports

if TYPE_CHECKING:
    from flext_tests import c, d, e, h, m, p, r, s, t, td, tf, tk, tm, tv, u, x

    from .cprofile_report_tests import TestsFlextInfraCProfileReport
    from .main_cli_tests import TestValidateCli
    from .namespace_validator_tests import TestFlextInfraNamespaceValidator
    from .pytest_runner_tests import TestsFlextInfraPytestRunner
    from .pytest_selector_tests import TestsFlextInfraPytestSelectorValidator
    from .testmon_db_tests import (
        TestsFlextInfraTestmonDbInspector,
        TestsFlextInfraTestmonDbInvalidator,
    )
__all__: tuple[str, ...] = (
    "TestFlextInfraNamespaceValidator",
    "TestValidateCli",
    "TestsFlextInfraCProfileReport",
    "TestsFlextInfraPytestRunner",
    "TestsFlextInfraPytestSelectorValidator",
    "TestsFlextInfraTestmonDbInspector",
    "TestsFlextInfraTestmonDbInvalidator",
    "c",
    "d",
    "e",
    "h",
    "m",
    "p",
    "r",
    "s",
    "t",
    "td",
    "tf",
    "tk",
    "tm",
    "tv",
    "u",
    "x",
)

_LAZY_IMPORTS = MappingProxyType(
    build_lazy_import_map(
        MappingProxyType({
            ".cprofile_report_tests": ("TestsFlextInfraCProfileReport",),
            ".main_cli_tests": ("TestValidateCli",),
            ".namespace_validator_tests": ("TestFlextInfraNamespaceValidator",),
            ".pytest_runner_tests": ("TestsFlextInfraPytestRunner",),
            ".pytest_selector_tests": ("TestsFlextInfraPytestSelectorValidator",),
            ".testmon_db_tests": (
                "TestsFlextInfraTestmonDbInspector",
                "TestsFlextInfraTestmonDbInvalidator",
            ),
            "flext_tests": (
                "c",
                "d",
                "e",
                "h",
                "m",
                "p",
                "r",
                "s",
                "t",
                "td",
                "tf",
                "tk",
                "tm",
                "tv",
                "u",
                "x",
            ),
        }),
        alias_groups=MappingProxyType({}),
        sort_keys=False,
    )
)

install_lazy_exports(__name__, globals(), _LAZY_IMPORTS, public_exports=__all__)
