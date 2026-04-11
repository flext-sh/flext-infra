# AUTO-GENERATED FILE — Regenerate with: make gen
"""Docs package."""

from __future__ import annotations

from flext_core.lazy import build_lazy_import_map, install_lazy_exports

_LAZY_IMPORTS = build_lazy_import_map(
    {
        ".auditor_budgets_tests": ("auditor_budgets_tests",),
        ".auditor_cli_tests": ("auditor_cli_tests",),
        ".auditor_links_tests": ("auditor_links_tests",),
        ".auditor_scope_tests": ("auditor_scope_tests",),
        ".auditor_tests": ("auditor_tests",),
        ".builder_scope_tests": ("builder_scope_tests",),
        ".builder_tests": ("builder_tests",),
        ".fixer_internals_tests": ("fixer_internals_tests",),
        ".fixer_tests": ("fixer_tests",),
        ".generator_internals_tests": ("generator_internals_tests",),
        ".generator_tests": ("generator_tests",),
        ".main_commands_tests": ("main_commands_tests",),
        ".main_entry_tests": ("main_entry_tests",),
        ".main_tests": ("main_tests",),
        ".shared_iter_tests": ("shared_iter_tests",),
        ".shared_tests": ("shared_tests",),
        ".shared_write_tests": ("shared_write_tests",),
        ".validator_internals_tests": ("validator_internals_tests",),
        ".validator_tests": ("validator_tests",),
    },
)


install_lazy_exports(__name__, globals(), _LAZY_IMPORTS, publish_all=False)
