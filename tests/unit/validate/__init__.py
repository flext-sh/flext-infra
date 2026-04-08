# AUTO-GENERATED FILE — DO NOT EDIT MANUALLY.
# Regenerate with: make gen
#
"""Validate package."""

from __future__ import annotations

from flext_core.lazy import install_lazy_exports

_LAZY_IMPORTS = {
    "basemk_validator_tests": "tests.unit.validate.basemk_validator_tests",
    "c": ("flext_core.constants", "FlextConstants"),
    "d": ("flext_core.decorators", "FlextDecorators"),
    "e": ("flext_core.exceptions", "FlextExceptions"),
    "h": ("flext_core.handlers", "FlextHandlers"),
    "init_tests": "tests.unit.validate.init_tests",
    "inventory_tests": "tests.unit.validate.inventory_tests",
    "m": ("flext_core.models", "FlextModels"),
    "main_cli_tests": "tests.unit.validate.main_cli_tests",
    "main_tests": "tests.unit.validate.main_tests",
    "namespace_validator_tests": "tests.unit.validate.namespace_validator_tests",
    "p": ("flext_core.protocols", "FlextProtocols"),
    "pytest_diag": "tests.unit.validate.pytest_diag",
    "r": ("flext_core.result", "FlextResult"),
    "s": ("flext_core.service", "FlextService"),
    "scanner_tests": "tests.unit.validate.scanner_tests",
    "skill_validator_tests": "tests.unit.validate.skill_validator_tests",
    "stub_chain_tests": "tests.unit.validate.stub_chain_tests",
    "t": ("flext_core.typings", "FlextTypes"),
    "u": ("flext_core.utilities", "FlextUtilities"),
    "x": ("flext_core.mixins", "FlextMixins"),
}


install_lazy_exports(__name__, globals(), _LAZY_IMPORTS, publish_all=False)
