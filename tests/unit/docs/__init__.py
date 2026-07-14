# AUTO-GENERATED FILE — Regenerate with: make gen
"""Docs package."""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_core.lazy import build_lazy_import_map, install_lazy_exports

# mro-i6nq.10: The package consumes its manifest's public-export contract.
from tests.unit.docs.__unit__ import (
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

    from tests.unit.docs import (
        auditor_cli_tests as auditor_cli_tests,
        auditor_codeblocks_tests as auditor_codeblocks_tests,
        auditor_stale_symbols_tests as auditor_stale_symbols_tests,
        builder_scope_tests as builder_scope_tests,
        fixer_internals_tests as fixer_internals_tests,
        fixer_tests as fixer_tests,
        generator_internals_tests as generator_internals_tests,
        generator_tests as generator_tests,
        main_commands_tests as main_commands_tests,
        main_entry_tests as main_entry_tests,
        main_tests as main_tests,
        shared_tests as shared_tests,
        shared_write_tests as shared_write_tests,
        validator_internals_tests as validator_internals_tests,
        validator_tests as validator_tests,
    )
    from tests.unit.docs.auditor_budgets_tests import (
        TestLoadAuditBudgets as TestLoadAuditBudgets,
    )
    from tests.unit.docs.auditor_docstring_tests import (
        TestsDocstringCoverage as TestsDocstringCoverage,
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
    from tests.unit.docs.render_tests import (
        TestsDocsRenderExcludeDocs as TestsDocsRenderExcludeDocs,
    )
    from tests.unit.docs.server_tests import (
        TestsFlextInfraDocServer as TestsFlextInfraDocServer,
    )
    from tests.unit.docs.shared_iter_tests import (
        TestIterMarkdownFiles as TestIterMarkdownFiles,
        TestSelectedProjectNames as TestSelectedProjectNames,
    )

__all__: tuple[str, ...] = (
    "TestAuditorBrokenLinks",
    "TestAuditorCore",
    "TestAuditorForbiddenTerms",
    "TestAuditorNormalize",
    "TestAuditorScope",
    "TestAuditorToMarkdown",
    "TestBuilderCore",
    "TestIterMarkdownFiles",
    "TestLoadAuditBudgets",
    "TestSelectedProjectNames",
    "TestsDocsCli",
    "TestsDocsRenderExcludeDocs",
    "TestsDocstringCoverage",
    "TestsFlextInfraDocServer",
)
