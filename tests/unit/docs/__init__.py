# AUTO-GENERATED FILE — Regenerate with: make gen
"""Docs package."""

from __future__ import annotations

from .auditor_budgets_tests import TestLoadAuditBudgets as TestLoadAuditBudgets
from .auditor_docstring_tests import TestsDocstringCoverage as TestsDocstringCoverage
from .auditor_links_tests import (
    TestAuditorBrokenLinks as TestAuditorBrokenLinks,
    TestAuditorToMarkdown as TestAuditorToMarkdown,
)
from .auditor_scope_tests import (
    TestAuditorForbiddenTerms as TestAuditorForbiddenTerms,
    TestAuditorScope as TestAuditorScope,
)
from .auditor_tests import (
    TestAuditorCore as TestAuditorCore,
    TestAuditorNormalize as TestAuditorNormalize,
)
from .builder_tests import TestBuilderCore as TestBuilderCore
from .main_entry_tests import TestsDocsCli as TestsDocsCli
from .render_tests import TestsDocsRenderExcludeDocs as TestsDocsRenderExcludeDocs
from .server_tests import TestsFlextInfraDocServer as TestsFlextInfraDocServer
from .shared_iter_tests import (
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
