# AUTO-GENERATED FILE — Regenerate with: make gen
"""Tests.unit.docs package."""

from __future__ import annotations

from typing import TYPE_CHECKING

from types import MappingProxyType

from flext_core.lazy import build_lazy_import_map, install_lazy_exports

if TYPE_CHECKING:
    from . import auditor_cli_tests as auditor_cli_tests
    from . import auditor_codeblocks_tests as auditor_codeblocks_tests
    from . import auditor_stale_symbols_tests as auditor_stale_symbols_tests
    from . import builder_scope_tests as builder_scope_tests
    from . import fixer_internals_tests as fixer_internals_tests
    from . import fixer_tests as fixer_tests
    from . import generator_internals_tests as generator_internals_tests
    from . import generator_tests as generator_tests
    from . import main_commands_tests as main_commands_tests
    from . import main_tests as main_tests
    from . import render_guides_index_tests as render_guides_index_tests
    from . import shared_tests as shared_tests
    from . import shared_write_tests as shared_write_tests
    from . import test_docs_update_toc_frontmatter as test_docs_update_toc_frontmatter
    from . import validator_internals_tests as validator_internals_tests
    from . import validator_tests as validator_tests
    from flext_tests import c, d, e, h, m, p, r, s, t, td, tf, tk, tm, tv, u, x

    from .auditor_budgets_tests import TestLoadAuditBudgets
    from .auditor_docstring_tests import TestsDocstringCoverage
    from .auditor_links_tests import (
        TestAuditorBrokenLinks,
        TestAuditorGithubLinks,
        TestAuditorToMarkdown,
    )
    from .auditor_scope_tests import TestAuditorForbiddenTerms, TestAuditorScope
    from .auditor_tests import TestAuditorCore, TestAuditorNormalize
    from .builder_tests import TestBuilderCore
    from .main_entry_tests import TestsDocsCli
    from .render_tests import TestsDocsRenderExcludeDocs
    from .server_tests import TestsFlextInfraDocServer
    from .shared_iter_tests import TestIterMarkdownFiles
__all__: tuple[str, ...] = (
    "TestAuditorBrokenLinks",
    "TestAuditorCore",
    "TestAuditorForbiddenTerms",
    "TestAuditorGithubLinks",
    "TestAuditorNormalize",
    "TestAuditorScope",
    "TestAuditorToMarkdown",
    "TestBuilderCore",
    "TestIterMarkdownFiles",
    "TestLoadAuditBudgets",
    "TestsDocsCli",
    "TestsDocsRenderExcludeDocs",
    "TestsDocstringCoverage",
    "TestsFlextInfraDocServer",
    "auditor_cli_tests",
    "auditor_codeblocks_tests",
    "auditor_stale_symbols_tests",
    "builder_scope_tests",
    "c",
    "d",
    "e",
    "fixer_internals_tests",
    "fixer_tests",
    "generator_internals_tests",
    "generator_tests",
    "h",
    "m",
    "main_commands_tests",
    "main_tests",
    "p",
    "r",
    "render_guides_index_tests",
    "s",
    "shared_tests",
    "shared_write_tests",
    "t",
    "td",
    "test_docs_update_toc_frontmatter",
    "tf",
    "tk",
    "tm",
    "tv",
    "u",
    "validator_internals_tests",
    "validator_tests",
    "x",
)

_LAZY_IMPORTS = MappingProxyType(
    build_lazy_import_map(
        MappingProxyType({
            ".auditor_budgets_tests": ("TestLoadAuditBudgets",),
            ".auditor_cli_tests": ("auditor_cli_tests",),
            ".auditor_codeblocks_tests": ("auditor_codeblocks_tests",),
            ".auditor_docstring_tests": ("TestsDocstringCoverage",),
            ".auditor_links_tests": (
                "TestAuditorBrokenLinks",
                "TestAuditorGithubLinks",
                "TestAuditorToMarkdown",
            ),
            ".auditor_scope_tests": ("TestAuditorForbiddenTerms", "TestAuditorScope"),
            ".auditor_stale_symbols_tests": ("auditor_stale_symbols_tests",),
            ".auditor_tests": ("TestAuditorCore", "TestAuditorNormalize"),
            ".builder_scope_tests": ("builder_scope_tests",),
            ".builder_tests": ("TestBuilderCore",),
            ".fixer_internals_tests": ("fixer_internals_tests",),
            ".fixer_tests": ("fixer_tests",),
            ".generator_internals_tests": ("generator_internals_tests",),
            ".generator_tests": ("generator_tests",),
            ".main_commands_tests": ("main_commands_tests",),
            ".main_entry_tests": ("TestsDocsCli",),
            ".main_tests": ("main_tests",),
            ".render_guides_index_tests": ("render_guides_index_tests",),
            ".render_tests": ("TestsDocsRenderExcludeDocs",),
            ".server_tests": ("TestsFlextInfraDocServer",),
            ".shared_iter_tests": ("TestIterMarkdownFiles",),
            ".shared_tests": ("shared_tests",),
            ".shared_write_tests": ("shared_write_tests",),
            ".test_docs_update_toc_frontmatter": ("test_docs_update_toc_frontmatter",),
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
        }),
        alias_groups=MappingProxyType({}),
        sort_keys=False,
    )
)

install_lazy_exports(__name__, globals(), _LAZY_IMPORTS, public_exports=__all__)
