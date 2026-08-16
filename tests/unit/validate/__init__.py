# AUTO-GENERATED FILE — Regenerate with: make gen
"""Tests.unit.validate package."""

from __future__ import annotations

from typing import TYPE_CHECKING

from types import MappingProxyType

from flext_core.lazy import build_lazy_import_map, install_lazy_exports

if TYPE_CHECKING:
    from . import basemk_validator_tests as basemk_validator_tests
    from . import fresh_import_tests as fresh_import_tests
    from . import governance_authority_tests as governance_authority_tests
    from . import import_cycles_tests as import_cycles_tests
    from . import init_tests as init_tests
    from . import inventory_tests as inventory_tests
    from . import lazy_map_freshness_tests as lazy_map_freshness_tests
    from . import loc_delta_tests as loc_delta_tests
    from . import main_tests as main_tests
    from . import manual_command_tests as manual_command_tests
    from . import metadata_discipline_tests as metadata_discipline_tests
    from . import persisted_references_tests as persisted_references_tests
    from . import pytest_diag_tests as pytest_diag_tests
    from . import scanner_helpers_tests as scanner_helpers_tests
    from . import scanner_tests as scanner_tests
    from . import silent_failure_tests as silent_failure_tests
    from . import skill_validator_tests as skill_validator_tests
    from . import stub_chain_tests as stub_chain_tests
    from . import test_import_dag_tests as test_import_dag_tests
    from . import tier_whitelist_tests as tier_whitelist_tests
    from flext_tests import c, d, e, h, m, p, r, s, t, td, tf, tk, tm, tv, u, x

    from .cprofile_report_tests import TestsFlextInfraCProfileReport
    from .main_cli_tests import TestValidateCli
    from .namespace_validator_tests import TestFlextInfraNamespaceValidator
    from .pytest_runner_tests import TestsFlextInfraPytestRunner
    from .pytest_selector_tests import TestsFlextInfraPytestSelectorValidator
    from .testmon_db_tests import TestsFlextInfraTestmonDbInspector
__all__: tuple[str, ...] = (
    "TestFlextInfraNamespaceValidator",
    "TestValidateCli",
    "TestsFlextInfraCProfileReport",
    "TestsFlextInfraPytestRunner",
    "TestsFlextInfraPytestSelectorValidator",
    "TestsFlextInfraTestmonDbInspector",
    "basemk_validator_tests",
    "c",
    "d",
    "e",
    "fresh_import_tests",
    "governance_authority_tests",
    "h",
    "import_cycles_tests",
    "init_tests",
    "inventory_tests",
    "lazy_map_freshness_tests",
    "loc_delta_tests",
    "m",
    "main_tests",
    "manual_command_tests",
    "metadata_discipline_tests",
    "p",
    "persisted_references_tests",
    "pytest_diag_tests",
    "r",
    "s",
    "scanner_helpers_tests",
    "scanner_tests",
    "silent_failure_tests",
    "skill_validator_tests",
    "stub_chain_tests",
    "t",
    "td",
    "test_import_dag_tests",
    "tf",
    "tier_whitelist_tests",
    "tk",
    "tm",
    "tv",
    "u",
    "x",
)

install_lazy_exports(
    __name__,
    globals(),
    MappingProxyType(
        build_lazy_import_map(
            MappingProxyType({
                ".basemk_validator_tests": ("basemk_validator_tests",),
                ".cprofile_report_tests": ("TestsFlextInfraCProfileReport",),
                ".fresh_import_tests": ("fresh_import_tests",),
                ".governance_authority_tests": ("governance_authority_tests",),
                ".import_cycles_tests": ("import_cycles_tests",),
                ".init_tests": ("init_tests",),
                ".inventory_tests": ("inventory_tests",),
                ".lazy_map_freshness_tests": ("lazy_map_freshness_tests",),
                ".loc_delta_tests": ("loc_delta_tests",),
                ".main_cli_tests": ("TestValidateCli",),
                ".main_tests": ("main_tests",),
                ".manual_command_tests": ("manual_command_tests",),
                ".metadata_discipline_tests": ("metadata_discipline_tests",),
                ".namespace_validator_tests": ("TestFlextInfraNamespaceValidator",),
                ".persisted_references_tests": ("persisted_references_tests",),
                ".pytest_diag_tests": ("pytest_diag_tests",),
                ".pytest_runner_tests": ("TestsFlextInfraPytestRunner",),
                ".pytest_selector_tests": ("TestsFlextInfraPytestSelectorValidator",),
                ".scanner_helpers_tests": ("scanner_helpers_tests",),
                ".scanner_tests": ("scanner_tests",),
                ".silent_failure_tests": ("silent_failure_tests",),
                ".skill_validator_tests": ("skill_validator_tests",),
                ".stub_chain_tests": ("stub_chain_tests",),
                ".test_import_dag_tests": ("test_import_dag_tests",),
                ".testmon_db_tests": ("TestsFlextInfraTestmonDbInspector",),
                ".tier_whitelist_tests": ("tier_whitelist_tests",),
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
    ),
    public_exports=__all__,
)
