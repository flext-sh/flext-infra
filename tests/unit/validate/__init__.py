# AUTO-GENERATED FILE — Regenerate with: make gen
"""Validate package."""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_core.lazy import build_lazy_import_map, install_lazy_exports

if TYPE_CHECKING:
    from flext_infra.tests.unit.validate.main_cli_tests import (
        TestValidateCli as TestValidateCli,
    )
    from flext_infra.tests.unit.validate.namespace_validator_tests import (
        TestFlextInfraNamespaceValidator as TestFlextInfraNamespaceValidator,
    )
_LAZY_IMPORTS = build_lazy_import_map(
    {
        ".basemk_validator_tests": ("basemk_validator_tests",),
        ".fresh_import_tests": ("fresh_import_tests",),
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
        ".pytest_diag_tests": ("pytest_diag_tests",),
        ".scanner_helpers_tests": ("scanner_helpers_tests",),
        ".scanner_tests": ("scanner_tests",),
        ".silent_failure_tests": ("silent_failure_tests",),
        ".skill_validator_tests": ("skill_validator_tests",),
        ".stub_chain_tests": ("stub_chain_tests",),
        ".tier_whitelist_tests": ("tier_whitelist_tests",),
    },
)


install_lazy_exports(
    __name__,
    globals(),
    _LAZY_IMPORTS,
    publish_all=False,
)
