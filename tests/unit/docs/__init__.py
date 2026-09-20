# AUTO-GENERATED FILE — Regenerate with: make gen
"""Tests.unit.docs package."""

from __future__ import annotations

from types import MappingProxyType
from typing import TYPE_CHECKING

from flext_core.lazy import build_lazy_import_map, install_lazy_exports

if TYPE_CHECKING:
    from flext_tests import c, d, e, h, m, p, r, s, t, td, tf, tk, tm, tv, u, x

    from .auditor_cli_tests import TestsFlextInfraAuditorCli
    from .auditor_codeblocks_tests import TestsFlextInfraAuditorCodeblocks
    from .auditor_command_contract_tests import TestsFlextInfraAuditorCommandContract
    from .auditor_contract_tests import TestsFlextInfraAuditorContract
    from .auditor_docstring_tests import TestsFlextInfraAuditorDocstring
    from .auditor_links_tests import TestsFlextInfraAuditorLinks
    from .auditor_scope_tests import TestsFlextInfraAuditorScope
    from .auditor_stale_symbols_tests import TestsFlextInfraAuditorStaleSymbols
    from .auditor_tests import TestsFlextInfraAuditor
    from .builder_scope_tests import TestsFlextInfraBuilderScope
    from .builder_tests import TestsFlextInfraBuilder
    from .fixer_internals_tests import TestsFlextInfraFixerInternals
    from .fixer_tests import TestsFlextInfraDocsFixer
    from .generator_bundle_tests import TestsFlextInfraDocsGeneratorBundle
    from .generator_guides_tests import TestsFlextInfraDocsGeneratorGuides
    from .generator_internals_tests import TestsFlextInfraDocsGeneratorInternals
    from .generator_plan_tests import TestsFlextInfraDocsGeneratorPlan
    from .generator_tests import TestsFlextInfraDocsGenerator
    from .main_commands_tests import TestsFlextInfraDocsMainCommands
    from .main_entry_tests import TestsFlextInfraDocsMainEntry
    from .main_tests import TestsFlextInfraDocsMain
    from .render_guides_index_tests import TestsFlextInfraDocsRenderGuidesIndex
    from .render_tests import TestsFlextInfraDocsRender
    from .server_tests import TestsFlextInfraDocServer
    from .shared_iter_tests import TestsFlextInfraDocsSharedIter
    from .shared_tests import TestsFlextInfraDocsShared
    from .shared_write_tests import TestsFlextInfraDocsSharedWrite
    from .test_docs_update_toc_frontmatter import (
        TestsFlextInfraDocsUpdateTocFrontmatter,
    )
    from .validator_internals_tests import TestsFlextInfraDocsValidatorInternals
    from .validator_tests import TestsFlextInfraDocsValidator
    from .workspace_manifest_tests import TestsFlextInfraWorkspaceManifest
__all__: tuple[str, ...] = (
    "TestsFlextInfraAuditor", "TestsFlextInfraAuditorCli", "TestsFlextInfraAuditorCodeblocks", "TestsFlextInfraAuditorCommandContract",
    "TestsFlextInfraAuditorContract", "TestsFlextInfraAuditorDocstring", "TestsFlextInfraAuditorLinks", "TestsFlextInfraAuditorScope",
    "TestsFlextInfraAuditorStaleSymbols", "TestsFlextInfraBuilder", "TestsFlextInfraBuilderScope", "TestsFlextInfraDocServer",
    "TestsFlextInfraDocsFixer", "TestsFlextInfraDocsGenerator", "TestsFlextInfraDocsGeneratorBundle", "TestsFlextInfraDocsGeneratorGuides",
    "TestsFlextInfraDocsGeneratorInternals", "TestsFlextInfraDocsGeneratorPlan", "TestsFlextInfraDocsMain", "TestsFlextInfraDocsMainCommands",
    "TestsFlextInfraDocsMainEntry", "TestsFlextInfraDocsRender", "TestsFlextInfraDocsRenderGuidesIndex", "TestsFlextInfraDocsShared",
    "TestsFlextInfraDocsSharedIter", "TestsFlextInfraDocsSharedWrite", "TestsFlextInfraDocsUpdateTocFrontmatter", "TestsFlextInfraDocsValidator",
    "TestsFlextInfraDocsValidatorInternals", "TestsFlextInfraFixerInternals", "TestsFlextInfraWorkspaceManifest", "c",
    "d", "e", "h", "m",
    "p", "r", "s", "t",
    "td", "tf", "tk", "tm",
    "tv", "u", "x",
)

_LAZY_IMPORTS = MappingProxyType(
    build_lazy_import_map(
        MappingProxyType({
            ".auditor_cli_tests": ("TestsFlextInfraAuditorCli",),
            ".auditor_codeblocks_tests": ("TestsFlextInfraAuditorCodeblocks",),
            ".auditor_command_contract_tests": (
                "TestsFlextInfraAuditorCommandContract",
            ),
            ".auditor_contract_tests": ("TestsFlextInfraAuditorContract",),
            ".auditor_docstring_tests": ("TestsFlextInfraAuditorDocstring",),
            ".auditor_links_tests": ("TestsFlextInfraAuditorLinks",),
            ".auditor_scope_tests": ("TestsFlextInfraAuditorScope",),
            ".auditor_stale_symbols_tests": ("TestsFlextInfraAuditorStaleSymbols",),
            ".auditor_tests": ("TestsFlextInfraAuditor",),
            ".builder_scope_tests": ("TestsFlextInfraBuilderScope",),
            ".builder_tests": ("TestsFlextInfraBuilder",),
            ".fixer_internals_tests": ("TestsFlextInfraFixerInternals",),
            ".fixer_tests": ("TestsFlextInfraDocsFixer",),
            ".generator_bundle_tests": ("TestsFlextInfraDocsGeneratorBundle",),
            ".generator_guides_tests": ("TestsFlextInfraDocsGeneratorGuides",),
            ".generator_internals_tests": ("TestsFlextInfraDocsGeneratorInternals",),
            ".generator_plan_tests": ("TestsFlextInfraDocsGeneratorPlan",),
            ".generator_tests": ("TestsFlextInfraDocsGenerator",),
            ".main_commands_tests": ("TestsFlextInfraDocsMainCommands",),
            ".main_entry_tests": ("TestsFlextInfraDocsMainEntry",),
            ".main_tests": ("TestsFlextInfraDocsMain",),
            ".render_guides_index_tests": ("TestsFlextInfraDocsRenderGuidesIndex",),
            ".render_tests": ("TestsFlextInfraDocsRender",),
            ".server_tests": ("TestsFlextInfraDocServer",),
            ".shared_iter_tests": ("TestsFlextInfraDocsSharedIter",),
            ".shared_tests": ("TestsFlextInfraDocsShared",),
            ".shared_write_tests": ("TestsFlextInfraDocsSharedWrite",),
            ".test_docs_update_toc_frontmatter": (
                "TestsFlextInfraDocsUpdateTocFrontmatter",
            ),
            ".validator_internals_tests": ("TestsFlextInfraDocsValidatorInternals",),
            ".validator_tests": ("TestsFlextInfraDocsValidator",),
            ".workspace_manifest_tests": ("TestsFlextInfraWorkspaceManifest",),
            "flext_tests": (
                "c", "d", "e", "h", "m", "p", "r", "s", "t", "td", "tf", "tk", "tm",
                "tv", "u", "x",
            ),
        }),
        alias_groups=MappingProxyType({}),
        sort_keys=False,
    )
)

install_lazy_exports(__name__, globals(), _LAZY_IMPORTS, public_exports=__all__)
