# AUTO-GENERATED FILE — Regenerate with: make gen
"""Docs package."""

from __future__ import annotations

import typing as _t

from flext_core.lazy import build_lazy_import_map, install_lazy_exports

if _t.TYPE_CHECKING:
    from flext_tests import (
        c as c,
        d as d,
        e as e,
        h as h,
        m as m,
        p as p,
        r as r,
        s as s,
        t as t,
        td as td,
        tf as tf,
        tk as tk,
        tm as tm,
        tv as tv,
        u as u,
        x as x,
    )

    from tests.unit.docs.auditor_budgets_tests import (
        TestLoadAuditBudgets as TestLoadAuditBudgets,
    )
    from tests.unit.docs.auditor_links_tests import (
        TestAuditorBrokenLinks as TestAuditorBrokenLinks,
        TestAuditorToMarkdown as TestAuditorToMarkdown,
    )
    from tests.unit.docs.auditor_scope_tests import (
        TestAuditorForbiddenTerms as TestAuditorForbiddenTerms,
        TestAuditorScope as TestAuditorScope,
    )
    from tests.unit.docs.auditor_tests import (
        TestAuditorCore as TestAuditorCore,
        TestAuditorNormalize as TestAuditorNormalize,
    )
    from tests.unit.docs.builder_tests import TestBuilderCore as TestBuilderCore
    from tests.unit.docs.shared_iter_tests import (
        TestIterMarkdownFiles as TestIterMarkdownFiles,
        TestSelectedProjectNames as TestSelectedProjectNames,
    )
_LAZY_IMPORTS = build_lazy_import_map(
    {
        ".auditor_budgets_tests": ("TestLoadAuditBudgets",),
        ".auditor_cli_tests": ("auditor_cli_tests",),
        ".auditor_codeblocks_tests": ("auditor_codeblocks_tests",),
        ".auditor_links_tests": (
            "TestAuditorBrokenLinks",
            "TestAuditorToMarkdown",
        ),
        ".auditor_scope_tests": (
            "TestAuditorForbiddenTerms",
            "TestAuditorScope",
        ),
        ".auditor_tests": (
            "TestAuditorCore",
            "TestAuditorNormalize",
        ),
        ".builder_scope_tests": ("builder_scope_tests",),
        ".builder_tests": ("TestBuilderCore",),
        ".fixer_internals_tests": ("fixer_internals_tests",),
        ".fixer_tests": ("fixer_tests",),
        ".generator_internals_tests": ("generator_internals_tests",),
        ".generator_tests": ("generator_tests",),
        ".main_commands_tests": ("main_commands_tests",),
        ".main_entry_tests": ("main_entry_tests",),
        ".main_tests": ("main_tests",),
        ".shared_iter_tests": (
            "TestIterMarkdownFiles",
            "TestSelectedProjectNames",
        ),
        ".shared_tests": ("shared_tests",),
        ".shared_write_tests": ("shared_write_tests",),
        ".validator_internals_tests": ("validator_internals_tests",),
        ".validator_tests": ("validator_tests",),
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
    },
)


install_lazy_exports(__name__, globals(), _LAZY_IMPORTS, publish_all=False)
