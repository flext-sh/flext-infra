# AUTO-GENERATED FILE — DO NOT EDIT MANUALLY.
# Regenerate with: make gen
#
"""Docs package."""

from __future__ import annotations

import typing as _t

from flext_core.lazy import install_lazy_exports

if _t.TYPE_CHECKING:
    import tests.unit.docs.auditor_budgets_tests as _tests_unit_docs_auditor_budgets_tests

    auditor_budgets_tests = _tests_unit_docs_auditor_budgets_tests
    import tests.unit.docs.auditor_cli_tests as _tests_unit_docs_auditor_cli_tests

    auditor_cli_tests = _tests_unit_docs_auditor_cli_tests
    import tests.unit.docs.auditor_links_tests as _tests_unit_docs_auditor_links_tests

    auditor_links_tests = _tests_unit_docs_auditor_links_tests
    import tests.unit.docs.auditor_scope_tests as _tests_unit_docs_auditor_scope_tests

    auditor_scope_tests = _tests_unit_docs_auditor_scope_tests
    import tests.unit.docs.auditor_tests as _tests_unit_docs_auditor_tests

    auditor_tests = _tests_unit_docs_auditor_tests
    import tests.unit.docs.builder_scope_tests as _tests_unit_docs_builder_scope_tests

    builder_scope_tests = _tests_unit_docs_builder_scope_tests
    import tests.unit.docs.builder_tests as _tests_unit_docs_builder_tests

    builder_tests = _tests_unit_docs_builder_tests
    import tests.unit.docs.fixer_internals_tests as _tests_unit_docs_fixer_internals_tests

    fixer_internals_tests = _tests_unit_docs_fixer_internals_tests
    import tests.unit.docs.fixer_tests as _tests_unit_docs_fixer_tests

    fixer_tests = _tests_unit_docs_fixer_tests
    import tests.unit.docs.generator_internals_tests as _tests_unit_docs_generator_internals_tests

    generator_internals_tests = _tests_unit_docs_generator_internals_tests
    import tests.unit.docs.generator_tests as _tests_unit_docs_generator_tests

    generator_tests = _tests_unit_docs_generator_tests
    import tests.unit.docs.init_tests as _tests_unit_docs_init_tests

    init_tests = _tests_unit_docs_init_tests
    import tests.unit.docs.main_commands_tests as _tests_unit_docs_main_commands_tests

    main_commands_tests = _tests_unit_docs_main_commands_tests
    import tests.unit.docs.main_entry_tests as _tests_unit_docs_main_entry_tests

    main_entry_tests = _tests_unit_docs_main_entry_tests
    import tests.unit.docs.main_tests as _tests_unit_docs_main_tests

    main_tests = _tests_unit_docs_main_tests
    import tests.unit.docs.shared_iter_tests as _tests_unit_docs_shared_iter_tests

    shared_iter_tests = _tests_unit_docs_shared_iter_tests
    import tests.unit.docs.shared_tests as _tests_unit_docs_shared_tests

    shared_tests = _tests_unit_docs_shared_tests
    import tests.unit.docs.shared_write_tests as _tests_unit_docs_shared_write_tests

    shared_write_tests = _tests_unit_docs_shared_write_tests
    import tests.unit.docs.validator_internals_tests as _tests_unit_docs_validator_internals_tests

    validator_internals_tests = _tests_unit_docs_validator_internals_tests
    import tests.unit.docs.validator_tests as _tests_unit_docs_validator_tests

    validator_tests = _tests_unit_docs_validator_tests
    from flext_core.decorators import FlextDecorators as d
    from flext_core.exceptions import FlextExceptions as e
    from flext_core.handlers import FlextHandlers as h
    from flext_core.mixins import FlextMixins as x
    from flext_core.result import FlextResult as r
    from flext_core.service import FlextService as s
_LAZY_IMPORTS = {
    "auditor_budgets_tests": "tests.unit.docs.auditor_budgets_tests",
    "auditor_cli_tests": "tests.unit.docs.auditor_cli_tests",
    "auditor_links_tests": "tests.unit.docs.auditor_links_tests",
    "auditor_scope_tests": "tests.unit.docs.auditor_scope_tests",
    "auditor_tests": "tests.unit.docs.auditor_tests",
    "builder_scope_tests": "tests.unit.docs.builder_scope_tests",
    "builder_tests": "tests.unit.docs.builder_tests",
    "d": ("flext_core.decorators", "FlextDecorators"),
    "e": ("flext_core.exceptions", "FlextExceptions"),
    "fixer_internals_tests": "tests.unit.docs.fixer_internals_tests",
    "fixer_tests": "tests.unit.docs.fixer_tests",
    "generator_internals_tests": "tests.unit.docs.generator_internals_tests",
    "generator_tests": "tests.unit.docs.generator_tests",
    "h": ("flext_core.handlers", "FlextHandlers"),
    "init_tests": "tests.unit.docs.init_tests",
    "main_commands_tests": "tests.unit.docs.main_commands_tests",
    "main_entry_tests": "tests.unit.docs.main_entry_tests",
    "main_tests": "tests.unit.docs.main_tests",
    "r": ("flext_core.result", "FlextResult"),
    "s": ("flext_core.service", "FlextService"),
    "shared_iter_tests": "tests.unit.docs.shared_iter_tests",
    "shared_tests": "tests.unit.docs.shared_tests",
    "shared_write_tests": "tests.unit.docs.shared_write_tests",
    "validator_internals_tests": "tests.unit.docs.validator_internals_tests",
    "validator_tests": "tests.unit.docs.validator_tests",
    "x": ("flext_core.mixins", "FlextMixins"),
}

__all__ = [
    "auditor_budgets_tests",
    "auditor_cli_tests",
    "auditor_links_tests",
    "auditor_scope_tests",
    "auditor_tests",
    "builder_scope_tests",
    "builder_tests",
    "d",
    "e",
    "fixer_internals_tests",
    "fixer_tests",
    "generator_internals_tests",
    "generator_tests",
    "h",
    "init_tests",
    "main_commands_tests",
    "main_entry_tests",
    "main_tests",
    "r",
    "s",
    "shared_iter_tests",
    "shared_tests",
    "shared_write_tests",
    "validator_internals_tests",
    "validator_tests",
    "x",
]


install_lazy_exports(__name__, globals(), _LAZY_IMPORTS)
