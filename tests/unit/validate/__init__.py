# AUTO-GENERATED FILE — Regenerate with: make gen
"""Tests.unit.validate package."""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_core.lazy import build_lazy_import_map, install_lazy_exports

# mro-i6nq.10: The package consumes its manifest's public-export contract.
from tests.unit.validate.__unit__ import (
    LAZY_ALIAS_GROUPS as _LAZY_ALIAS_GROUPS,
    LAZY_MODULES as _LAZY_MODULES,
    PUBLIC_EXPORTS as _PUBLIC_EXPORTS,
)

if TYPE_CHECKING:
    from flext_tests import (
        c as c,
        d as d,
        e as e,
        h as h,
        m as m,
        p,
        r as r,
        s as s,
        t as t,
        td as td,
        tf as tf,
        tk as tk,
        tm as tm,
        tv as tv,
        u,
        x as x,
    )

    from tests.unit.validate import (
        basemk_validator_tests as basemk_validator_tests,
        fresh_import_tests as fresh_import_tests,
        import_cycles_tests as import_cycles_tests,
        init_tests as init_tests,
        inventory_tests as inventory_tests,
        lazy_map_freshness_tests as lazy_map_freshness_tests,
        loc_delta_tests as loc_delta_tests,
        main_tests as main_tests,
        manual_command_tests as manual_command_tests,
        metadata_discipline_tests as metadata_discipline_tests,
        pytest_diag_tests as pytest_diag_tests,
        scanner_helpers_tests as scanner_helpers_tests,
        scanner_tests as scanner_tests,
        silent_failure_tests as silent_failure_tests,
        skill_validator_tests as skill_validator_tests,
        stub_chain_tests as stub_chain_tests,
        tier_whitelist_tests as tier_whitelist_tests,
    )
    from tests.unit.validate.main_cli_tests import TestValidateCli as TestValidateCli
    from tests.unit.validate.namespace_validator_tests import (
        TestFlextInfraNamespaceValidator as TestFlextInfraNamespaceValidator,
    )

    # mro-i6nq.10: Static declaration mirrors the installer-owned runtime binding.
    __all__: tuple[str, ...]

_LAZY_IMPORTS = build_lazy_import_map(
    _LAZY_MODULES, alias_groups=_LAZY_ALIAS_GROUPS, sort_keys=False
)

# mro-i6nq.10: The installer publishes __all__ from the manifest's literal ABI.
install_lazy_exports(__name__, globals(), _LAZY_IMPORTS, public_exports=_PUBLIC_EXPORTS)
