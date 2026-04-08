# AUTO-GENERATED FILE — DO NOT EDIT MANUALLY.
# Regenerate with: make gen
#
"""Validate package."""

from __future__ import annotations

import typing as _t

from flext_core.lazy import install_lazy_exports

if _t.TYPE_CHECKING:
    import tests.unit.validate.basemk_validator_tests as _tests_unit_validate_basemk_validator_tests

    basemk_validator_tests = _tests_unit_validate_basemk_validator_tests
    import tests.unit.validate.init_tests as _tests_unit_validate_init_tests

    init_tests = _tests_unit_validate_init_tests
    import tests.unit.validate.inventory_tests as _tests_unit_validate_inventory_tests

    inventory_tests = _tests_unit_validate_inventory_tests
    import tests.unit.validate.main_cli_tests as _tests_unit_validate_main_cli_tests

    main_cli_tests = _tests_unit_validate_main_cli_tests
    import tests.unit.validate.main_tests as _tests_unit_validate_main_tests

    main_tests = _tests_unit_validate_main_tests
    import tests.unit.validate.namespace_validator_tests as _tests_unit_validate_namespace_validator_tests

    namespace_validator_tests = _tests_unit_validate_namespace_validator_tests
    import tests.unit.validate.pytest_diag as _tests_unit_validate_pytest_diag

    pytest_diag = _tests_unit_validate_pytest_diag
    import tests.unit.validate.scanner_tests as _tests_unit_validate_scanner_tests

    scanner_tests = _tests_unit_validate_scanner_tests
    import tests.unit.validate.skill_validator_tests as _tests_unit_validate_skill_validator_tests

    skill_validator_tests = _tests_unit_validate_skill_validator_tests
    import tests.unit.validate.stub_chain_tests as _tests_unit_validate_stub_chain_tests

    stub_chain_tests = _tests_unit_validate_stub_chain_tests
    from flext_core.decorators import FlextDecorators as d
    from flext_core.exceptions import FlextExceptions as e
    from flext_core.handlers import FlextHandlers as h
    from flext_core.mixins import FlextMixins as x
    from flext_core.result import FlextResult as r
    from flext_core.service import FlextService as s
_LAZY_IMPORTS = {
    "basemk_validator_tests": "tests.unit.validate.basemk_validator_tests",
    "d": ("flext_core.decorators", "FlextDecorators"),
    "e": ("flext_core.exceptions", "FlextExceptions"),
    "h": ("flext_core.handlers", "FlextHandlers"),
    "init_tests": "tests.unit.validate.init_tests",
    "inventory_tests": "tests.unit.validate.inventory_tests",
    "main_cli_tests": "tests.unit.validate.main_cli_tests",
    "main_tests": "tests.unit.validate.main_tests",
    "namespace_validator_tests": "tests.unit.validate.namespace_validator_tests",
    "pytest_diag": "tests.unit.validate.pytest_diag",
    "r": ("flext_core.result", "FlextResult"),
    "s": ("flext_core.service", "FlextService"),
    "scanner_tests": "tests.unit.validate.scanner_tests",
    "skill_validator_tests": "tests.unit.validate.skill_validator_tests",
    "stub_chain_tests": "tests.unit.validate.stub_chain_tests",
    "x": ("flext_core.mixins", "FlextMixins"),
}

__all__ = [
    "basemk_validator_tests",
    "d",
    "e",
    "h",
    "init_tests",
    "inventory_tests",
    "main_cli_tests",
    "main_tests",
    "namespace_validator_tests",
    "pytest_diag",
    "r",
    "s",
    "scanner_tests",
    "skill_validator_tests",
    "stub_chain_tests",
    "x",
]


install_lazy_exports(__name__, globals(), _LAZY_IMPORTS)
