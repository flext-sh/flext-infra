# AUTO-GENERATED FILE — Regenerate with: make gen
"""Tests.unit.validate package."""

from __future__ import annotations

from typing import TYPE_CHECKING

from types import MappingProxyType

from flext_core.lazy import build_lazy_import_map, install_lazy_exports

if TYPE_CHECKING:
    from flext_tests import c, d, e, h, m, p, r, s, t, td, tf, tk, tm, tv, u, x

    from .cprofile_report_tests import TestsFlextInfraCProfileReport
    from .governance_authority_tests import (
        ROOT,
        test_markdownlint_does_not_suppress_strict_rules,
        test_standalone_governance_never_climbs_to_parent_authority,
    )
    from .main_cli_tests import TestValidateCli
    from .namespace_validator_tests import TestFlextInfraNamespaceValidator
    from .pytest_runner_tests import TestsFlextInfraPytestRunner
    from .pytest_selector_tests import TestsFlextInfraPytestSelectorValidator
    from .testmon_db_tests import TestsFlextInfraTestmonDbInspector
__all__: tuple[str, ...] = (
    "ROOT",
    "TestFlextInfraNamespaceValidator",
    "TestValidateCli",
    "TestsFlextInfraCProfileReport",
    "TestsFlextInfraPytestRunner",
    "TestsFlextInfraPytestSelectorValidator",
    "TestsFlextInfraTestmonDbInspector",
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
    "test_markdownlint_does_not_suppress_strict_rules",
    "test_standalone_governance_never_climbs_to_parent_authority",
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
            ".governance_authority_tests": (
                "ROOT",
                "test_markdownlint_does_not_suppress_strict_rules",
                "test_standalone_governance_never_climbs_to_parent_authority",
            ),
            ".main_cli_tests": ("TestValidateCli",),
            ".namespace_validator_tests": ("TestFlextInfraNamespaceValidator",),
            ".pytest_runner_tests": ("TestsFlextInfraPytestRunner",),
            ".pytest_selector_tests": ("TestsFlextInfraPytestSelectorValidator",),
            ".testmon_db_tests": ("TestsFlextInfraTestmonDbInspector",),
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
